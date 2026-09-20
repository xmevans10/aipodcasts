#!/usr/bin/env python3
"""Render the four existing Sound Science episodes with Kokoro-82M directly.

Kokoro's fixed voicepacks (Apache-2.0 code and weights, no cloning) are the identity;
each character uses the voice assigned in tools/tts/voice_cast.json. Kokoro segments
long text internally, so there is no chunking, splicing or reference clip — one model,
one pass. This is the direct alternative to the Kokoro-ref -> Chatterbox experiment.

Each episode is titled:
    {character name}, {commit hash}, {date}, kokoro-82M {voice} speed={speed}

No paid API, no key. `python tools/tts/kokoro_episodes.py --out kokoro-episodes`
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demos/three-hosts-2026-09-17"
OUT_SR = 24000
SPEED = 1.0

CHARACTERS = [
    {"id": "mira", "host": "nova", "name": "Mira Vale", "script": "mira.txt"},
    {"id": "clara", "host": "fern", "name": "Clara Rowan", "script": "clara.txt"},
    {"id": "elias", "host": "ada", "name": "Elias Reed", "script": "elias.txt"},
    {"id": "theo", "host": "atlas", "name": "Theo Mercer", "script": "theo.txt"},
]


def load_cast() -> dict:
    data = json.loads((ROOT / "tools/tts/voice_cast.json").read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def short_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:  # noqa: BLE001
        return "nogit"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="kokoro-episodes")
    parser.add_argument("--episodes", default="", help="comma-separated character ids (default: all four)")
    parser.add_argument("--smoke-words", type=int, default=0, help="truncate each script for a fast test")
    parser.add_argument("--speed", type=float, default=SPEED)
    args = parser.parse_args()

    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cast = load_cast()
    wanted = [c for c in CHARACTERS if not args.episodes or c["id"] in args.episodes.split(",")]
    sha, date = short_sha(), dt.date.today().isoformat()
    pipelines: dict[str, object] = {}

    def pipeline_for(voice: str):
        language = "b" if voice.startswith("b") else "a"
        if language not in pipelines:
            pipelines[language] = KPipeline(lang_code=language)
        return pipelines[language]

    manifest = []
    for char in wanted:
        script = (DEMO / char["script"]).read_text().strip()
        if args.smoke_words:
            script = " ".join(script.split()[:args.smoke_words])
        voice = cast[char["host"]]["voice"]
        print(f"rendering {char['name']} ({char['id']}) voice={voice} words={len(script.split())}", flush=True)
        audio = [chunk for _, _, chunk in pipeline_for(voice)(script, voice=voice, speed=args.speed)]
        mixed = np.concatenate(audio) if audio else np.zeros(OUT_SR, dtype="float32")
        peak = float(np.max(np.abs(mixed))) if len(mixed) else 0.0
        if peak > 0.97:
            mixed = mixed * (0.97 / peak)
        config = f"kokoro-82M {voice} speed={args.speed}"
        title = f"{char['name']}, {sha}, {date}, {config}"
        dest = out / f"{title}.wav"
        sf.write(str(dest), mixed, OUT_SR)
        print(f"  saved {dest.name} ({len(mixed) / OUT_SR:.1f}s)", flush=True)
        manifest.append({
            "character": char["id"], "name": char["name"], "host": char["host"],
            "kokoro_voice": voice, "engine": "kokoro-82M", "title": title, "file": dest.name,
            "config": config, "words": len(script.split()),
            "duration_s": round(len(mixed) / OUT_SR, 1),
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        })

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "titles.txt").write_text("\n".join(row["title"] for row in manifest) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
