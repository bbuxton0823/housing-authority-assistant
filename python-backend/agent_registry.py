from typing import Any, Dict, List

from main import (
    general_info_agent,
    hps_agent,
    inspection_agent,
    landlord_services_agent,
    triage_agent,
)


ALL_AGENTS = (
    triage_agent,
    general_info_agent,
    inspection_agent,
    landlord_services_agent,
    hps_agent,
)


def get_agent_by_name(name: str):
    agents_by_name = {agent.name: agent for agent in ALL_AGENTS}
    return agents_by_name.get(name, triage_agent)


def get_guardrail_name(guardrail) -> str:
    name_attr = getattr(guardrail, "name", None)
    if isinstance(name_attr, str) and name_attr:
        return name_attr
    guard_fn = getattr(guardrail, "guardrail_function", None)
    if guard_fn is not None and hasattr(guard_fn, "__name__"):
        return guard_fn.__name__.replace("_", " ").title()
    fn_name = getattr(guardrail, "__name__", None)
    if isinstance(fn_name, str) and fn_name:
        return fn_name.replace("_", " ").title()
    return str(guardrail)


def build_agents_list() -> List[Dict[str, Any]]:
    def make_agent_dict(agent) -> Dict[str, Any]:
        return {
            "name": agent.name,
            "description": getattr(agent, "handoff_description", ""),
            "handoffs": [
                getattr(handoff, "agent_name", getattr(handoff, "name", ""))
                for handoff in getattr(agent, "handoffs", [])
            ],
            "tools": [
                getattr(tool, "name", getattr(tool, "__name__", ""))
                for tool in getattr(agent, "tools", [])
            ],
            "input_guardrails": [
                get_guardrail_name(guardrail)
                for guardrail in getattr(agent, "input_guardrails", [])
            ],
        }

    return [make_agent_dict(agent) for agent in ALL_AGENTS]
