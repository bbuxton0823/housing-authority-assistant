# Example 2: Income Change Routed To HPS Agent

- Route: Routing live
- Specialist path: Triage -> HPS
- Rendered duration: 86.4 seconds
- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments

**Triage Agent:** Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?
_Source/context: Call intake with privacy reminder_

**Caller:** My hours got cut at work, and I'm worried I won't be able to pay the same rent next month. Do I report that for my voucher, or do I wait until annual recertification?
_Source/context: Caller question_

**Triage Agent:** I understand. Your income went down, and you want to know whether to report it now instead of waiting for your annual recertification. That is about income reporting and program changes, so I'll route you to the Housing Program Specialist Agent.
_Source/context: Voice route: triage to HPS_

**Caller:** Thanks. I mostly need to know if asking for a review is allowed, and what proof they usually ask for.
_Source/context: Caller feedback after handoff_

**HPS Agent:** Yes, asking for a review is allowed. You're asking whether an income decrease can be reviewed between annual recertifications. HUD's HCV guidance says PHAs must process an interim reexamination whenever the family requests one. Staff will verify the change before any rent or assistance adjustment.
_Source/context: Source: HUD_HCV_Guidebook_Reexaminations.pdf, Section 2.2 Interim Reexaminations_

**Caller:** Should I send pay stubs? And do I pay the old rent amount until they answer?
_Source/context: Caller follow-up_

**HPS Agent:** A real next step is to report the change in writing and include proof, such as recent pay stubs, an employer letter, or notice of reduced hours. I do not have access to your case file or the HPS calendar here, so staff must confirm the effective date. Until you receive an official updated rent notice, keep following your current rent notice.
_Source/context: Real-world limitation: no case access, staff confirm effective date_
