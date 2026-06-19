from pydantic import BaseModel

from agents import Agent, RunContextWrapper, Runner, function_tool

from assistant_config import GUARDRAIL_MODEL
from assistant_context import HousingAuthorityContext

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
