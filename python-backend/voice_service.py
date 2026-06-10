"""
Voice Service for Housing Authority Assistant
Provides text-to-speech using ElevenLabs with housing-specific optimizations
"""

import os
import re
import base64
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import elevenlabs, gracefully handle if not available.
# Supports both the modern SDK (>= 1.0, client-based) and the legacy 0.x SDK.
ELEVENLABS_MODE = None
try:
    from elevenlabs.client import ElevenLabs  # SDK >= 1.0
    try:
        from elevenlabs import VoiceSettings  # available in 1.x
    except ImportError:
        VoiceSettings = None
    ELEVENLABS_MODE = "v1"
    ELEVENLABS_AVAILABLE = True
except ImportError:
    try:
        from elevenlabs import generate, Voice, VoiceSettings, set_api_key  # SDK 0.x
        ELEVENLABS_MODE = "v0"
        ELEVENLABS_AVAILABLE = True
    except ImportError:
        ELEVENLABS_AVAILABLE = False
        logger.warning("ElevenLabs not installed. Voice synthesis will be unavailable.")


class HousingVoiceService:
    """Voice service for housing authority assistant with ElevenLabs TTS."""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel

        self._client = None
        if self.api_key and ELEVENLABS_AVAILABLE:
            if ELEVENLABS_MODE == "v1":
                self._client = ElevenLabs(api_key=self.api_key)
            else:
                set_api_key(self.api_key)
            self.enabled = True
            logger.info(f"ElevenLabs voice service initialized (SDK mode: {ELEVENLABS_MODE})")
        else:
            self.enabled = False
            if not self.api_key:
                logger.warning("ELEVENLABS_API_KEY not set - voice synthesis disabled")

        # Cache for common responses
        self._audio_cache: Dict[str, bytes] = {}

        # Agent-specific voice settings
        self.agent_settings = {
            "triage": {
                "stability": 0.71,
                "similarity_boost": 0.5,
                "style": 0.0,
                "intro": ""
            },
            "inspection": {
                "stability": 0.75,  # More stable for clarity
                "similarity_boost": 0.5,
                "style": 0.0,
                "intro": ""
            },
            "hps": {
                "stability": 0.68,  # Slightly warmer
                "similarity_boost": 0.55,
                "style": 0.1,
                "intro": ""
            },
            "landlord": {
                "stability": 0.72,
                "similarity_boost": 0.5,
                "style": 0.0,
                "intro": ""
            },
            "general": {
                "stability": 0.70,
                "similarity_boost": 0.5,
                "style": 0.05,
                "intro": ""
            }
        }

    def text_to_speech(
        self,
        text: str,
        agent_type: str = "triage",
        language: str = "english"
    ) -> Optional[bytes]:
        """
        Convert text to speech audio.

        Args:
            text: The text to synthesize
            agent_type: The agent type (triage, inspection, hps, landlord, general)
            language: The language (english, spanish, mandarin)

        Returns:
            Audio bytes or None if unavailable
        """
        if not self.enabled:
            logger.warning("Voice synthesis not available")
            return None

        try:
            # Optimize text for speech
            optimized_text = self.optimize_for_speech(text, agent_type)

            # Check cache
            cache_key = f"{agent_type}:{language}:{optimized_text}"
            if cache_key in self._audio_cache:
                return self._audio_cache[cache_key]

            # Get agent settings
            settings = self.agent_settings.get(agent_type, self.agent_settings["triage"])

            # Generate audio
            model_id = "eleven_multilingual_v2" if language != "english" else "eleven_monolingual_v1"
            if ELEVENLABS_MODE == "v1":
                voice_settings = None
                if VoiceSettings is not None:
                    voice_settings = VoiceSettings(
                        stability=settings["stability"],
                        similarity_boost=settings["similarity_boost"],
                        style=settings["style"],
                        use_speaker_boost=True,
                    )
                audio = self._client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=optimized_text,
                    model_id=model_id,
                    voice_settings=voice_settings,
                )
            else:
                audio = generate(
                    text=optimized_text,
                    voice=Voice(
                        voice_id=self.voice_id,
                        settings=VoiceSettings(
                            stability=settings["stability"],
                            similarity_boost=settings["similarity_boost"],
                            style=settings["style"],
                            use_speaker_boost=True
                        )
                    ),
                    model=model_id
                )

            # Convert generator to bytes if needed
            if hasattr(audio, '__iter__') and not isinstance(audio, bytes):
                audio = b''.join(audio)

            # Cache the result (limit cache size)
            if len(self._audio_cache) < 100:
                self._audio_cache[cache_key] = audio

            return audio

        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            return None

    def text_to_speech_base64(
        self,
        text: str,
        agent_type: str = "triage",
        language: str = "english"
    ) -> Optional[str]:
        """
        Convert text to speech and return as base64 string.

        Returns:
            Base64 encoded audio string or None
        """
        audio = self.text_to_speech(text, agent_type, language)
        if audio:
            return base64.b64encode(audio).decode('utf-8')
        return None

    def optimize_for_speech(self, text: str, agent_type: str = "triage") -> str:
        """
        Optimize text for natural speech delivery.

        - Expands abbreviations
        - Adds pauses for clarity
        - Spells out codes and numbers
        """
        optimized = text

        # Housing-specific abbreviations
        abbreviations = {
            r'\bHQS\b': 'H-Q-S',
            r'\bHPS\b': 'H-P-S',
            r'\bHUD\b': 'HUD',  # Keep as-is, commonly spoken
            r'\bSMC\b': 'S-M-C',
            r'\bSSN\b': 'Social Security Number',
            r'\bHCV\b': 'Housing Choice Voucher',
            r'\bPBV\b': 'Project Based Voucher',
        }

        for pattern, replacement in abbreviations.items():
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)

        # T-codes: spell out for clarity (T-12345 -> T code 1-2-3-4-5)
        def expand_tcode(match):
            code = match.group(1)
            spelled = '-'.join(code)
            return f"T code {spelled}"

        optimized = re.sub(r'T-?(\d{4,6})', expand_tcode, optimized, flags=re.IGNORECASE)

        # Inspection IDs: spell out (INS-2024-001234 -> Inspection I-D 2024-001234)
        def expand_inspection_id(match):
            year = match.group(1)
            number = match.group(2)
            return f"Inspection I-D {year}-{number}"

        optimized = re.sub(r'INS-(\d{4})-(\d+)', expand_inspection_id, optimized)

        # Phone numbers: add pauses
        def format_phone(match):
            area = match.group(1)
            prefix = match.group(2)
            line = match.group(3)
            return f"{area}, {prefix}, {line}"

        optimized = re.sub(r'\((\d{3})\)\s*(\d{3})-(\d{4})', format_phone, optimized)
        optimized = re.sub(r'(\d{3})-(\d{3})-(\d{4})', format_phone, optimized)

        # Email addresses: spell out @ and .
        optimized = optimized.replace('@', ' at ')
        optimized = re.sub(r'\.(?=com|org|gov|edu)', ' dot ', optimized)

        # Add slight pauses after sentences for clarity
        # (ElevenLabs handles this naturally, but explicit helps)

        # Agent-specific intros (optional)
        settings = self.agent_settings.get(agent_type, {})
        if settings.get("intro"):
            optimized = f"{settings['intro']} {optimized}"

        return optimized

    def get_welcome_message(self, language: str = "english") -> str:
        """Get the welcome message for voice calls."""
        messages = {
            "english": (
                "Hello, and welcome to the S-M-C Housing Authority Assistant. "
                "I can help you with H-Q-S inspections, Housing Program Specialist appointments, "
                "landlord services, and general housing questions. "
                "How can I assist you today?"
            ),
            "spanish": (
                "Hola, bienvenido al Asistente de la Autoridad de Vivienda de S-M-C. "
                "Puedo ayudarle con inspecciones H-Q-S, citas con Especialistas del Programa de Vivienda, "
                "servicios para propietarios, y preguntas generales sobre vivienda. "
                "Como puedo ayudarle hoy?"
            ),
            "mandarin": (
                "Hello, and welcome to the S-M-C Housing Authority Assistant. "
                "I can help you with housing inspections, appointments, "
                "and general housing questions. "
                "How can I assist you today?"
            )
        }
        return messages.get(language, messages["english"])

    def get_goodbye_message(self, language: str = "english") -> str:
        """Get the goodbye message for voice calls."""
        messages = {
            "english": (
                "Thank you for contacting S-M-C Housing Authority. "
                "Have a great day!"
            ),
            "spanish": (
                "Gracias por contactar la Autoridad de Vivienda de S-M-C. "
                "Que tenga un buen dia!"
            ),
            "mandarin": (
                "Thank you for contacting S-M-C Housing Authority. "
                "Have a great day!"
            )
        }
        return messages.get(language, messages["english"])

    def get_error_message(self, language: str = "english") -> str:
        """Get error message for voice calls."""
        messages = {
            "english": (
                "I apologize, but I'm having trouble processing your request. "
                "Please try again, or call our office directly at 6-5-0, 1-2-3, 4-5-6-7."
            ),
            "spanish": (
                "Lo siento, pero estoy teniendo problemas para procesar su solicitud. "
                "Por favor intente de nuevo, o llame a nuestra oficina directamente al 6-5-0, 1-2-3, 4-5-6-7."
            )
        }
        return messages.get(language, messages["english"])

    def clear_cache(self):
        """Clear the audio cache."""
        self._audio_cache.clear()

    def is_enabled(self) -> bool:
        """Check if voice service is enabled."""
        return self.enabled


# Singleton instance
voice_service = HousingVoiceService()
