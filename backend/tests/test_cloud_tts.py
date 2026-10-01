import os
import array
import io
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/tts"))
sys.path.insert(0, str(ROOT / "backend"))

import cloud_tts  # noqa: E402
import bundle_shows  # noqa: E402
from estimate_cost import estimate  # noqa: E402


def wav_data(rate=24000, channels=1):
    frames = array.array("h", [0, 8192, -8192, 16384])
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(frames.tobytes())
    return buffer.getvalue()


class CloudTtsTests(unittest.TestCase):
    def test_retries_transient_synthesis_errors_with_backoff(self):
        class TemporaryFailure(Exception):
            pass

        client = mock.Mock()
        client.synthesize_speech.side_effect = [TemporaryFailure(), TemporaryFailure(), "audio"]
        with mock.patch.object(cloud_tts.time, "sleep") as sleep:
            result = cloud_tts._synthesize_with_retry(client, {}, (TemporaryFailure,))
        self.assertEqual(result, "audio")
        self.assertTrue(all(call.kwargs["retry"] is None for call in client.synthesize_speech.call_args_list))
        self.assertEqual(client.synthesize_speech.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_stops_after_three_transient_synthesis_failures(self):
        class TemporaryFailure(Exception):
            pass

        client = mock.Mock()
        client.synthesize_speech.side_effect = TemporaryFailure()
        with mock.patch.object(cloud_tts.time, "sleep") as sleep:
            with self.assertRaises(TemporaryFailure):
                cloud_tts._synthesize_with_retry(client, {}, (TemporaryFailure,))
        self.assertEqual(client.synthesize_speech.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_every_host_has_a_distinct_google_cloud_voice(self):
        cast = bundle_shows.load_cast(ROOT / "tools/tts/voice_cast.json")
        voices = [host.get("geminiVoice") for host in cast.values()]
        self.assertTrue(all(voices))
        self.assertEqual(len(voices), len(set(voices)))

    def test_cast_rejects_duplicate_google_cloud_voice(self):
        cast = bundle_shows.load_cast(ROOT / "tools/tts/voice_cast.json")
        cast["dev"]["geminiVoice"] = cast["ines"]["geminiVoice"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cast.json"
            path.write_text(json.dumps(cast))
            with self.assertRaisesRegex(ValueError, "distinct geminiVoice"):
                bundle_shows.load_cast(path)

    def test_narration_uses_the_written_character_for_every_host(self):
        from hosts import HOSTS
        directions = set()
        for host_id, host in HOSTS.items():
            direction = cloud_tts.narration_direction(host_id)
            self.assertIn(host.persona, direction)
            self.assertIn(host.delivery, direction)
            self.assertIn("natural chuckle", direction)
            self.assertIn("Do not add words", direction)
            directions.add(direction)
        self.assertEqual(len(directions), len(HOSTS))

    def test_unknown_narration_character_fails_instead_of_becoming_generic(self):
        with self.assertRaises(KeyError):
            cloud_tts.narration_direction("missing-host")

    def test_episode_audio_cost_upper_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "episode.m4a").write_bytes(b"audio")
            (directory / "episode.json").write_text(json.dumps({
                "duration": 200,
                "story": {"id": "episode", "title": "A story", "hostID": "nova"},
            }))
            (directory / "index.json").write_text(json.dumps(["episode"]))
            (directory / "cost-estimate.json").write_text(json.dumps({"episodes": []}))
            self.assertEqual(estimate(directory)[0]["audioCostUpperBoundUSD"], 0.05)

    def test_decodes_cloud_linear16_wav_to_normalized_audio(self):
        audio = cloud_tts.decode_linear16(wav_data())
        self.assertEqual(audio.dtype, np.float32)
        self.assertTrue(np.allclose(audio, [0.0, 0.25, -0.25, 0.5]))

    def test_rejects_unexpected_cloud_audio_format(self):
        with self.assertRaisesRegex(ValueError, "mono 24 kHz PCM"):
            cloud_tts.decode_linear16(wav_data(rate=22050))

    def test_episode_renderer_routes_provider_voice_and_accent(self):
        with mock.patch.object(bundle_shows, "_GOOGLE_ACCENTS", {"Leda": "UK"}), \
             mock.patch.object(bundle_shows, "_GOOGLE_HOSTS", {"Leda": "nova"}), \
             mock.patch.object(cloud_tts, "synthesize", return_value=np.ones(4, dtype=np.float32)) as call:
            audio = bundle_shows.render_google_cloud("Hello.", "Leda", 1.0)
        self.assertEqual(len(audio), 4)
        call.assert_called_once_with("Hello.", "Leda", "UK", host_id="nova", passage="body")

    def test_episode_renderer_passes_position_without_changing_spoken_words(self):
        inputs = [{"text": text, "voice": "Leda"} for text in
                  ["A question?", "Here is the result.", "We still don't know."]]
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(bundle_shows, "render_google_cloud", return_value=np.ones(2400)) as render:
            bundle_shows.render_turns(inputs, Path(tmp) / "test.wav", 1.0, render=render)
        self.assertEqual([call.kwargs["passage"] for call in render.call_args_list],
                         ["opening", "body", "closing"])
        self.assertEqual([call.args[0] for call in render.call_args_list],
                         [item["text"] for item in inputs])

    def test_single_passage_gets_complete_arc_and_invalid_position_fails(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(bundle_shows, "render_google_cloud", return_value=np.ones(2400)) as render:
            bundle_shows.render_turns([{"text": "Hello.", "voice": "Leda"}],
                                     Path(tmp) / "test.wav", 1.0, render=render)
        self.assertEqual(render.call_args.kwargs["passage"], "complete")
        with self.assertRaises(KeyError):
            cloud_tts.narration_direction("nova", passage="unknown")


if __name__ == "__main__":
    unittest.main()


class NarrationUsageTests(unittest.TestCase):
    def test_failed_attempts_are_logged_without_script_or_credentials(self):
        class Transient(Exception): pass
        client = mock.Mock(); client.synthesize_speech.side_effect = [Transient(), 'audio']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'usage.jsonl'
            with mock.patch.dict(os.environ, {'LILT_AUDIO_USAGE_FILE': str(path)}), mock.patch.object(cloud_tts.time, 'sleep'):
                cloud_tts._synthesize_with_retry(client, {}, (Transient,), record=cloud_tts.record_usage)
            events = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual([e['event'] for e in events], ['attempt', 'transient_failure', 'attempt', 'response'])
            self.assertFalse(any('text' in e or 'apiKey' in e for e in events))
