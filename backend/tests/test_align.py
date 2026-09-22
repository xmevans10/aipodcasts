import math
import random
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/tts"))
import align  # noqa: E402

SR = 24000


def tone(seconds, amp=0.4, seed=1):
    random.seed(seed)
    frames = int(seconds * SR)
    out = []
    for i in range(frames):
        value = (0.5 * math.sin(2 * math.pi * 180 * i / SR)
                 + 0.3 * math.sin(2 * math.pi * 620 * i / SR)
                 + random.uniform(-0.2, 0.2))
        out.append(amp * value)
    return out


def silence(seconds):
    return [0.0] * int(seconds * SR)


def monotonic(words, results):
    starts = [r["start"] for r in results]
    if any(a > b for a, b in zip(starts, starts[1:])):
        raise AssertionError(f"starts not monotonic for {words}: {starts}")
    for r in results:
        if not (0 <= r["start"] <= r["end"]):
            raise AssertionError(f"bad span {r}")


class EnergyAlignmentTests(unittest.TestCase):
    def test_first_word_starts_where_speech_starts(self):
        words = ["The", "quick", "brown", "fox."]
        results = align.align(words, silence(0.4) + tone(1.0) + silence(0.2), SR)
        self.assertEqual([r["text"] for r in results], words)
        monotonic(words, results)
        self.assertGreater(results[0]["start"], 0.3)
        self.assertLess(results[0]["start"], 0.5)

    def test_clause_pause_lands_in_the_gap(self):
        words = ["The", "quick", "brown", "fox.", "Jumps", "over", "the", "dog."]
        audio = silence(0.3) + tone(0.8) + silence(0.4) + tone(1.0)
        results = align.align(words, audio, SR)
        monotonic(words, results)
        # the second clause must not start before the first clause's speech ends (1.1s)
        jump = next(r for r in results if r["text"] == "Jumps")
        self.assertGreater(jump["start"], 1.2)

    def test_longer_words_get_more_time(self):
        words = ["a", "a", "extraordinarily"]
        results = align.align(words, tone(1.5), SR)
        monotonic(words, results)
        short = results[0]["end"] - results[0]["start"]
        long = results[-1]["end"] - results[-1]["start"]
        self.assertGreater(long, short)

    def test_constant_audio_starts_at_zero(self):
        # the injected render in the render tests is a constant, so there is no silence
        results = align.align(["Hello", "world"], [0.1] * (SR * 2), SR)
        monotonic(["Hello", "world"], results)
        self.assertAlmostEqual(results[0]["start"], 0.0, places=3)

    def test_tiny_audio_falls_back_proportionally(self):
        results = align.align(["one", "two", "three", "four", "five"], [0.2] * 8, SR)
        monotonic(["one", "two", "three", "four", "five"], results)
        self.assertEqual(len(results), 5)

    def test_empty_words(self):
        self.assertEqual(align.align([], tone(0.5), SR), [])


class SegmentAnchorTests(unittest.TestCase):
    def test_ranges_map_words_to_chunk_text(self):
        words = ["Hello", "there.", "General", "Kenobi."]
        ranges = align._segment_word_ranges(words, ["Hello there.", "General Kenobi."])
        self.assertEqual(ranges, [(0, 2), (2, 4)])

    def test_ranges_reject_mismatched_text(self):
        words = ["Hello", "there.", "General", "Kenobi."]
        self.assertIsNone(align._segment_word_ranges(words, ["Something else entirely"]))

    def test_segments_align_within_their_slice(self):
        first = tone(0.8)
        second = tone(0.8, seed=2)
        samples = first + second
        words = ["Hello", "there.", "General", "Kenobi."]
        segments = [{"text": "Hello there.", "samples": len(first)},
                    {"text": "General Kenobi.", "samples": len(second)}]
        results = align.align(words, samples, SR, segments=segments)
        self.assertEqual([r["text"] for r in results], words)
        monotonic(words, results)
        general = next(r for r in results if r["text"] == "General")
        self.assertGreaterEqual(general["start"], 0.8 - 1e-6)
        self.assertLess(general["start"], 0.9)

    def test_bad_segments_fall_back_to_whole_turn(self):
        words = ["Hello", "there.", "General", "Kenobi."]
        segments = [{"text": "nonsense text", "samples": SR}, {"text": "more", "samples": SR}]
        results = align.align(words, tone(2.0), SR, segments=segments)
        self.assertEqual(len(results), len(words))
        monotonic(words, results)


class WeightTests(unittest.TestCase):
    def test_spelling_syllables(self):
        self.assertEqual(align._spelling_syllables("cat"), 1)
        self.assertEqual(align._spelling_syllables("water"), 2)
        self.assertEqual(align._spelling_syllables("banana"), 3)
        self.assertEqual(align._spelling_syllables("the"), 1)
        self.assertGreaterEqual(align._spelling_syllables(""), 1)

    def test_vowel_classifier(self):
        self.assertTrue(align._is_vowel("a"))
        self.assertTrue(align._is_vowel("'E"))
        self.assertTrue(align._is_vowel("@"))
        self.assertFalse(align._is_vowel("k"))
        self.assertFalse(align._is_vowel("tS"))

    def test_injected_phonemizer_sets_weights(self):
        calls = []

        def fake(word):
            calls.append(word)
            return list("a a a")

        results = align.align(["delta", "epsilon"], tone(1.0), SR, phonemizer=fake)
        self.assertEqual(calls, ["delta", "epsilon"])
        monotonic(["delta", "epsilon"], results)
        # epsilon has three vowel states against delta's three too (both from fake),
        # so both are timed; the check is that the injected path ran without espeak
        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
