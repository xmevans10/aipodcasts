import array
import json
import math
import sys
import tempfile
import wave
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tools/tts"))
sys.path.insert(0, str(ROOT / "tools"))
from bundle_shows import episode_key, slug, story_for, timings  # noqa: E402
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


class EpisodeIdTests(unittest.TestCase):
    def test_deterministic_and_opaque(self):
        first = episode_key("2026-09-21", "10.1/x", "Mycelium")
        self.assertEqual(first, episode_key("2026-09-21", "10.1/x", "Mycelium"))
        self.assertRegex(first, r"^[0-9a-f]{16}$")

    def test_distinct_per_episode(self):
        self.assertNotEqual(episode_key("2026-09-21", "10.1/x", "Mycelium"),
                            episode_key("2026-09-22", "10.1/x", "Mycelium"))
        self.assertNotEqual(episode_key("2026-09-21", "10.1/x", "Mycelium"),
                            episode_key("2026-09-21", "10.2/y", "Mycelium"))


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


class DialogueRenderTests(unittest.TestCase):
    def fixture(self, host='ines'):
        from test_dialogue import build_draft, SOURCE
        from hosts import HOSTS
        from bundle_shows import load_cast
        from verify import draft_fingerprint
        draft = build_draft()
        if host == 'jax':
            replacements = {'Ines Marlowe': HOSTS['jax'].name, 'Dev Raman': HOSTS['kai'].name}
            for turn in draft['turns']:
                turn['speaker'] = replacements[turn['speaker']]
                turn['text'] = turn['text'].replace(HOSTS['ines'].sign_off, HOSTS['jax'].sign_off).replace(HOSTS['dev'].sign_off, HOSTS['kai'].sign_off)
            for _ in range(2):
                draft['turns'] += [{'speaker': HOSTS[h].name, 'text': HOSTS[h].sign_off} for h in ['benny', 'chase']]
        import audience
        return ({'host': host, 'show': HOSTS[host].show, 'draft': draft, 'source': SOURCE,
                 'verification': {'pass': True, 'draft_sha256': draft_fingerprint(draft)},
                 'audience': {'pass': True, 'draft_sha256': draft_fingerprint(draft),
                              'contract_version': audience.CONTRACT_VERSION,
                              'review_version': audience.REVIEW_VERSION}},
                load_cast(ROOT / 'tools/tts/voice_cast.json'))

    def test_two_and_four_host_audio_offsets_and_payload(self):
        from bundle_shows import narration_inputs, render_turns, wav_duration, SR, TURN_GAP
        for host, count in [('ines', 2), ('jax', 4)]:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                artifact, cast = self.fixture(host)
                inputs = narration_inputs(artifact, cast)
                calls = []
                def synthesize(text, voice, speed):
                    calls.append((text, voice))
                    return [0.1] * (SR if len(calls) % 2 else SR * 2)
                wav = Path(tmp) / 'dialogue.wav'
                paragraphs = render_turns(inputs, wav, 1, render=synthesize)
                duration = wav_duration(wav)
                payload = story_for(artifact, duration, '2026-09-22', paragraphs=paragraphs)
                self.assertEqual(len(set(v for _, v in calls)), count)
                self.assertEqual([text for text, _ in calls], [t['text'] for t in artifact['draft']['turns']])
                self.assertEqual(len(payload['story']['hostIDs']), count)
                self.assertEqual(payload['story']['turns'], artifact['draft']['turns'])
                offset = 0
                for i, paragraph in enumerate(paragraphs):
                    turn_duration = 1 if i % 2 == 0 else 2
                    self.assertAlmostEqual(paragraph['words'][0]['start'], offset, places=3)
                    self.assertLess(paragraph['words'][-1]['start'], offset + turn_duration)
                    self.assertEqual(paragraph['speaker'], inputs[i]['speaker'])
                    self.assertEqual(paragraph['hostID'], inputs[i]['host'])
                    offset += turn_duration + TURN_GAP
                self.assertAlmostEqual(duration, offset - TURN_GAP)
                self.assertTrue(envelope_wav(wav))

    def test_rejects_unverified_unknown_and_missing_voices(self):
        from bundle_shows import narration_inputs
        artifact, cast = self.fixture()
        artifact['verification']['pass'] = False
        with self.assertRaisesRegex(ValueError, 'verification'):
            narration_inputs(artifact, cast)
        artifact['verification']['pass'] = True
        artifact['audience']['pass'] = False
        with self.assertRaisesRegex(ValueError, 'audience review'):
            narration_inputs(artifact, cast)
        artifact['audience'].update(decision='revise', beat_fit='grounded')
        with patch.dict('os.environ', {'LILT_ENTERTAINMENT_RELEASE': '1'}):
            self.assertTrue(narration_inputs(artifact, cast))
        artifact['audience']['decision'] = 'withhold'
        with patch.dict('os.environ', {'LILT_ENTERTAINMENT_RELEASE': '1'}):
            with self.assertRaisesRegex(ValueError, 'audience review'):
                narration_inputs(artifact, cast)
        artifact['audience']['decision'] = 'revise'
        artifact['audience']['pass'] = True
        stale = dict(artifact, audience={**artifact['audience'], 'draft_sha256': 'x' * 64})
        with self.assertRaisesRegex(ValueError, 'audience review is stale'):
            narration_inputs(stale, cast)
        with self.assertRaisesRegex(ValueError, 'Missing voice'):
            narration_inputs(artifact, {k: v for k, v in cast.items() if k != 'dev'})
        cast['dev']['voice'] = cast['ines']['voice']
        with self.assertRaisesRegex(ValueError, 'distinct'):
            narration_inputs(artifact, cast)
        artifact['draft']['turns'][0]['speaker'] = 'Unknown'
        with self.assertRaisesRegex(ValueError, 'speaker'):
            narration_inputs(artifact, cast)

    def test_edited_script_cannot_reuse_approval(self):
        from bundle_shows import narration_inputs
        artifact, cast = self.fixture()
        artifact['draft']['turns'][1]['text'] += ' A new sentence.'
        with self.assertRaisesRegex(ValueError, 'stale'):
            narration_inputs(artifact, cast)

    def test_empty_audio_fails(self):
        from bundle_shows import render_turns
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, 'empty'):
            render_turns([{'text': 'Hello.', 'voice': 'af_alloy'}], Path(tmp) / 'bad.wav', 1,
                         render=lambda *args: [])


if __name__ == "__main__":
    unittest.main()
