"""
Housing Authority Voice Agent for Twilio Phone Calls

Handles inbound phone calls via Twilio, providing voice-based access to
the housing authority assistant for inspections, HPS appointments, and general inquiries.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CallState(Enum):
    """States for the phone call conversation."""
    WELCOME = "welcome"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    TRANSFERRING = "transferring"
    ENDED = "ended"


class HousingIntent(Enum):
    """Housing-specific intents detected from caller speech."""
    INSPECTION_SCHEDULE = "inspection_schedule"
    INSPECTION_RESCHEDULE = "inspection_reschedule"
    INSPECTION_STATUS = "inspection_status"
    HPS_APPOINTMENT = "hps_appointment"
    LANDLORD_SERVICES = "landlord_services"
    VOUCHER_QUESTION = "voucher_question"
    GENERAL_INFO = "general_info"
    TRANSFER_AGENT = "transfer_agent"
    UNKNOWN = "unknown"


@dataclass
class HousingCallContext:
    """Context maintained throughout a phone call."""
    call_sid: str
    caller_phone: str = ""
    language: str = "english"
    current_state: CallState = CallState.WELCOME
    detected_intent: HousingIntent = HousingIntent.UNKNOWN
    conversation_history: list = field(default_factory=list)
    tenant_code: Optional[str] = None
    inspection_id: Optional[str] = None
    collected_data: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})


class HousingVoiceAgent:
    """
    Voice agent for housing authority phone calls.

    Handles the conversation flow for callers seeking assistance with:
    - HQS inspections (scheduling, rescheduling, status)
    - HPS appointments
    - Landlord services
    - General housing information
    """

    def __init__(self):
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "")

        # Active calls storage (in production, use Redis or similar)
        self._active_calls: Dict[str, HousingCallContext] = {}

        # Welcome messages by language
        self.welcome_messages = {
            "english": (
                "Hello, and welcome to the S-M-C Housing Authority. "
                "I can help you with H-Q-S inspections, "
                "housing program specialist appointments, "
                "landlord services, and general questions. "
                "How can I assist you today?"
            ),
            "spanish": (
                "Hola, bienvenido a la Autoridad de Vivienda de S-M-C. "
                "Puedo ayudarle con inspecciones H-Q-S, "
                "citas con especialistas del programa de vivienda, "
                "servicios para propietarios, y preguntas generales. "
                "Como puedo ayudarle hoy?"
            )
        }

        # Error messages
        self.error_messages = {
            "english": (
                "I apologize, but I'm having trouble processing your request. "
                "Please try again, or press zero to speak with a representative."
            ),
            "spanish": (
                "Lo siento, pero estoy teniendo problemas para procesar su solicitud. "
                "Por favor intente de nuevo, o presione cero para hablar con un representante."
            )
        }

        # Goodbye messages
        self.goodbye_messages = {
            "english": (
                "Thank you for calling S-M-C Housing Authority. "
                "Have a great day!"
            ),
            "spanish": (
                "Gracias por llamar a la Autoridad de Vivienda de S-M-C. "
                "Que tenga un buen dia!"
            )
        }

    def get_or_create_call(self, call_sid: str, caller_phone: str = "") -> HousingCallContext:
        """Get existing call context or create a new one."""
        if call_sid not in self._active_calls:
            self._active_calls[call_sid] = HousingCallContext(
                call_sid=call_sid,
                caller_phone=caller_phone
            )
            logger.info(f"Created new call context for {call_sid}")
        return self._active_calls[call_sid]

    def get_call(self, call_sid: str) -> Optional[HousingCallContext]:
        """Get an existing call context."""
        return self._active_calls.get(call_sid)

    def end_call(self, call_sid: str):
        """Clean up call context when call ends."""
        if call_sid in self._active_calls:
            del self._active_calls[call_sid]
            logger.info(f"Ended call context for {call_sid}")

    def get_welcome_message(self, language: str = "english") -> str:
        """Get the welcome message for the specified language."""
        return self.welcome_messages.get(language, self.welcome_messages["english"])

    def get_error_message(self, language: str = "english") -> str:
        """Get the error message for the specified language."""
        return self.error_messages.get(language, self.error_messages["english"])

    def get_goodbye_message(self, language: str = "english") -> str:
        """Get the goodbye message for the specified language."""
        return self.goodbye_messages.get(language, self.goodbye_messages["english"])

    def detect_intent(self, text: str) -> HousingIntent:
        """
        Detect the caller's intent from their speech.

        In production, this could use a more sophisticated NLU model.
        """
        text_lower = text.lower()

        # Inspection-related intents
        if any(word in text_lower for word in ["inspection", "inspect", "hqs"]):
            if any(word in text_lower for word in ["schedule", "set up", "book", "new"]):
                return HousingIntent.INSPECTION_SCHEDULE
            elif any(word in text_lower for word in ["reschedule", "change", "move", "different"]):
                return HousingIntent.INSPECTION_RESCHEDULE
            elif any(word in text_lower for word in ["status", "when", "date", "check"]):
                return HousingIntent.INSPECTION_STATUS
            return HousingIntent.INSPECTION_STATUS

        # HPS appointment intents
        if any(word in text_lower for word in ["appointment", "hps", "specialist", "caseworker", "case worker"]):
            return HousingIntent.HPS_APPOINTMENT

        # Landlord intents
        if any(word in text_lower for word in ["landlord", "property owner", "owner", "rent", "payment"]):
            return HousingIntent.LANDLORD_SERVICES

        # Voucher questions
        if any(word in text_lower for word in ["voucher", "section 8", "subsidy", "assistance"]):
            return HousingIntent.VOUCHER_QUESTION

        # Transfer to human
        if any(word in text_lower for word in ["agent", "human", "person", "representative", "operator"]):
            return HousingIntent.TRANSFER_AGENT

        # General information or unknown
        if any(word in text_lower for word in ["hours", "address", "location", "contact", "email", "phone"]):
            return HousingIntent.GENERAL_INFO

        return HousingIntent.UNKNOWN

    def detect_language(self, text: str) -> str:
        """
        Detect language from caller's speech.

        Simple heuristic for Spanish vs English.
        """
        spanish_indicators = [
            "hola", "gracias", "por favor", "ayuda", "necesito",
            "inspeccion", "cita", "vivienda", "como", "cuando"
        ]
        text_lower = text.lower()
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)

        return "spanish" if spanish_count >= 2 else "english"

    def extract_tenant_code(self, text: str) -> Optional[str]:
        """Extract tenant code (T-code) from speech."""
        import re
        # Match patterns like "T12345", "T-12345", "T 12345", "t code 12345"
        patterns = [
            r't[\s-]?code[\s-]?(\d{4,6})',
            r't[\s-]?(\d{4,6})',
        ]
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return f"T-{match.group(1)}"
        return None

    async def process_speech(
        self,
        call_sid: str,
        speech_text: str,
        chat_endpoint_callback
    ) -> str:
        """
        Process caller's speech and generate a response.

        Args:
            call_sid: The Twilio call SID
            speech_text: Transcribed speech from caller
            chat_endpoint_callback: Async function to call the main chat endpoint

        Returns:
            Response text to speak to the caller
        """
        context = self.get_call(call_sid)
        if not context:
            return self.get_error_message()

        # Detect language on first real input
        if len(context.conversation_history) == 0:
            context.language = self.detect_language(speech_text)

        # Add user message to history
        context.add_message("user", speech_text)

        # Detect intent
        context.detected_intent = self.detect_intent(speech_text)

        # Extract tenant code if present
        tenant_code = self.extract_tenant_code(speech_text)
        if tenant_code:
            context.tenant_code = tenant_code

        # Handle transfer to human agent
        if context.detected_intent == HousingIntent.TRANSFER_AGENT:
            return (
                "I'll transfer you to a representative now. "
                "Please hold while I connect you."
            )

        try:
            # Call the main chat endpoint
            response = await chat_endpoint_callback(speech_text)

            if response and "messages" in response and len(response["messages"]) > 0:
                assistant_response = response["messages"][0]["content"]
                context.add_message("assistant", assistant_response)
                return assistant_response
            else:
                return self.get_error_message(context.language)

        except Exception as e:
            logger.error(f"Error processing speech: {e}")
            return self.get_error_message(context.language)

    def generate_twiml_gather(
        self,
        prompt: str,
        call_sid: str,
        action_url: str,
        language: str = "english"
    ) -> str:
        """
        Generate TwiML for gathering speech input.

        Returns TwiML XML string.
        """
        voice = "Polly.Joanna" if language == "english" else "Polly.Lupe"
        twiml_language = "en-US" if language == "english" else "es-MX"

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="{action_url}" method="POST" speechTimeout="auto" language="{twiml_language}">
        <Say voice="{voice}">{prompt}</Say>
    </Gather>
    <Say voice="{voice}">I didn't hear anything. Goodbye.</Say>
</Response>"""

    def generate_twiml_say(
        self,
        message: str,
        language: str = "english",
        hangup: bool = False
    ) -> str:
        """
        Generate TwiML for saying a message.

        Returns TwiML XML string.
        """
        voice = "Polly.Joanna" if language == "english" else "Polly.Lupe"

        hangup_tag = "<Hangup/>" if hangup else ""

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{voice}">{message}</Say>
    {hangup_tag}
</Response>"""


# Singleton instance
housing_voice_agent = HousingVoiceAgent()
