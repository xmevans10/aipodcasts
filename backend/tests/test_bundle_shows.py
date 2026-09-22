import array
import json
import math
import sys
import tempfile
import wave
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tools/tts"))
from bundle_shows import slug, story_for, timings  # noqa: E402
from envelope import envelope_wav  # noqa: E402
from publish_feed import build_feed  # noqa: E402


def write_tone(path: Path, seconds: float, sr: int = 24000, freq: float = 440.0):
    frames = int(seconds * sr)
    data = array.array("h", (int(12000 * math.sin(2 * math.pi * freq * i / sr)) for i in range(frames)))
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(data.tobytes())


def artifact():
    body = "A dead leaf looks quiet until you remember that decay is a construction site too."
    return {
        "show": "Mycelium", "host": "rosa", "doi": "10.1/x",
        "source": {"title": "Cell wall chitin", "url": "http://dx.doi.org/10.1/x",
                   "attribution": "Trupti Gaikwad", "license": "cc-by", "doi": "10.1/x"},
        "draft": {"title": "Cell wall-forming chitin synthases", "dek": "A short dek.",
                  "body": body, "caveat": "One species only.", "claims": []},
    }


class TimingsTests(unittest.TestCase):
    def test_monotonic_and_inside_duration(self):
        words = "the quick brown fox jumps".split()
        starts = timings(words, 10.0)
        self.assertEqual(len(starts), len(words))
        self.assertTrue(all(a <= b for a, b in zip(starts, starts[1:])))
        self.assertGreaterEqual(starts[0], 0.0)
        self.assertLessEqual(starts[-1], 10.0)

    def test_length_weighted(self):
        starts = timings(["a", "bbbbbbbbbb"], 10.0)
        self.assertLess(starts[0], starts[1])

    def test_empty(self):
        self.assertEqual(timings([], 5.0), [])


class StoryTests(unittest.TestCase):
    def test_story_shape_and_https(self):
        payload = story_for(artifact(), 120.0, "2026-09-21")
        story = payload["story"]
        self.assertEqual(story["audioURL"], "bundle:mycelium.m4a")
        self.assertTrue(story["sources"][0]["url"].startswith("https://"))
        self.assertEqual(story["hostID"], "rosa")
        self.assertFalse(story["isDemo"])
        words = [w["text"] for p in payload["transcript"] for w in p["words"]]
        self.assertEqual(" ".join(words), story["body"])
        self.assertTrue(all(a <= b for a, b in zip(
            [w["start"] for p in payload["transcript"] for w in p["words"]],
            [w["start"] for p in payload["transcript"] for w in p["words"]][1:])))

    def test_slug(self):
        self.assertEqual(slug("Signal & Noise"), "signal-noise")


class EnvelopeTests(unittest.TestCase):
    def test_envelope_wav_shape_and_peak(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "t.wav"
            write_tone(wav, 3.0)
            frames = envelope_wav(wav)
        self.assertTrue(3.0 / 0.1 - 5 < len(frames) < 3.0 / 0.1 + 5)
        self.assertTrue(all(len(f) == 5 for f in frames))
        self.assertTrue(all(0.0 <= v <= 1.0 for f in frames for v in f))
        self.assertTrue(any(v > 0.5 for f in frames for v in f))


class FeedTests(unittest.TestCase):
    def test_build_feed_rewrites_audio_urls(self):
        episodes = [{"_file": "/tmp/gradient.json",
                     "story": {"id": "episode-gradient", "title": "T", "published": "2026-09-21"}}]
        feed = build_feed(episodes, "https://cdn.example.com/", "v1")
        self.assertEqual(feed[0]["audioURL"], "https://cdn.example.com/v1/audio/gradient.m4a")

    def test_build_feed_orders_newest_first(self):
        episodes = [{"_file": "/tmp/a.json", "story": {"id": "a", "published": "2026-09-19"}},
                    {"_file": "/tmp/b.json", "story": {"id": "b", "published": "2026-09-21"}}]
        feed = build_feed(episodes, "https://c.example", "v1")
        self.assertEqual([s["id"] for s in feed], ["b", "a"])


if __name__ == "__main__":
    unittest.main()
