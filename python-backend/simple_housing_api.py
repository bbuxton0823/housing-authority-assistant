#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
import time
import logging
import os
import sys
from dotenv import load_dotenv

# Force UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Import voice service only
try:
    from voice_service import voice_service
    VOICE_ENABLED = voice_service.enabled
except Exception as e:
    print(f"Voice service unavailable: {e}")
    VOICE_ENABLED = False

# Configure logging
logging.basicConfig(level=logging.INFO, encoding='utf-8')
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

class ChatResponse(BaseModel):
    conversation_id: str
    current_agent: str
    messages: List[MessageResponse]
    events: List[AgentEvent]
    context: Dict[str, Any]
    agents: List[Dict[str, Any]]
    guardrails: List[Dict[str, Any]] = []

# Simple conversation store
conversations: Dict[str, Dict[str, Any]] = {}

# Simple agent responses
def get_agent_response(message: str, agent_name: str = "Triage Agent") -> str:
    """Simple rule-based responses for testing without OpenAI SDK"""
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "help", "start"]):
        return f"""Hello! I'm the {agent_name} from San Mateo County Housing Authority. 

I can help you with:
• Housing Choice Voucher Program (Section 8)
• Public Housing applications and waitlists
• Rental assistance and emergency aid
• Housing inspections and quality standards
• Landlord services and property management
• General housing information and resources

What specific housing assistance do you need today?"""

    elif any(word in message_lower for word in ["voucher", "section 8", "rental assistance"]):
        return """For Housing Choice Voucher Program (Section 8):

• Applications: Currently accepting applications - visit www.smcgov.org/housing
• Waitlist: Check your status online or call (650) 802-3300
• Income limits: Must meet HUD income guidelines for San Mateo County
• Required documents: ID, Social Security cards, income verification, bank statements

Would you like specific information about eligibility, application process, or current availability?"""

    elif any(word in message_lower for word in ["inspection", "housing quality", "repairs"]):
        return """Housing Quality Standards (HQS) Inspections:

• Initial inspections required before voucher approval
• Annual inspections for all assisted units
• Request repairs: Contact your Housing Specialist
• Emergency repairs: Call (650) 802-3300 immediately
• Inspection checklist available at www.smcgov.org/housing

Is this about scheduling an inspection, reporting needed repairs, or understanding inspection requirements?"""

    elif any(word in message_lower for word in ["landlord", "property", "owner"]):
        return """Landlord Services:

• Property registration: Required for all rental units
• Rent reasonableness studies and HAP contracts
• Direct deposit setup for rental payments
• Landlord portal: www.smcgov.org/housing/landlords
• Training workshops available monthly

Are you interested in participating in our voucher program, need help with paperwork, or have questions about payments?"""

    elif any(word in message_lower for word in ["tenant", "landlord", "dispute", "conflict"]):
        return """For tenant-landlord disputes outside HUD scope, I recommend contacting Project Sentinel:

🏠 Project Sentinel - Tenant-Landlord Mediation
📞 Phone: (888) 324-7468
🌐 Website: www.housing.org
📧 Email: info@housing.org

They provide free mediation services for rental disputes, fair housing issues, and tenant rights advocacy.

For HUD-related housing authority matters, I can continue to assist you here."""

    else:
        return f"""Thank you for your question. As the {agent_name}, I'm here to help with San Mateo County Housing Authority services.

If you need immediate assistance:
📞 Phone: (650) 802-3300
📧 Email: customerservice@smchousing.org
🕒 Hours: Monday-Friday, 8:00 AM - 5:00 PM

Could you please clarify what specific housing assistance you need? I can help with vouchers, applications, inspections, or general housing information."""

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "voice_enabled": VOICE_ENABLED,
        "agents": ["Triage", "Inspection", "HPS", "Landlord Services", "General Info"],
        "encoding": "utf-8"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Simple chat endpoint with basic housing responses and voice support"""
    
    # Initialize or retrieve conversation
    conversation_id = req.conversation_id or uuid4().hex
    
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "messages": [],
            "current_agent": "Triage Agent"
        }
    
    conversation = conversations[conversation_id]
    
    # Determine appropriate agent based on message content
    message_lower = req.message.lower()
    if any(word in message_lower for word in ["inspection", "housing quality", "repairs"]):
        current_agent = "Inspection Agent"
    elif any(word in message_lower for word in ["landlord", "property", "owner"]):
        current_agent = "Landlord Services Agent"  
    elif any(word in message_lower for word in ["voucher", "section 8", "hps"]):
        current_agent = "HPS Agent"
    elif any(word in message_lower for word in ["general", "info", "information"]):
        current_agent = "General Information Agent"
    else:
        current_agent = "Triage Agent"
    
    conversation["current_agent"] = current_agent
    
    # Generate response
    response_text = get_agent_response(req.message, current_agent)
    
    # Generate voice if requested
    audio_base64 = None
    if req.enable_voice and VOICE_ENABLED:
        try:
            from voice_service import voice_service
            audio_base64 = voice_service.text_to_speech_base64(response_text, current_agent)
            if audio_base64:
                logger.info(f"Generated voice response for {current_agent}")
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
    
    # Create response
    message_response = MessageResponse(
        content=response_text,
        agent=current_agent,
        audio_base64=audio_base64
    )
    
    # Add to conversation history
    conversation["messages"].append({
        "role": "user",
        "content": req.message
    })
    conversation["messages"].append({
        "role": "assistant", 
        "content": response_text,
        "agent": current_agent
    })
    
    # Build response
    return ChatResponse(
        conversation_id=conversation_id,
        current_agent=current_agent,
        messages=[message_response],
        events=[
            AgentEvent(
                id=uuid4().hex,
                type="message",
                agent=current_agent,
                content=response_text,
                timestamp=time.time()
            )
        ],
        context={
            "conversation_length": len(conversation["messages"]),
            "current_agent": current_agent
        },
        agents=[
            {"name": "Triage Agent", "description": "Initial assistance and routing", "handoffs": ["Inspection Agent", "HPS Agent", "Landlord Services Agent", "General Information Agent"], "tools": [], "input_guardrails": []},
            {"name": "Inspection Agent", "description": "Housing quality and inspections", "handoffs": ["Triage Agent"], "tools": [], "input_guardrails": []},
            {"name": "HPS Agent", "description": "Housing Choice Voucher Program", "handoffs": ["Triage Agent"], "tools": [], "input_guardrails": []},
            {"name": "Landlord Services Agent", "description": "Property owner assistance", "handoffs": ["Triage Agent"], "tools": [], "input_guardrails": []},
            {"name": "General Information Agent", "description": "General housing information", "handoffs": ["Triage Agent"], "tools": [], "input_guardrails": []}
        ],
        guardrails=[]
    )

@app.get("/voice/info")
async def voice_info():
    if VOICE_ENABLED:
        try:
            from voice_service import voice_service
            return voice_service.get_voice_info()
        except:
            pass
    return {"enabled": False, "reason": "Voice service unavailable"}

if __name__ == "__main__":
    import uvicorn
    print("🏠 San Mateo County Housing Authority Assistant")
    print("=" * 50)
    print(f"Voice Service: {'✅ Enabled' if VOICE_ENABLED else '❌ Disabled'}")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")
    print("Encoding: UTF-8")
    print("=" * 50)
    
    uvicorn.run(app, host="127.0.0.1", port=8000)