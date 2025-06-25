"""
ElevenLabs Voice Integration Service
Provides text-to-speech capabilities with agent-specific characteristics
"""

import os
import base64
import logging
from typing import Optional, Dict, Any
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
import io

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        """Initialize ElevenLabs voice service with API key and voice settings."""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not found. Voice service will be disabled.")
            self.enabled = False
            return
            
        try:
            set_api_key(api_key)
            self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice
            self.enabled = True
            logger.info("ElevenLabs voice service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs: {e}")
            self.enabled = False
    
    def get_agent_voice_settings(self, agent_name: str) -> VoiceSettings:
        """Get voice characteristics specific to each agent type."""
        
        # Agent-specific voice characteristics
        agent_settings = {
            "Triage Agent": {
                "stability": 0.75,
                "similarity_boost": 0.80,
                "style": 0.30,  # Neutral, welcoming
                "use_speaker_boost": True
            },
            "Inspection Agent": {
                "stability": 0.85,
                "similarity_boost": 0.85, 
                "style": 0.20,  # Professional, clear
                "use_speaker_boost": True
            },
            "HPS Agent": {
                "stability": 0.70,
                "similarity_boost": 0.75,
                "style": 0.60,  # Warmer, more empathetic
                "use_speaker_boost": True
            },
            "Landlord Services Agent": {
                "stability": 0.80,
                "similarity_boost": 0.80,
                "style": 0.25,  # Professional, confident
                "use_speaker_boost": True
            },
            "General Information Agent": {
                "stability": 0.75,
                "similarity_boost": 0.78,
                "style": 0.35,  # Friendly, informative
                "use_speaker_boost": True
            }
        }
        
        # Default settings if agent not found
        default_settings = {
            "stability": 0.75,
            "similarity_boost": 0.80,
            "style": 0.30,
            "use_speaker_boost": True
        }
        
        settings = agent_settings.get(agent_name, default_settings)
        
        return VoiceSettings(
            stability=settings["stability"],
            similarity_boost=settings["similarity_boost"],
            style=settings["style"],
            use_speaker_boost=settings["use_speaker_boost"]
        )
    
    def optimize_text_for_speech(self, text: str, agent_name: str) -> str:
        """Optimize text response to sound more natural when spoken."""
        
        # Remove markdown formatting
        text = text.replace("**", "")
        text = text.replace("*", "")
        text = text.replace("#", "")
        
        # Add natural pauses after sentences
        text = text.replace(". ", ". ")
        text = text.replace("? ", "? ")
        text = text.replace("! ", "! ")
        
        # Make numbers more speakable
        text = text.replace("&", "and")
        
        # Agent-specific speech patterns
        if "Inspection" in agent_name:
            # Add clarity markers for inspection agent
            if text.startswith("You"):
                text = f"Let me help you with that. {text}"
            elif "inspection" in text.lower() and not text.startswith("I"):
                text = f"Regarding your inspection, {text.lower()}"
                
        elif "HPS" in agent_name:
            # Add empathy markers for HPS agent
            if "application" in text.lower() or "assistance" in text.lower():
                text = f"I understand this can be complex. {text}"
            elif text.startswith("You need"):
                text = text.replace("You need", "You'll need")
                
        elif "Triage" in agent_name:
            # Add welcoming tone for triage agent
            if not any(greeting in text.lower() for greeting in ["hello", "hi", "welcome"]):
                if "?" in text:
                    text = f"I'd be happy to help you with that. {text}"
        
        # Ensure text isn't too long for voice synthesis
        if len(text) > 500:
            # Split at sentence boundaries
            sentences = text.split(". ")
            if len(sentences) > 1:
                text = ". ".join(sentences[:3]) + "."
                if len(text) < 400:
                    text += " Would you like me to continue with more details?"
        
        return text
    
    def text_to_speech(self, text: str, agent_name: str = "Triage Agent") -> Optional[bytes]:
        """Convert text to speech using ElevenLabs API with agent-specific voice characteristics."""
        
        if not self.enabled:
            logger.warning("Voice service is disabled")
            return None
            
        if not text or not text.strip():
            logger.warning("Empty text provided for speech synthesis")
            return None
        
        try:
            # Optimize text for speech
            speech_text = self.optimize_text_for_speech(text, agent_name)
            
            # Get agent-specific voice settings
            voice_settings = self.get_agent_voice_settings(agent_name)
            
            logger.info(f"Generating speech for {agent_name}: {speech_text[:50]}...")
            
            # Generate speech with ElevenLabs
            audio = generate(
                text=speech_text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=voice_settings
                ),
                model="eleven_monolingual_v1"  # Fast, high-quality English model
            )
            
            # Convert to bytes if needed
            if isinstance(audio, io.BytesIO):
                audio_bytes = audio.getvalue()
            else:
                audio_bytes = audio
            
            logger.info(f"Successfully generated {len(audio_bytes)} bytes of audio")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {e}")
            return None
    
    def text_to_speech_base64(self, text: str, agent_name: str = "Triage Agent") -> Optional[str]:
        """Convert text to speech and return as base64 string for web transmission."""
        
        audio_bytes = self.text_to_speech(text, agent_name)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get information about the current voice configuration."""
        return {
            "enabled": self.enabled,
            "voice_id": self.voice_id if self.enabled else None,
            "supported_agents": [
                "Triage Agent",
                "Inspection Agent", 
                "HPS Agent",
                "Landlord Services Agent",
                "General Information Agent"
            ] if self.enabled else []
        }

# Global voice service instance
voice_service = VoiceService()