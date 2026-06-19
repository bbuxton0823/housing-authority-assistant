import random

from pydantic import BaseModel


class HousingAuthorityContext(BaseModel):
    """Context for housing authority customer service agents."""

    # Identification
    t_code: str | None = None
    participant_name: str | None = None
    phone_number: str | None = None
    email: str | None = None
    participant_type: str | None = None

    # Language preference
    language: str = "english"

    # Service Context
    unit_address: str | None = None
    inspection_id: str | None = None
    inspection_date: str | None = None
    inspector_name: str | None = None
    door_codes: str | None = None
    reschedule_reason: str | None = None
    requested_reschedule_date: str | None = None

    # Landlord specific
    payment_method: str | None = None
    documentation_pending: bool = False

    # HPS related
    hps_worker_name: str | None = None
    appointment_date: str | None = None
    case_type: str | None = None

    # General
    account_number: str | None = None


def create_initial_context() -> HousingAuthorityContext:
    """
    Factory for a new HousingAuthorityContext.
    For demo: generates a fake account number.
    In production, this should be set from real user data.
    """
    ctx = HousingAuthorityContext()
    ctx.account_number = str(random.randint(10000000, 99999999))
    ctx.language = "english"
    return ctx


def get_multilingual_response(message_key: str, language: str, **kwargs) -> str:
    """Get a response in the specified language."""
    messages = {
        "greeting": {
            "english": "Hello! How can I assist you with housing authority services today?",
            "spanish": "¡Hola! ¿Cómo puedo ayudarle con los servicios de la autoridad de vivienda hoy?",
            "mandarin": "您好！今天我如何为您提供住房管理局服务方面的帮助？",
        },
        "need_tcode": {
            "english": "Could you please provide your T-code or contact information so I can assist you better? Your T-code is printed in the top right-hand corner of any letter the Housing Authority has sent you.",
            "spanish": "¿Podría proporcionar su código T o información de contacto para poder ayudarle mejor? Su código T aparece en la esquina superior derecha de cualquier carta que la Autoridad de Vivienda le haya enviado.",
            "mandarin": "请您提供T代码或联系信息，以便我更好地为您提供帮助？您的T代码印在住房管理局寄给您的任何信件的右上角。",
        },
        "inspection_scheduled": {
            "english": "Your inspection has been scheduled for {date} at {time}.",
            "spanish": "Su inspección ha sido programada para el {date} a las {time}.",
            "mandarin": "您的检查已安排在{date} {time}。",
        },
        "contact_hps": {
            "english": "Please contact your Housing Program Specialist at (555) 123-4567 for assistance.",
            "spanish": "Por favor contacte a su Especialista del Programa de Vivienda al (555) 123-4567 para asistencia.",
            "mandarin": "请致电(555) 123-4567联系您的住房项目专员寻求帮助。",
        },
    }

    if message_key in messages and language in messages[message_key]:
        return messages[message_key][language].format(**kwargs)

    return messages.get(message_key, {}).get("english", "I'm sorry, I don't understand.").format(**kwargs)
