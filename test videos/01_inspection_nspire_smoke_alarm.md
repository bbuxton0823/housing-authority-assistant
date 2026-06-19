# Example 1: Inspection Question Routed To Inspection Agent

- Route: Routing live
- Specialist path: Triage -> Inspection
- Rendered duration: 81.1 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?
_Source/context: Call intake with privacy reminder_

**Caller:** Hi. I got an inspection notice, and I'm worried because one smoke alarm chirps and another one might be missing. What does HUD actually look for now under NSPIRE?
_Source/context: Caller question_

**Triage Agent:** I hear you asking what HUD requires for smoke alarms during an NSPIRE inspection, especially because one alarm may be missing or not working. That is an inspection standards question, so I'll route you to the Inspection Agent. Stay on the line.
_Source/context: Voice route: triage to inspection_

**Caller:** Okay, thanks. I just want to know what I should check before the inspector comes, and whether this is urgent.
_Source/context: Caller feedback after handoff_

**Inspection Agent:** Absolutely. You're asking what to check before inspection, especially whether the smoke alarms are present and working. Under HUD's NSPIRE standard, smoke alarms are required inside each sleeping area, outside sleeping areas, and on each level. They should not be blocked, and they should produce an audible or visual alarm when tested.
_Source/context: Source: NSPIRE_Final_Standards_HUD.pdf, Table 52 Smoke Alarm Standard_

**Caller:** So if it keeps chirping, should I wait for the inspection, or tell someone now?
_Source/context: Caller follow-up_

**Inspection Agent:** Do not wait for the inspection if a smoke alarm is missing or not working. Report it to your landlord or property manager right away because it is a life-safety item. I can explain the standard, but the inspector and housing authority staff make the official inspection decision.
_Source/context: Real-world limitation: explain standard, staff determine inspection result_
