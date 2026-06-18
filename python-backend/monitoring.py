import json
from datetime import datetime
from pathlib import Path


CONVERSATION_LOG_PATH = Path(__file__).parent / "conversation_logs.jsonl"


def log_conversation(conversation_id, message, response, agent_name, guardrails_status) -> None:
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": conversation_id,
        "input": message,
        "output": response,
        "agent": agent_name,
        "guardrails": guardrails_status,
    }

    with CONVERSATION_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
