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

    def test_episode_audio_cost_upper_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "episode.m4a").write_bytes(b"audio")
            (directory / "episode.json").write_text(json.dumps({
                "duration": 200,
                "story": {"id": "episode", "title": "A story", "hostID": "nova"},
            }))
            self.assertEqual(estimate(directory)[0]["audioCostUpperBoundUSD"], 0.05)

    def test_decodes_cloud_linear16_wav_to_normalized_audio(self):
        audio = cloud_tts.decode_linear16(wav_data())
        self.assertEqual(audio.dtype, np.float32)
        self.assertTrue(np.allclose(audio, [0.0, 0.25, -0.25, 0.5]))

    def test_rejects_unexpected_cloud_audio_format(self):
        with self.assertRaisesRegex(ValueError, "mono 24 kHz PCM"):
            cloud_tts.decode_linear16(wav_data(rate=22050))

    def test_episode_renderer_routes_provider_voice_and_accent(self):
        bundle_shows._GOOGLE_ACCENTS = {"Leda": "UK"}
        with mock.patch.object(cloud_tts, "synthesize", return_value=np.ones(4, dtype=np.float32)) as call:
            audio = bundle_shows.render_google_cloud("Hello.", "Leda", 1.0)
        self.assertEqual(len(audio), 4)
        call.assert_called_once_with("Hello.", "Leda", "UK")


if __name__ == "__main__":
    unittest.main()
