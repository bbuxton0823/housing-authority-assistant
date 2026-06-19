# Example 4: Spanish Caller Routed To General Information

- Route: Enrutamiento en español
- Specialist path: Triage -> General Info
- Rendered duration: 100.3 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?
_Source/context: Call intake_

**Caller:** Hola, buenos días. ¿Hablan español? Es que recibí una carta de la vivienda y no la entiendo muy bien.
_Source/context: Caller asks for Spanish support_

**Triage Agent:** Sí, podemos continuar en español. Entiendo que recibió una carta de la autoridad de vivienda y quiere saber qué significa. Por favor no comparta su Seguro Social, datos bancarios ni información médica por esta línea. Le voy a comunicar con Información General para orientarle.
_Source/context: Language switch: triage continues in Spanish and routes to general information_

**Caller:** Gracias. La carta dice que tengo que mandar documentos antes de una fecha, pero no sé si tengo que ir a la oficina o si puedo enviarlos por correo electrónico.
_Source/context: Caller explains the practical problem_

**General Information Agent:** Claro. Usted está preguntando cómo entregar documentos y si necesita ir en persona. En general, puede comunicarse con la autoridad de vivienda para confirmar el método aceptado para su caso. Si la carta incluye un correo electrónico, número de teléfono o portal, use ese contacto y conserve una copia de lo que envíe.
_Source/context: General information response in Spanish_

**Caller:** ¿Y si se me pasa la fecha? Me preocupa que me quiten la ayuda.
_Source/context: Caller follow-up with realistic concern_

**General Information Agent:** Entiendo la preocupación. No puedo ver su expediente ni decidir una extensión desde esta llamada. Lo más seguro es responder antes de la fecha indicada. Si necesita más tiempo, llame o escriba lo antes posible, explique la razón y pida confirmación por escrito. Si tiene un código de caso o T-code, puede incluirlo, pero no envíe números de Seguro Social por este medio.
_Source/context: Real-world limitation: no case access, staff confirm deadlines or extensions_
