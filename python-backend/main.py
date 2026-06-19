from __future__ import annotations as _annotations

from pydantic import BaseModel

from agents import (
    Agent,
    RunContextWrapper,
    Runner,
    function_tool,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from assistant_config import (
    GUARDRAIL_MODEL,
    KB_NOTE,
    KB_TOOLS,
    MAIN_MODEL,
    OFFICE_EMAIL,
    OFFICE_PHONE,
    SCOPE_NOTE,
)
from assistant_context import (
    HousingAuthorityContext,
    create_initial_context,
    get_multilingual_response,
)
from guardrails import (
    authority_limitation_guardrail,
    data_privacy_guardrail,
    jailbreak_guardrail,
    language_support_guardrail,
    relevance_guardrail,
)
from referrals import TEAMS, normalize_team, submit_referral

# =========================
# LANGUAGE SUPPORT TOOLS
# =========================

class LanguageDetectionOutput(BaseModel):
    """Schema for language detection results."""
    detected_language: str  # "english", "spanish", "mandarin"
    confidence: float  # 0.0 to 1.0
    reasoning: str

language_detection_agent = Agent(
    model=GUARDRAIL_MODEL,
    name="Language Detection Agent",
    instructions=(
        "Detect the language of the user's message. Return one of: 'english', 'spanish', 'mandarin'. "
        "If the message contains mixed languages, detect the primary language. "
        "For greetings or very short messages, use context clues or default to 'english'. "
        "Provide confidence score (0.0-1.0) and brief reasoning for the detection."
    ),
    output_type=LanguageDetectionOutput,
)

@function_tool(
    name_override="detect_language",
    description_override="Detect the language of user input and update context."
)
async def detect_language(
    context: RunContextWrapper[HousingAuthorityContext], user_message: str
) -> str:
    """Detect user's language and update context."""
    try:
        result = await Runner.run(language_detection_agent, [{"content": user_message, "role": "user"}])
        detection = result.final_output_as(LanguageDetectionOutput)
        
        # Update context with detected language
        context.context.language = detection.detected_language
        
        return f"Language detected: {detection.detected_language} (confidence: {detection.confidence:.2f})"
    except Exception as e:
        # Default to English if detection fails
        context.context.language = "english"
        return "Language detection failed, defaulting to English"

# =========================
# TOOLS
# =========================

@function_tool(
    name_override="get_language_instructions",
    description_override="Get instructions for responding in the user's preferred language."
)
async def get_language_instructions(
    context: RunContextWrapper[HousingAuthorityContext]
) -> str:
    """Get language-specific response instructions."""
    language = getattr(context.context, 'language', 'english')
    
    instructions = {
        'spanish': "Responde en español. Mantén un tono profesional y servicial.",
        'mandarin': "请用中文回复。保持专业和友善的语气。",
        'english': "Respond in English. Maintain a professional and helpful tone."
    }
    
    return instructions.get(language, instructions['english'])

@function_tool(
    name_override="housing_faq_lookup_tool", 
    description_override="Lookup frequently asked questions about housing authority services."
)
async def housing_faq_lookup_tool(
    context: RunContextWrapper[HousingAuthorityContext], question: str
) -> str:
    """Lookup answers to frequently asked housing authority questions."""
    language = getattr(context.context, 'language', 'english')
    q = question.lower()
    
    # English responses
    answers_en = {
        "hours": "Housing Authority hours: Monday-Friday 8:00 AM - 5:00 PM. Closed weekends and holidays.",
        "phone": "Main phone number: (555) 123-4567. Emergency maintenance: (555) 123-4568.",
        "inspection": "Housing Quality Standards (HQS) inspections ensure units meet safety and habitability requirements.",
        "section8": "Section 8 provides rental assistance to eligible low-income families, elderly, and disabled individuals.",
        "waitlist": "Contact your Housing Program Specialist to check your waitlist status and position.",
        "application": "Housing applications can be submitted online or in person during business hours."
    }
    
    # Spanish responses
    answers_es = {
        "hours": "Horarios de la Autoridad de Vivienda: Lunes-Viernes 8:00 AM - 5:00 PM. Cerrado fines de semana y días festivos.",
        "phone": "Número de teléfono principal: (555) 123-4567. Mantenimiento de emergencia: (555) 123-4568.",
        "inspection": "Las inspecciones HQS aseguran que las unidades cumplan con los requisitos de seguridad y habitabilidad.",
        "section8": "Sección 8 proporciona asistencia de alquiler a familias elegibles de bajos ingresos, personas mayores y discapacitadas.",
        "waitlist": "Contacte a su Especialista del Programa de Vivienda para verificar su estado en la lista de espera.",
        "application": "Las solicitudes de vivienda se pueden enviar en línea o en persona durante horas de oficina."
    }
    
    # Mandarin responses
    answers_zh = {
        "hours": "住房管理局营业时间：周一至周五上午8:00-下午5:00。周末和节假日关闭。",
        "phone": "主要电话号码：(555) 123-4567。紧急维修：(555) 123-4568。",
        "inspection": "住房质量标准(HQS)检查确保住房单位符合安全和宜居要求。",
        "section8": "第8节为符合条件的低收入家庭、老年人和残疾人提供租金援助。",
        "waitlist": "请联系您的住房项目专员查询您的等候名单状态和位置。",
        "application": "住房申请可以在线提交或在营业时间内亲自提交。"
    }
    
    answers = answers_en
    if language == "spanish":
        answers = answers_es
    elif language == "mandarin":
        answers = answers_zh
    
    # Find matching answer
    for key, answer in answers.items():
        if key in q:
            return answer
    
    # Default response
    defaults = {
        "english": "I don't have specific information about that. Please contact the Housing Authority at (555) 123-4567.",
        "spanish": "No tengo información específica sobre eso. Por favor contacte a la Autoridad de Vivienda al (555) 123-4567.",
        "mandarin": "我没有关于这个问题的具体信息。请致电(555) 123-4567联系住房管理局。"
    }
    
    return defaults.get(language, defaults["english"])

@function_tool(
    name_override="research_income_limits",
    description_override="Research current HUD income limits for specific areas and housing programs."
)
async def research_income_limits(
    context: RunContextWrapper[HousingAuthorityContext], 
    area_name: str = "",
    family_size: str = "",
    program_type: str = "Section 8"
) -> str:
    """Research current income limits for housing programs in specific areas."""
    language = getattr(context.context, 'language', 'english')
    
    # HUD income limits are typically based on Area Median Income (AMI)
    # This is a simplified lookup for demonstration - in production, this would query HUD APIs
    
    income_limit_data = {
        "los_angeles": {
            "1_person": {"very_low": "$50,500", "low": "$80,800", "moderate": "$96,960"},
            "2_person": {"very_low": "$57,650", "low": "$92,400", "moderate": "$110,880"},
            "3_person": {"very_low": "$64,850", "low": "$103,950", "moderate": "$124,740"},
            "4_person": {"very_low": "$72,000", "low": "$115,500", "moderate": "$138,600"},
            "5_person": {"very_low": "$77,800", "low": "$124,800", "moderate": "$149,760"},
            "6_person": {"very_low": "$83,550", "low": "$134,050", "moderate": "$160,860"}
        },
        "san_francisco": {
            "1_person": {"very_low": "$82,200", "low": "$131,450", "moderate": "$157,800"},
            "2_person": {"very_low": "$93,950", "low": "$150,300", "moderate": "$180,350"},
            "3_person": {"very_low": "$105,650", "low": "$169,100", "moderate": "$202,950"},
            "4_person": {"very_low": "$117,400", "low": "$187,900", "moderate": "$225,500"},
            "5_person": {"very_low": "$126,850", "low": "$203,000", "moderate": "$243,600"},
            "6_person": {"very_low": "$136,250", "low": "$218,050", "moderate": "$261,650"}
        },
        "general": {
            "1_person": {"very_low": "$35,000", "low": "$56,000", "moderate": "$67,200"},
            "2_person": {"very_low": "$40,000", "low": "$64,000", "moderate": "$76,800"},
            "3_person": {"very_low": "$45,000", "low": "$72,000", "moderate": "$86,400"},
            "4_person": {"very_low": "$50,000", "low": "$80,000", "moderate": "$96,000"},
            "5_person": {"very_low": "$54,000", "low": "$86,400", "moderate": "$103,680"},
            "6_person": {"very_low": "$58,000", "low": "$92,800", "moderate": "$111,360"}
        }
    }
    
    # Normalize area name
    area_key = area_name.lower().replace(" ", "_")
    if area_key not in income_limit_data:
        area_key = "general"
    
    # Normalize family size
    size_key = f"{family_size}_person" if family_size.isdigit() else "4_person"
    
    limits = income_limit_data[area_key].get(size_key, income_limit_data[area_key]["4_person"])
    
    response_templates = {
        "english": f"""Income Limits for {area_name or 'your area'} ({family_size or '4'} person household):

• Very Low Income (50% AMI): {limits['very_low']}
• Low Income (80% AMI): {limits['low']} 
• Moderate Income (100% AMI): {limits['moderate']}

Section 8 vouchers are typically available for Very Low Income households.

For the most current income limits specific to your exact location, please:
- Visit HUD.gov and search "Income Limits"
- Contact your local Housing Authority
- Email: customerservice@smchousing.org

Note: Income limits are updated annually and vary by county/metropolitan area.""",

        "spanish": f"""Límites de Ingresos para {area_name or 'su área'} (hogar de {family_size or '4'} personas):

• Ingresos Muy Bajos (50% AMI): {limits['very_low']}
• Ingresos Bajos (80% AMI): {limits['low']}
• Ingresos Moderados (100% AMI): {limits['moderate']}

Los vales de la Sección 8 están típicamente disponibles para hogares de Ingresos Muy Bajos.

Para obtener los límites de ingresos más actuales específicos para su ubicación exacta:
- Visite HUD.gov y busque "Income Limits"
- Contacte su Autoridad de Vivienda local
- Email: customerservice@smchousing.org

Nota: Los límites de ingresos se actualizan anualmente y varían por condado/área metropolitana.""",

        "mandarin": f"""收入限制 - {area_name or '您的地区'} ({family_size or '4'}人家庭):

• 极低收入 (50% AMI): {limits['very_low']}
• 低收入 (80% AMI): {limits['low']}
• 中等收入 (100% AMI): {limits['moderate']}

第8节住房券通常适用于极低收入家庭。

要获取您确切位置的最新收入限制：
- 访问 HUD.gov 搜索 "Income Limits"
- 联系当地住房管理局
- 邮箱: customerservice@smchousing.org

注意：收入限制每年更新，因县/都市区而异。"""
    }
    
    return response_templates.get(language, response_templates["english"])

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

@function_tool(
    name_override="update_door_codes",
    description_override="Store door codes for inspector access."
)
async def update_door_codes(
    context: RunContextWrapper[HousingAuthorityContext], door_codes: str
) -> str:
    """Store door codes for inspector reference."""
    context.context.door_codes = door_codes
    
    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Door codes recorded for inspector: {door_codes}",
        "spanish": f"Códigos de puerta registrados para el inspector: {door_codes}",
        "mandarin": f"门禁密码已为检查员记录：{door_codes}"
    }
    
    return responses.get(language, responses["english"])

# =========================
# INSPECTION TOOLS
# =========================

@function_tool(
    name_override="schedule_inspection",
    description_override="Schedule a new HQS inspection."
)
async def schedule_inspection(
    context: RunContextWrapper[HousingAuthorityContext], 
    unit_address: str, 
    preferred_date: str = None
) -> str:
    """Record an inspection request to be forwarded to staff (no direct scheduling)."""
    context.context.unit_address = unit_address
    requested = preferred_date or "no preference given"
    if preferred_date:
        context.context.inspection_date = f"requested: {preferred_date}"

    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Your HQS inspection request for {unit_address} has been recorded (preferred date: {requested}). I'm not connected to the scheduling system, so a housing authority staff member will contact you to confirm the actual date and time. Inspections are conducted Monday-Friday between 9:00 AM - 4:00 PM. For urgent requests, call {OFFICE_PHONE}.",
        "spanish": f"Su solicitud de inspección HQS para {unit_address} ha sido registrada (fecha preferida: {requested}). No estoy conectado al sistema de programación, así que un miembro del personal se comunicará con usted para confirmar la fecha y hora. Las inspecciones se realizan de lunes a viernes entre 9:00 AM - 4:00 PM. Para solicitudes urgentes, llame al {OFFICE_PHONE}.",
        "mandarin": f"您对{unit_address}的HQS检查请求已记录（首选日期：{requested}）。我未连接到排程系统，住房管理局工作人员将联系您确认实际日期和时间。检查时间为周一至周五上午9:00 - 下午4:00。如有紧急需求，请致电{OFFICE_PHONE}。"
    }
    
    return responses.get(language, responses["english"])

async def _forward_reschedule_request(
    context: RunContextWrapper[HousingAuthorityContext],
    new_date: str,
    reason: str = "tenant request"
) -> str:
    """Record a reschedule request to be forwarded to staff (no direct scheduling)."""
    inspection_id = getattr(context.context, 'inspection_id', None) or "your scheduled inspection"
    
    # Update inspection date with standard time block
    context.context.inspection_date = f"{new_date} between 9:00 AM - 4:00 PM"
    
    # Get contact information for HPS notification
    participant_name = getattr(context.context, 'participant_name', 'N/A')
    phone_number = getattr(context.context, 'phone_number', 'N/A')
    email = getattr(context.context, 'email', 'N/A')
    t_code = getattr(context.context, 't_code', 'N/A')
    unit_address = getattr(context.context, 'unit_address', 'N/A')
    
    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"""Inspection {inspection_id} reschedule request received:

📅 Requested Date: {new_date}
🕐 Time Block: 9:00 AM - 4:00 PM
📝 Reason: {reason}

Your reschedule request and contact information will be forwarded to your Housing Program Specialist (HPS) for processing:
• Name: {participant_name}
• Phone: {phone_number}
• Email: {email}
• T-Code: {t_code}
• Unit: {unit_address}

A confirmation will be sent to you once your request has been approved.""",

        "spanish": f"""Solicitud de reprogramación de inspección {inspection_id} recibida:

📅 Fecha Solicitada: {new_date}
🕐 Bloque de Tiempo: 9:00 AM - 4:00 PM
📝 Motivo: {reason}

Su solicitud de reprogramación e información de contacto será enviada a su Especialista del Programa de Vivienda (HPS) para procesamiento:
• Nombre: {participant_name}
• Teléfono: {phone_number}
• Email: {email}
• Código T: {t_code}
• Unidad: {unit_address}

Se le enviará una confirmación una vez que su solicitud haya sido aprobada.""",

        "mandarin": f"""检查{inspection_id}重新安排请求已收到：

📅 请求日期：{new_date}
🕐 时间段：上午9:00 - 下午4:00
📝 原因：{reason}

您的重新安排请求和联系信息将转发给您的住房项目专员(HPS)处理：
• 姓名：{participant_name}
• 电话：{phone_number}
• 邮箱：{email}
• T代码：{t_code}
• 住房单位：{unit_address}

一旦您的请求获得批准，将向您发送确认信息。"""
    }
    
    return responses.get(language, responses["english"])

@function_tool(
    name_override="reschedule_inspection",
    description_override="Submit a request to reschedule an existing inspection. The request is forwarded to staff; nothing is booked directly."
)
async def reschedule_inspection(
    context: RunContextWrapper[HousingAuthorityContext],
    new_date: str,
    reason: str = "tenant request"
) -> str:
    """Submit a reschedule request (forwarded to staff)."""
    return await _forward_reschedule_request(context, new_date, reason)

@function_tool(
    name_override="request_inspection_reschedule",
    description_override="Start the process to reschedule an inspection by gathering required information."
)
async def request_inspection_reschedule(
    context: RunContextWrapper[HousingAuthorityContext],
    inspection_id: str = "",
    new_date: str = "",
    reason: str = ""
) -> str:
    """Guide user through inspection rescheduling process."""
    language = getattr(context.context, 'language', 'english')
    
    # If user provided date, proceed with reschedule
    if new_date:
        return await _forward_reschedule_request(context, new_date, reason or "tenant request")
    
    # Otherwise, prompt for missing information
    prompt_templates = {
        "english": """I can help you reschedule your inspection. To process your request, I need:

• Preferred date (e.g., 2024-03-15 or March 15, 2024)

Please provide your preferred date for the rescheduled inspection. Inspections are conducted between 9:00 AM - 4:00 PM.

Note: Your contact information and reschedule request will be forwarded to your Housing Program Specialist (HPS) for processing.""",

        "spanish": """Puedo ayudarle a reprogramar su inspección. Para procesar su solicitud, necesito:

• Fecha preferida (ej., 2024-03-15 o 15 de marzo, 2024)

Por favor proporcione su fecha preferida para la inspección reprogramada. Las inspecciones se realizan entre las 9:00 AM - 4:00 PM.

Nota: Su información de contacto y solicitud de reprogramación será enviada a su Especialista del Programa de Vivienda (HPS) para procesamiento.""",

        "mandarin": """我可以帮助您重新安排检查。为了处理您的请求，我需要：

• 首选日期（例如，2024-03-15或2024年3月15日）

请提供您重新安排检查的首选日期。检查在上午9:00 - 下午4:00之间进行。

注意：您的联系信息和重新安排请求将转发给您的住房项目专员(HPS)处理。"""
    }
    
    return prompt_templates.get(language, prompt_templates["english"])

@function_tool(
    name_override="process_reschedule_reason",
    description_override="Process reschedule reason provided by user and complete the reschedule if date was already provided."
)
async def process_reschedule_reason(
    context: RunContextWrapper[HousingAuthorityContext],
    reason: str,
    new_date: str = ""
) -> str:
    """Process the reason for rescheduling and complete the request if date is available."""
    # Store the reason in context
    context.context.reschedule_reason = reason
    
    # If we have a date stored from previous interaction, complete the reschedule
    stored_date = getattr(context.context, 'requested_reschedule_date', '')
    if new_date or stored_date:
        date_to_use = new_date or stored_date
        return await _forward_reschedule_request(context, date_to_use, reason)
    
    # Otherwise, ask for the date
    language = getattr(context.context, 'language', 'english')
    prompt_templates = {
        "english": f"""Thank you for providing the reason: {reason}

Now I need your preferred date for the rescheduled inspection:

• Preferred date (e.g., 2024-03-15 or March 15, 2024)

Inspections are conducted between 9:00 AM - 4:00 PM.

Your reschedule request will be forwarded to your Housing Program Specialist (HPS) for processing.""",

        "spanish": f"""Gracias por proporcionar la razón: {reason}

Ahora necesito su fecha preferida para la inspección reprogramada:

• Fecha preferida (ej., 2024-03-15 o 15 de marzo, 2024)

Las inspecciones se realizan entre las 9:00 AM - 4:00 PM.

Su solicitud de reprogramación será enviada a su Especialista del Programa de Vivienda (HPS) para procesamiento.""",

        "mandarin": f"""感谢您提供原因：{reason}

现在我需要您重新安排检查的首选日期：

• 首选日期（例如，2024-03-15或2024年3月15日）

检查在上午9:00 - 下午4:00之间进行。

您的重新安排请求将转发给您的住房项目专员(HPS)处理。"""
    }
    
    return prompt_templates.get(language, prompt_templates["english"])

@function_tool(
    name_override="parse_reschedule_info",
    description_override="Parse user input that contains T-code, date, and/or reason information for rescheduling."
)
async def parse_reschedule_info(
    context: RunContextWrapper[HousingAuthorityContext],
    user_input: str
) -> str:
    """Parse user input to extract T-code, date, and reason for inspection reschedule."""
    import re
    from datetime import datetime
    
    # Extract T-code
    t_code_pattern = r'\b(T[-\s]?\d{4,8})\b'
    t_code_match = re.search(t_code_pattern, user_input, re.IGNORECASE)
    if t_code_match:
        t_code = t_code_match.group(1).upper().replace(' ', '').replace('-', '')
        if not t_code.startswith('T'):
            t_code = 'T' + t_code
        context.context.t_code = t_code
        # Remove T-code from input for further parsing
        user_input = re.sub(t_code_pattern, '', user_input, flags=re.IGNORECASE).strip()
    
    # Extract date patterns (MM/DD/YYYY, M/D/YYYY, etc.)
    date_patterns = [
        r'\bfor\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})\b',  # "for July 30, 2025"
        r'\b(\w+)\s+(\d{1,2}),?\s+(\d{4})\b',  # Month DD, YYYY
        r'\b(\d{1,2})\s+(\w+)\s+(\d{4})\b',   # DD Month YYYY
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # MM/DD/YYYY or M/D/YYYY
        r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # YYYY-MM-DD
    ]
    
    extracted_date = None
    remaining_text = user_input
    
    for pattern in date_patterns:
        date_match = re.search(pattern, user_input, re.IGNORECASE)
        if date_match:
            try:
                groups = date_match.groups()
                if len(groups) == 3:
                    # Try different date formats
                    if groups[0].isdigit() and groups[1].isdigit() and groups[2].isdigit():
                        # Numeric format - assume MM/DD/YYYY or YYYY-MM-DD
                        if len(groups[0]) == 4:  # YYYY-MM-DD
                            extracted_date = f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                        else:  # MM/DD/YYYY
                            extracted_date = f"{groups[2]}-{groups[0].zfill(2)}-{groups[1].zfill(2)}"
                    else:
                        # Text format with month names
                        try:
                            if groups[0].isalpha():  # Month DD, YYYY
                                date_obj = datetime.strptime(f"{groups[0]} {groups[1]} {groups[2]}", "%B %d %Y")
                            else:  # DD Month YYYY
                                date_obj = datetime.strptime(f"{groups[1]} {groups[0]} {groups[2]}", "%B %d %Y")
                            extracted_date = date_obj.strftime("%Y-%m-%d")
                        except ValueError:
                            try:
                                if groups[0].isalpha():  # Month DD, YYYY (abbreviated)
                                    date_obj = datetime.strptime(f"{groups[0]} {groups[1]} {groups[2]}", "%b %d %Y")
                                else:  # DD Month YYYY (abbreviated)
                                    date_obj = datetime.strptime(f"{groups[1]} {groups[0]} {groups[2]}", "%b %d %Y")
                                extracted_date = date_obj.strftime("%Y-%m-%d")
                            except ValueError:
                                continue
                    
                    # Remove date from remaining text
                    remaining_text = re.sub(pattern, '', user_input, flags=re.IGNORECASE).strip()
                    break
            except (ValueError, IndexError):
                continue
    
    # Remaining text is likely the reason
    reason = remaining_text.strip() if remaining_text.strip() else "tenant request"
    
    # Store the reason in context
    if reason and reason != "tenant request":
        context.context.reschedule_reason = reason
    
    # If we have both T-code and date, proceed with reschedule
    if extracted_date:
        context.context.requested_reschedule_date = extracted_date
        return await _forward_reschedule_request(context, extracted_date, reason)
    
    # If we have T-code but no date, ask for date
    language = getattr(context.context, 'language', 'english')
    t_code = getattr(context.context, 't_code', '')
    
    if t_code:
        prompt_templates = {
            "english": f"""T-code {t_code} recorded for your inspection reschedule.

Now I need your preferred date for the rescheduled inspection:

• Preferred date (e.g., 2024-03-15 or March 15, 2024)

Inspections are conducted between 9:00 AM - 4:00 PM.

Your reschedule request will be forwarded to your Housing Program Specialist (HPS) for processing.""",

            "spanish": f"""Código T {t_code} registrado para la reprogramación de su inspección.

Ahora necesito su fecha preferida para la inspección reprogramada:

• Fecha preferida (ej., 2024-03-15 o 15 de marzo, 2024)

Las inspecciones se realizan entre las 9:00 AM - 4:00 PM.

Su solicitud de reprogramación será enviada a su Especialista del Programa de Vivienda (HPS) para procesamiento.""",

            "mandarin": f"""T代码{t_code}已记录用于您的检查重新安排。

现在我需要您重新安排检查的首选日期：

• 首选日期（例如，2024-03-15或2024年3月15日）

检查在上午9:00 - 下午4:00之间进行。

您的重新安排请求将转发给您的住房项目专员(HPS)处理。"""
        }
        return prompt_templates.get(language, prompt_templates["english"])
    
    # Default response if no clear information was extracted: prompt for a date
    language = getattr(context.context, 'language', 'english')
    fallback_prompts = {
        "english": "I can help request an inspection reschedule. Please provide your preferred date (e.g., 2026-07-15 or July 15, 2026). Your request will be forwarded to your Housing Program Specialist (HPS) for processing.",
        "spanish": "Puedo ayudarle a solicitar la reprogramación de su inspección. Por favor proporcione su fecha preferida (ej., 2026-07-15 o 15 de julio, 2026). Su solicitud será enviada a su Especialista del Programa de Vivienda (HPS) para procesamiento.",
        "mandarin": "我可以帮助您提交检查改期请求。请提供您的首选日期（例如2026-07-15或2026年7月15日）。您的请求将转发给您的住房项目专员(HPS)处理。"
    }
    return fallback_prompts.get(language, fallback_prompts["english"])

@function_tool(
    name_override="cancel_inspection",
    description_override="Cancel an existing inspection."
)
async def cancel_inspection(
    context: RunContextWrapper[HousingAuthorityContext],
    reason: str = "tenant request"
) -> str:
    """Record a cancellation request to be forwarded to staff."""
    inspection_id = getattr(context.context, 'inspection_id', None) or "your scheduled inspection"

    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Your cancellation request for {inspection_id} has been recorded (reason: {reason}) and will be forwarded to the inspections team. A staff member will contact you to confirm. To confirm immediately, call {OFFICE_PHONE}.",
        "spanish": f"Su solicitud de cancelación para {inspection_id} ha sido registrada (motivo: {reason}) y será enviada al equipo de inspecciones. Un miembro del personal se comunicará con usted para confirmar. Para confirmar de inmediato, llame al {OFFICE_PHONE}.",
        "mandarin": f"您对{inspection_id}的取消请求已记录（原因：{reason}），将转发给检查团队。工作人员将联系您确认。如需立即确认，请致电{OFFICE_PHONE}。"
    }
    
    return responses.get(language, responses["english"])

@function_tool(
    name_override="check_inspection_status",
    description_override="Check the status of a scheduled inspection."
)
async def check_inspection_status(
    context: RunContextWrapper[HousingAuthorityContext]
) -> str:
    """Check current inspection status."""
    inspection_id = getattr(context.context, 'inspection_id', None)
    inspection_date = getattr(context.context, 'inspection_date', None)
    inspector_name = getattr(context.context, 'inspector_name', None)
    unit_address = getattr(context.context, 'unit_address', None)
    
    language = getattr(context.context, 'language', 'english')
    
    if inspection_date or unit_address:
        responses = {
            "english": f"I don't have access to inspection records, but here is the request information from this conversation:\n- Requested date: {inspection_date or 'Not provided'}\n- Address: {unit_address or 'Not provided'}\n\nTo check the official status of your inspection, please call {OFFICE_PHONE} or ask me to connect you with a live representative.",
            "spanish": f"No tengo acceso a los registros de inspección, pero esta es la información de su solicitud en esta conversación:\n- Fecha solicitada: {inspection_date or 'No proporcionada'}\n- Dirección: {unit_address or 'No proporcionada'}\n\nPara verificar el estado oficial de su inspección, llame al {OFFICE_PHONE} o pídame conectarle con un representante.",
            "mandarin": f"我无法访问检查记录，但这是本次对话中的请求信息：\n- 请求日期：{inspection_date or '未提供'}\n- 地址：{unit_address or '未提供'}\n\n要查询检查的官方状态，请致电{OFFICE_PHONE}或让我为您转接真人代表。"
        }
    else:
        responses = {
            "english": f"I don't have access to inspection records or your case file, so I can't look up an existing inspection. To check your status, call {OFFICE_PHONE}, or I can take down a request and have staff follow up with you.",
            "spanish": f"No tengo acceso a los registros de inspección ni a su expediente, así que no puedo consultar una inspección existente. Para verificar su estado, llame al {OFFICE_PHONE}, o puedo registrar una solicitud para que el personal le dé seguimiento.",
            "mandarin": f"我无法访问检查记录或您的档案，因此无法查询现有检查。要查询状态，请致电{OFFICE_PHONE}，或者我可以记录您的请求，由工作人员跟进。"
        }
    
    return responses.get(language, responses["english"])

@function_tool(
    name_override="get_inspection_requirements",
    description_override="Get HQS inspection requirements and preparation information."
)
async def get_inspection_requirements(
    context: RunContextWrapper[HousingAuthorityContext]
) -> str:
    """Provide HQS inspection requirements."""
    language = getattr(context.context, 'language', 'english')
    
    requirements = {
        "english": """Inspection Preparation (HUD NSPIRE standards):
• All utilities must be on (water, gas, electric)
• Unit must be clean and accessible
• Smoke detectors must be present and working
• All rooms, closets, cabinets must be accessible
• Remove all personal items from areas to be inspected
• Repair any obvious safety hazards
• Ensure all windows and doors open and close properly
• Have unit keys available for inspector

The inspection typically takes 30-60 minutes. You or an adult representative must be present.""",
        
        "spanish": """Preparación para la Inspección (estándares NSPIRE de HUD):
• Todos los servicios públicos deben estar encendidos (agua, gas, electricidad)
• La unidad debe estar limpia y accesible
• Los detectores de humo deben estar presentes y funcionando
• Todas las habitaciones, armarios, gabinetes deben ser accesibles
• Retire todos los artículos personales de las áreas a inspeccionar
• Repare cualquier peligro de seguridad obvio
• Asegúrese de que todas las ventanas y puertas abran y cierren correctamente
• Tenga las llaves de la unidad disponibles para el inspector

La inspección típicamente toma 30-60 minutos. Usted o un representante adulto debe estar presente.""",
        
        "mandarin": """检查准备（HUD NSPIRE标准）：
• 所有公用设施必须开启（水、煤气、电）
• 住房单位必须干净且可进入
• 必须有烟雾探测器且工作正常
• 所有房间、壁橱、柜子必须可进入
• 从待检查区域移除所有个人物品
• 修复任何明显的安全隐患
• 确保所有门窗能正常开关
• 为检查员准备好住房钥匙

检查通常需要30-60分钟。您或成年代表必须在场。"""
    }
    
    return requirements.get(language, requirements["english"])

# =========================
# AGENTS
# =========================

def inspection_instructions(
    run_context: RunContextWrapper[HousingAuthorityContext], agent: Agent[HousingAuthorityContext]
) -> str:
    ctx = run_context.context
    t_code = getattr(ctx, 't_code', None) or "[not provided]"
    participant_name = getattr(ctx, 'participant_name', None) or "[not provided]"
    language = getattr(ctx, 'language', 'english')
    
    # Get language-specific instructions
    instructions_map = {
        "english": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "You are the Inspection Agent. You help with inspection requests and explain inspection standards. "
            "HUD has transitioned from HQS to NSPIRE (National Standards for the Physical Inspection of Real Estate); explain requirements using NSPIRE standards.\n"
            f"Current participant: {participant_name} (T-code: {t_code})\n"
            "Your responsibilities:\n"
            "1. SCHEDULING: Help schedule new HQS inspections with preferred dates/times\n"
            "2. RESCHEDULING: Modify existing inspection appointments as needed. Always notify users that their reschedule request and contact information will be sent to their HPS worker for processing\n"
            "3. CANCELLATION: Cancel inspections when requested\n"
            "4. STATUS CHECKS: Provide current inspection status and details\n"
            "5. REQUIREMENTS: Explain HQS inspection preparation requirements\n"
            "6. CONTACT UPDATES: Record door codes and updated contact information for inspectors\n"
            "Never invent inspection IDs or confirmations; summarize what was recorded and explain that staff will follow up.\n"
            "Whenever the user provides a T-code, phone number, email, or name, ALWAYS record it with the extract_t_code and extract_contact_info tools.\n"
            "If the request is not inspection-related, transfer to the triage agent."
        ),
        "spanish": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "Eres el Agente de Inspecciones. Ayudas con solicitudes de inspección y explicas los estándares. "
            "HUD ha pasado de HQS a NSPIRE (Estándares Nacionales para la Inspección Física de Bienes Raíces); explica los requisitos usando los estándares NSPIRE.\n"
            f"Participante actual: {participant_name} (código T: {t_code})\n"
            "Tus responsabilidades:\n"
            "1. PROGRAMACIÓN: Ayudar a programar nuevas inspecciones HQS con fechas/horas preferidas\n"
            "2. REPROGRAMACIÓN: Modificar citas de inspección existentes según sea necesario. Siempre notificar a los usuarios que su solicitud de reprogramación e información de contacto será enviada a su trabajador HPS para procesamiento\n"
            "3. CANCELACIÓN: Cancelar inspecciones cuando se solicite\n"
            "4. VERIFICACIÓN DE ESTADO: Proporcionar estado actual de inspección y detalles\n"
            "5. REQUISITOS: Explicar requisitos de preparación para inspección HQS\n"
            "6. ACTUALIZACIONES DE CONTACTO: Registrar códigos de puerta e información de contacto actualizada para inspectores\n"
            "Nunca inventes IDs de inspección ni confirmaciones; resume lo registrado y explica que el personal hará seguimiento.\n"
            "Si la solicitud no está relacionada con inspecciones, transfiere al agente de triaje."
        ),
        "mandarin": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "您是检查代理。您帮助处理检查请求并解释检查标准。HUD已从HQS过渡到NSPIRE（房地产实物检查国家标准）；请使用NSPIRE标准解释要求。\n"
            f"当前参与者：{participant_name}（T代码：{t_code}）\n"
            "您的职责：\n"
            "1. 安排：帮助安排新的HQS检查，包括首选日期/时间\n"
            "2. 重新安排：根据需要修改现有检查预约。始终通知用户他们的重新安排请求和联系信息将发送给他们的HPS工作人员进行处理\n"
            "3. 取消：应要求取消检查\n"
            "4. 状态检查：提供当前检查状态和详细信息\n"
            "5. 要求：解释HQS检查准备要求\n"
            "6. 联系更新：为检查员记录门禁密码和更新的联系信息\n"
            "绝不编造检查ID或确认信息；总结已记录的内容，并说明工作人员将跟进。\n"
            "如果请求与检查无关，请转至分诊代理。"
        )
    }
    
    return (
        instructions_map.get(language, instructions_map["english"])
        + SCOPE_NOTE.get(language, SCOPE_NOTE["english"])
        + (KB_NOTE.get(language, KB_NOTE["english"]) if KB_TOOLS else "")
    )

inspection_agent = Agent[HousingAuthorityContext](
    name="Inspection Agent",
    model=MAIN_MODEL,
    handoff_description="A helpful agent for HQS inspection scheduling, rescheduling, cancellation, and requirements.",
    instructions=inspection_instructions,
    tools=[
        schedule_inspection, 
        request_inspection_reschedule,
        parse_reschedule_info,
        process_reschedule_reason,
        reschedule_inspection, 
        cancel_inspection, 
        check_inspection_status, 
        get_inspection_requirements,
        update_door_codes,
        extract_t_code,
        extract_contact_info,
        get_language_instructions,
        transfer_to_live_representative,
        submit_team_referral,
        *KB_TOOLS
    ],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail, data_privacy_guardrail, authority_limitation_guardrail, language_support_guardrail],
)

@function_tool(
    name_override="update_payment_method",
    description_override="Update how landlord receives Section 8 payments."
)
async def update_payment_method(
    context: RunContextWrapper[HousingAuthorityContext], 
    payment_method: str,
    landlord_name: str = None
) -> str:
    """Update landlord payment delivery method."""
    context.context.payment_method = payment_method
    context.context.participant_type = "landlord"
    if landlord_name:
        context.context.participant_name = landlord_name
    
    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Payment method updated to: {payment_method}. Changes will take effect next payment cycle.",
        "spanish": f"Método de pago actualizado a: {payment_method}. Los cambios tomarán efecto en el próximo ciclo de pago.",
        "mandarin": f"付款方式已更新为：{payment_method}。更改将在下个付款周期生效。"
    }
    
    return responses.get(language, responses["english"])

@function_tool(
    name_override="request_landlord_forms",
    description_override="Request forms for landlord documentation updates."
)
async def request_landlord_forms(
    context: RunContextWrapper[HousingAuthorityContext], 
    form_type: str = "payment_change"
) -> str:
    """Send forms to landlord for documentation updates."""
    context.context.documentation_pending = True
    
    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"We will email you the {form_type} forms within 24 hours. Please complete and return them to process your request.",
        "spanish": f"Le enviaremos por correo electrónico los formularios de {form_type} dentro de 24 horas. Por favor complete y devuelva para procesar su solicitud.",
        "mandarin": f"我们将在24小时内通过电子邮件向您发送{form_type}表格。请填写完整并返回以处理您的请求。"
    }
    
    return responses.get(language, responses["english"])

def landlord_services_instructions(
    run_context: RunContextWrapper[HousingAuthorityContext], agent: Agent[HousingAuthorityContext]
) -> str:
    ctx = run_context.context
    participant_name = getattr(ctx, 'participant_name', None) or "[not provided]"
    payment_method = getattr(ctx, 'payment_method', None) or "[not specified]"
    language = getattr(ctx, 'language', 'english')
    
    instructions_map = {
        "english": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "You are a Landlord Services Agent. You help landlords with Section 8 documentation and payment changes.\n"
            f"Current landlord: {participant_name} (Payment method: {payment_method})\n"
            "Your responsibilities:\n"
            "1. PAYMENT CHANGES: Help update how landlords receive Section 8 payments (direct deposit, check mailing)\n"
            "2. DOCUMENTATION: Send forms for updating landlord information\n"
            "3. FORM PROCESSING: Guide through form completion and submission\n"
            "4. VERIFICATION: Confirm landlord identity and property details\n"
            "5. HQS QUESTIONS: Answer landlord questions about Housing Quality Standards\n"
            "Always confirm changes and provide reference numbers when applicable.\n"
            "If the request is not landlord-related, transfer to the triage agent."
        ),
        "spanish": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "Eres un Agente de Servicios para Propietarios. Ayudas a los propietarios con documentación de Sección 8 y cambios de pago.\n"
            f"Propietario actual: {participant_name} (Método de pago: {payment_method})\n"
            "Tus responsabilidades:\n"
            "1. CAMBIOS DE PAGO: Ayudar a actualizar cómo los propietarios reciben pagos de Sección 8\n"
            "2. DOCUMENTACIÓN: Enviar formularios para actualizar información del propietario\n"
            "3. PROCESAMIENTO DE FORMULARIOS: Guiar a través de completar y enviar formularios\n"
            "4. VERIFICACIÓN: Confirmar identidad del propietario y detalles de propiedad\n"
            "5. PREGUNTAS HQS: Responder preguntas de propietarios sobre Estándares de Calidad de Vivienda\n"
            "Siempre confirma cambios y proporciona números de referencia cuando sea aplicable.\n"
            "Si la solicitud no está relacionada con propietarios, transfiere al agente de triaje."
        ),
        "mandarin": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "您是房东服务代理。您帮助房东处理第8节文档和付款变更。\n"
            f"当前房东：{participant_name}（付款方式：{payment_method}）\n"
            "您的职责：\n"
            "1. 付款变更：帮助更新房东接收第8节付款的方式\n"
            "2. 文档：发送更新房东信息的表格\n"
            "3. 表格处理：指导完成和提交表格\n"
            "4. 验证：确认房东身份和财产详情\n"
            "5. HQS问题：回答房东关于住房质量标准的问题\n"
            "始终确认更改并在适用时提供参考号码。\n"
            "如果请求与房东无关，请转至分诊代理。"
        )
    }
    
    return (
        instructions_map.get(language, instructions_map["english"])
        + SCOPE_NOTE.get(language, SCOPE_NOTE["english"])
        + (KB_NOTE.get(language, KB_NOTE["english"]) if KB_TOOLS else "")
    )

landlord_services_agent = Agent[HousingAuthorityContext](
    name="Landlord Services Agent",
    model=MAIN_MODEL,
    handoff_description="An agent to assist landlords with Section 8 documentation and payment changes.",
    instructions=landlord_services_instructions,
    tools=[update_payment_method, request_landlord_forms, housing_faq_lookup_tool, extract_contact_info, transfer_to_live_representative, submit_team_referral, *KB_TOOLS],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail, data_privacy_guardrail, authority_limitation_guardrail, language_support_guardrail],
)

# HPS Agent tools and functions
@function_tool(
    name_override="schedule_hps_appointment",
    description_override="Schedule appointment with Housing Program Specialist."
)
async def schedule_hps_appointment(
    context: RunContextWrapper[HousingAuthorityContext],
    appointment_type: str,
    preferred_date: str = None,
    preferred_time: str = None
) -> str:
    """Schedule HPS appointment."""
    import random
    from datetime import datetime, timedelta
    
    context.context.case_type = appointment_type
    context.context.participant_type = "tenant"
    
    requested = f"{preferred_date or 'no date preference'}" + (f" at {preferred_time}" if preferred_time else "")
    if preferred_date:
        context.context.appointment_date = f"requested: {requested}"

    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Your request for an HPS appointment ({appointment_type}) has been recorded (preferred time: {requested}). I don't have access to your case file or the HPS calendar, so your assigned Housing Program Specialist will contact you to confirm a time. For urgent matters, call {OFFICE_PHONE}.",
        "spanish": f"Su solicitud de cita con HPS ({appointment_type}) ha sido registrada (horario preferido: {requested}). No tengo acceso a su expediente ni al calendario de HPS, así que su Especialista del Programa de Vivienda asignado se comunicará con usted para confirmar. Para asuntos urgentes, llame al {OFFICE_PHONE}.",
        "mandarin": f"您的HPS预约请求（{appointment_type}）已记录（首选时间：{requested}）。我无法访问您的档案或HPS日历，您的住房项目专员将联系您确认时间。如有紧急事务，请致电{OFFICE_PHONE}。"
    }
    
    return responses.get(language, responses["english"])

@function_tool(
    name_override="request_income_reporting_form",
    description_override="Request forms for income change reporting."
)
async def request_income_reporting_form(
    context: RunContextWrapper[HousingAuthorityContext]
) -> str:
    """Send income reporting forms to tenant."""
    context.context.case_type = "income_change"
    
    language = getattr(context.context, 'language', 'english')
    responses = {
        "english": f"Your request for income reporting forms has been recorded and will be forwarded to the office. Forms are typically mailed within 3 business days; complete and return them within 30 days to avoid disruption of benefits. If you don't receive them, call {OFFICE_PHONE}.",
        "spanish": f"Su solicitud de formularios de reporte de ingresos ha sido registrada y será enviada a la oficina. Los formularios normalmente se envían por correo dentro de 3 días hábiles; complételos y devuélvalos dentro de 30 días para evitar interrupción de beneficios. Si no los recibe, llame al {OFFICE_PHONE}.",
        "mandarin": f"您的收入报告表格请求已记录，并将转发给办公室。表格通常在3个工作日内寄出；请在30天内填写并寄回，以避免福利中断。如未收到，请致电{OFFICE_PHONE}。"
    }
    
    return responses.get(language, responses["english"])

async def on_hps_handoff(
    context: RunContextWrapper[HousingAuthorityContext]
) -> None:
    """Set context when handed off to HPS agent."""
    if not getattr(context.context, 'participant_type', None):
        context.context.participant_type = "tenant"

def hps_instructions(
    run_context: RunContextWrapper[HousingAuthorityContext], agent: Agent[HousingAuthorityContext]
) -> str:
    ctx = run_context.context
    participant_name = getattr(ctx, 'participant_name', None) or "[not provided]"
    case_type = getattr(ctx, 'case_type', None) or "[not specified]"
    language = getattr(ctx, 'language', 'english')
    
    instructions_map = {
        "english": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "You are a Housing Program Specialist (HPS) Agent. You help tenants with appointments and program changes.\n"
            f"Current participant: {participant_name} (Case type: {case_type})\n"
            "Your responsibilities:\n"
            "1. APPOINTMENTS: Schedule meetings with HPS workers for various needs\n"
            "2. INCOME CHANGES: Process income reporting and send required forms\n"
            "3. RECIPIENT CHANGES: Help add or remove household members\n"
            "4. RECERTIFICATION: Assist with annual recertification processes\n"
            "5. PROGRAM QUESTIONS: Answer questions about Section 8 program requirements\n"
            "Always confirm appointment details and provide HPS worker contact information.\n"
            "If the request is not HPS-related, transfer to the triage agent."
        ),
        "spanish": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "Eres un Agente de Especialista en Programa de Vivienda (HPS). Ayudas a inquilinos con citas y cambios de programa.\n"
            f"Participante actual: {participant_name} (Tipo de caso: {case_type})\n"
            "Tus responsabilidades:\n"
            "1. CITAS: Programar reuniones con trabajadores HPS para varias necesidades\n"
            "2. CAMBIOS DE INGRESOS: Procesar reporte de ingresos y enviar formularios requeridos\n"
            "3. CAMBIOS DE BENEFICIARIOS: Ayudar a agregar o quitar miembros del hogar\n"
            "4. RECERTIFICACIÓN: Asistir con procesos de recertificación anual\n"
            "5. PREGUNTAS DEL PROGRAMA: Responder preguntas sobre requisitos del programa Sección 8\n"
            "Siempre confirma detalles de citas y proporciona información de contacto del trabajador HPS.\n"
            "Si la solicitud no está relacionada con HPS, transfiere al agente de triaje."
        ),
        "mandarin": (
            f"{RECOMMENDED_PROMPT_PREFIX}\n"
            "您是住房项目专员(HPS)代理。您帮助租户安排预约和项目变更。\n"
            f"当前参与者：{participant_name}（案例类型：{case_type}）\n"
            "您的职责：\n"
            "1. 预约：为各种需求安排与HPS工作人员的会议\n"
            "2. 收入变更：处理收入报告并发送所需表格\n"
            "3. 受益人变更：帮助添加或移除家庭成员\n"
            "4. 重新认证：协助年度重新认证流程\n"
            "5. 项目问题：回答关于第8节项目要求的问题\n"
            "始终确认预约详情并提供HPS工作人员联系信息。\n"
            "如果请求与HPS无关，请转至分诊代理。"
        )
    }
    
    return (
        instructions_map.get(language, instructions_map["english"])
        + SCOPE_NOTE.get(language, SCOPE_NOTE["english"])
        + (KB_NOTE.get(language, KB_NOTE["english"]) if KB_TOOLS else "")
    )

hps_agent = Agent[HousingAuthorityContext](
    name="HPS Agent",
    model=MAIN_MODEL,
    handoff_description="An agent to schedule HPS appointments and assist with housing program changes.",
    instructions=hps_instructions,
    tools=[schedule_hps_appointment, request_income_reporting_form, extract_t_code, extract_contact_info, transfer_to_live_representative, submit_team_referral, *KB_TOOLS],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail, data_privacy_guardrail, authority_limitation_guardrail, language_support_guardrail],
)

general_info_agent = Agent[HousingAuthorityContext](
    name="General Information Agent",
    model=MAIN_MODEL,
    handoff_description="A helpful agent that provides housing authority hours, contact information, and general questions.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a General Information Agent for the Housing Authority. You provide hours, contact information, and answer general questions.
    Your responsibilities:
    1. HOURS: Provide Housing Authority operating hours and holiday schedules
    2. CONTACT INFO: Give phone numbers, addresses, and department contacts
    3. GENERAL FAQ: Answer common questions about housing programs, policies, and procedures
    4. INCOME LIMITS: Research HUD income limits for specific areas and family sizes
    5. WEBSITE LINKS: Provide relevant web resources and forms
    6. DIRECTIONS: Help with office locations and accessibility information
    
    Use the housing FAQ lookup tool for specific questions and the income limit research tool for questions about eligibility thresholds. Always provide accurate contact information.
    If the request requires specialized help, transfer to the appropriate agent.""" + SCOPE_NOTE["english"] + (KB_NOTE["english"] if KB_TOOLS else ""),
    tools=[housing_faq_lookup_tool, research_income_limits, get_language_instructions, transfer_to_live_representative, submit_team_referral, *KB_TOOLS],
    input_guardrails=[relevance_guardrail, jailbreak_guardrail, data_privacy_guardrail, authority_limitation_guardrail, language_support_guardrail],
)

triage_agent = Agent[HousingAuthorityContext](
    name="Triage Agent",
    model=MAIN_MODEL,
    handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent for a housing authority. You can use your tools to delegate questions to other appropriate agents. "
        "This assistant is front-facing guidance only: it is not connected to Yardi or any case records, and cannot perform real scheduling. "
        "If the user asks about their individual file or asks for a human, live person, representative, agent, or "
        "operator, IMMEDIATELY call the transfer_to_live_representative tool - do NOT ask clarifying questions first. "
        "For policy or standards questions you answer yourself, you MUST ground the answer with the file_search knowledge base "
        "(HACSM Admin Plan, NSPIRE standards, HUD HCV guidebook, California housing law) and mention the source document. "
        "Prefer handing off: inspections/NSPIRE -> Inspection Agent, landlord/payments -> Landlord Services Agent, "
        "income/appointments -> HPS Agent, hours/contacts/general -> General Information Agent."
    ),
    tools=[transfer_to_live_representative, submit_team_referral, *KB_TOOLS],
    handoffs=[
        inspection_agent,
        landlord_services_agent,
        hps_agent,
        general_info_agent,
    ],
    # All five guardrails share one combined classifier call, so the full set
    # costs the same as the two triage used to run.
    input_guardrails=[relevance_guardrail, jailbreak_guardrail, data_privacy_guardrail,
                      authority_limitation_guardrail, language_support_guardrail],
)

# Set up handoff relationships
general_info_agent.handoffs.append(triage_agent)
inspection_agent.handoffs.append(triage_agent)
landlord_services_agent.handoffs.append(triage_agent)
hps_agent.handoffs.append(triage_agent)
