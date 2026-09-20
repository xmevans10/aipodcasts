"""Objective, provenance-blind metrics for Chatterbox takes.

Everything here is deterministic signal/text analysis, so it can run on a free CI
runner with no API key and no listening model:

- duration, RMS/peak level, clipping ratio
- silence ratio and longest internal pause (via a short-time RMS gate)
- F0 mean and F0 variability in semitones (librosa.yin)
- ASR word-error rate against the intended script (faster-whisper, optional)
- hallucination flags: extra ASR words, match ratio, speaking rate

ASR is optional: if faster-whisper or its model cannot be loaded the rest of the
metrics still compute and `wer` stays None. Never let a metric crash a run.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

_WORD = re.compile(r"[a-z0-9']+")


def normalize_words(text: str) -> list[str]:
    return _WORD.findall(text.lower().replace("-", " "))


def wer(reference: str, hypothesis: str) -> dict:
    """Levenshtein word error rate with insertion/deletion/substitution breakdown."""
    ref = normalize_words(reference)
    hyp = normalize_words(hypothesis)
    n, m = len(ref), len(hyp)
    # dp[i][j] = edit distance between ref[:i] and hyp[:j]
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    distance = prev[m]
    subs = ins = dele = 0
    sm = SequenceMatcher(None, ref, hyp, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            subs += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            dele += i2 - i1
        elif tag == "insert":
            ins += j2 - j1
    return {
        "wer": round(distance / n, 4) if n else None,
        "ref_words": n,
        "hyp_words": m,
        "subs": subs,
        "insertions": ins,
        "deletions": dele,
        "match_ratio": round(sm.ratio(), 4) if n else None,
        "extra_words": m - n,
    }


class Asr:
    """Lazy faster-whisper wrapper; degrades to a no-op if unavailable."""

    def __init__(self, size: str = "base.en", compute_type: str = "int8"):
        self.size = size
        self.compute_type = compute_type
        self._model = None
        self.error = None

    def _load(self):
        if self._model is not None or self.error:
            return
        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self.size, device="cpu", compute_type=self.compute_type)
        except Exception as error:  # noqa: BLE001 - report, never crash
            self.error = f"{type(error).__name__}: {error}"

    def transcribe(self, path: str) -> str | None:
        self._load()
        if self._model is None:
            return None
        segments, _info = self._model.transcribe(path, beam_size=1, language="en", vad_filter=False)
        return " ".join(segment.text.strip() for segment in segments).strip()


def _db(x: float) -> float:
    import math

    return 20 * math.log10(max(abs(x), 1e-9))


def analyze_audio(path: str, script: str, asr: Asr | None = None) -> dict:
    """All metrics for one wav file. Imports heavy libs lazily so the core works anywhere."""
    import numpy as np
    import soundfile as sf

    wav, sr = sf.read(path, always_2d=False)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    wav = wav.astype("float32")
    n = len(wav)
    duration = n / sr if sr else 0.0

    peak = float(np.max(np.abs(wav))) if n else 0.0
    rms = float(np.sqrt(np.mean(wav.astype("float64") ** 2))) if n else 0.0
    clip_ratio = float(np.mean(np.abs(wav) > 0.99)) if n else 0.0

    # Short-time RMS gate for silence / pauses.
    frame = max(1, int(0.02 * sr))
    hop = max(1, int(0.01 * sr))
    if n >= frame:
        frames = np.lib.stride_tricks.sliding_window_view(wav, frame)[::hop]
        frame_rms = np.sqrt(np.mean(frames.astype("float64") ** 2, axis=1))
    else:
        frame_rms = np.array([rms])
    gate = max(float(np.max(frame_rms)) * 10 ** (-40 / 20), 1e-5)
    voiced = frame_rms > gate
    silence_ratio = float(1.0 - voiced.mean()) if len(voiced) else 0.0
    longest_pause = 0.0
    run = 0
    for flag in voiced:
        if not flag:
            run += 1
            longest_pause = max(longest_pause, run * hop / sr)
        else:
            run = 0

    # F0 (pitched frames only).
    try:
        import librosa

        f0 = librosa.yin(wav, fmin=60, fmax=400, sr=sr, frame_length=2048, hop_length=256)
        voiced_f0 = f0[(f0 > 60) & (f0 < 400) & np.isfinite(f0)]
        f0_mean = float(np.mean(voiced_f0)) if len(voiced_f0) else None
        if len(voiced_f0) > 2:
            f0_semitone_std = float(np.std(12 * np.log2(voiced_f0 / np.median(voiced_f0))))
        else:
            f0_semitone_std = None
    except Exception:  # noqa: BLE001
        f0_mean = None
        f0_semitone_std = None

    record = {
        "file": path,
        "duration_s": round(duration, 3),
        "sr": sr,
        "peak": round(peak, 4),
        "rms_dbfs": round(_db(rms), 2) if rms else None,
        "clip_ratio": round(clip_ratio, 5),
        "silence_ratio": round(silence_ratio, 4),
        "longest_pause_s": round(longest_pause, 3),
        "f0_mean_hz": round(f0_mean, 1) if f0_mean else None,
        "f0_std_semitones": round(f0_semitone_std, 3) if f0_semitone_std is not None else None,
        "script_words": len(normalize_words(script)),
        "speaking_rate_wpm": round(len(normalize_words(script)) / duration * 60, 1) if duration else None,
    }
    if asr is not None:
        heard = asr.transcribe(path)
        record["asr_error"] = asr.error
        if heard is not None:
            record["transcript"] = heard
            record.update(wer(script, heard))
            record["asr_wpm"] = round(len(normalize_words(heard)) / duration * 60, 1) if duration else None
    return record
