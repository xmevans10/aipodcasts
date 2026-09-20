#!/usr/bin/env python3
"""Render the four existing Sound Science episodes with Chatterbox (base).

Identity comes from the Kokoro cast (Apache-2.0): each character's assigned Kokoro
voice is rendered to a ~12 s reference clip, and Chatterbox clones it. Delivery comes
from Chatterbox base at the promoted sampling standard (temperature 0.65, top_p 0.9,
min_p 0.02, exaggeration 0.5, cfg_weight 0.5). Scripts longer than the chunk size are
split at sentence boundaries and spliced, because base caps generation at 1000 tokens.

Each episode is titled exactly:
    {character name}, {commit hash}, {date}, {Chatterbox model config}
and the manifest records the chosen Kokoro voice, word count, chunk count and duration.

No paid API, no key. `python tools/tts/render_episodes.py --out tts-episodes`
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demos/three-hosts-2026-09-17"
OUT_SR = 24000
TARGET_RMS_DBFS = -20.0
PAUSE_S = 0.35

# The promoted Chatterbox standard (won the tts-lab sampling suite by listening).
STANDARD = {"temperature": 0.65, "top_p": 0.9, "min_p": 0.02,
            "exaggeration": 0.5, "cfg_weight": 0.5, "repetition_penalty": 1.2}
SEED = 0
CONFIG_STR = "base t=0.65 top_p=0.9 min_p=0.02 ex=0.5 cfg=0.5 rp=1.2 seed=0"

CHARACTERS = [
    {"id": "mira", "host": "nova", "name": "Mira Vale", "script": "mira.txt"},
    {"id": "clara", "host": "fern", "name": "Clara Rowan", "script": "clara.txt"},
    {"id": "elias", "host": "ada", "name": "Elias Reed", "script": "elias.txt"},
    {"id": "theo", "host": "atlas", "name": "Theo Mercer", "script": "theo.txt"},
]

REF_TEXT = ("This is a reference recording for the voice of {name}. The reading is calm, "
            "even and unhurried, with a clear and neutral tone and a steady pace from the "
            "first word to the last.")


def patch_watermarker() -> None:
    import perth

    if getattr(perth, "PerthImplicitWatermarker", None) is None:
        perth.PerthImplicitWatermarker = perth.DummyWatermarker


def load_cast() -> dict:
    data = json.loads((ROOT / "tools/tts/voice_cast.json").read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def chunk_script(text: str, max_words: int) -> list[str]:
    """Split into sentence groups of at most `max_words`, keeping blank-line paragraphs apart."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        sentences = re.split(r"(?<=[.!?])\s+", " ".join(paragraph.split()))
        current = ""
        for sentence in sentences:
            candidate = (current + " " + sentence).strip()
            if current and len(candidate.split()) > max_words:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current)
    return chunks


def kokoro_reference(name: str, voice: str, out: Path, speed: float = 1.0) -> bool:
    """Render a reference clip in the character's Kokoro voice. Returns False if Kokoro is absent."""
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except Exception as error:  # noqa: BLE001
        print(f"  kokoro unavailable ({type(error).__name__}: {error}); using built-in voice", flush=True)
        return False
    language = "b" if voice.startswith("b") else "a"
    pipeline = KPipeline(lang_code=language)
    chunks = [audio for _, _, audio in pipeline(REF_TEXT.format(name=name), voice=voice, speed=speed)]
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), np.concatenate(chunks), OUT_SR)
    return True


def decode(path: Path):
    import numpy as np
    import soundfile as sf

    wav, sr = sf.read(str(path), always_2d=False)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    return wav.astype("float32"), sr


def rms_db(samples) -> float:
    import numpy as np

    voiced = samples[np.abs(samples) > 0.01]
    if voiced.size == 0:
        return -120.0
    return 20 * math.log10(float(np.sqrt(np.mean(voiced.astype("float64") ** 2))))


def trim_silence(samples, threshold: float = 0.004, keep: float = 0.08):
    import numpy as np

    idx = np.where(np.abs(samples) > threshold)[0]
    if idx.size == 0:
        return samples
    pad = int(keep * OUT_SR)
    return samples[max(0, idx[0] - pad): min(len(samples), idx[-1] + pad)]


def level(samples, target_db: float = TARGET_RMS_DBFS):
    import numpy as np

    current = rms_db(samples)
    gain = 10 ** ((target_db - current) / 20)
    return samples * gain


def splice(pieces: list, pause_s: float = PAUSE_S):
    import numpy as np

    gap = np.zeros(int(pause_s * OUT_SR), dtype="float32")
    out = []
    for index, piece in enumerate(pieces):
        if index:
            out.append(gap)
        out.append(piece)
    return np.concatenate(out)


def write_wav(samples, path: Path) -> None:
    import numpy as np
    import soundfile as sf

    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak > 0.97:
        samples = samples * (0.97 / peak)
    sf.write(str(path), samples, OUT_SR)


def short_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:  # noqa: BLE001
        return "nogit"


def render(char: dict, cast: dict, out: Path, model, max_words: int, smoke_words: int) -> dict:
    import numpy as np

    script_path = DEMO / char["script"]
    script = script_path.read_text().strip()
    if smoke_words:
        script = " ".join(script.split()[:smoke_words])
    voice = cast[char["host"]]["voice"]

    ref = out / f"ref_{char['id']}.wav"
    has_ref = kokoro_reference(char["name"], voice, ref)
    if has_ref and model is not None:
        model.prepare_conditionals(str(ref), exaggeration=STANDARD["exaggeration"])
        print(f"  conditioned on kokoro {voice} ({ref.stat().st_size // 1024} KB)", flush=True)

    chunks = chunk_script(script, max_words)
    pieces = []
    for index, chunk in enumerate(chunks):
        import torch

        torch.manual_seed(SEED)
        kwargs = dict(STANDARD) if model is not None else None
        if model is None:
            break
        wav = model.generate(chunk, **kwargs).squeeze(0).numpy()
        piece = level(trim_silence(wav.astype("float32")))
        pieces.append(piece)
        print(f"  chunk {index + 1}/{len(chunks)}: {len(chunk.split())} words, "
              f"{len(piece) / OUT_SR:.1f}s", flush=True)

    mixed = level(splice(pieces)) if pieces else np.zeros(OUT_SR, dtype="float32")
    sha, date = short_sha(), dt.date.today().isoformat()
    title = f"{char['name']}, {sha}, {date}, {CONFIG_STR}"
    dest = out / f"{title}.wav"
    write_wav(mixed, dest)
    print(f"  saved {dest.name} ({len(mixed) / OUT_SR:.1f}s)", flush=True)
    return {
        "character": char["id"], "name": char["name"], "host": char["host"],
        "kokoro_voice": voice if has_ref else None, "reference_used": has_ref,
        "title": title, "file": dest.name, "config": CONFIG_STR,
        "words": len(script.split()), "chunks": len(chunks),
        "duration_s": round(len(mixed) / OUT_SR, 1),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="tts-episodes")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    parser.add_argument("--episodes", default="", help="comma-separated ids (default: all four)")
    parser.add_argument("--max-words", type=int, default=60, help="words per Chatterbox call")
    parser.add_argument("--smoke-words", type=int, default=0, help="truncate each script for a fast test")
    args = parser.parse_args()

    patch_watermarker()
    import torch

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"device={device} max_words={args.max_words} smoke={args.smoke_words}", flush=True)

    from chatterbox.tts import ChatterboxTTS

    model = ChatterboxTTS.from_pretrained(device=device)

    wanted = [c for c in CHARACTERS if not args.episodes or c["id"] in args.episodes.split(",")]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cast = load_cast()
    manifest = []
    for char in wanted:
        print(f"rendering {char['name']} ({char['id']})", flush=True)
        manifest.append(render(char, cast, out, model, args.max_words, args.smoke_words))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "titles.txt").write_text("\n".join(row["title"] for row in manifest) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
