"""
Team referral routing for the Housing Authority Assistant.

When a caller's question needs follow-up from a specific team, the agent
collects the caller's name and contact info, and this module formats and
routes a referral email to the agency's general mailbox. The subject line
carries a [Referral][<Team>] tag so existing mailbox rules can filter it
to the right team.

Configuration (.env):
    REFERRAL_MAILBOX=hcvinbox@smchousing.org     # general mailbox (required for email)
    SMTP_HOST=smtp.office365.com                  # or your relay
    SMTP_PORT=587
    SMTP_USER=noreply@smchousing.org
    SMTP_PASSWORD=...
    SMTP_FROM=noreply@smchousing.org              # defaults to SMTP_USER

    # Optional per-team overrides (otherwise everything goes to REFERRAL_MAILBOX):
    # TEAM_EMAIL_LEASING=leasing@smchousing.org
    # TEAM_EMAIL_PROJECT_BASED=pbv@smchousing.org
    # TEAM_EMAIL_FSS=fss@smchousing.org
    # TEAM_EMAIL_PORTABILITY=portability@smchousing.org
    # TEAM_EMAIL_VOUCHER_OTHER=vouchers@smchousing.org
    # TEAM_EMAIL_HCD=hcd@smchousing.org

If SMTP is not configured, referrals are appended to referrals_outbox.jsonl
so no request is ever lost; staff (or a retry job) can process that file.
"""

import json
import logging
import os
import smtplib
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)

OUTBOX_PATH = Path(__file__).parent / "referrals_outbox.jsonl"

# Canonical team registry: key -> (display name, env var for override address)
TEAMS = {
    "leasing": ("Leasing Team", "TEAM_EMAIL_LEASING"),
    "project_based": ("Project-Based Voucher Team", "TEAM_EMAIL_PROJECT_BASED"),
    "fss": ("FSS Coordinator", "TEAM_EMAIL_FSS"),
    "portability": ("Portability Team", "TEAM_EMAIL_PORTABILITY"),
    "voucher_other": ("Voucher/Other Team", "TEAM_EMAIL_VOUCHER_OTHER"),
    "hcd": ("HCD", "TEAM_EMAIL_HCD"),
}


def normalize_team(team: str) -> str | None:
    """Map free-form team names to registry keys."""
    t = (team or "").lower().replace("-", "_").replace(" ", "_")
    if t in TEAMS:
        return t
    aliases = {
        "lease": "leasing", "leasing_team": "leasing", "landlord_leasing": "leasing",
        "pbv": "project_based", "project": "project_based", "projectbased": "project_based",
        "project_based_team": "project_based",
        "fss_coordinator": "fss", "family_self_sufficiency": "fss",
        "port": "portability", "portability_team": "portability",
        "voucher": "voucher_other", "voucherother": "voucher_other", "other": "voucher_other",
        "vouchers": "voucher_other",
        "housing_community_development": "hcd",
    }
    return aliases.get(t)


def _smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST", "").strip() and os.getenv("REFERRAL_MAILBOX", "").strip())


def _team_address(team_key: str) -> str:
    _, env_var = TEAMS[team_key]
    return os.getenv(env_var, "").strip() or os.getenv("REFERRAL_MAILBOX", "").strip()


def build_referral(team_key: str, *, name: str, email: str = "", phone: str = "",
                   question: str = "", t_code: str = "", language: str = "english",
                   conversation_id: str = "") -> dict:
    """Build the structured referral record."""
    team_name, _ = TEAMS[team_key]
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "team_key": team_key,
        "team": team_name,
        "name": name,
        "email": email,
        "phone": phone,
        "t_code": t_code,
        "language": language,
        "question": question,
        "conversation_id": conversation_id,
    }


def format_email(ref: dict) -> EmailMessage:
    msg = EmailMessage()
    sender = os.getenv("SMTP_FROM", "").strip() or os.getenv("SMTP_USER", "").strip()
    msg["From"] = sender
    msg["To"] = _team_address(ref["team_key"])
    msg["Subject"] = f"[Referral][{ref['team']}] {ref['name']} - assistant follow-up request"
    contact_lines = []
    if ref["email"]:
        contact_lines.append(f"Email:    {ref['email']}")
    if ref["phone"]:
        contact_lines.append(f"Phone:    {ref['phone']}")
    body = (
        f"A follow-up request was submitted through the Housing Authority Assistant.\n"
        f"\n"
        f"Team:     {ref['team']}\n"
        f"Name:     {ref['name']}\n"
        + "\n".join(contact_lines) + "\n"
        + (f"T-Code:   {ref['t_code']}\n" if ref["t_code"] else "")
        + f"Language: {ref['language']}\n"
        f"Received: {ref['timestamp']}\n"
        f"Conversation ID: {ref['conversation_id']}\n"
        f"\n"
        f"Question / request:\n"
        f"{ref['question']}\n"
        f"\n"
        f"--\n"
        f"Automated referral from the Housing Authority Assistant. "
        f"Reply directly to the contact above.\n"
    )
    msg.set_content(body)
    if ref["email"]:
        msg["Reply-To"] = ref["email"]
    return msg


def _send_smtp(msg: EmailMessage) -> None:
    host = os.getenv("SMTP_HOST").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        try:
            server.starttls()
            server.ehlo()
        except smtplib.SMTPNotSupportedError:
            pass  # plain relay without TLS (internal relays)
        if user and password:
            server.login(user, password)
        server.send_message(msg)


def _write_outbox(ref: dict, status: str, error: str = "") -> None:
    record = dict(ref, delivery_status=status, delivery_error=error)
    with open(OUTBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def submit_referral(team_key: str, **kwargs) -> tuple[bool, str]:
    """
    Send a referral. Returns (delivered_by_email, status_string).
    Always records the referral in the local outbox as an audit trail; if SMTP
    is unavailable or fails, the outbox entry is the fallback of record.
    """
    ref = build_referral(team_key, **kwargs)
    if _smtp_configured():
        try:
            _send_smtp(format_email(ref))
            _write_outbox(ref, "sent")
            logger.info(f"Referral emailed to {_team_address(team_key)} [{ref['team']}]")
            return True, "sent"
        except Exception as e:
            logger.error(f"Referral email failed ({e}); queued to outbox")
            _write_outbox(ref, "queued", str(e))
            return False, "queued"
    _write_outbox(ref, "queued", "SMTP not configured")
    logger.warning("SMTP not configured; referral queued to referrals_outbox.jsonl")
    return False, "queued"
