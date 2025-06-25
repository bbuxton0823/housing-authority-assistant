from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
import time
import logging
import os
import json
import asyncio
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai
import tempfile

# Load environment variables
load_dotenv()

# Import voice and navigation services
from voice_service import voice_service
from playwright_navigation import navigation_service

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

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """Initialize voice and navigation services on startup."""
    await navigation_service.initialize()
    logger.info("Voice and navigation services initialized")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up services on shutdown."""
    await navigation_service.cleanup()
    logger.info("Services cleaned up")

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
    enable_voice: Optional[bool] = False
    enable_navigation: Optional[bool] = False
    user_id: Optional[str] = None

class NavigationCommand(BaseModel):
    type: str  # 'navigate', 'highlight', 'guidance', 'scroll'
    page_key: Optional[str] = None
    selector: Optional[str] = None
    message: Optional[str] = None
    duration: Optional[int] = 5000

class MessageResponse(BaseModel):
    content: str
    agent: str
    audio_base64: Optional[str] = None
    navigation_commands: Optional[List[NavigationCommand]] = None

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

class RecordingMetadata(BaseModel):
    recording_id: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: str
    duration: Optional[float] = None
    file_size: Optional[int] = None
    transcript: Optional[str] = None
    agent_response: Optional[str] = None
    confidence_score: Optional[float] = None
    language: Optional[str] = "en-US"
    file_format: str = "webm"
    
class RecordingResponse(BaseModel):
    recording_id: str
    status: str
    message: str
    metadata: Optional[RecordingMetadata] = None

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
# Recording Storage
# =========================

class RecordingStore:
    def save_recording(self, recording_id: str, audio_data: bytes, metadata: RecordingMetadata) -> bool:
        pass
    
    def get_recording(self, recording_id: str) -> Optional[tuple[bytes, RecordingMetadata]]:
        pass
    
    def list_recordings(self, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> List[RecordingMetadata]:
        pass
    
    def delete_recording(self, recording_id: str) -> bool:
        pass

class FileRecordingStore(RecordingStore):
    def __init__(self, storage_dir: str = "recordings"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_store: Dict[str, RecordingMetadata] = {}
        
    def save_recording(self, recording_id: str, audio_data: bytes, metadata: RecordingMetadata) -> bool:
        try:
            # Save audio file
            file_path = self.storage_dir / f"{recording_id}.{metadata.file_format}"
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            # Update metadata with file size
            metadata.file_size = len(audio_data)
            
            # Save metadata
            self.metadata_store[recording_id] = metadata
            
            # Also save metadata to JSON file for persistence
            metadata_path = self.storage_dir / f"{recording_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata.model_dump(), f, indent=2)
            
            logger.info(f"Saved recording {recording_id} ({len(audio_data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save recording {recording_id}: {e}")
            return False
    
    def get_recording(self, recording_id: str) -> Optional[tuple[bytes, RecordingMetadata]]:
        try:
            metadata = self.metadata_store.get(recording_id)
            if not metadata:
                # Try to load from file
                metadata_path = self.storage_dir / f"{recording_id}.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        data = json.load(f)
                        metadata = RecordingMetadata(**data)
                        self.metadata_store[recording_id] = metadata
                else:
                    return None
            
            file_path = self.storage_dir / f"{recording_id}.{metadata.file_format}"
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    audio_data = f.read()
                return audio_data, metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get recording {recording_id}: {e}")
            return None
    
    def list_recordings(self, conversation_id: Optional[str] = None, user_id: Optional[str] = None) -> List[RecordingMetadata]:
        recordings = []
        
        # Load all metadata files if not in memory
        for metadata_file in self.storage_dir.glob("*.json"):
            recording_id = metadata_file.stem
            if recording_id not in self.metadata_store:
                try:
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                        self.metadata_store[recording_id] = RecordingMetadata(**data)
                except Exception as e:
                    logger.error(f"Failed to load metadata for {recording_id}: {e}")
        
        # Filter recordings
        for metadata in self.metadata_store.values():
            if conversation_id and metadata.conversation_id != conversation_id:
                continue
            if user_id and metadata.user_id != user_id:
                continue
            recordings.append(metadata)
        
        # Sort by timestamp (newest first)
        recordings.sort(key=lambda x: x.timestamp, reverse=True)
        return recordings
    
    def delete_recording(self, recording_id: str) -> bool:
        try:
            metadata = self.metadata_store.get(recording_id)
            if metadata:
                file_path = self.storage_dir / f"{recording_id}.{metadata.file_format}"
                metadata_path = self.storage_dir / f"{recording_id}.json"
                
                if file_path.exists():
                    file_path.unlink()
                if metadata_path.exists():
                    metadata_path.unlink()
                
                del self.metadata_store[recording_id]
                logger.info(f"Deleted recording {recording_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete recording {recording_id}: {e}")
            return False

# Initialize recording store
recording_store = FileRecordingStore()

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

def _generate_navigation_commands(response_text: str, agent_name: str) -> List[NavigationCommand]:
    """Generate navigation commands based on agent response and type."""
    commands = []
    response_lower = response_text.lower()
    
    # Inspection Agent navigation
    if "Inspection" in agent_name:
        if any(word in response_lower for word in ["requirements", "checklist", "need", "documents"]):
            commands.append(NavigationCommand(
                type="navigate",
                page_key="inspection_requirements",
                message="Taking you to the inspection requirements page"
            ))
            commands.append(NavigationCommand(
                type="highlight",
                selector=".requirements-checklist, .inspection-requirements",
                message="Here are the inspection requirements",
                duration=8000
            ))
        elif any(word in response_lower for word in ["schedule", "appointment", "book"]):
            commands.append(NavigationCommand(
                type="navigate", 
                page_key="inspection_scheduling",
                message="Opening the inspection scheduling page"
            ))
            commands.append(NavigationCommand(
                type="guidance",
                selector=".scheduling-form, #schedule-form",
                message="Fill out this form to schedule your inspection",
                duration=10000
            ))
    
    # HPS Agent navigation
    elif "HPS" in agent_name:
        if any(word in response_lower for word in ["apply", "application", "assistance"]):
            commands.append(NavigationCommand(
                type="navigate",
                page_key="application",
                message="Directing you to the housing application page"
            ))
            commands.append(NavigationCommand(
                type="highlight",
                selector=".online-application, #online-app",
                message="You can apply online using this form",
                duration=8000
            ))
    
    # Landlord Services Agent navigation
    elif "Landlord" in agent_name:
        if any(word in response_lower for word in ["payment", "direct deposit", "forms"]):
            commands.append(NavigationCommand(
                type="navigate",
                page_key="landlord_payments", 
                message="Taking you to the landlord payment information"
            ))
            if "direct deposit" in response_lower:
                commands.append(NavigationCommand(
                    type="highlight",
                    selector=".direct-deposit",
                    message="Here's how to set up direct deposit",
                    duration=8000
                ))
    
    # General Info Agent navigation  
    elif "General" in agent_name:
        if any(word in response_lower for word in ["contact", "office hours", "phone"]):
            commands.append(NavigationCommand(
                type="navigate",
                page_key="contact",
                message="Here's our contact information"
            ))
            if "hours" in response_lower:
                commands.append(NavigationCommand(
                    type="highlight",
                    selector=".office-hours",
                    message="These are our current office hours",
                    duration=6000
                ))
    
    # Project Sentinel for tenant-landlord disputes (any agent can trigger this)
    if any(phrase in response_lower for phrase in [
        "tenant rights", "landlord dispute", "eviction", "security deposit", 
        "repairs", "maintenance", "habitability", "discrimination",
        "project sentinel", "mediation", "tenant-landlord"
    ]):
        commands.append(NavigationCommand(
            type="navigate",
            page_key="project_sentinel",
            message="Taking you to Project Sentinel for tenant-landlord dispute resolution"
        ))
        commands.append(NavigationCommand(
            type="guidance",
            selector="main, .content",
            message="Project Sentinel provides free mediation and counseling for tenant-landlord disputes that fall outside of HUD regulations",
            duration=10000
        ))
    
    return commands

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
        return ChatResponse(
            conversation_id=conversation_id,
            current_agent=current_agent.name,
            messages=[MessageResponse(content=refusal, agent=current_agent.name)],
            events=[],
            context=state["context"].model_dump(),
            agents=_build_agents_list(),
            guardrails=guardrail_checks,
        )

    messages: List[MessageResponse] = []
    events: List[AgentEvent] = []

    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            text = ItemHelpers.text_message_output(item)
            
            # Generate voice response if requested
            audio_base64 = None
            if req.enable_voice and voice_service.enabled:
                try:
                    audio_base64 = voice_service.text_to_speech_base64(text, item.agent.name)
                    if audio_base64:
                        logger.info(f"Generated voice response for {item.agent.name}")
                except Exception as e:
                    logger.error(f"Voice generation failed: {e}")
            
            # Generate navigation commands if requested
            navigation_commands = []
            if req.enable_navigation:
                try:
                    nav_commands = _generate_navigation_commands(text, item.agent.name)
                    navigation_commands = nav_commands
                    if nav_commands:
                        logger.info(f"Generated {len(nav_commands)} navigation commands for {item.agent.name}")
                except Exception as e:
                    logger.error(f"Navigation command generation failed: {e}")
            
            messages.append(MessageResponse(
                content=text, 
                agent=item.agent.name,
                audio_base64=audio_base64,
                navigation_commands=navigation_commands
            ))
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
            # If the tool is display_seat_map, send a special message so the UI can render the seat selector.
            if tool_name == "display_seat_map":
                messages.append(
                    MessageResponse(
                        content="DISPLAY_SEAT_MAP",
                        agent=item.agent.name,
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
# Voice and Navigation Endpoints
# =========================

@app.get("/voice/info")
async def voice_info():
    """Get voice service information and status."""
    return voice_service.get_voice_info()

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech audio to text using OpenAI Whisper."""
    try:
        logger.info(f"Received audio file: {audio.filename}, content_type: {audio.content_type}")
        
        # Read audio file
        audio_data = await audio.read()
        logger.info(f"Audio data size: {len(audio_data)} bytes")
        
        if len(audio_data) == 0:
            return {
                "error": "Empty audio file received",
                "success": False,
                "transcript": None
            }
        
        # Use OpenAI Whisper for transcription
        
        # Determine file extension based on content type
        if audio.content_type:
            if 'webm' in audio.content_type:
                suffix = '.webm'
            elif 'mp4' in audio.content_type:
                suffix = '.mp4'
            elif 'wav' in audio.content_type:
                suffix = '.wav'
            else:
                suffix = '.webm'  # Default fallback
        else:
            suffix = '.webm'  # Default fallback
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Read API key directly from file to avoid dotenv issues
            api_key = None
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
                if not api_key:
                    api_key = os.getenv("OPENAI_API_KEY")
            except:
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {
                    "error": "OpenAI API key not configured",
                    "success": False,
                    "transcript": None
                }
            
            logger.info(f"Using OpenAI API key length: {len(api_key)}, starts with: {api_key[:10]}...")
            
            client = openai.OpenAI(api_key=api_key)
            
            # Transcribe using OpenAI Whisper
            with open(temp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            return {
                "transcript": transcript.text,
                "success": True
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Speech-to-text transcription failed: {repr(e)}")
        return {
            "error": "Speech transcription failed",
            "success": False,
            "transcript": None
        }

@app.post("/voice/synthesize")
async def synthesize_voice(
    text: str,
    agent: str = "Triage Agent",
    return_base64: bool = True
):
    """Synthesize text to speech."""
    if not voice_service.enabled:
        return {"error": "Voice service not available"}
    
    if return_base64:
        audio_data = voice_service.text_to_speech_base64(text, agent)
        return {"audio_base64": audio_data}
    else:
        audio_data = voice_service.text_to_speech(text, agent)
        return {"audio_bytes": len(audio_data) if audio_data else 0}

# WebSocket endpoint for real-time navigation
@app.websocket("/ws/navigation/{user_id}")
async def navigation_websocket(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time navigation commands."""
    await websocket.accept()
    logger.info(f"Navigation WebSocket connected for user {user_id}")
    
    try:
        while True:
            # Receive navigation command from frontend
            data = await websocket.receive_text()
            command_data = json.loads(data)
            command_type = command_data.get("type")
            
            logger.info(f"Received navigation command: {command_type} for user {user_id}")
            
            # Execute navigation command
            if command_type == "navigate":
                page_key = command_data.get("page_key")
                result = await navigation_service.navigate_to_page(user_id, page_key)
            
            elif command_type == "highlight":
                selector = command_data.get("selector")
                duration = command_data.get("duration", 5000)
                result = await navigation_service.highlight_element(user_id, selector, duration)
            
            elif command_type == "guidance":
                selector = command_data.get("selector")
                message = command_data.get("message", "Voice assistant guidance")
                duration = command_data.get("duration", 8000)
                result = await navigation_service.show_guidance_overlay(user_id, selector, message, duration)
            
            elif command_type == "get_sections":
                result = await navigation_service.get_page_sections(user_id)
            
            else:
                result = {
                    "success": False,
                    "error": f"Unknown command type: {command_type}"
                }
            
            # Send result back to frontend
            await websocket.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info(f"Navigation WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"Navigation WebSocket error for user {user_id}: {e}")
        await websocket.send_text(json.dumps({
            "success": False,
            "error": str(e),
            "message": "Navigation session ended due to error"
        }))
    finally:
        # Clean up user session
        await navigation_service.close_user_session(user_id)

@app.get("/navigation/pages")
async def get_available_pages():
    """Get list of available pages for navigation."""
    return {
        "pages": list(navigation_service.site_map.keys()),
        "site_map": navigation_service.site_map
    }

# =========================
# Recording Endpoints
# =========================

@app.post("/recordings/save", response_model=RecordingResponse)
async def save_recording(
    audio: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    transcript: Optional[str] = Form(None),
    agent_response: Optional[str] = Form(None),
    duration: Optional[float] = Form(None),
    confidence_score: Optional[float] = Form(None),
    language: str = Form("en-US"),
):
    """Save a voice recording with metadata."""
    try:
        # Generate recording ID
        recording_id = uuid4().hex
        
        # Read audio data
        audio_data = await audio.read()
        
        # Determine file format from content type or filename
        file_format = "webm"  # default
        if audio.content_type:
            if "mp3" in audio.content_type:
                file_format = "mp3"
            elif "wav" in audio.content_type:
                file_format = "wav"
            elif "ogg" in audio.content_type:
                file_format = "ogg"
        elif audio.filename:
            if audio.filename.endswith('.mp3'):
                file_format = "mp3"
            elif audio.filename.endswith('.wav'):
                file_format = "wav"
            elif audio.filename.endswith('.ogg'):
                file_format = "ogg"
        
        # Create metadata
        metadata = RecordingMetadata(
            recording_id=recording_id,
            conversation_id=conversation_id,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            duration=duration,
            file_size=len(audio_data),
            transcript=transcript,
            agent_response=agent_response,
            confidence_score=confidence_score,
            language=language,
            file_format=file_format
        )
        
        # Save recording
        success = recording_store.save_recording(recording_id, audio_data, metadata)
        
        if success:
            return RecordingResponse(
                recording_id=recording_id,
                status="success",
                message="Recording saved successfully",
                metadata=metadata
            )
        else:
            return RecordingResponse(
                recording_id=recording_id,
                status="error",
                message="Failed to save recording"
            )
            
    except Exception as e:
        logger.error(f"Error saving recording: {e}")
        return RecordingResponse(
            recording_id="",
            status="error",
            message=f"Failed to save recording: {str(e)}"
        )

@app.get("/recordings", response_model=List[RecordingMetadata])
async def list_recordings(
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50
):
    """List recordings with optional filtering."""
    try:
        recordings = recording_store.list_recordings(conversation_id, user_id)
        return recordings[:limit]
    except Exception as e:
        logger.error(f"Error listing recordings: {e}")
        return []

@app.get("/recordings/{recording_id}")
async def get_recording(recording_id: str):
    """Get a specific recording and its metadata."""
    try:
        result = recording_store.get_recording(recording_id)
        if result:
            audio_data, metadata = result
            # Return audio as base64 for web consumption
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return {
                "recording_id": recording_id,
                "audio_base64": audio_base64,
                "metadata": metadata.model_dump()
            }
        else:
            return {"error": "Recording not found"}
    except Exception as e:
        logger.error(f"Error getting recording {recording_id}: {e}")
        return {"error": f"Failed to get recording: {str(e)}"}

@app.delete("/recordings/{recording_id}")
async def delete_recording(recording_id: str):
    """Delete a recording."""
    try:
        success = recording_store.delete_recording(recording_id)
        if success:
            return {"status": "success", "message": "Recording deleted"}
        else:
            return {"status": "error", "message": "Recording not found"}
    except Exception as e:
        logger.error(f"Error deleting recording {recording_id}: {e}")
        return {"status": "error", "message": f"Failed to delete recording: {str(e)}"}

@app.get("/recordings/{recording_id}/download")
async def download_recording(recording_id: str):
    """Download a recording file."""
    try:
        result = recording_store.get_recording(recording_id)
        if result:
            audio_data, metadata = result
            from fastapi.responses import Response
            return Response(
                content=audio_data,
                media_type=f"audio/{metadata.file_format}",
                headers={
                    "Content-Disposition": f"attachment; filename={recording_id}.{metadata.file_format}"
                }
            )
        else:
            return {"error": "Recording not found"}
    except Exception as e:
        logger.error(f"Error downloading recording {recording_id}: {e}")
        return {"error": f"Failed to download recording: {str(e)}"}

# =========================
# ElevenLabs Conversational AI Endpoints
# =========================

@app.get("/elevenlabs/signed-url")
async def get_elevenlabs_signed_url(agent_id: str):
    """Get a signed URL for ElevenLabs Conversational AI agent."""
    try:
        import requests
        
        # Get ElevenLabs API key from environment
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if not elevenlabs_api_key:
            return {"error": "ElevenLabs API key not configured"}
        
        # Make request to ElevenLabs API
        url = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"
        headers = {
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        params = {
            "agent_id": agent_id
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return {"error": f"Failed to get signed URL: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error getting ElevenLabs signed URL: {e}")
        return {"error": f"Failed to get signed URL: {str(e)}"}

@app.get("/elevenlabs/config")
async def get_elevenlabs_config():
    """Get ElevenLabs configuration for the frontend."""
    return {
        "has_api_key": bool(os.getenv("ELEVENLABS_API_KEY")),
        "default_agent_id": os.getenv("ELEVENLABS_AGENT_ID"),
        "public_agent": os.getenv("ELEVENLABS_PUBLIC_AGENT", "false").lower() == "true",
    }

class VoiceNavigationRequest(BaseModel):
    message: str
    user_id: str = "voice_user"
    action: str = "navigate"

@app.post("/elevenlabs/navigation")
async def handle_voice_navigation(request: VoiceNavigationRequest):
    """Handle navigation commands triggered by ElevenLabs voice agent."""
    try:
        # Generate navigation commands based on the voice message
        navigation_commands = _generate_navigation_commands(request.message, "Voice Assistant")
        
        if not navigation_commands:
            return {
                "success": False,
                "message": "No navigation action identified in the message"
            }
        
        # Execute the first navigation command
        command = navigation_commands[0]
        result = None
        
        # If no specific page is mentioned, navigate to home page for general housing requests
        if command.type == "navigate" and not command.page_key:
            command.page_key = "home"
        
        if command.type == "navigate" and command.page_key:
            result = await navigation_service.navigate_to_page(request.user_id, command.page_key)
        elif command.type == "highlight" and command.selector:
            result = await navigation_service.highlight_element(
                request.user_id, 
                command.selector, 
                command.duration or 5000
            )
        elif command.type == "guidance" and command.message:
            result = await navigation_service.provide_guidance(request.user_id, command.message)
        elif command.type == "scroll" and command.selector:
            result = await navigation_service.scroll_to_element(request.user_id, command.selector)
        
        if result:
            return {
                "success": True,
                "action": command.type,
                "result": result,
                "message": f"Navigation action '{command.type}' completed"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to execute navigation action: {command.type}"
            }
            
    except Exception as e:
        logger.error(f"Error handling voice navigation: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process navigation request"
        }

@app.post("/elevenlabs/start-session")
async def start_voice_session(user_id: str = "voice_user"):
    """Initialize a voice session by opening the housing authority homepage."""
    try:
        # Navigate to the housing authority home page
        result = await navigation_service.navigate_to_page(user_id, "home")
        
        if result and result.get("success"):
            return {
                "success": True,
                "message": "Voice session started - opened Housing Authority homepage",
                "url": result.get("url"),
                "title": result.get("title")
            }
        else:
            return {
                "success": False,
                "message": "Failed to open homepage",
                "error": result.get("error") if result else "Unknown error"
            }
            
    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start voice session"
        }

# =========================
# ElevenLabs + OpenAI Agent Integration
# =========================

class VoiceAgentRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str = "voice_user"
    enable_voice: bool = True
    enable_navigation: bool = True

@app.post("/voice/agent-chat")
async def voice_agent_chat(request: VoiceAgentRequest):
    """
    Process voice messages through OpenAI agents and return response with appropriate voice.
    This bridges ElevenLabs voice input with OpenAI agent system.
    """
    try:
        # Process message through existing OpenAI agent system
        chat_response = await call_chat_api_internal(
            message=request.message,
            conversation_id=request.conversation_id or "",
            enable_voice=request.enable_voice,
            enable_navigation=request.enable_navigation,
            user_id=request.user_id
        )
        
        if not chat_response:
            return {
                "success": False,
                "error": "Failed to get response from agents",
                "message": "I'm having trouble processing your request right now."
            }
        
        # Extract the agent response and current agent
        current_agent = chat_response.get("current_agent", "Triage Agent")
        messages = chat_response.get("messages", [])
        
        if not messages:
            return {
                "success": False,
                "error": "No response from agents",
                "message": "I don't have a response for that."
            }
        
        # Get the latest assistant message
        agent_message = messages[-1] if messages else None
        response_text = agent_message.get("content", "") if agent_message else ""
        
        # Get appropriate voice for the current agent
        voice_id = get_agent_voice_id(current_agent)
        
        # Synthesize voice response
        voice_response = None
        if request.enable_voice and response_text:
            voice_response = await synthesize_agent_voice(response_text, current_agent, voice_id)
        
        # Process navigation commands if any
        navigation_result = None
        navigation_commands = chat_response.get("navigation_commands", [])
        if request.enable_navigation and navigation_commands:
            # Execute the first navigation command
            command = navigation_commands[0]
            if command.type == "navigate" and command.page_key:
                navigation_result = await navigation_service.navigate_to_page(request.user_id, command.page_key)
        
        return {
            "success": True,
            "conversation_id": chat_response.get("conversation_id"),
            "current_agent": current_agent,
            "message": response_text,
            "audio_base64": voice_response.get("audio_base64") if voice_response else None,
            "voice_id": voice_id,
            "agents": chat_response.get("agents", []),
            "events": chat_response.get("events", []),
            "navigation_result": navigation_result,
            "handoff_occurred": len(chat_response.get("events", [])) > 0  # Check if handoff happened
        }
        
    except Exception as e:
        logger.error(f"Error in voice agent chat: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "I encountered an error processing your request."
        }

def get_agent_voice_id(agent_name: str) -> str:
    """Get the appropriate ElevenLabs voice ID for each agent."""
    agent_voices = {
        "Triage Agent": "21m00Tcm4TlvDq8ikWAM",  # Rachel - warm, professional
        "General Information Agent": "EXAVITQu4vr4xnSDxMaL",  # Natasha - sophisticated  
        "Inspection Agent": "29vD33N1CtxCmqQRPOHJ",  # Daniel - clear, authoritative
        "Landlord Services Agent": "pNInz6obpgDQGcFmaJgB",  # Adam - deep, business-like
        "HPS Agent": "AZnzlk1XvdvUeBnXmlld",  # Bella - friendly, approachable
    }
    return agent_voices.get(agent_name, "21m00Tcm4TlvDq8ikWAM")  # Default to Rachel

async def synthesize_agent_voice(text: str, agent_name: str, voice_id: str) -> Optional[Dict]:
    """Synthesize voice response using agent-specific voice."""
    try:
        # Use existing voice synthesis with specific voice ID
        return await voice_service.synthesize_speech(
            text=text,
            agent=agent_name,
            voice_id=voice_id,
            return_base64=True
        )
    except Exception as e:
        logger.error(f"Error synthesizing voice for {agent_name}: {e}")
        return None

async def call_chat_api_internal(
    message: str,
    conversation_id: str,
    enable_voice: bool = True,
    enable_navigation: bool = True,
    user_id: Optional[str] = None
):
    """
    Internal helper to call the existing chat API logic.
    This reuses your existing OpenAI agent system.
    """
    try:
        # Create a ChatRequest object
        chat_request = ChatRequest(
            conversation_id=conversation_id,
            message=message,
            enable_voice=enable_voice,
            enable_navigation=enable_navigation,
            user_id=user_id
        )
        
        # Process through existing agent system logic
        # This calls the same logic as your /chat endpoint
        return await process_chat_request(chat_request)
        
    except Exception as e:
        logger.error(f"Error in internal chat API call: {e}")
        return None

async def process_chat_request(request: ChatRequest):
    """
    Process chat request through OpenAI agents.
    This extracts the core logic from your existing /chat endpoint.
    """
    try:
        # Initialize conversation if needed
        if not request.conversation_id:
            # Create new conversation
            conversation_id = uuid4().hex
            context = create_initial_context()
            current_agent = "Triage Agent"
            runner = Runner(agent=triage_agent, context=context)
        else:
            # Get existing conversation (implement conversation storage if needed)
            conversation_id = request.conversation_id
            context = {}  # Load from storage
            current_agent = "Triage Agent"  # Load from storage
            runner = Runner(agent=triage_agent, context=context)
        
        # Process message through runner
        messages = []
        events = []
        
        if request.message:
            # Add user message and process
            result = await runner.run(request.message)
            
            # Extract results
            for item in result.items:
                if isinstance(item, MessageOutputItem):
                    voice_data = None
                    if request.enable_voice:
                        voice_data = await voice_service.synthesize_speech(
                            item.content, 
                            item.agent.name,
                            return_base64=True
                        )
                    
                    messages.append({
                        "content": item.content,
                        "agent": item.agent.name,
                        "audio_base64": voice_data.get("audio_base64") if voice_data else None
                    })
                
                elif isinstance(item, HandoffOutputItem):
                    events.append({
                        "id": uuid4().hex,
                        "type": "handoff",
                        "agent": item.agent.name,
                        "content": f"Handed off to {item.target}",
                        "timestamp": time.time(),
                        "metadata": {
                            "source_agent": current_agent,
                            "target_agent": item.target
                        }
                    })
                    current_agent = item.target
        
        # Generate navigation commands
        navigation_commands = []
        if request.enable_navigation and messages:
            last_message = messages[-1]["content"]
            navigation_commands = _generate_navigation_commands(last_message, current_agent)
        
        return {
            "conversation_id": conversation_id,
            "current_agent": current_agent,
            "messages": messages,
            "events": events,
            "navigation_commands": navigation_commands,
            "agents": [
                {"name": "Triage Agent", "description": "Routes inquiries to appropriate specialists"},
                {"name": "General Information Agent", "description": "Provides general housing information"},
                {"name": "Inspection Agent", "description": "Handles inspection-related inquiries"},
                {"name": "Landlord Services Agent", "description": "Assists landlords with property services"},
                {"name": "HPS Agent", "description": "Handles Housing Payment Standards"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return None
