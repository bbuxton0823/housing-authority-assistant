# Example 2: Income Change Routed To HPS Agent

- Route: Routing live
- Specialist path: Triage -> HPS
- Rendered duration: 44.9 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can help route your housing question to the right specialist. How can I help today?
_Source/context: Call intake_

**Caller:** My work hours were cut and my income went down. Do I need to report that for my voucher?
_Source/context: Caller question_

**Triage Agent:** I understand. Your income went down, and you want to know whether to report that for your voucher. That is about income reporting and program changes, so I am routing you to the Housing Program Specialist Agent.
_Source/context: Voice route: triage to HPS_

**Caller:** Thanks. I mostly want to know if asking for a review is allowed.
_Source/context: Caller feedback after handoff_

**HPS Agent:** Yes, asking for a review is allowed. You're asking whether an income decrease can be reviewed between annual recertifications. HUD's HCV guidance says PHAs must process an interim reexamination whenever the family requests one. Staff will verify the change before any rent or assistance adjustment.
_Source/context: Source: HUD_HCV_Guidebook_Reexaminations.pdf, Section 2.2 Interim Reexaminations_
