from agents import RunContextWrapper, function_tool

from assistant_config import OFFICE_PHONE
from assistant_context import HousingAuthorityContext

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
