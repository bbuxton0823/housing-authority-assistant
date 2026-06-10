# Data Access & PII Policy — Housing Authority Assistant

This document defines what the assistant can and cannot access, and the controls that enforce those boundaries. The governing principle is **data minimization**: the assistant is a front-facing guide that helps people understand programs and submit requests — it is not a system of record and must never become one.

## Access tiers

### Tier 1 — Knowledge base (full read access)
The assistant's RAG knowledge base (OpenAI vector store `housing-authority-kb`, built by `python-backend/build_rag.py` from `python-backend/rag_docs/`) contains **public documents only**:

| Area | Documents |
| --- | --- |
| HACSM policy | Administrative Plan FY 2025-26 (Housing Voucher & MTW), MTW Annual Plan FY 2025 |
| Inspections | HUD NSPIRE Final Standards, NSPIRE Inspection Protocol & Guidance |
| HUD / HCV program | HCV Guidebook chapters: Eligibility, Payment Standards, Reexaminations, Moves & Portability, Housing Search & Leasing; HCV Landlord Fact Sheet |
| California law | AB 1482 Tenant Protection Act toolkit (English/Spanish), CA DRE Tenants' & Landlords' Rights Guide (2025) |

Rule: **anything uploaded to the knowledge base must be publishable on the public website.** If a document couldn't be posted publicly, it doesn't go in the vector store. No tenant lists, no internal staff directories, no case files, no documents containing names of program participants.

### Tier 2 — Conversation-scoped data (collected, not retrieved)
The assistant may *collect* limited contact details a caller volunteers so staff can follow up: T-code, name, phone, email, unit address, preferred dates, reason for request. This data:

- lives only in the per-conversation context (in-memory) and the local `conversation_logs.jsonl`
- is never used to look anything up — the assistant has no retrieval path into tenant systems
- is forwarded one-way to staff via the team referral email (`submit_team_referral` -> tagged email to the general mailbox, or `referrals_outbox.jsonl` when SMTP is unconfigured). Referral emails contain only: name, contact info, T-code if volunteered, language, and the question summary - never anything retrieved from agency systems
- `referrals_outbox.jsonl` is an audit trail of all referrals; treat it with the same controls as `conversation_logs.jsonl` (gitignored, retention window, controlled access)

### Tier 3 — Systems of record (NO access, by design)
The assistant has **no connection** to Yardi, waitlist systems, payment ledgers, case files, or any database containing participant PII. This is enforced structurally, not just by prompt: there are no credentials, no API clients, and no tools in the codebase that reach those systems. Questions about an individual's file are answered with "I can't see your file" plus a warm transfer to a live representative.

## Enforcement layers

1. **Structural**: no tools exist that can read tenant records. A prompt injection cannot use a tool that isn't there.
2. **Instructional**: every agent's system prompt includes scope limits (no Yardi/case access, never invent confirmations or IDs, offer live transfer for case-specific questions).
3. **Guardrails** (LLM classifiers run on every user message):
   - *Data Privacy Guardrail* — blocks messages containing SSNs, bank/credit card numbers, routing numbers, or detailed medical information, and responds with guidance to share those only with a caseworker directly.
   - *Relevance, Jailbreak, Authority Limitation* guardrails bound the assistant to housing topics and prevent prompt-extraction or over-promising.
4. **Human handoff**: the `transfer_to_live_representative` tool is available to all agents and is the default answer for case-specific questions.

## Operational guidance

- **Logs**: `conversation_logs.jsonl` will contain whatever callers type, including contact info they volunteer. Treat it as sensitive: keep it on controlled infrastructure, set a retention period (suggest 90 days), and exclude it from backups shared outside the agency. It is gitignored.
- **Model provider**: conversation content is processed by OpenAI's API. Under OpenAI's API terms, API data is not used for training by default. If the agency requires it, a Zero Data Retention agreement or a Business Associate-style addendum can be pursued; alternatively, route guardrail/triage calls to a locally hosted model later.
- **Voice calls (Twilio)**: call audio is transcribed via Whisper (OpenAI). The same minimization rules apply; the IVR greeting should tell callers not to read out SSNs or bank details.
- **Knowledge base refresh**: re-run `python build_rag.py` whenever the Admin Plan, NSPIRE standards, or income limits are updated (at minimum annually). The script is idempotent — it skips files already uploaded; replace a file in `rag_docs/` with the new version (same review rule: public docs only).
- **Future Yardi integration** (if ever desired): keep the bot write-only — e.g., it creates a ticket/work order in a queue staff review — never read access. A read API, even "just for status checks," makes the bot a PII disclosure surface that must authenticate callers, which a chat widget cannot do reliably.

## What the assistant says about its own access
The agents are instructed to be transparent: "I don't have access to your case file or scheduling system. I can explain how the program works, take down your request for staff, or connect you with a live representative."
