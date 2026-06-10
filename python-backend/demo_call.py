#!/usr/bin/env python3
"""
Generate a demo phone call between a caller and the Housing Authority Assistant.

This is a REAL end-to-end run: every assistant reply comes from the live
multi-agent backend (/chat), and every voice line is synthesized with the
production ElevenLabs voices (caller gets her own voice; each agent keeps its
assigned voice, so handoffs are audible).

Outputs (in ../docs/demo/):
    demo_call.mp3              - the full stitched call
    demo_call_waveform.mp4     - waveform video (for sharing/embedding)
    demo_call_waveform.png     - static voice-wave image (for screenshots)
    demo_call_transcript.md    - transcript with agent attribution

The script is resumable: segments already synthesized are skipped, so it can
be re-run until complete. Requires the backend running on localhost:8000.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

from voice_service import voice_service  # noqa: E402

BACKEND = os.getenv("DEMO_BACKEND_URL", "http://localhost:8000")
DEMO_DIR = Path(__file__).parent.parent / "docs" / "demo"
WORK_DIR = DEMO_DIR / "work"
STATE_PATH = WORK_DIR / "state.json"

# Caller voice: ElevenLabs "Domi" - distinct from all agent voices
CALLER_VOICE_ID = "AZnzlk1XvdvUeBnXmlld"
CALLER_NAME = "Maria (caller)"

CALLER_TURNS = [
    "Hi, I got a letter about my annual inspection, but I'm going to be at work that day. Can I reschedule it?",
    "Sure. My name is Maria Lopez, my T-code is T-45678, and my phone number is 650-555-0143. "
    "Could we do July 24th, 2026? I have a work conflict on the original date.",
    "Thank you! Quick question - what do the new NSPIRE standards say about smoke alarms?",
    "Good to know. One more thing: I might move to Sacramento next year. "
    "Can someone from the right team call me about transferring my voucher?",
    "Yes please - same name and number, Maria Lopez, 650-555-0143.",
    "That's everything I needed. Thank you so much!",
]

MAX_TTS_CHARS = 460  # keep spoken replies concise


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"conversation_id": None, "turns": []}


def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def chat(message: str, conversation_id: str | None) -> dict:
    r = httpx.post(f"{BACKEND}/chat", json={"message": message, "conversation_id": conversation_id},
                   timeout=60)
    r.raise_for_status()
    return r.json()


def tts_caller(text: str) -> bytes:
    """Synthesize the caller's voice."""
    client = voice_service._client
    audio = client.text_to_speech.convert(
        voice_id=CALLER_VOICE_ID, text=text, model_id="eleven_monolingual_v1")
    if hasattr(audio, "__iter__") and not isinstance(audio, bytes):
        audio = b"".join(audio)
    return audio


def shorten(text: str) -> str:
    """Trim long replies to a natural spoken length (sentence boundary)."""
    if len(text) <= MAX_TTS_CHARS:
        return text
    cut = text[:MAX_TTS_CHARS]
    for sep in (". ", "! ", "? "):
        idx = cut.rfind(sep)
        if idx > 200:
            return cut[: idx + 1]
    return cut + "..."


def ensure_segment(path: Path, synth):
    if path.exists() and path.stat().st_size > 0:
        print(f"  skip {path.name}")
        return
    audio = synth()
    if not audio:
        sys.exit(f"TTS failed for {path.name} - check ELEVENLABS_API_KEY")
    path.write_bytes(audio)
    print(f"  wrote {path.name} ({len(audio)//1024} KB)")


def run_conversation(state: dict):
    """Drive the scripted call through the live backend, synthesizing as we go."""
    # Segment 0: assistant welcome
    welcome = voice_service.get_welcome_message("english")
    ensure_segment(WORK_DIR / "seg_000_assistant.mp3",
                   lambda: voice_service.text_to_speech(welcome, "triage"))
    if not state["turns"]:
        state["turns"].append({"speaker": "Assistant (Triage Agent)", "text": welcome})
        save_state(state)

    for i, caller_line in enumerate(CALLER_TURNS):
        seg_caller = WORK_DIR / f"seg_{2*i+1:03d}_caller.mp3"
        seg_agent = WORK_DIR / f"seg_{2*i+2:03d}_assistant.mp3"

        ensure_segment(seg_caller, lambda line=caller_line: tts_caller(line))

        # Find or fetch the agent reply for this turn
        turn_key = f"reply_{i}"
        reply = next((t for t in state["turns"] if t.get("key") == turn_key), None)
        if reply is None:
            print(f"  chat turn {i + 1}/{len(CALLER_TURNS)}...")
            data = chat(caller_line, state["conversation_id"])
            state["conversation_id"] = data["conversation_id"]
            text = " ".join(m["content"] for m in data["messages"]) or "One moment please."
            agent = data["current_agent"]
            state["turns"].append({"key": f"caller_{i}", "speaker": CALLER_NAME, "text": caller_line})
            reply = {"key": turn_key, "speaker": f"Assistant ({agent})", "agent": agent,
                     "text": text}
            state["turns"].append(reply)
            save_state(state)

        spoken = shorten(reply["text"])
        ensure_segment(seg_agent,
                       lambda s=spoken, a=reply["agent"]: voice_service.text_to_speech(s, a))


def stitch():
    """Concatenate segments with short pauses; render waveform video and image."""
    segs = sorted(WORK_DIR.glob("seg_*.mp3"))
    if not segs:
        sys.exit("No segments to stitch")
    silence = WORK_DIR / "silence.wav"
    if not silence.exists():
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=mono", "-t", "0.55", str(silence)],
                       check=True, capture_output=True)
    # convert each to wav and build concat list
    listfile = WORK_DIR / "concat.txt"
    lines = []
    for seg in segs:
        wav = seg.with_suffix(".wav")
        if not wav.exists():
            subprocess.run(["ffmpeg", "-y", "-i", str(seg), "-ar", "44100", "-ac", "1", str(wav)],
                           check=True, capture_output=True)
        lines.append(f"file '{wav.name}'")
        lines.append(f"file '{silence.name}'")
    listfile.write_text("\n".join(lines))

    final_mp3 = DEMO_DIR / "demo_call.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-c:a", "libmp3lame", "-b:a", "128k", str(final_mp3)],
                   cwd=WORK_DIR, check=True, capture_output=True)
    print(f"wrote {final_mp3.name}")

    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    title = "Housing Authority Assistant - Live Call Demo"
    sub = "Real multi-agent responses - ElevenLabs voices - NSPIRE knowledge base"
    # waveform video
    vf = (
        f"[0:a]showwaves=s=1280x520:mode=cline:rate=25:colors=0x4F86F7[w];"
        f"color=s=1280x720:c=0x10141C[bg];"
        f"[bg][w]overlay=0:140,"
        f"drawtext=fontfile={font}:text='{title}':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=48,"
        f"drawtext=fontfile={font}:text='{sub}':fontcolor=0x9FB4D8:fontsize=20:x=(w-text_w)/2:y=100"
    )
    final_mp4 = DEMO_DIR / "demo_call_waveform.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", str(final_mp3), "-filter_complex", vf,
                    "-map", "0:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(final_mp4)],
                   check=True, capture_output=True)
    print(f"wrote {final_mp4.name}")

    # static voice-wave image
    final_png = DEMO_DIR / "demo_call_waveform.png"
    subprocess.run(["ffmpeg", "-y", "-i", str(final_mp3), "-filter_complex",
                    "showwavespic=s=1600x420:colors=0x4F86F7|0x9FB4D8", "-frames:v", "1",
                    str(final_png)], check=True, capture_output=True)
    print(f"wrote {final_png.name}")


def write_transcript(state: dict):
    lines = ["# Demo Call Transcript", "",
             "Every assistant line below was generated live by the multi-agent backend; "
             "voices are the production ElevenLabs assignments.", ""]
    for t in state["turns"]:
        lines.append(f"**{t['speaker']}:** {t['text']}")
        lines.append("")
    (DEMO_DIR / "demo_call_transcript.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote demo_call_transcript.md")


if __name__ == "__main__":
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state()
    if "--stitch-only" not in sys.argv:
        run_conversation(state)
    expected = 1 + 2 * len(CALLER_TURNS)
    have = len(list(WORK_DIR.glob("seg_*.mp3")))
    print(f"segments: {have}/{expected}")
    if have >= expected or "--stitch-only" in sys.argv:
        stitch()
        write_transcript(state)
        print("DONE")
