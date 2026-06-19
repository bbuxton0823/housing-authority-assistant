# Example 1: Inspection Question Routed To Inspection Agent

- Route: Incoming call -> Triage Agent -> Inspection Agent
- Rendered duration: 27.6 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. How can I help you today?
_Source/context: Call intake_

**Caller:** I have an upcoming inspection. What does HUD say about smoke alarms under the new NSPIRE standards?
_Source/context: Caller question_

**Triage Agent:** That is an inspection standards question, so I am routing you to the Inspection Agent.
_Source/context: Voice route: triage to inspection_

**Inspection Agent:** HUD's NSPIRE smoke alarm standard says smoke alarms are required inside each bedroom, outside the bedrooms, and on each level. The alarm should not be obstructed, and it should produce an audio or visual alarm when tested.
_Source/context: Source: NSPIRE_Final_Standards_HUD.pdf, Table 52 Smoke Alarm Standard_
