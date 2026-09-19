"""Pluggable narration providers.

Every provider takes ordered inputs `[{speaker, host, voice_env, text}]` and returns a
single MP3 byte string. Keys and endpoints come from the environment; nothing is
contacted until `pipeline.narrate` runs.

`VOICE_PROVIDER` selects the backend:
  elevenlabs (default) — text-to-dialogue for co-hosted, text-to-speech for single-host
  openai               — per-turn gpt-4o-mini-tts, concatenated (no cloning; preset voices)
  local                — POST to VOICE_LOCAL_URL: a self-hosted Chatterbox/Higgs/Dia wrapper

A self-hosted server only needs to accept
`{"inputs":[{"speaker","text","voice"}]}` and return audio bytes; that is the seam for the
open-source models in docs/VOICE-OPTIONS.md. No API key is required for `local`.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request

VALID_PROVIDERS = ("elevenlabs", "openai", "local")
_DEFAULT_TTS_VOICES = ("alloy", "echo", "fable", "onyx", "nova", "shimmer")


def selected_provider() -> str:
    name = os.environ.get("VOICE_PROVIDER", "elevenlabs").strip().lower()
    if name not in VALID_PROVIDERS:
        raise ValueError("Unknown VOICE_PROVIDER: " + name)
    return name


def strip_id3(data: bytes) -> bytes:
    """Drop a leading ID3v2 tag so concatenated chunks join cleanly."""
    if data[:3] != b"ID3" or len(data) < 10:
        return data
    size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
    return data[10 + size:]


def chunks(inputs: list[dict], budget: int = 1900) -> list[list[dict]]:
    """Group consecutive turns so each request stays inside the provider's safe budget."""
    grouped, current, size = [], [], 0
    for item in inputs:
        length = len(item["text"])
        if current and size + length > budget:
            grouped.append(current); current, size = [], 0
        current.append(item); size += length
    if current:
        grouped.append(current)
    return grouped


def _fetch(fetch, url: str, payload: dict, headers: dict, limit: int = 30_000_000) -> bytes:
    if fetch is not None:
        return fetch(url, payload=payload, headers=headers, limit=limit)
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=300) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Response exceeded size limit")
    return data


def _elevenlabs(inputs: list[dict], dialogue: bool, fetch) -> bytes:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError("Set ELEVENLABS_API_KEY, or use VOICE_PROVIDER=openai or local")
    voices: dict[str, str] = {}
    for item in inputs:
        voice = os.environ.get(item.get("voice_env", ""), "")
        if not voice or not re.fullmatch(r"[A-Za-z0-9_-]+", voice):
            raise ValueError("Configure a licensed voice for " + item.get("speaker", "?") + " (" + item.get("voice_env", "") + ")")
        voices[item["speaker"]] = voice
    headers = {"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    if not dialogue:
        url = "https://api.elevenlabs.io/v1/text-to-speech/" + voices[inputs[0]["speaker"]] + "?output_format=mp3_44100_128"
        payload = {"text": "\n\n".join(item["text"] for item in inputs),
                   "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
                   "voice_settings": {"stability": 0.55, "similarity_boost": 0.75}}
        return _fetch(fetch, url, payload, headers)
    model = os.environ.get("ELEVENLABS_DIALOGUE_MODEL", "eleven_v3")
    parts = []
    for group in chunks(inputs):
        payload = {"inputs": [{"text": item["text"], "voice_id": voices[item["speaker"]]} for item in group], "model_id": model}
        parts.append(_fetch(fetch, "https://api.elevenlabs.io/v1/text-to-dialogue?output_format=mp3_44100_128", payload, headers))
    return parts[0] + b"".join(strip_id3(part) for part in parts[1:])


def _openai(inputs: list[dict], fetch) -> bytes:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("Set OPENAI_API_KEY for VOICE_PROVIDER=openai")
    model = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    default_voice = os.environ.get("OPENAI_TTS_VOICE", "alloy")
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    parts = []
    for index, item in enumerate(inputs):
        host = item.get("host", "")
        voice = os.environ.get("VOICE_OPENAI_" + host.upper()) or _DEFAULT_TTS_VOICES[index % len(_DEFAULT_TTS_VOICES)] or default_voice
        payload = {"model": model, "input": item["text"], "voice": voice, "response_format": "mp3"}
        parts.append(_fetch(fetch, "https://api.openai.com/v1/audio/speech", payload, headers))
    return parts[0] + b"".join(strip_id3(part) for part in parts[1:])


def _local(inputs: list[dict], fetch) -> bytes:
    url = os.environ.get("VOICE_LOCAL_URL")
    if not url:
        raise ValueError("Set VOICE_LOCAL_URL for VOICE_PROVIDER=local")
    payload = {"inputs": [{"speaker": item.get("speaker", ""), "text": item["text"],
                           "voice": os.environ.get(item.get("voice_env", ""), "")} for item in inputs]}
    return _fetch(fetch, url, payload, {"Content-Type": "application/json"})


def synthesize(inputs: list[dict], *, dialogue: bool = False, fetch=None, provider: str | None = None) -> bytes:
    provider = provider or selected_provider()
    if not inputs:
        raise ValueError("No narration inputs")
    if provider == "elevenlabs":
        return _elevenlabs(inputs, dialogue, fetch)
    if provider == "openai":
        return _openai(inputs, fetch)
    if provider == "local":
        return _local(inputs, fetch)
    raise ValueError("Unknown VOICE_PROVIDER: " + provider)


def status() -> dict:
    """What is configured, for `pipeline.py doctor`. Presence only; never contacts a provider."""
    return {
        "selected": os.environ.get("VOICE_PROVIDER", "elevenlabs"),
        "elevenlabs": {"api_key": bool(os.environ.get("ELEVENLABS_API_KEY")),
                       "dialogue_model": os.environ.get("ELEVENLABS_DIALOGUE_MODEL", "eleven_v3")},
        "openai_tts": {"api_key": bool(os.environ.get("OPENAI_API_KEY")),
                       "model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")},
        "local": {"url": bool(os.environ.get("VOICE_LOCAL_URL"))},
    }
