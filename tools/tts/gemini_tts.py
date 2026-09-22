#!/usr/bin/env python3
"""Render with Google's Gemini TTS (paid API; key from GEMINI_API_KEY).

Supports single-speaker and multi-speaker (`--speaker Name:Voice` repeated), a
`--system` instruction for persona/delivery, and inline audio tags in the transcript
(e.g. [whispers], [laughs], [cough], [sighs], [gasp]). The 30 prebuilt voices are
listed at https://ai.google.dev/gemini-api/docs/speech-generation.

Output is PCM16 24 kHz mono, wrapped as WAV. `usageMetadata` is printed so the token
cost can be checked against Google's price ($20 / 1M audio tokens; 25 tokens/second).

    export GEMINI_API_KEY=...
    python tools/tts/gemini_tts.py --model gemini-2.5-flash-preview-tts \
      --voice Charon --file script.txt --system "Calm, grounded science host." --out out.wav
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import urllib.error
import urllib.request
import wave
from pathlib import Path

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def build_payload(text, system, voices: list[tuple[str, str]], language: str | None):
    generation: dict = {"responseModalities": ["AUDIO"]}
    if len(voices) == 1:
        generation["speechConfig"] = {
            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voices[0][1]}}
        }
    else:
        generation["speechConfig"] = {
            "multiSpeakerVoiceConfig": {
                "speakerVoiceConfigs": [
                    {"speaker": name, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}
                    for name, voice in voices
                ]
            }
        }
    if language:
        generation["speechConfig"]["languageCode"] = language
    payload: dict = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": generation,
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    return payload


def pcm_rate(mime: str) -> int:
    match = re.search(r"rate=(\d+)", mime or "")
    return int(match.group(1)) if match else 24000


def write_wav(path: Path, pcm: bytes, rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm)


def call(model: str, key: str, payload: dict) -> dict:
    request = urllib.request.Request(
        ENDPOINT.format(model=model) + "?key=" + key,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise SystemExit(f"HTTP {error.code}: {error.read().decode()[:800]}") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-2.5-flash-preview-tts")
    parser.add_argument("--voice", help="single speaker voice (e.g. Charon)")
    parser.add_argument("--speaker", action="append", default=[], help="Name:Voice (repeat for multi-speaker)")
    parser.add_argument("--system", default="", help="persona/delivery instruction")
    parser.add_argument("--text", default="")
    parser.add_argument("--file")
    parser.add_argument("--language", default="")
    parser.add_argument("--out", default="gemini-out.wav")
    args = parser.parse_args()

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise SystemExit("Set GEMINI_API_KEY")

    text = open(args.file, encoding="utf-8").read().strip() if args.file else args.text
    if not text:
        raise SystemExit("Provide --text or --file")

    voices: list[tuple[str, str]] = []
    for spec in args.speaker:
        name, _, voice = spec.partition(":")
        voices.append((name, voice))
    if not voices:
        voices = [("Narrator", args.voice or "Charon")]

    payload = build_payload(text, args.system, voices, args.language or None)
    print(f"model={args.model} voices={voices} words={len(text.split())}", flush=True)
    data = call(args.model, key, payload)

    candidate = (data.get("candidates") or [{}])[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    audio = next((part["inlineData"] for part in parts if part.get("inlineData")), None)
    if audio is None:
        raise SystemExit("No audio in response: " + json.dumps(data)[:800])
    pcm = base64.b64decode(audio["data"])
    rate = pcm_rate(audio.get("mimeType", ""))
    out = Path(args.out)
    write_wav(out, pcm, rate)
    seconds = len(pcm) / 2 / rate
    usage = data.get("usageMetadata", {})
    audio_tokens = usage.get("candidatesTokenCount") or usage.get("totalTokenCount")
    cost = (audio_tokens or 0) / 1_000_000 * 20
    print(f"saved {out} rate={rate} seconds={seconds:.1f} prompt_tokens={usage.get('promptTokenCount')} "
          f"audio_tokens={audio_tokens} est_cost=${cost:.4f}", flush=True)


if __name__ == "__main__":
    main()
