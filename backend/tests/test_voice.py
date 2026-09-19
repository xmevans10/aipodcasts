import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice import synthesize, chunks, strip_id3, selected_provider, status

MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb" + b"\x00" * 2000


def recorder(calls):
    def fetch(url, *, payload=None, headers=None, limit=None):
        calls.append({"url": url, "payload": payload, "headers": headers})
        return MP3
    return fetch


def inputs(large=False):
    size = 1500 if large else 12
    return [{"speaker": "Ines Marlowe", "host": "ines", "voice_env": "ELEVENLABS_VOICE_INES", "text": "a" * size},
            {"speaker": "Dev Raman", "host": "dev", "voice_env": "ELEVENLABS_VOICE_DEV", "text": "b" * size}]


class HelperTests(unittest.TestCase):
    def test_chunks_split_by_budget(self):
        grouped = chunks(inputs(large=True))
        self.assertEqual(len(grouped), 2)
        self.assertEqual([len(group) for group in grouped], [1, 1])

    def test_chunks_keep_small_inputs_together(self):
        self.assertEqual(len(chunks(inputs())), 1)

    def test_strip_id3_removes_tag(self):
        plain = strip_id3(b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"payload")
        self.assertTrue(plain.startswith(b"payload"))

    def test_selected_provider_default_and_invalid(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(selected_provider(), "elevenlabs")
        with mock.patch.dict(os.environ, {"VOICE_PROVIDER": "nope"}, clear=True):
            with self.assertRaisesRegex(ValueError, "Unknown VOICE_PROVIDER"):
                selected_provider()


class ElevenLabsTests(unittest.TestCase):
    def test_dialogue_uses_text_to_dialogue_with_both_voices(self):
        calls = []
        env = {"VOICE_PROVIDER": "elevenlabs", "ELEVENLABS_API_KEY": "k",
               "ELEVENLABS_VOICE_INES": "v1", "ELEVENLABS_VOICE_DEV": "v2"}
        with mock.patch.dict(os.environ, env, clear=True):
            audio = synthesize(inputs(), dialogue=True, fetch=recorder(calls))
        self.assertEqual(len(calls), 1)
        self.assertIn("text-to-dialogue", calls[0]["url"])
        voice_ids = [item["voice_id"] for item in calls[0]["payload"]["inputs"]]
        self.assertEqual(voice_ids, ["v1", "v2"])
        self.assertTrue(audio.startswith(b"ID3"))

    def test_dialogue_chunks_long_scripts(self):
        calls = []
        env = {"VOICE_PROVIDER": "elevenlabs", "ELEVENLABS_API_KEY": "k",
               "ELEVENLABS_VOICE_INES": "v1", "ELEVENLABS_VOICE_DEV": "v2"}
        with mock.patch.dict(os.environ, env, clear=True):
            synthesize(inputs(large=True), dialogue=True, fetch=recorder(calls))
        self.assertEqual(len(calls), 2)

    def test_single_uses_text_to_speech(self):
        calls = []
        env = {"VOICE_PROVIDER": "elevenlabs", "ELEVENLABS_API_KEY": "k", "ELEVENLABS_VOICE_INES": "v1"}
        with mock.patch.dict(os.environ, env, clear=True):
            synthesize([inputs()[0]], dialogue=False, fetch=recorder(calls))
        self.assertIn("text-to-speech/v1", calls[0]["url"])

    def test_missing_key_is_a_clear_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "ELEVENLABS_API_KEY"):
                synthesize(inputs(), dialogue=True, fetch=recorder([]))


class OpenAITests(unittest.TestCase):
    def test_openai_maps_speakers_to_preset_voices(self):
        calls = []
        env = {"VOICE_PROVIDER": "openai", "OPENAI_API_KEY": "k", "VOICE_OPENAI_INES": "onyx"}
        with mock.patch.dict(os.environ, env, clear=True):
            audio = synthesize(inputs(), dialogue=True, fetch=recorder(calls))
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["payload"]["voice"], "onyx")     # honoured per host
        self.assertTrue(audio.startswith(b"ID3"))


class LocalTests(unittest.TestCase):
    def test_local_posts_to_configured_url(self):
        calls = []
        env = {"VOICE_PROVIDER": "local", "VOICE_LOCAL_URL": "http://localhost:9000/tts"}
        with mock.patch.dict(os.environ, env, clear=True):
            synthesize(inputs(), dialogue=True, fetch=recorder(calls))
        self.assertEqual(calls[0]["url"], "http://localhost:9000/tts")
        self.assertEqual(len(calls[0]["payload"]["inputs"]), 2)


class StatusTests(unittest.TestCase):
    def test_status_reports_presence_without_network(self):
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "k"}, clear=True):
            report = status()
        self.assertTrue(report["elevenlabs"]["api_key"])
        self.assertFalse(report["local"]["url"])


if __name__ == "__main__":
    unittest.main()
