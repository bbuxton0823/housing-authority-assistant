# Example 3: Landlord Question Routed To Landlord Services

- Route: Routing live
- Specialist path: Triage -> Landlord
- Rendered duration: 83.9 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?
_Source/context: Call intake with privacy reminder_

**Caller:** I'm a landlord with a voucher tenant, and the tenant told me the kitchen outlet and bathroom fan might be inspection issues. What does HUD expect me to maintain?
_Source/context: Caller question_

**Triage Agent:** Thanks. You're asking what HUD expects a voucher landlord to maintain, including possible inspection issues in the unit. That is a landlord services question, so I'll route you to the Landlord Services Agent.
_Source/context: Voice route: triage to landlord services_

**Caller:** Perfect. I want to handle it correctly before the next inspection, and I don't want to accidentally charge the tenant for something I should fix.
_Source/context: Caller feedback after handoff_

**Landlord Services Agent:** That makes sense. You're asking about your role as the landlord before inspection. HUD says the landlord provides decent, safe, and sanitary housing at a reasonable rent. The unit must pass housing quality standards and be maintained to those standards while assistance payments are being made.
_Source/context: Source: HUD_HCV_Landlord_Fact_Sheet.pdf, landlord role summary_

**Caller:** So should I document repairs and call the housing authority, or just fix it and wait?
_Source/context: Caller follow-up_

**Landlord Services Agent:** The realistic next step is to make the repair promptly, document what was done, and keep communication in writing. If there is an upcoming inspection, contact landlord services or the assigned housing authority contact with the update. I can explain program expectations, but I cannot decide payment, rent reasonableness, or inspection outcomes on this call.
_Source/context: Real-world limitation: explain expectations, staff decide payment and inspection outcomes_
