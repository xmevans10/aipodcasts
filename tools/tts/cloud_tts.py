"""Google Cloud Text-to-Speech client for Gemini episode narration."""
from __future__ import annotations

import io
import datetime as dt
import hashlib
import json
from pathlib import Path
import uuid
import os
import time
import wave

import numpy as np

SAMPLE_RATE = 24_000
MODEL = "gemini-2.5-flash-tts"


def _make_client():
    from google.api_core.client_options import ClientOptions
    from google.cloud import texttospeech

    region = os.environ.get("GOOGLE_CLOUD_REGION", "eu").strip().lower()
    endpoint = "texttospeech.googleapis.com" if region == "global" else f"{region}-texttospeech.googleapis.com"
    return texttospeech, texttospeech.TextToSpeechClient(
        client_options=ClientOptions(api_endpoint=endpoint)
    )


def decode_linear16(wav_data: bytes) -> np.ndarray:
    with wave.open(io.BytesIO(wav_data), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, SAMPLE_RATE):
            raise ValueError("Google Cloud TTS returned audio outside the required mono 24 kHz PCM format")
        pcm = audio.readframes(audio.getnframes())
    return np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0


def record_usage(event: dict) -> None:
    path = os.environ.get('LILT_AUDIO_USAGE_FILE')
    if not path:
        return
    record = {**event, 'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'model': MODEL}
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a') as log:
        log.write(json.dumps(record, allow_nan=False) + '\n')


def _synthesize_with_retry(client, request, transient_errors, *, record=None):
    for attempt in range(3):
        if record: record({'event': 'attempt', 'attempt': attempt + 1})
        try:
            # Disable hidden SDK retries; this loop is the explicit three-attempt limit.
            response = client.synthesize_speech(request=request, retry=None)
            if record: record({'event': 'response', 'attempt': attempt + 1})
            return response
        except transient_errors:
            if record: record({'event': 'transient_failure', 'attempt': attempt + 1})
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


PASSAGE_DIRECTIONS = {
    "opening": "Begin as if welcoming one familiar listener. Let the opening question carry curiosity; leave room before its answer. Do not use an announcer's introduction.",
    "body": "Continue the conversation without restarting or greeting the listener again. Follow the meaning of this passage, not a repeated sing-song pattern.",
    "closing": "Let the final thought settle, then give the sign-off an easy, personal warmth. Do not turn the ending into a promotional announcement.",
    "complete": "Give the opening, explanation and ending a connected conversational arc.",
}


def narration_direction(host_id: str | None = None, *, passage: str = "body") -> str:
    """Performance direction from the same character used by the writer."""
    from hosts import HOSTS
    passage_direction = PASSAGE_DIRECTIONS[passage]
    character = "Use clear, natural conversational delivery. "
    if host_id is not None:
        host = HOSTS[host_id]  # A bad production mapping must not silently lose the character.
        character = (f"You are performing the fictional presenter {host.name}. "
            f"Character: {host.persona} Delivery: {host.delivery} "
            f"Emotional range: {', '.join(host.emotion_palette)}. ")
    return (character + passage_direction + " "
            "Let the supplied words carry genuine-feeling reactions and small imperfections. "
            "Use subtle changes in emphasis, pace and warmth, not a caricature. "
            "Shape each sentence around its meaning: lightly stress the word that changes the idea, "
            "leave a short beat after a surprising result, and slow slightly for an honest limit or admission. "
            "Keep uncertainty audible without sounding ominous or implying the evidence is stronger than written. "
            "A genuine question may lift in pitch; a settled statement should land. "
            "Vary phrase lengths and pauses naturally; avoid lifting the pitch at every sentence ending. "
            "Keep numbers and qualifications clear, at a conversational volume. "
            "Keep this character consistent across the episode's separate turns. "
            "A small natural chuckle or thoughtful breath is welcome when the supplied words earn it. "
            "Do not add words, ums or sound effects, and do not force a reaction into every line. ")


def synthesize(text: str, voice_name: str, accent: str, *, host_id: str | None = None,
               passage: str = "body") -> np.ndarray:
    """Synthesize text with ADC and retry transient Google service/rate errors."""
    from google.api_core.exceptions import DeadlineExceeded, InternalServerError, ServiceUnavailable, TooManyRequests

    if len(text.encode("utf-8")) > 4000:
        raise ValueError("Google Cloud TTS text limit is 4000 bytes per turn")

    texttospeech, client = _make_client()
    prompt = (f"Speak in a natural {accent} English voice for a science podcast. "
              + narration_direction(host_id, passage=passage) + " "
              "Read only the supplied text; do not add words.")
    request = {
        "input": texttospeech.SynthesisInput(text=text, prompt=prompt),
        "voice": texttospeech.VoiceSelectionParams(
            language_code="en-GB" if accent == "UK" else "en-US",
            name=voice_name, model_name=MODEL
        ),
        "audio_config": texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
        ),
    }
    transient = (DeadlineExceeded, InternalServerError, ServiceUnavailable, TooManyRequests)
    identity = {'requestID': uuid.uuid4().hex, 'hostID': host_id, 'voice': voice_name,
                'textSHA256': hashlib.sha256(text.encode()).hexdigest(), 'textBytes': len(text.encode())}
    response = _synthesize_with_retry(client, request, transient,
                                      record=lambda event: record_usage({**identity, **event}))
    audio = decode_linear16(response.audio_content)
    record_usage({**identity, 'event': 'decoded_audio', 'durationSeconds': len(audio) / SAMPLE_RATE})
    return audio
