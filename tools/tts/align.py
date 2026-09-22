#!/usr/bin/env python3
"""Waveform-guided read-along alignment.

Kokoro renders a turn in one voice and we hold the exact reviewed script, so the words
are known — only their place in the audio is not. Instead of spreading word starts by
letter count across the turn (which drifts against the voice), this reads the audio:

  1. Frame energies locate the speech and its silences (leading/trailing silence, and
     the pauses at clause boundaries).
  2. Kokoro's own per-segment audio boundaries, when supplied, anchor the pieces so a
     long turn cannot drift; each piece is aligned on its own.
  3. A monotone dynamic-programming pass fits the known words onto those energy frames.
     Each syllable is a state whose duration weight comes from its phonemes (vowels and
     stressed syllables last longer); clause punctuation inserts a state that prefers
     silence, so a comma or full stop lands on the real pause.

Pure standard library. numpy is used only if present (it is in the render workflow) to
speed the frame extraction; espeak-ng supplies phonemes when installed, otherwise a
spelling-based syllable estimate stands in. Both are optional, so this is importable and
testable with no third-party packages.

The public entry point is :func:`align`, which returns ``{"text", "start", "end"}`` per
word — the same shape ``bundle_shows`` writes into the transcript sidecar.
"""
from __future__ import annotations

import math
import re
import shutil
import subprocess

# --- tuning -----------------------------------------------------------------

HOP = 0.02          # seconds per energy frame
WINDOW = 0.04       # seconds per analysis window
LAMBDA = 0.3        # weight of the duration prior (proportional pacing)
VOICED = 0.3        # speech-probability threshold that marks a frame as spoken
VOWEL_WEIGHT = 1.6  # relative duration of an unstressed vowel/syllable
STRESS_WEIGHT = 2.0  # a stressed vowel lasts longer
CONSONANT_WEIGHT = 1.0
PAUSE_STRONG = 2.5  # after . ! ?
PAUSE_WEAK = 1.4    # after , ; :

_STRONG_END = ".!?"
_WEAK_END = ",;:"
_VOWEL_FIRST = set("aeiouAEIOUV@360")  # espeak mnemonics that begin a vowel nucleus


# --- phonemes (optional) ----------------------------------------------------

_ESPEAK: str | None = None
_ESPEAK_CHECKED = False
_PHONEME_CACHE: dict[str, list[str]] = {}


def _espeak() -> str | None:
    global _ESPEAK, _ESPEAK_CHECKED
    if not _ESPEAK_CHECKED:
        _ESPEAK = shutil.which("espeak-ng") or shutil.which("espeak")
        _ESPEAK_CHECKED = True
    return _ESPEAK


def phonemize(word: str) -> list[str]:
    """Phoneme mnemonics for one word via espeak-ng, or [] when it is unavailable.

    One word per subprocess is fine because results are cached across a render; the
    render workflow renders thousands of words but reuses a small vocabulary.
    """
    if word in _PHONEME_CACHE:
        return _PHONEME_CACHE[word]
    exe = _espeak()
    if not exe:
        _PHONEME_CACHE[word] = []
        return []
    try:
        out = subprocess.run([exe, "-q", "-x", "--ipa=no"], input=word + "\n",
                             capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        _PHONEME_CACHE[word] = []
        return []
    phones = out.split()
    _PHONEME_CACHE[word] = phones
    return phones


def _is_vowel(phoneme: str) -> bool:
    core = phoneme.lstrip("'").rstrip(":")
    return bool(core) and core[0] in _VOWEL_FIRST


def _syllable_tokens(word: str, phonemizer) -> list[float]:
    """Duration weight per syllable, taken from phonemes when available."""
    phones = phonemizer(word) if phonemizer else []
    weights = []
    for phone in phones:
        if _is_vowel(phone):
            weights.append(STRESS_WEIGHT if phone.startswith("'") else VOWEL_WEIGHT)
        # consonants do not start a new syllable state; their time is folded into the
        # vowel they attach to, which is what read-along pacing cares about
    if weights:
        return weights
    return [VOWEL_WEIGHT] * _spelling_syllables(word)


def _spelling_syllables(word: str) -> int:
    """Fallback syllable estimate when espeak-ng is unavailable."""
    letters = re.sub(r"[^a-z]", "", word.lower())
    if not letters:
        return 1
    groups = re.findall(r"[aeiouy]+", letters)
    count = len(groups)
    if count > 1 and letters.endswith("e") and not letters.endswith(("le", "ee", "ye", "oe")):
        count -= 1
    return max(1, count)


# --- energy frames ----------------------------------------------------------


def _energy_frames(samples, sr: int, hop: float = HOP, window: float = WINDOW) -> list[float]:
    """Root-mean-square energy per frame, from samples in [-1, 1]."""
    hop_n = max(1, int(hop * sr))
    win_n = max(1, int(window * sr))
    try:
        import numpy as np  # optional; present in the render workflow, absent in tests
        x = np.asarray(samples, dtype=np.float64)
        if x.size < win_n:
            return [0.0]
        count = 1 + (x.size - win_n) // hop_n
        offsets = np.arange(count)[:, None] * hop_n + np.arange(win_n)[None, :]
        framed = x[offsets]
        return np.sqrt((framed * framed).mean(axis=1)).tolist()
    except Exception:
        pass

    total = len(samples)
    if total < win_n:
        return [0.0]
    frames = []
    for start in range(0, total - win_n + 1, hop_n):
        acc = 0.0
        for i in range(start, start + win_n):
            value = float(samples[i])
            acc += value * value
        frames.append(math.sqrt(acc / win_n))
    return frames


def _speech_probability(energies: list[float]) -> list[float]:
    """Energy mapped to 0..1 between the noise floor and the loud percentile, smoothed."""
    if not energies:
        return []
    ordered = sorted(energies)
    low = ordered[int(len(ordered) * 0.05)]
    high = ordered[int(len(ordered) * 0.95)]
    span = high - low
    if span <= 1e-9:
        return [1.0] * len(energies)
    values = [min(1.0, max(0.0, (e - low) / span)) for e in energies]
    return _smooth(values, 3)


def _smooth(values: list[float], width: int) -> list[float]:
    if width <= 1 or len(values) <= 2:
        return values
    half = width // 2
    out = []
    for i in range(len(values)):
        lo, hi = max(0, i - half), min(len(values), i + half + 1)
        window = values[lo:hi]
        out.append(sum(window) / len(window))
    return out


# --- dynamic-programming alignment -----------------------------------------


def _tokenize(words: list[str], phonemizer) -> tuple[list[float], list[bool], list[int]]:
    """States for the DP: duration weight, speech-preference, owning word index (-1 pause)."""
    weights: list[float] = []
    speech: list[bool] = []
    owner: list[int] = []
    for index, word in enumerate(words):
        syllables = _syllable_tokens(word, phonemizer)
        for weight in syllables or [VOWEL_WEIGHT]:
            weights.append(weight)
            speech.append(True)
            owner.append(index)
        pause = _pause_weight(word)
        if pause:
            weights.append(pause)
            speech.append(False)
            owner.append(-1)
    return weights, speech, owner


def _pause_weight(word: str) -> float:
    if not word:
        return 0.0
    last = word[-1]
    if last in _STRONG_END:
        return PAUSE_STRONG
    if last in _WEAK_END:
        return PAUSE_WEAK
    return 0.0


def _boundaries(weights: list[float], speech: list[bool], prob: list[float]) -> list[int]:
    """Boundary frame for every state: state ``k`` covers ``[b[k], b[k+1])``.

    A monotone DP decides where each state starts. A speech state pays for the silence it
    covers and a pause state pays for the speech it covers, so a comma or full stop
    expands into the real gap; a quadratic duration prior pulls every state toward the
    length its phoneme weight implies, which keeps word pacing proportional instead of
    collapsing onto the loudest moment.
    """
    states, frames = len(weights), len(prob)
    if states == 0 or frames == 0 or states > frames:
        return []
    if states * frames > 1_500_000:
        return []  # a very long turn without segment anchors: fall back, stay fast
    if states == 1:
        return [0, frames]

    total = sum(weights) or 1.0
    target = [max(1.0, frames * weight / total) for weight in weights]

    # prefix cost of covering frames with each kind of state: a speech state pays for the
    # silence it crosses, a pause state pays for the speech it crosses
    speech_prefix = [0.0] * (frames + 1)
    silence_prefix = [0.0] * (frames + 1)
    for t in range(frames):
        speech_prefix[t + 1] = speech_prefix[t] + (1.0 - prob[t])
        silence_prefix[t + 1] = silence_prefix[t] + prob[t]

    inf = float("inf")
    previous = [inf] * (frames + 1)
    previous[0] = 0.0
    parents: list[list[int]] = []
    for k in range(states):
        current = [inf] * (frames + 1)
        parent = [-1] * (frames + 1)
        expected = target[k]
        longest = int(expected * 3) + 4
        prefix = speech_prefix if speech[k] else silence_prefix
        remaining = states - (k + 1)
        for end in range(k + 1, frames - remaining + 1):
            lo = max(k, end - longest)
            best, best_start = inf, -1
            for start in range(lo, end):
                base = previous[start]
                if base == inf:
                    continue
                length = end - start
                cost = base + (prefix[end] - prefix[start]) + LAMBDA * (length - expected) ** 2 / expected
                if cost < best:
                    best, best_start = cost, start
            current[end] = best
            parent[end] = best_start
        parents.append(parent)
        previous = current

    if previous[frames] == inf:
        return []
    boundary = [0] * (states + 1)
    end = frames
    for k in range(states - 1, -1, -1):
        start = parents[k][end]
        boundary[k] = start
        boundary[k + 1] = end
        end = start
    return boundary


def _align_span(words: list[str], samples, sr: int, phonemizer) -> list[dict]:
    """Align one contiguous block of words against its own audio."""
    weights, speech, owner = _tokenize(words, phonemizer)
    prob = _speech_probability(_energy_frames(samples, sr))
    duration = len(samples) / sr
    if not prob or not words:
        return _proportional(words, duration)
    # Trim to the spoken region so leading/trailing silence is never charged to the first
    # or last word; the first word then starts exactly where the voice does.
    voiced = [t for t, value in enumerate(prob) if value >= VOICED]
    t0, t1 = (voiced[0], voiced[-1]) if voiced else (0, len(prob) - 1)
    bounds = _boundaries(weights, speech, prob[t0:t1 + 1])
    if not bounds:
        return _proportional(words, duration)
    result = []
    for index, word in enumerate(words):
        token_indices = [k for k, owner_index in enumerate(owner) if owner_index == index]
        first, last = token_indices[0], token_indices[-1]
        start = round(min((t0 + bounds[first]) * HOP, duration), 3)
        end = round(min((t0 + bounds[last + 1]) * HOP, duration), 3)
        if end < start:
            end = start
        result.append({"text": word, "start": start, "end": end})
    return result


def _proportional(words: list[str], duration: float) -> list[dict]:
    weights = [len(w) + 1 for w in words]
    total = sum(weights) or 1
    out, cumulative = [], 0.0
    for word, weight in zip(words, weights):
        start = round(min(duration, duration * cumulative / total), 3)
        cumulative += weight
        end = round(min(duration, duration * cumulative / total), 3)
        out.append({"text": word, "start": start, "end": end})
    return out


# --- segment anchoring (Kokoro) --------------------------------------------

def _segment_word_ranges(words: list[str], segment_texts: list[str]) -> list[tuple[int, int]] | None:
    """Map Kokoro's chunk texts onto word ranges, or None when the match is not clean."""
    joined = " ".join(words)
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for text in segment_texts:
        chunk = " ".join(text.split())
        if not chunk:
            ranges.append((cursor, cursor))
            continue
        found = joined.find(chunk, cursor)
        if found < 0:
            return None
        start_word = len(joined[:found].split())
        end_word = start_word + len(chunk.split())
        ranges.append((start_word, end_word))
        cursor = found + len(chunk)
    if joined[cursor:].strip():
        return None
    return ranges


def align(words: list[str], samples, sr: int, *, segments=None, hop: float = HOP,
          phonemizer=None) -> list[dict]:
    """Word timings from the audio.

    ``segments`` is an optional ordered list of ``{"text", "samples"}`` from Kokoro: when
    the chunk texts map cleanly onto the words, each chunk is aligned to its own slice of
    audio (tighter and drift-free); otherwise the whole turn is aligned in one pass.
    ``phonemizer`` overrides the espeak-backed phoneme source (used in tests).
    """
    words = list(words)
    if not words:
        return []
    phonemizer = phonemizer or phonemize

    if segments:
        texts = [s.get("text", "") for s in segments]
        ranges = _segment_word_ranges(words, texts)
        if ranges:
            result: list[dict] = []
            offset = 0
            for segment, (start_word, end_word) in zip(segments, ranges):
                count = int(segment.get("samples", 0))
                block = words[start_word:end_word]
                if block:
                    piece = _align_span(block, samples[offset:offset + count], sr, phonemizer)
                    for item in piece:
                        item["start"] = round(item["start"] + offset / sr, 3)
                        item["end"] = round(item["end"] + offset / sr, 3)
                    result.extend(piece)
                offset += count
            if len(result) == len(words):
                return result

    return _align_span(words, samples, sr, phonemizer)
