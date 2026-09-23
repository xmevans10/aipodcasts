"""Deterministic, speech-safe sound design for rendered episodes.

The eight notes of the opener encode all 64 bits of the episode ID. Every ID gets a
different PCM stinger, while a quiet CC0 sample gives the series a shared sound.
Effects play in gaps between narration sections; nothing is mixed over speech.
"""
from __future__ import annotations

import array
import hashlib
import math
import sys
import wave
from pathlib import Path

SR = 24000
ASSETS = Path(__file__).resolve().parents[2] / "assets/audio/kenney"
PITCHES = (311.127, 349.228, 391.995, 466.164)  # Eb, F, G, Bb; fits the steel sample
STEP = 0.18
STINGER_SECONDS = 1.62


def silence(seconds: float) -> array.array:
    return array.array("h", [0]) * round(seconds * SR)


def read_asset(name: str, directory: Path = ASSETS) -> array.array:
    with wave.open(str(directory / name), "rb") as stream:
        if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1, 2, SR):
            raise ValueError(f"Sound asset must be mono 16-bit {SR} Hz: {name}")
        samples = array.array("h")
        samples.frombytes(stream.readframes(stream.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def quiet(samples: array.array, gain: float) -> array.array:
    return array.array("h", (round(max(-32767, min(32767, sample * gain))) for sample in samples))


def overlay(base: array.array, extra: array.array, at: int = 0) -> array.array:
    for index, sample in enumerate(extra):
        place = at + index
        if place >= len(base):
            break
        base[place] = max(-32767, min(32767, base[place] + sample))
    return base


def stinger(episode_id: str, steel: array.array) -> array.array:
    """Encode each of the ID's eight bytes as pitch, length and brightness.

    The mapping is injective: 2 pitch bits + 2 duration bits + 4 brightness bits.
    The common steel sample sits quietly under the notes, so the brand has continuity.
    """
    if len(episode_id) != 16:
        raise ValueError("Episode ID must be 16 hex digits")
    try:
        identifier = bytes.fromhex(episode_id)
    except ValueError as exc:
        raise ValueError("Episode ID must be 16 hex digits") from exc
    result = silence(STINGER_SECONDS)
    overlay(result, quiet(steel, 0.15), 0)
    for index, value in enumerate(identifier):
        pitch = PITCHES[value & 3]
        length = 0.105 + ((value >> 2) & 3) * 0.018
        brightness = 0.10 + (value >> 4) * 0.025
        start = round(index * STEP * SR)
        for frame in range(round(length * SR)):
            t = frame / SR
            envelope = (1 - math.exp(-t * 115)) * math.exp(-t * 17)
            tone = math.sin(2 * math.pi * pitch * t) + brightness * math.sin(4 * math.pi * pitch * t)
            sample = round(9000 * envelope * tone)
            place = start + frame
            result[place] = max(-32767, min(32767, result[place] + sample))
    return result


def transition_positions(section_count: int) -> set[int]:
    """At most two story breaks, with no cue for short episodes or every speaker turn."""
    if section_count < 4:
        return set()
    if section_count < 6:
        return {section_count // 2}
    return {position for position in (round(section_count / 3), round(2 * section_count / 3))
            if 1 <= position < section_count}


class SoundDesign:
    def __init__(self, episode_id: str, directory: Path = ASSETS):
        self.episode_id = episode_id
        self.steel = read_asset("steel-jingle.wav", directory)
        self.effects = (read_asset("soft-confirmation.wav", directory),
                        read_asset("glass-accent.wav", directory))
        self.signature = stinger(episode_id, self.steel)

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.signature.tobytes()).hexdigest()

    def intro(self) -> array.array:
        return self.signature + silence(0.28)

    def between(self, completed: int, total: int) -> array.array:
        positions = sorted(transition_positions(total))
        if completed not in positions:
            return silence(0.18)
        choice = (int(self.episode_id[:2], 16) + positions.index(completed)) % len(self.effects)
        return silence(0.12) + quiet(self.effects[choice], 0.20) + silence(0.20)

    def outro(self) -> array.array:
        return silence(0.22) + quiet(self.steel, 0.12)
