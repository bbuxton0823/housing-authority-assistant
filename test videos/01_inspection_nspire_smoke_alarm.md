# Example 1: Inspection Question Routed To Inspection Agent

- Route: Routing live
- Specialist path: Triage -> Inspection
- Rendered duration: 36.2 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can help route your housing question to the right specialist. How can I help today?
_Source/context: Call intake_

**Caller:** I have an upcoming inspection. What does HUD say about smoke alarms under the new NSPIRE standards?
_Source/context: Caller question_

**Triage Agent:** I hear you asking what HUD requires for smoke alarms during an NSPIRE inspection. That is an inspection standards question, so I am routing you to the Inspection Agent now.
_Source/context: Voice route: triage to inspection_

**Caller:** Great, I just want to know what to check before the inspector comes.
_Source/context: Caller feedback after handoff_

**Inspection Agent:** Absolutely. You're asking what to check before inspection, especially smoke alarms. HUD's NSPIRE standard says smoke alarms are required inside each bedroom, outside the bedrooms, and on each level. They should not be blocked, and they should produce an audio or visual alarm when tested.
_Source/context: Source: NSPIRE_Final_Standards_HUD.pdf, Table 52 Smoke Alarm Standard_
