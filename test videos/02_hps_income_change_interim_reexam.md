# Example 2: Income Change Routed To HPS Agent

- Route: Incoming call -> Triage Agent -> HPS Agent
- Rendered duration: 33.1 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. How can I help you today?
_Source/context: Call intake_

**Caller:** My work hours were cut and my income went down. Do I need to report that for my voucher?
_Source/context: Caller question_

**Triage Agent:** That is about income reporting and program changes, so I am routing you to the Housing Program Specialist Agent.
_Source/context: Voice route: triage to HPS_

**HPS Agent:** Yes. HUD's HCV reexamination guidance says PHAs must process an interim reexamination whenever the family requests one. Your housing authority's administrative plan controls the reporting deadline, and staff will verify the change before any rent or assistance adjustment.
_Source/context: Source: HUD_HCV_Guidebook_Reexaminations.pdf, Section 2.2 Interim Reexaminations_
