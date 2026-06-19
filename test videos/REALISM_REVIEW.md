# Routed Call Realism Review

## What was missing

- The first version sounded too polished. Real callers often lead with worry, partial facts, and practical consequences, not clean policy keywords.
- The triage agent routed correctly, but needed a stronger caller-facing confirmation: repeat the concern, name the reason for the transfer, and tell the caller to stay on the line.
- The specialist answers needed real-world limits. The assistant can explain standards and likely next steps, but it should not imply it can access case files, schedule calendars, decide inspection results, or change rent amounts.
- The examples needed a second caller turn after transfer. That back-and-forth shows the specialist handling the real concern instead of just giving a policy paragraph.
- Privacy should be modeled in the call greeting. A housing call may involve sensitive information, so the agent should remind callers not to share Social Security numbers, bank details, or medical details.

## Changes applied

- Added a privacy reminder to the intake greeting.
- Rewrote caller questions to sound more like real calls: uncertainty, anxiety, and concrete situations.
- Made triage paraphrase the caller's concern before routing.
- Added caller feedback after each handoff.
- Added a practical follow-up in each scenario.
- Added specialist caveats:
  - Inspection: explain NSPIRE smoke alarm standards, but staff/inspectors decide official outcomes.
  - HPS: explain interim reexamination rights, but staff verify documentation and effective dates.
  - Landlord Services: explain landlord responsibilities, but staff decide payment, rent reasonableness, and inspection outcomes.

## Remaining production considerations

- A real phone deployment should authenticate callers before discussing case-specific status.
- Emergency and life-safety cases should have escalation language, not only general guidance.
- If the assistant collects contact details for follow-up, the call should disclose how that information is used and stored.
- Live staff transfer rules should be clear: office hours, voicemail fallback, and what happens when no staff member is available.
- Multilingual callers should be routed without forcing them to restate the full issue in English.
