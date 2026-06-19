from agents import RunContextWrapper, function_tool

from assistant_context import HousingAuthorityContext

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
