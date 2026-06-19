from __future__ import annotations as _annotations

from agents import (
    Agent,
    RunContextWrapper,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from assistant_config import (
    KB_NOTE,
    KB_TOOLS,
    MAIN_MODEL,
    SCOPE_NOTE,
)
from assistant_context import (
    HousingAuthorityContext,
    create_initial_context,
)
from guardrails import (
    authority_limitation_guardrail,
    data_privacy_guardrail,
    jailbreak_guardrail,
    language_support_guardrail,
    relevance_guardrail,
)
from general_tools import (
    get_language_instructions,
    housing_faq_lookup_tool,
    research_income_limits,
)
from hps_tools import (
    request_income_reporting_form,
    schedule_hps_appointment,
)
from inspection_tools import (
    cancel_inspection,
    check_inspection_status,
    get_inspection_requirements,
    parse_reschedule_info,
    process_reschedule_reason,
    request_inspection_reschedule,
    reschedule_inspection,
    schedule_inspection,
    update_door_codes,
)
from landlord_tools import request_landlord_forms, update_payment_method
from participant_tools import (
    extract_contact_info,
    extract_t_code,
    submit_team_referral,
    transfer_to_live_representative,
)

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
