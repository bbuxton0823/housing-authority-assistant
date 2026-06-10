#!/usr/bin/env python3
"""
Latency profiler for the Housing Authority Assistant.

Usage:
    python profile_latency.py guardrails   # time each guardrail classifier alone
    python profile_latency.py e2e          # time full /chat turns (server must be running)
"""

import asyncio
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

TEST_MESSAGE = "I need to reschedule my HQS inspection to July 24th because of a work conflict"


async def profile_guardrails():
    import main
    from agents import Runner

    candidates = [
        ("Relevance", getattr(main, "guardrail_agent", None)),
        ("Jailbreak", getattr(main, "jailbreak_guardrail_agent", None)),
        ("DataPrivacy", getattr(main, "data_privacy_guardrail_agent", None)),
        ("Authority", getattr(main, "authority_limitation_guardrail_agent", None)),
        ("Language", getattr(main, "language_support_guardrail_agent", None)),
        ("Combined", getattr(main, "combined_guardrail_agent", None)),
    ]
    agents = [(n, a) for n, a in candidates if a is not None]

    print(f"{'classifier':12s} {'t1':>7s} {'t2':>7s} {'t3':>7s} {'median':>8s}")
    seq_total = 0.0
    par_max = 0.0
    for name, agent in agents:
        times = []
        for _ in range(3):
            t0 = time.perf_counter()
            await Runner.run(agent, TEST_MESSAGE)
            times.append(time.perf_counter() - t0)
        med = sorted(times)[1]
        if name != "Combined":
            seq_total += med
            par_max = max(par_max, med)
        print(f"{name:12s} {times[0]:6.2f}s {times[1]:6.2f}s {times[2]:6.2f}s {med:7.2f}s")
    if any(n == "Combined" for n, _ in agents):
        print(f"\nold parallel guardrail latency (max of 5): ~{par_max:.2f}s | old token cost: 5 calls")
    else:
        print(f"\nparallel guardrail latency (max of 5): ~{par_max:.2f}s | sum if serial: {seq_total:.2f}s")


async def profile_e2e(n_turns: int = 3):
    msgs = [
        "What are your office hours?",
        TEST_MESSAGE,
        "What do NSPIRE standards require for smoke alarms?",
    ][:n_turns]
    cid = None
    async with httpx.AsyncClient(timeout=90) as client:
        for m in msgs:
            t0 = time.perf_counter()
            r = await client.post("http://localhost:8000/chat",
                                  json={"message": m, "conversation_id": cid})
            dt = time.perf_counter() - t0
            d = r.json()
            cid = d["conversation_id"]
            print(f"{dt:6.2f}s  [{d['current_agent']:24s}] {m[:50]}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "guardrails"
    asyncio.run(profile_guardrails() if mode == "guardrails" else profile_e2e())
