# Example 3: Landlord Question Routed To Landlord Services

- Route: Incoming call -> Triage Agent -> Landlord Services Agent
- Rendered duration: 28.9 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. How can I help you today?
_Source/context: Call intake_

**Caller:** I am a landlord with a Section 8 tenant. What does HUD expect me to maintain?
_Source/context: Caller question_

**Triage Agent:** That is a landlord services question, so I am routing you to the Landlord Services Agent.
_Source/context: Voice route: triage to landlord services_

**Landlord Services Agent:** HUD describes the landlord's role as providing decent, safe, and sanitary housing at a reasonable rent. The unit must pass housing quality standards and be maintained to those standards as long as the owner receives housing assistance payments.
_Source/context: Source: HUD_HCV_Landlord_Fact_Sheet.pdf, landlord role summary_
