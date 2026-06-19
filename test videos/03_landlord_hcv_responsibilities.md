# Example 3: Landlord Question Routed To Landlord Services

- Route: Routing live
- Specialist path: Triage -> Landlord
- Rendered duration: 36.4 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can help route your housing question to the right specialist. How can I help today?
_Source/context: Call intake_

**Caller:** I am a landlord with a Section 8 tenant. What does HUD expect me to maintain?
_Source/context: Caller question_

**Triage Agent:** Thanks. You're asking what HUD expects a Section 8 landlord to maintain. That is a landlord services question, so I am routing you to the Landlord Services Agent.
_Source/context: Voice route: triage to landlord services_

**Caller:** Perfect. I want to make sure I understand my role before the next inspection.
_Source/context: Caller feedback after handoff_

**Landlord Services Agent:** That makes sense. You're asking about your role as the landlord before inspection. HUD says the landlord provides decent, safe, and sanitary housing at a reasonable rent. The unit must pass housing quality standards and be maintained to those standards while assistance payments are being made.
_Source/context: Source: HUD_HCV_Landlord_Fact_Sheet.pdf, landlord role summary_
