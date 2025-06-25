#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re

# Force UTF-8 encoding early
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['LANG'] = 'en_US.UTF-8'

# CRITICAL UNICODE FIX: Sanitize environment variables to remove non-ASCII characters
# that cause 'ascii' codec can't encode character errors in HTTP headers

def sanitize_env_var(key: str) -> str:
    """Remove problematic Unicode characters from environment variables"""
    value = os.environ.get(key, "")
    if not value:
        return value
    
    # Replace problematic Unicode characters that can sneak into API keys/org IDs
    cleaned = value
    cleaned = cleaned.replace("‑", "-")    # non-breaking hyphen (\u2011) to regular hyphen
    cleaned = cleaned.replace("–", "-")    # en dash (\u2013) to hyphen  
    cleaned = cleaned.replace("—", "-")    # em dash (\u2014) to hyphen
    cleaned = cleaned.replace(""", "\"")   # left double quotation mark (\u201c)
    cleaned = cleaned.replace(""", "\"")   # right double quotation mark (\u201d)
    cleaned = cleaned.replace("'", "'")    # left single quotation mark (\u2018)
    cleaned = cleaned.replace("'", "'")    # right single quotation mark (\u2019)
    
    # Strip any remaining non-ASCII characters (keep only 0-127 range)
    cleaned = re.sub(r'[^\x00-\x7F]+', '', cleaned)
    
    # Update environment variable with cleaned value
    os.environ[key] = cleaned
    
    if cleaned != value:
        print(f"⚠️  Cleaned non-ASCII characters from {key}")
    
    return cleaned

# Sanitize critical OpenAI environment variables
sanitize_env_var('OPENAI_API_KEY')
sanitize_env_var('OPENAI_ORGANIZATION')
sanitize_env_var('ELEVENLABS_API_KEY')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
import time
import logging
from dotenv import load_dotenv

# Load environment variables AFTER sanitization
load_dotenv()

# Import voice service
try:
    from voice_service import voice_service
except Exception as e:
    print(f"Voice service unavailable: {e}")
    voice_service = None

# Import main agents with additional header sanitization
try:
    import openai
    from agents import set_tracing_disabled
    
    # Disable tracing to reduce potential Unicode exposure
    set_tracing_disabled(True)
    
    # Additional safeguard: Sanitize OpenAI client configuration
    if hasattr(openai, 'api_key') and openai.api_key:
        openai.api_key = sanitize_env_var('OPENAI_API_KEY')
    if hasattr(openai, 'organization') and openai.organization:
        openai.organization = sanitize_env_var('OPENAI_ORGANIZATION')
    
    # Import ASCII-safe main agents 
    from main_ascii import (
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
    AGENTS_AVAILABLE = True
    print("✅ OpenAI Agents loaded with Unicode sanitization")
except Exception as e:
    print(f"❌ OpenAI Agents not available: {e}")
    AGENTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    enable_voice: Optional[bool] = False

class MessageResponse(BaseModel):
    content: str
    agent: str
    audio_base64: Optional[str] = None

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

# In-memory store
class InMemoryConversationStore:
    _conversations: Dict[str, Dict[str, Any]] = {}

    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._conversations.get(conversation_id)

    def save(self, conversation_id: str, state: Dict[str, Any]):
        self._conversations[conversation_id] = state

conversation_store = InMemoryConversationStore()

# Helpers
def _get_agent_by_name(name: str):
    if not AGENTS_AVAILABLE:
        return None
        
    agents = {
        triage_agent.name: triage_agent,
        general_info_agent.name: general_info_agent,
        inspection_agent.name: inspection_agent,
        landlord_services_agent.name: landlord_services_agent,
        hps_agent.name: hps_agent,
    }
    return agents.get(name, triage_agent)

def _get_guardrail_name(g) -> str:
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
    if not AGENTS_AVAILABLE:
        return [
            {"name": "Triage Agent", "description": "Initial assistance and routing", "handoffs": [], "tools": [], "input_guardrails": []},
            {"name": "General Information Agent", "description": "General housing information", "handoffs": [], "tools": [], "input_guardrails": []},
            {"name": "Inspection Agent", "description": "Housing quality and inspections", "handoffs": [], "tools": [], "input_guardrails": []},
            {"name": "Landlord Services Agent", "description": "Property owner assistance", "handoffs": [], "tools": [], "input_guardrails": []},
            {"name": "HPS Agent", "description": "Housing Choice Voucher Program", "handoffs": [], "tools": [], "input_guardrails": []},
        ]
    
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

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "voice_enabled": voice_service.enabled if voice_service else False,
        "agents": ["Triage", "Inspection", "HPS", "Landlord Services", "General Info"],
        "agents_sdk": AGENTS_AVAILABLE,
        "unicode_sanitized": True,
        "encoding": "utf-8"
    }

# Main Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Real OpenAI Agents with Unicode sanitization to prevent header encoding errors"""
    
    if not AGENTS_AVAILABLE:
        return ChatResponse(
            conversation_id="error",
            current_agent="Error",
            messages=[MessageResponse(content="OpenAI Agents SDK not available", agent="Error")],
            events=[],
            context={},
            agents=[],
            guardrails=[]
        )
    
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
        conversation_id = req.conversation_id
        state = conversation_store.get(conversation_id)

    current_agent = _get_agent_by_name(state["current_agent"])
    state["input_items"].append({"content": req.message, "role": "user"})
    old_context = state["context"].model_dump().copy()
    guardrail_checks: List[GuardrailCheck] = []

    try:
        # Run the real OpenAI Agents with sanitized environment
        result = await Runner.run(current_agent, state["input_items"], context=state["context"])
        logger.info("✅ OpenAI Agents executed successfully")
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
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(f"Chat processing error: {e}")
        
        # If it's still the Unicode error, provide specific feedback
        if "'ascii' codec can't encode character" in str(e):
            return ChatResponse(
                conversation_id=conversation_id,
                current_agent=current_agent.name,
                messages=[MessageResponse(content="I'm still experiencing Unicode encoding issues. Please check that all environment variables contain only ASCII characters.", agent=current_agent.name)],
                events=[],
                context=state["context"].model_dump(),
                agents=_build_agents_list(),
                guardrails=[],
            )
        else:
            return ChatResponse(
                conversation_id=conversation_id,
                current_agent=current_agent.name,
                messages=[MessageResponse(content="I'm experiencing technical difficulties. Please try again.", agent=current_agent.name)],
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
            
            # Generate voice response if requested and available
            audio_base64 = None
            if req.enable_voice and voice_service and voice_service.enabled:
                try:
                    audio_base64 = voice_service.text_to_speech_base64(text, item.agent.name)
                    if audio_base64:
                        logger.info(f"Generated voice response for {item.agent.name}")
                except Exception as e:
                    logger.error(f"Voice generation failed: {e}")
            
            messages.append(MessageResponse(
                content=text,
                agent=item.agent.name,
                audio_base64=audio_base64
            ))
            events.append(AgentEvent(id=uuid4().hex, type="message", agent=item.agent.name, content=text))
        
        elif isinstance(item, HandoffOutputItem):
            events.append(
                AgentEvent(
                    id=uuid4().hex,
                    type="handoff",
                    agent=item.source_agent.name,
                    content=f"{item.source_agent.name} -> {item.target_agent.name}",
                    metadata={"source_agent": item.source_agent.name, "target_agent": item.target_agent.name},
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

    # Build guardrail results
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

# Voice endpoints
@app.get("/voice/info")
async def voice_info():
    if voice_service and voice_service.enabled:
        return voice_service.get_voice_info()
    return {"enabled": False, "reason": "Voice service not available"}

@app.post("/voice/synthesize")
async def synthesize_voice(text: str, agent: str = "Triage Agent"):
    if not voice_service or not voice_service.enabled:
        return {"error": "Voice service not available"}
    
    audio_data = voice_service.text_to_speech_base64(text, agent)
    return {"audio_base64": audio_data}

if __name__ == "__main__":
    import uvicorn
    print("🏠 Housing Authority Assistant - Real AI (Unicode Sanitized)")
    print("=" * 65)
    print(f"Voice Service: {'✅ Enabled' if voice_service and voice_service.enabled else '❌ Disabled'}")
    print(f"OpenAI Agents: {'✅ Available' if AGENTS_AVAILABLE else '❌ Unavailable'}")
    print("Unicode Fix: ✅ Environment variables sanitized")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")
    print("=" * 65)
    
    uvicorn.run(app, host="127.0.0.1", port=8000)