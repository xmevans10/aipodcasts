"""Google Cloud Text-to-Speech client for Gemini episode narration."""
from __future__ import annotations

import io
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


def _synthesize_with_retry(client, request, transient_errors):
    for attempt in range(3):
        try:
            return client.synthesize_speech(request=request)
        except transient_errors:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def synthesize(text: str, voice_name: str, accent: str) -> np.ndarray:
    """Synthesize text with ADC and retry transient Google service/rate errors."""
    from google.api_core.exceptions import DeadlineExceeded, InternalServerError, ServiceUnavailable, TooManyRequests

    if len(text.encode("utf-8")) > 4000:
        raise ValueError("Google Cloud TTS text limit is 4000 bytes per turn")

    texttospeech, client = _make_client()
    prompt = (f"Speak in a natural {accent} English voice for a science podcast. "
              "Use clear, warm, conversational delivery at a measured pace. "
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
    response = _synthesize_with_retry(client, request, transient)
    return decode_linear16(response.audio_content)
