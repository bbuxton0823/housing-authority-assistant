from agents import RunContextWrapper, function_tool

from assistant_config import OFFICE_PHONE
from assistant_context import HousingAuthorityContext

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
