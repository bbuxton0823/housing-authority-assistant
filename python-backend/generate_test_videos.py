#!/usr/bin/env python3
"""
Generate routed sample-call MP4s for local testing.

Outputs are written to ../test videos/:
  01_inspection_nspire_smoke_alarm.mp4
  02_hps_income_change_interim_reexam.mp4
  03_landlord_hcv_responsibilities.mp4
  04_spanish_general_information.mp4

The media folder is intentionally gitignored because it contains generated
audio/video assets and may contain paid ElevenLabs output.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

from voice_service import voice_service  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "test videos"
WORK_DIR = Path("/private/tmp/housing_call_video_work_realistic")
FONT_REGULAR = "/Library/Fonts/Inter-Regular.ttf"
FONT_BOLD = "/Library/Fonts/Inter-Bold.ttf"
CALLER_VOICE_ID = "AZnzlk1XvdvUeBnXmlld"  # Domi, distinct from app agent voices.
FPS = 30
WIDTH = 1280
HEIGHT = 720


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + result.stdout
            + "\n\nSTDERR:\n"
            + result.stderr
        )


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def synthesize(text: str, agent: str, output: Path, *, language: str = "english") -> None:
    if output.exists() and output.stat().st_size > 0:
        return

    if agent == "caller":
        if not voice_service.is_enabled() or voice_service._client is None:
            raise RuntimeError("ElevenLabs voice service is not enabled.")
        audio = voice_service._client.text_to_speech.convert(
            voice_id=CALLER_VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v2" if language != "english" else "eleven_monolingual_v1",
        )
        if hasattr(audio, "__iter__") and not isinstance(audio, bytes):
            audio = b"".join(audio)
    else:
        audio = voice_service.text_to_speech(text, agent_type=agent, language=language)

    if not audio:
        raise RuntimeError(f"Failed to synthesize audio for {agent}: {text[:80]}")
    output.write_bytes(audio)


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    *,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    width: int,
    line_gap: int,
) -> None:
    x, y = xy
    for line in textwrap.wrap(text, width=width, break_long_words=False):
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_gap


def draw_centered(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    *,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = box[0] + ((box[2] - box[0]) - (bbox[2] - bbox[0])) // 2
    y = box[1] + ((box[3] - box[1]) - (bbox[3] - bbox[1])) // 2 - 2
    draw.text((x, y), text, font=font, fill=fill)


def agent_label(agent: str) -> str:
    return {
        "inspection": "Inspection",
        "hps": "HPS",
        "landlord": "Landlord",
        "general": "General Info",
    }.get(agent, "Specialist")


def draw_flow(
    draw: ImageDraw.ImageDraw,
    *,
    specialist: str,
    active_agent: str,
    font: ImageFont.FreeTypeFont,
) -> None:
    steps = [
        ("caller", "Caller"),
        ("triage", "Triage"),
        (specialist, agent_label(specialist)),
    ]
    x = 76
    y = 156
    w = 240
    h = 52
    gap = 62
    muted_fill = (31, 42, 62)
    muted_outline = (75, 89, 113)
    active_colors = {
        "caller": (240, 180, 41),
        "triage": (79, 134, 247),
        "inspection": (47, 179, 68),
        "hps": (180, 90, 242),
        "landlord": (249, 115, 22),
        "general": (20, 184, 166),
    }

    for idx, (key, label) in enumerate(steps):
        left = x + idx * (w + gap)
        box = (left, y, left + w, y + h)
        is_active = active_agent == key
        color = active_colors.get(key, (79, 134, 247))
        draw.rounded_rectangle(
            box,
            radius=8,
            fill=tuple(max(0, int(c * 0.30)) for c in color) if is_active else muted_fill,
            outline=color if is_active else muted_outline,
            width=3 if is_active else 1,
        )
        draw_centered(
            draw,
            box,
            label,
            font=font,
            fill=(255, 255, 255) if is_active else (185, 198, 221),
        )
        if idx < len(steps) - 1:
            line_x1 = left + w + 10
            line_x2 = left + w + gap - 10
            line_y = y + h // 2
            draw.line((line_x1, line_y, line_x2, line_y), fill=(118, 133, 160), width=3)
            draw.polygon(
                [(line_x2, line_y), (line_x2 - 10, line_y - 7), (line_x2 - 10, line_y + 7)],
                fill=(118, 133, 160),
            )


def render_card(
    *,
    path: Path,
    example_title: str,
    route: str,
    speaker: str,
    agent: str,
    specialist: str,
    body: str,
    source: str,
) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), color=(13, 20, 36))
    draw = ImageDraw.Draw(image)

    font_title = load_font(FONT_BOLD, 32)
    font_speaker = load_font(FONT_BOLD, 30)
    font_body = load_font(FONT_REGULAR, 28)
    font_source = load_font(FONT_REGULAR, 20)
    font_flow = load_font(FONT_BOLD, 22)

    agent_color = {
        "caller": (240, 180, 41),
        "triage": (79, 134, 247),
        "inspection": (47, 179, 68),
        "hps": (180, 90, 242),
        "landlord": (249, 115, 22),
    }.get(agent, (79, 134, 247))

    draw.rounded_rectangle((48, 48, 1232, 140), radius=8, fill=(23, 32, 51))
    draw.rounded_rectangle((48, 154, 1232, 218), radius=8, fill=(30, 42, 65))
    draw.rounded_rectangle((48, 244, 1232, 556), radius=8, fill=(26, 37, 58))
    draw.rounded_rectangle(
        (48, 600, 1232, 668),
        radius=8,
        fill=tuple(max(0, int(c * 0.35)) for c in agent_color),
        outline=agent_color,
        width=2,
    )

    draw.text((76, 70), example_title, font=font_title, fill=(255, 255, 255))
    draw_flow(draw, specialist=specialist, active_agent=agent, font=font_flow)
    draw.text((76, 268), speaker, font=font_speaker, fill=agent_color)
    draw_wrapped(
        draw,
        body,
        (76, 320),
        font=font_body,
        fill=(255, 255, 255),
        width=68,
        line_gap=9,
    )
    draw_wrapped(
        draw,
        source,
        (76, 620),
        font=font_source,
        fill=(215, 225, 242),
        width=96,
        line_gap=6,
    )
    image.save(path)


def render_segment(
    *,
    index: int,
    case_dir: Path,
    audio_path: Path,
    video_path: Path,
    example_title: str,
    route: str,
    speaker: str,
    agent: str,
    specialist: str,
    body: str,
    source: str,
) -> None:
    duration = ffprobe_duration(audio_path) + 0.65
    card_path = case_dir / f"{index:02d}_{agent}.png"
    render_card(
        path=card_path,
        example_title=example_title,
        route=route,
        speaker=speaker,
        agent=agent,
        specialist=specialist,
        body=body,
        source=source,
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-t",
            f"{duration:.3f}",
            "-i",
            str(card_path),
            "-i",
            str(audio_path),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "22",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(video_path),
        ]
    )


def concat_segments(parts: list[Path], output: Path, case_dir: Path) -> None:
    concat = case_dir / "concat.txt"
    concat.write_text("\n".join(f"file '{part}'" for part in parts), encoding="utf-8")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(output),
        ]
    )


def concat_videos(parts: list[Path], output: Path, work_dir: Path) -> None:
    concat = work_dir / f"{output.stem}_concat.txt"
    concat.write_text("\n".join(f"file '{part}'" for part in parts), encoding="utf-8")
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(output),
        ]
    )


def verify_video(path: Path) -> float:
    run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    return ffprobe_duration(path)


EXAMPLES = [
    {
        "slug": "01_inspection_nspire_smoke_alarm",
        "title": "Example 1: Inspection Question Routed To Inspection Agent",
        "route": "Routing live",
        "specialist": "inspection",
        "transcript": [
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?",
                "source": "Call intake with privacy reminder",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Hi. I got an inspection notice, and I'm worried because one smoke alarm chirps and another one might be missing. What does HUD actually look for now under NSPIRE?",
                "source": "Caller question",
            },
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "I hear you asking what HUD requires for smoke alarms during an NSPIRE inspection, especially because one alarm may be missing or not working. That is an inspection standards question, so I'll route you to the Inspection Agent. Stay on the line.",
                "source": "Voice route: triage to inspection",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Okay, thanks. I just want to know what I should check before the inspector comes, and whether this is urgent.",
                "source": "Caller feedback after handoff",
            },
            {
                "speaker": "Inspection Agent",
                "agent": "inspection",
                "text": "Absolutely. You're asking what to check before inspection, especially whether the smoke alarms are present and working. Under HUD's NSPIRE standard, smoke alarms are required inside each sleeping area, outside sleeping areas, and on each level. They should not be blocked, and they should produce an audible or visual alarm when tested.",
                "source": "Source: NSPIRE_Final_Standards_HUD.pdf, Table 52 Smoke Alarm Standard",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "So if it keeps chirping, should I wait for the inspection, or tell someone now?",
                "source": "Caller follow-up",
            },
            {
                "speaker": "Inspection Agent",
                "agent": "inspection",
                "text": "Do not wait for the inspection if a smoke alarm is missing or not working. Report it to your landlord or property manager right away because it is a life-safety item. I can explain the standard, but the inspector and housing authority staff make the official inspection decision.",
                "source": "Real-world limitation: explain standard, staff determine inspection result",
            },
        ],
    },
    {
        "slug": "02_hps_income_change_interim_reexam",
        "title": "Example 2: Income Change Routed To HPS Agent",
        "route": "Routing live",
        "specialist": "hps",
        "transcript": [
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?",
                "source": "Call intake with privacy reminder",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "My hours got cut at work, and I'm worried I won't be able to pay the same rent next month. Do I report that for my voucher, or do I wait until annual recertification?",
                "source": "Caller question",
            },
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "I understand. Your income went down, and you want to know whether to report it now instead of waiting for your annual recertification. That is about income reporting and program changes, so I'll route you to the Housing Program Specialist Agent.",
                "source": "Voice route: triage to HPS",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Thanks. I mostly need to know if asking for a review is allowed, and what proof they usually ask for.",
                "source": "Caller feedback after handoff",
            },
            {
                "speaker": "HPS Agent",
                "agent": "hps",
                "text": "Yes, asking for a review is allowed. You're asking whether an income decrease can be reviewed between annual recertifications. HUD's HCV guidance says PHAs must process an interim reexamination whenever the family requests one. Staff will verify the change before any rent or assistance adjustment.",
                "source": "Source: HUD_HCV_Guidebook_Reexaminations.pdf, Section 2.2 Interim Reexaminations",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Should I send pay stubs? And do I pay the old rent amount until they answer?",
                "source": "Caller follow-up",
            },
            {
                "speaker": "HPS Agent",
                "agent": "hps",
                "text": "A real next step is to report the change in writing and include proof, such as recent pay stubs, an employer letter, or notice of reduced hours. I do not have access to your case file or the HPS calendar here, so staff must confirm the effective date. Until you receive an official updated rent notice, keep following your current rent notice.",
                "source": "Real-world limitation: no case access, staff confirm effective date",
            },
        ],
    },
    {
        "slug": "03_landlord_hcv_responsibilities",
        "title": "Example 3: Landlord Question Routed To Landlord Services",
        "route": "Routing live",
        "specialist": "landlord",
        "transcript": [
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?",
                "source": "Call intake with privacy reminder",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "I'm a landlord with a voucher tenant, and the tenant told me the kitchen outlet and bathroom fan might be inspection issues. What does HUD expect me to maintain?",
                "source": "Caller question",
            },
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "Thanks. You're asking what HUD expects a voucher landlord to maintain, including possible inspection issues in the unit. That is a landlord services question, so I'll route you to the Landlord Services Agent.",
                "source": "Voice route: triage to landlord services",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Perfect. I want to handle it correctly before the next inspection, and I don't want to accidentally charge the tenant for something I should fix.",
                "source": "Caller feedback after handoff",
            },
            {
                "speaker": "Landlord Services Agent",
                "agent": "landlord",
                "text": "That makes sense. You're asking about your role as the landlord before inspection. HUD says the landlord provides decent, safe, and sanitary housing at a reasonable rent. The unit must pass housing quality standards and be maintained to those standards while assistance payments are being made.",
                "source": "Source: HUD_HCV_Landlord_Fact_Sheet.pdf, landlord role summary",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "So should I document repairs and call the housing authority, or just fix it and wait?",
                "source": "Caller follow-up",
            },
            {
                "speaker": "Landlord Services Agent",
                "agent": "landlord",
                "text": "The realistic next step is to make the repair promptly, document what was done, and keep communication in writing. If there is an upcoming inspection, contact landlord services or the assigned housing authority contact with the update. I can explain program expectations, but I cannot decide payment, rent reasonableness, or inspection outcomes on this call.",
                "source": "Real-world limitation: explain expectations, staff decide payment and inspection outcomes",
            },
        ],
    },
    {
        "slug": "04_spanish_general_information",
        "title": "Example 4: Spanish Caller Routed To General Information",
        "route": "Enrutamiento en español",
        "specialist": "general",
        "language": "spanish",
        "transcript": [
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "Hello, and welcome to the S-M-C Housing Authority Assistant. I can route general housing questions to the right specialist. Please do not share Social Security numbers, bank details, or medical details on this line. How can I help today?",
                "source": "Call intake",
                "language": "english",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Hola, buenos días. ¿Hablan español? Es que recibí una carta de la vivienda y no la entiendo muy bien.",
                "source": "Caller asks for Spanish support",
            },
            {
                "speaker": "Triage Agent",
                "agent": "triage",
                "text": "Sí, podemos continuar en español. Entiendo que recibió una carta de la autoridad de vivienda y quiere saber qué significa. Por favor no comparta su Seguro Social, datos bancarios ni información médica por esta línea. Le voy a comunicar con Información General para orientarle.",
                "source": "Language switch: triage continues in Spanish and routes to general information",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "Gracias. La carta dice que tengo que mandar documentos antes de una fecha, pero no sé si tengo que ir a la oficina o si puedo enviarlos por correo electrónico.",
                "source": "Caller explains the practical problem",
            },
            {
                "speaker": "General Information Agent",
                "agent": "general",
                "text": "Claro. Usted está preguntando cómo entregar documentos y si necesita ir en persona. En general, puede comunicarse con la autoridad de vivienda para confirmar el método aceptado para su caso. Si la carta incluye un correo electrónico, número de teléfono o portal, use ese contacto y conserve una copia de lo que envíe.",
                "source": "General information response in Spanish",
            },
            {
                "speaker": "Caller",
                "agent": "caller",
                "text": "¿Y si se me pasa la fecha? Me preocupa que me quiten la ayuda.",
                "source": "Caller follow-up with realistic concern",
            },
            {
                "speaker": "General Information Agent",
                "agent": "general",
                "text": "Entiendo la preocupación. No puedo ver su expediente ni decidir una extensión desde esta llamada. Lo más seguro es responder antes de la fecha indicada. Si necesita más tiempo, llame o escriba lo antes posible, explique la razón y pida confirmación por escrito. Si tiene un código de caso o T-code, puede incluirlo, pero no envíe números de Seguro Social por este medio.",
                "source": "Real-world limitation: no case access, staff confirm deadlines or extensions",
            },
        ],
    },
]


def render_example(example: dict) -> tuple[Path, float]:
    slug = example["slug"]
    case_dir = WORK_DIR / slug
    case_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []

    for index, turn in enumerate(example["transcript"], start=1):
        audio = case_dir / f"{index:02d}_{turn['agent']}.mp3"
        part = case_dir / f"{index:02d}_{turn['agent']}.mp4"
        language = turn.get("language", example.get("language", "english"))
        synthesize(turn["text"], turn["agent"], audio, language=language)
        render_segment(
            index=index,
            case_dir=case_dir,
            audio_path=audio,
            video_path=part,
            example_title=example["title"],
            route=example["route"],
            speaker=turn["speaker"],
            agent=turn["agent"],
            specialist=example["specialist"],
            body=turn["text"],
            source=turn["source"],
        )
        parts.append(part)

    output = OUT_DIR / f"{slug}.mp4"
    concat_segments(parts, output, case_dir)
    duration = verify_video(output)
    write_transcript(example, output.with_suffix(".md"), duration)
    return output, duration


def write_transcript(example: dict, output: Path, duration: float) -> None:
    lines = [
        f"# {example['title']}",
        "",
        f"- Route: {example['route']}",
        f"- Specialist path: Triage -> {agent_label(example['specialist'])}",
        f"- Rendered duration: {duration:.1f} seconds",
        "- Audio: ElevenLabs voices via `voice_service.py` agent voice assignments",
        "",
    ]
    for turn in example["transcript"]:
        lines.append(f"**{turn['speaker']}:** {turn['text']}")
        lines.append(f"_Source/context: {turn['source']}_")
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg and ffprobe are required.", file=sys.stderr)
        return 1
    if not voice_service.is_enabled():
        print("ELEVENLABS_API_KEY is required to generate voice audio.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    rendered: list[Path] = []
    for example in EXAMPLES:
        output, duration = render_example(example)
        rendered.append(output)
        manifest.append(
            {
                "file": str(output),
                "duration_seconds": round(duration, 2),
                "route": example["route"],
            }
        )
        print(f"wrote {output} ({duration:.1f}s)")

    combined = OUT_DIR / "00_all_three_routed_call_examples.mp4"
    concat_videos(rendered, combined, WORK_DIR)
    combined_duration = verify_video(combined)
    manifest.insert(
        0,
        {
            "file": str(combined),
            "duration_seconds": round(combined_duration, 2),
            "route": "Combined reel: inspection, HPS, landlord, and Spanish general information examples",
        },
    )
    print(f"wrote {combined} ({combined_duration:.1f}s)")

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
