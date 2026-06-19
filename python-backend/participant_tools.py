from agents import RunContextWrapper, function_tool

from assistant_config import OFFICE_EMAIL, OFFICE_PHONE
from assistant_context import HousingAuthorityContext
from referrals import TEAMS, normalize_team, submit_referral

@function_tool
async def update_tenant_info(
    context: RunContextWrapper[HousingAuthorityContext], t_code: str, phone_number: str
) -> str:
    """Update tenant contact information."""
    context.context.t_code = t_code
    context.context.phone_number = phone_number

    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Updated contact information for T-code {t_code}. Phone number: {phone_number}",
        "spanish": f"Información de contacto actualizada para código T {t_code}. Número de teléfono: {phone_number}",
        "mandarin": f"已更新T代码{t_code}的联系信息。电话号码：{phone_number}"
    }

    return responses.get(language, responses["english"])

@function_tool(
    name_override="submit_team_referral",
    description_override=(
        "Route the caller's question to the right team for follow-up by email. "
        "Teams: leasing, project_based (PBV), fss (FSS Coordinator), portability, voucher_other, hcd. "
        "REQUIRED before calling: the caller's name AND at least one of email or phone. "
        "If you don't have them yet, ask the caller first. Include a clear summary of their question."
    )
)
async def submit_team_referral(
    context: RunContextWrapper[HousingAuthorityContext],
    team: str,
    question_summary: str,
    name: str = "",
    email: str = "",
    phone: str = "",
    t_code: str = "",
) -> str:
    """Validate required contact info and route a referral email to the appropriate team."""
    language = getattr(context.context, 'language', 'english')

    # Fall back to anything already collected in this conversation
    name = (name or getattr(context.context, 'participant_name', None) or "").strip()
    t_code = (t_code or getattr(context.context, 't_code', None) or "").strip()
    if t_code:
        context.context.t_code = t_code
    email = (email or getattr(context.context, 'email', None) or "").strip()
    phone = (phone or getattr(context.context, 'phone_number', None) or "").strip()

    team_key = normalize_team(team)
    if not team_key:
        valid = ", ".join(TEAMS)
        return f"Unknown team '{team}'. Valid teams: {valid}. Pick the closest match and call this tool again."

    # Enforce: name + (email or phone)
    missing = []
    if not name:
        missing.append({"english": "full name", "spanish": "nombre completo", "mandarin": "全名"}[language if language in ("english","spanish","mandarin") else "english"])
    if not email and not phone:
        missing.append({"english": "an email address or phone number", "spanish": "un correo electrónico o número de teléfono", "mandarin": "电子邮箱或电话号码"}[language if language in ("english","spanish","mandarin") else "english"])
    if missing:
        needs = " + ".join(missing)
        prompts = {
            "english": f"MISSING REQUIRED INFO - do not submit yet. Ask the caller for: {needs}. Then call this tool again with the complete information.",
            "spanish": f"FALTA INFORMACIÓN REQUERIDA - no envíe todavía. Pida a la persona: {needs}. Luego llame a esta herramienta de nuevo con la información completa.",
            "mandarin": f"缺少必填信息 - 请勿提交。请向来电者询问：{needs}。然后用完整信息再次调用此工具。",
        }
        return prompts.get(language, prompts["english"])

    # Store contact info in context for the agent panel
    context.context.participant_name = name
    if email:
        context.context.email = email
    if phone:
        context.context.phone_number = phone

    delivered, status = submit_referral(
        team_key,
        name=name,
        email=email,
        phone=phone,
        question=question_summary,
        t_code=t_code,
        language=language,
        conversation_id=getattr(context.context, 'account_number', None) or "",
    )

    team_name = TEAMS[team_key][0]
    responses = {
        "english": (
            f"Your question has been routed to the {team_name}:\n\n"
            f"\u2022 Name: {name}\n"
            + (f"\u2022 Email: {email}\n" if email else "")
            + (f"\u2022 Phone: {phone}\n" if phone else "")
            + f"\u2022 Request: {question_summary}\n\n"
            f"Someone from the {team_name} will follow up with you, typically within 2 business days. "
            f"If it's urgent, call {OFFICE_PHONE} (Monday-Friday, 8:00 AM - 5:00 PM)."
        ),
        "spanish": (
            f"Su pregunta ha sido enviada al equipo: {team_name}:\n\n"
            f"\u2022 Nombre: {name}\n"
            + (f"\u2022 Correo: {email}\n" if email else "")
            + (f"\u2022 Teléfono: {phone}\n" if phone else "")
            + f"\u2022 Solicitud: {question_summary}\n\n"
            f"Alguien del equipo le dará seguimiento, normalmente dentro de 2 días hábiles. "
            f"Si es urgente, llame al {OFFICE_PHONE} (lunes a viernes, 8:00 AM - 5:00 PM)."
        ),
        "mandarin": (
            f"您的问题已转送至{team_name}：\n\n"
            f"\u2022 姓名：{name}\n"
            + (f"\u2022 邮箱：{email}\n" if email else "")
            + (f"\u2022 电话：{phone}\n" if phone else "")
            + f"\u2022 请求：{question_summary}\n\n"
            f"{team_name}的工作人员将跟进您的请求，通常在2个工作日内。"
            f"如有紧急情况，请致电{OFFICE_PHONE}（周一至周五，上午8:00 - 下午5:00）。"
        ),
    }
    return responses.get(language, responses["english"])

@function_tool(
    name_override="transfer_to_live_representative",
    description_override="Connect the user with a live housing authority representative. Use for any case-specific question, or when the user asks for a human."
)
async def transfer_to_live_representative(
    context: RunContextWrapper[HousingAuthorityContext],
    reason: str = "",
    callback_phone: str = ""
) -> str:
    """Record a request to speak with a live representative."""
    if callback_phone:
        context.context.phone_number = callback_phone
    language = getattr(context.context, 'language', 'english')
    reason_part = {
        "english": f" regarding: {reason}" if reason else "",
        "spanish": f" sobre: {reason}" if reason else "",
        "mandarin": f"，事由：{reason}" if reason else "",
    }
    responses = {
        "english": (
            f"I can transfer you to a live representative{reason_part['english']}. "
            f"Your request and contact information will be forwarded so a housing authority representative can follow up with you. "
            f"You can also reach a live person directly:\n\n"
            f"Phone: {OFFICE_PHONE} (Monday-Friday, 8:00 AM - 5:00 PM)\n"
            f"Email: {OFFICE_EMAIL}"
        ),
        "spanish": (
            f"Puedo transferirle a un representante en vivo{reason_part['spanish']}. "
            f"Su solicitud e informacion de contacto seran enviadas para que un representante le de seguimiento. "
            f"Tambien puede comunicarse directamente:\n\n"
            f"Telefono: {OFFICE_PHONE} (lunes a viernes, 8:00 AM - 5:00 PM)\n"
            f"Correo: {OFFICE_EMAIL}"
        ),
        "mandarin": (
            f"我可以为您转接真人代表{reason_part['mandarin']}。"
            f"您的请求和联系信息将被转发，住房管理局代表会跟进与您联系。"
            f"您也可以直接联系：\n\n"
            f"电话：{OFFICE_PHONE}（周一至周五，上午8:00 - 下午5:00）\n"
            f"邮箱：{OFFICE_EMAIL}"
        ),
    }
    return responses.get(language, responses["english"])

# =========================
# CONTEXT EXTRACTION TOOLS
# =========================

@function_tool(
    name_override="extract_t_code",
    description_override="Extract T-code from user message for case worker reference."
)
async def extract_t_code(
    context: RunContextWrapper[HousingAuthorityContext], user_message: str
) -> str:
    """Extract and store T-code from user message."""
    import re

    # Look for T-code patterns: T + digits, case insensitive
    t_code_patterns = [
        r'\bT[-\s]?(\d{4,8})\b',  # T1234, T-1234, T 1234
        r'\b(T\d{4,8})\b',       # T1234
        r'\bcode[-\s]?T[-\s]?(\d{4,8})\b',  # code T1234, code-T1234
    ]

    user_message_upper = user_message.upper()

    for pattern in t_code_patterns:
        matches = re.findall(pattern, user_message_upper, re.IGNORECASE)
        if matches:
            # Take the first match, format as T + digits
            raw_code = matches[0]
            if raw_code.startswith('T'):
                t_code = raw_code
            else:
                t_code = f"T{raw_code}"

            context.context.t_code = t_code

            language = getattr(context.context, 'language', 'english')
            responses = {
                "english": f"T-code {t_code} recorded for case worker reference.",
                "spanish": f"Código T {t_code} registrado para referencia del trabajador del caso.",
                "mandarin": f"T代码{t_code}已记录供个案工作者参考。"
            }

            return responses.get(language, responses["english"])

    # No T-code found
    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": "No T-code detected in message. TIP FOR THE CALLER: the T-code is printed in the top right-hand corner of any letter from the Housing Authority (PHA).",
        "spanish": "No se detectó código T en el mensaje. CONSEJO: el código T aparece en la esquina superior derecha de cualquier carta de la Autoridad de Vivienda (PHA).",
        "mandarin": "消息中未检测到T代码。提示：T代码印在住房管理局(PHA)寄出的任何信件的右上角。"
    }

    return responses.get(language, responses["english"])

@function_tool(
    name_override="extract_contact_info",
    description_override="Extract contact information from user message."
)
async def extract_contact_info(
    context: RunContextWrapper[HousingAuthorityContext], user_message: str
) -> str:
    """Extract and store contact information from user message."""
    import re

    extracted_info = []

    # Extract phone numbers
    phone_patterns = [
        r'\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b',  # 555-123-4567, 555.123.4567, 555 123 4567
        r'\b(\(\d{3}\)\s?\d{3}[-.\s]?\d{4})\b',  # (555) 123-4567
    ]

    for pattern in phone_patterns:
        matches = re.findall(pattern, user_message)
        if matches:
            phone = matches[0]
            context.context.phone_number = phone
            extracted_info.append(f"phone: {phone}")

    # Extract email addresses
    email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    email_matches = re.findall(email_pattern, user_message)
    if email_matches:
        email = email_matches[0]
        context.context.email = email
        extracted_info.append(f"email: {email}")

    # Extract names (simple pattern - first and last name)
    name_patterns = [
        r'\bmy name is\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
        r'\bI am\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
        r'\bI\'m\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
    ]

    for pattern in name_patterns:
        matches = re.findall(pattern, user_message, re.IGNORECASE)
        if matches:
            name = matches[0]
            context.context.participant_name = name
            extracted_info.append(f"name: {name}")

    language = getattr(context.context, 'language', 'english')

    if extracted_info:
        info_str = ", ".join(extracted_info)
        responses = {
            "english": f"Contact information recorded: {info_str}",
            "spanish": f"Información de contacto registrada: {info_str}",
            "mandarin": f"联系信息已记录：{info_str}"
        }
        return responses.get(language, responses["english"])
    else:
        responses = {
            "english": "No contact information detected in message.",
            "spanish": "No se detectó información de contacto en el mensaje.",
            "mandarin": "消息中未检测到联系信息。"
        }
        return responses.get(language, responses["english"])

@function_tool(
    name_override="set_participant_type",
    description_override="Identify if user is a tenant, landlord, or unknown."
)
async def set_participant_type(
    context: RunContextWrapper[HousingAuthorityContext], user_message: str
) -> str:
    """Determine participant type from user message context."""
    message_lower = user_message.lower()

    # Tenant indicators
    tenant_keywords = [
        "tenant", "renter", "live in", "my unit", "my apartment", "my home",
        "section 8", "voucher", "rent payment", "my lease", "move in"
    ]

    # Landlord indicators
    landlord_keywords = [
        "landlord", "property owner", "owner", "rent checks", "rental property",
        "my tenant", "my property", "receive payment", "direct deposit"
    ]

    tenant_score = sum(1 for keyword in tenant_keywords if keyword in message_lower)
    landlord_score = sum(1 for keyword in landlord_keywords if keyword in message_lower)

    if landlord_score > tenant_score:
        context.context.participant_type = "landlord"
        participant_type = "landlord"
    elif tenant_score > 0:
        context.context.participant_type = "tenant"
        participant_type = "tenant"
    else:
        context.context.participant_type = "unknown"
        participant_type = "unknown"

    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Participant type identified as: {participant_type}",
        "spanish": f"Tipo de participante identificado como: {participant_type}",
        "mandarin": f"参与者类型识别为：{participant_type}"
    }

    return responses.get(language, responses["english"])
