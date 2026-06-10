from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
import time
import logging
import os
import base64
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Apply safe OpenAI fix before any imports
from safe_openai_fix import apply_safe_fix
apply_safe_fix()

# Optional Opik observability (disabled unless OPIK_ENABLE=true and a local
# Opik instance is running -- see https://github.com/comet-ml/opik)
OPIK_ENABLED = False
if os.getenv("OPIK_ENABLE", "").lower() in ("1", "true", "yes"):
    try:
        import opik
        opik.configure(
            url=os.getenv("OPIK_URL", "http://localhost:8080"),
            workspace=os.getenv("OPIK_WORKSPACE", "housing-authority-assistant"),
        )
        OPIK_ENABLED = True
        print("✅ Opik configured successfully")
    except Exception as e:
        print(f"⚠️ Opik configuration failed (continuing without it): {e}")

# Simple monitoring helper
import json
from datetime import datetime

def log_conversation(conversation_id, message, response, agent_name, guardrails_status):
    """Simple local logging for monitoring"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": conversation_id,
        "input": message,
        "output": response,
        "agent": agent_name,
        "guardrails": guardrails_status
    }
    
    with open("conversation_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

from main import (
    triage_agent,
    general_info_agent,
    inspection_agent,
    landlord_services_agent,
    hps_agent,
    create_initial_context,
)

from agents import (
    Runner,
    ItemHelpers,
    MessageOutputItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    InputGuardrailTripwireTriggered,
    Handoff,
)

# Voice service
from voice_service import voice_service

# OpenAI client for Whisper transcription (created lazily so the server
# can still boot in degraded mode when OPENAI_API_KEY is not set)
import openai

def get_openai_client() -> "openai.OpenAI | None":
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return openai.OpenAI(api_key=key) if key else None

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# CORS configuration (adjust as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Models
# =========================

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

class MessageResponse(BaseModel):
    content: str
    agent: str

class AgentEvent(BaseModel):
    id: str
    type: str
    agent: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

class GuardrailCheck(BaseModel):
    id: str
    name: str
    input: str
    reasoning: str
    passed: bool
    timestamp: float

class ChatResponse(BaseModel):
    conversation_id: str
    current_agent: str
    messages: List[MessageResponse]
    events: List[AgentEvent]
    context: Dict[str, Any]
    agents: List[Dict[str, Any]]
    guardrails: List[GuardrailCheck] = []

# =========================
# In-memory store for conversation state
# =========================

class ConversationStore:
    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        pass

    def save(self, conversation_id: str, state: Dict[str, Any]):
        pass

class InMemoryConversationStore(ConversationStore):
    _conversations: Dict[str, Dict[str, Any]] = {}

    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._conversations.get(conversation_id)

    def save(self, conversation_id: str, state: Dict[str, Any]):
        self._conversations[conversation_id] = state

# TODO: when deploying this app in scale, switch to your own production-ready implementation
conversation_store = InMemoryConversationStore()

# =========================
# Helpers
# =========================

def _get_agent_by_name(name: str):
    """Return the agent object by name."""
    agents = {
        triage_agent.name: triage_agent,
        general_info_agent.name: general_info_agent,
        inspection_agent.name: inspection_agent,
        landlord_services_agent.name: landlord_services_agent,
        hps_agent.name: hps_agent,
    }
    return agents.get(name, triage_agent)

def _get_guardrail_name(g) -> str:
    """Extract a friendly guardrail name."""
    name_attr = getattr(g, "name", None)
    if isinstance(name_attr, str) and name_attr:
        return name_attr
    guard_fn = getattr(g, "guardrail_function", None)
    if guard_fn is not None and hasattr(guard_fn, "__name__"):
        return guard_fn.__name__.replace("_", " ").title()
    fn_name = getattr(g, "__name__", None)
    if isinstance(fn_name, str) and fn_name:
        return fn_name.replace("_", " ").title()
    return str(g)

def _build_agents_list() -> List[Dict[str, Any]]:
    """Build a list of all available agents and their metadata."""
    def make_agent_dict(agent):
        return {
            "name": agent.name,
            "description": getattr(agent, "handoff_description", ""),
            "handoffs": [getattr(h, "agent_name", getattr(h, "name", "")) for h in getattr(agent, "handoffs", [])],
            "tools": [getattr(t, "name", getattr(t, "__name__", "")) for t in getattr(agent, "tools", [])],
            "input_guardrails": [_get_guardrail_name(g) for g in getattr(agent, "input_guardrails", [])],
        }
    return [
        make_agent_dict(triage_agent),
        make_agent_dict(general_info_agent),
        make_agent_dict(inspection_agent),
        make_agent_dict(landlord_services_agent),
        make_agent_dict(hps_agent),
    ]

# =========================
# Main Chat Endpoint
# =========================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main chat endpoint for agent orchestration.
    Handles conversation state, agent routing, and guardrail checks.
    """

    # Initialize or retrieve conversation state
    is_new = not req.conversation_id or conversation_store.get(req.conversation_id) is None
    if is_new:
        conversation_id: str = uuid4().hex
        ctx = create_initial_context()
        current_agent_name = triage_agent.name
        state: Dict[str, Any] = {
            "input_items": [],
            "context": ctx,
            "current_agent": current_agent_name,
        }
        if req.message.strip() == "":
            conversation_store.save(conversation_id, state)
            return ChatResponse(
                conversation_id=conversation_id,
                current_agent=current_agent_name,
                messages=[],
                events=[],
                context=ctx.model_dump(),
                agents=_build_agents_list(),
                guardrails=[],
            )
    else:
        conversation_id = req.conversation_id  # type: ignore
        state = conversation_store.get(conversation_id)

    current_agent = _get_agent_by_name(state["current_agent"])
    state["input_items"].append({"content": req.message, "role": "user"})
    old_context = state["context"].model_dump().copy()
    guardrail_checks: List[GuardrailCheck] = []

    try:
        # Check if OpenAI API key is configured
        openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not openai_key:
            logger.warning("OPENAI_API_KEY is not set - returning degraded mode response")
            degraded_response = (
                "The Housing Authority Assistant is currently unavailable due to a configuration issue. "
                "Please try again later or contact us directly:\n\n"
                "Email: customerservice@smchousing.org\n"
                "Phone: (650) 123-4567\n\n"
                "Housing Authority Office Hours:\n"
                "Monday through Friday, 8:00 AM to 5:00 PM\n"
                "Closed weekends and holidays"
            )
            return ChatResponse(
                conversation_id=conversation_id,
                current_agent=current_agent.name,
                messages=[MessageResponse(content=degraded_response, agent=current_agent.name)],
                events=[],
                context=state["context"].model_dump(),
                agents=_build_agents_list(),
                guardrails=[],
            )

        # Execute agent
        result = await Runner.run(current_agent, state["input_items"], context=state["context"])

    except InputGuardrailTripwireTriggered as e:
        failed = e.guardrail_result.guardrail
        gr_output = e.guardrail_result.output.output_info
        gr_reasoning = getattr(gr_output, "reasoning", "")
        gr_input = req.message
        gr_timestamp = time.time() * 1000
        for g in current_agent.input_guardrails:
            guardrail_checks.append(GuardrailCheck(
                id=uuid4().hex,
                name=_get_guardrail_name(g),
                input=gr_input,
                reasoning=(gr_reasoning if g == failed else ""),
                passed=(g != failed),
                timestamp=gr_timestamp,
            ))
        # Check if this is a data privacy guardrail failure (income information)
        if _get_guardrail_name(failed) == "Data Privacy Guardrail":
            refusal = "For your security and privacy, please do not share social security numbers, bank account numbers, credit card information, or other sensitive personal identification through this chat system.\n\nFor sharing sensitive documents or personal identification, please contact your Housing Choice Voucher Program (HPS) specialist or caseworker directly:\n\nEmail: customerservice@smchousing.org\n\nHousing Authority Office Hours:\nMonday through Friday, 8:00 AM to 5:00 PM\nClosed weekends and holidays"
        else:
            refusal = "Sorry, I can only answer questions related to housing authority services.\n\nFor other inquiries, please send a detailed email to customerservice@smchousing.org and an HPS or housing authority specialist will be in contact with you.\n\nHousing Authority Office Hours:\nMonday through Friday, 8:00 AM to 5:00 PM\nClosed weekends and holidays"
        state["input_items"].append({"role": "assistant", "content": refusal})
        
        # Log guardrail failure
        log_conversation(
            conversation_id=conversation_id,
            message=req.message,
            response=refusal,
            agent_name=current_agent.name,
            guardrails_status={"failed": _get_guardrail_name(failed), "passed": []}
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            current_agent=current_agent.name,
            messages=[MessageResponse(content=refusal, agent=current_agent.name)],
            events=[],
            context=state["context"].model_dump(),
            agents=_build_agents_list(),
            guardrails=guardrail_checks,
        )

    except Exception as e:
        # Handle OpenAI API errors and other unexpected errors gracefully
        logger.error(f"Error processing chat request: {e}")
        error_message = str(e).lower()

        if "api key" in error_message or "authentication" in error_message or "401" in error_message:
            error_response = (
                "The Housing Authority Assistant is currently unavailable due to a configuration issue. "
                "Please try again later or contact us directly:\n\n"
                "Email: customerservice@smchousing.org\n"
                "Phone: (650) 123-4567\n\n"
                "Housing Authority Office Hours:\n"
                "Monday through Friday, 8:00 AM to 5:00 PM\n"
                "Closed weekends and holidays"
            )
        else:
            error_response = (
                "I apologize, but I encountered an error processing your request. "
                "Please try again or contact us directly:\n\n"
                "Email: customerservice@smchousing.org\n"
                "Phone: (650) 123-4567\n\n"
                "Housing Authority Office Hours:\n"
                "Monday through Friday, 8:00 AM to 5:00 PM\n"
                "Closed weekends and holidays"
            )

        return ChatResponse(
            conversation_id=conversation_id,
            current_agent=current_agent.name,
            messages=[MessageResponse(content=error_response, agent=current_agent.name)],
            events=[],
            context=state["context"].model_dump(),
            agents=_build_agents_list(),
            guardrails=[],
        )

    messages: List[MessageResponse] = []
    events: List[AgentEvent] = []

    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            messages.append(MessageResponse(content=text, agent=item.agent.name))
            events.append(AgentEvent(id=uuid4().hex, type="message", agent=item.agent.name, content=text))
        # Handle handoff output and agent switching
        elif isinstance(item, HandoffOutputItem):
            # Record the handoff event
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="handoff",
                    agent=item.source_agent.name,
                    content=f"{item.source_agent.name} -> {item.target_agent.name}",
                    metadata={"source_agent": item.source_agent.name, "target_agent": item.target_agent.name},
                )
            )
            # If there is an on_handoff callback defined for this handoff, show it as a tool call
            from_agent = item.source_agent
            to_agent = item.target_agent
            # Find the Handoff object on the source agent matching the target
            ho = next(
                (h for h in getattr(from_agent, "handoffs", [])
                 if isinstance(h, Handoff) and getattr(h, "agent_name", None) == to_agent.name),
                None,
            )
            if ho:
                fn = ho.on_invoke_handoff
                fv = fn.__code__.co_freevars
                cl = fn.__closure__ or []
                if "on_handoff" in fv:
                    idx = fv.index("on_handoff")
                    if idx < len(cl) and cl[idx].cell_contents:
                        cb = cl[idx].cell_contents
                        cb_name = getattr(cb, "__name__", repr(cb))
                        events.append(
                            AgentEvent(
                                id=uuid4().hex,
                                type="tool_call",
                                agent=to_agent.name,
                                content=cb_name,
                            )
                        )
            current_agent = item.target_agent
        elif isinstance(item, ToolCallItem):
            tool_name = getattr(item.raw_item, "name", None)
            raw_args = getattr(item.raw_item, "arguments", None)
            tool_args: Any = raw_args
            if isinstance(raw_args, str):
                try:
                    import json
                    tool_args = json.loads(raw_args)
                except Exception:
                    pass
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="tool_call",
                    agent=item.agent.name,
                    content=tool_name or "",
                    metadata={"tool_args": tool_args},
                )
            )
        elif isinstance(item, ToolCallOutputItem):
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="tool_output",
                    agent=item.agent.name,
                    content=str(item.output),
                    metadata={"tool_result": item.output},
                )
            )

    new_context = state["context"].model_dump()
    changes = {k: new_context[k] for k in new_context if old_context.get(k) != new_context[k]}
    if changes:
        events.append(
            AgentEvent(
                id=uuid4().hex,
                type="context_update",
                agent=current_agent.name,
                content="",
                metadata={"changes": changes},
            )
        )

    state["input_items"] = result.to_input_list()
    state["current_agent"] = current_agent.name
    conversation_store.save(conversation_id, state)

    # Build guardrail results: mark failures (if any), and any others as passed
    final_guardrails: List[GuardrailCheck] = []
    for g in getattr(current_agent, "input_guardrails", []):
        name = _get_guardrail_name(g)
        failed = next((gc for gc in guardrail_checks if gc.name == name), None)
        if failed:
            final_guardrails.append(failed)
        else:
            final_guardrails.append(GuardrailCheck(
                id=uuid4().hex,
                name=name,
                input=req.message,
                reasoning="",
                passed=True,
                timestamp=time.time() * 1000,
            ))

    # Log successful response
    response_content = [msg.content for msg in messages]
    guardrails_passed = [g.name for g in final_guardrails if g.passed]
    guardrails_failed = [g.name for g in final_guardrails if not g.passed]
    
    log_conversation(
        conversation_id=conversation_id,
        message=req.message,
        response=response_content,
        agent_name=current_agent.name,
        guardrails_status={"passed": guardrails_passed, "failed": guardrails_failed}
    )
    
    return ChatResponse(
        conversation_id=conversation_id,
        current_agent=current_agent.name,
        messages=messages,
        events=events,
        context=state["context"].model_dump(),
        agents=_build_agents_list(),
        guardrails=final_guardrails,
    )


# =========================
# Voice Models
# =========================

class VoiceSynthesizeRequest(BaseModel):
    text: str
    agent: str = "triage"
    language: str = "english"

class VoiceSynthesizeResponse(BaseModel):
    audio_base64: Optional[str] = None
    error: Optional[str] = None
    success: bool

class VoiceTranscribeResponse(BaseModel):
    text: str = ""
    language: str = "english"
    error: Optional[str] = None
    success: bool


# =========================
# Voice Endpoints
# =========================

@app.post("/voice/synthesize", response_model=VoiceSynthesizeResponse)
async def voice_synthesize(req: VoiceSynthesizeRequest):
    """
    Convert text to speech using ElevenLabs.
    Returns base64-encoded audio (MP3 format).
    """
    if not voice_service.is_enabled():
        return VoiceSynthesizeResponse(
            audio_base64=None,
            error="Voice synthesis is not available. Check ELEVENLABS_API_KEY configuration.",
            success=False
        )

    try:
        audio_base64 = voice_service.text_to_speech_base64(
            text=req.text,
            agent_type=req.agent,
            language=req.language
        )

        if audio_base64:
            return VoiceSynthesizeResponse(
                audio_base64=audio_base64,
                error=None,
                success=True
            )
        else:
            return VoiceSynthesizeResponse(
                audio_base64=None,
                error="Failed to generate audio",
                success=False
            )
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}")
        return VoiceSynthesizeResponse(
            audio_base64=None,
            error=str(e),
            success=False
        )


@app.post("/voice/transcribe", response_model=VoiceTranscribeResponse)
async def voice_transcribe(
    audio: UploadFile = File(...),
    language: str = Form(default="english")
):
    """
    Transcribe audio to text using OpenAI Whisper.
    Accepts audio file upload (WAV, MP3, M4A, etc.)
    """
    # Check if OpenAI API key is available
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not openai_key:
        return VoiceTranscribeResponse(
            text="",
            language=language,
            error="Transcription is not available. Check OPENAI_API_KEY configuration.",
            success=False
        )

    try:
        # Save uploaded audio to a temp file
        suffix = ".wav"
        if audio.filename:
            if audio.filename.endswith(".mp3"):
                suffix = ".mp3"
            elif audio.filename.endswith(".m4a"):
                suffix = ".m4a"
            elif audio.filename.endswith(".webm"):
                suffix = ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Transcribe with Whisper
            openai_client = get_openai_client()
            with open(tmp_path, "rb") as audio_file:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en" if language == "english" else "es" if language == "spanish" else "zh"
                )

            return VoiceTranscribeResponse(
                text=transcription.text,
                language=language,
                error=None,
                success=True
            )
        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        return VoiceTranscribeResponse(
            text="",
            language=language,
            error=str(e),
            success=False
        )


@app.get("/voice/status")
async def voice_status():
    """Check the status of voice services."""
    return {
        "tts_enabled": voice_service.is_enabled(),
        "stt_enabled": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
        "supported_languages": ["english", "spanish", "mandarin"]
    }


# =========================
# Twilio Voice Webhooks
# =========================

from housing_voice_agent import housing_voice_agent
from fastapi.responses import PlainTextResponse


@app.post("/webhooks/voice/incoming", response_class=PlainTextResponse)
async def twilio_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(default=""),
    To: str = Form(default=""),
):
    """
    Handle incoming Twilio voice calls.
    Returns TwiML to greet the caller and gather speech.
    """
    logger.info(f"Incoming call: {CallSid} from {From}")

    # Create call context
    context = housing_voice_agent.get_or_create_call(CallSid, From)

    # Get welcome message
    welcome = housing_voice_agent.get_welcome_message(context.language)

    # Generate TwiML to gather speech
    webhook_base = os.getenv("WEBHOOK_BASE_URL", "")
    action_url = f"{webhook_base}/webhooks/voice/process/{CallSid}"

    twiml = housing_voice_agent.generate_twiml_gather(
        prompt=welcome,
        call_sid=CallSid,
        action_url=action_url,
        language=context.language
    )

    return PlainTextResponse(content=twiml, media_type="application/xml")


@app.post("/webhooks/voice/process/{call_sid}", response_class=PlainTextResponse)
async def twilio_process_speech(
    call_sid: str,
    SpeechResult: str = Form(default=""),
    Confidence: float = Form(default=0.0),
    CallSid: str = Form(default=""),
):
    """
    Process speech gathered from the caller.
    Calls the main chat endpoint and returns TwiML with the response.
    """
    logger.info(f"Processing speech for {call_sid}: {SpeechResult}")

    context = housing_voice_agent.get_call(call_sid)
    if not context:
        logger.warning(f"No context found for call {call_sid}")
        error_msg = housing_voice_agent.get_error_message()
        return PlainTextResponse(
            content=housing_voice_agent.generate_twiml_say(error_msg, hangup=True),
            media_type="application/xml"
        )

    # Check for hangup keywords
    if SpeechResult.lower() in ["goodbye", "bye", "thank you", "thanks", "adios", "gracias"]:
        goodbye = housing_voice_agent.get_goodbye_message(context.language)
        housing_voice_agent.end_call(call_sid)
        return PlainTextResponse(
            content=housing_voice_agent.generate_twiml_say(goodbye, context.language, hangup=True),
            media_type="application/xml"
        )

    # Process through the main chat endpoint
    async def chat_callback(message: str):
        req = ChatRequest(message=message, conversation_id=f"voice-{call_sid}")
        # We need to call our chat endpoint logic directly
        # This is a simplified version - in production, refactor to share logic
        try:
            response = await chat_endpoint(req)
            return response.model_dump()
        except Exception as e:
            logger.error(f"Chat callback error: {e}")
            return None

    response_text = await housing_voice_agent.process_speech(
        call_sid=call_sid,
        speech_text=SpeechResult,
        chat_endpoint_callback=chat_callback
    )

    # Check if this is a transfer request
    if "transfer" in response_text.lower() and "representative" in response_text.lower():
        # Generate TwiML for transfer (Dial to the office number)
        office_number = os.getenv("HOUSING_OFFICE_PHONE", "+16501234567")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{response_text}</Say>
    <Dial>{office_number}</Dial>
</Response>"""
        return PlainTextResponse(content=twiml, media_type="application/xml")

    # Continue conversation - gather more speech
    webhook_base = os.getenv("WEBHOOK_BASE_URL", "")
    action_url = f"{webhook_base}/webhooks/voice/process/{call_sid}"

    twiml = housing_voice_agent.generate_twiml_gather(
        prompt=response_text,
        call_sid=call_sid,
        action_url=action_url,
        language=context.language
    )

    return PlainTextResponse(content=twiml, media_type="application/xml")


@app.post("/webhooks/voice/status", response_class=PlainTextResponse)
async def twilio_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
):
    """
    Handle Twilio call status callbacks.
    Cleans up call context when call ends.
    """
    logger.info(f"Call status update: {CallSid} -> {CallStatus}")

    if CallStatus in ["completed", "busy", "failed", "no-answer", "canceled"]:
        housing_voice_agent.end_call(CallSid)

    return PlainTextResponse(content="OK", media_type="text/plain")
