from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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


class RoutingUpdate(BaseModel):
    general_mailbox: str = ""
    teams: Dict[str, str] = {}


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
