import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/tts'))
from render_cache import reusable, save_json, sha256, signature
from bundle_shows import story_for


class RenderCacheTests(unittest.TestCase):
    def test_voice_script_speed_and_day_invalidate_reuse(self):
        arguments = [{'draft': {'body': 'hello'}}, {'rosa': {'geminiVoice': 'A'}}, 'google-cloud', 1.0, '2026-10-01']
        baseline = signature(*arguments)
        for position, value in [(0, {'draft': {'body': 'changed'}}), (1, {'rosa': {'geminiVoice': 'B'}}), (3, 1.1), (4, '2026-10-02')]:
            changed = arguments.copy(); changed[position] = value
            self.assertNotEqual(signature(*changed), baseline)

    @patch('mastering.validate_encoded')
    def test_reuse_requires_matching_provenance_audio_and_complete_words(self, measure):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp); name = 'abc'
            audio = out / f'{name}.m4a'; audio.write_bytes(b'\x00\x00\x00\x18ftypM4A ')
            transcript = {'host': 'rosa', 'show': 'Mycelium', 'doi': '10.1/x', 'source': {},
                          'draft': {'title': 'Title', 'dek': 'Dek', 'body': 'One real thought.', 'caveat': 'Limited.'}}
            payload = story_for(transcript, 4, '2026-10-01', episode=name)
            payload['renderProvenance'] = {'inputSHA256': 'sig', 'audioSHA256': sha256(audio)}
            save_json(out / f'{name}.json', payload)
            self.assertTrue(reusable(out, name, 'sig'))
            self.assertFalse(reusable(out, name, 'other'))
            payload['transcript'][0]['words'].pop()
            save_json(out / f'{name}.json', payload)
            self.assertFalse(reusable(out, name, 'sig'))
            audio.write_bytes(b'changed audio')
            self.assertFalse(reusable(out, name, 'sig'))
            self.assertEqual(measure.call_count, 1)

    @patch('mastering.validate_encoded', side_effect=ValueError('Bad master'))
    def test_failed_measurement_is_never_reused(self, measure):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp); audio = out / 'abc.m4a'; audio.write_bytes(b'\x00\x00\x00\x18ftypM4A ')
            payload = story_for({'host': 'rosa', 'show': 'Mycelium', 'source': {},
                                 'draft': {'title': 'T', 'dek': 'D', 'body': 'A word.', 'caveat': 'L'}}, 4, '2026-10-01', episode='abc')
            payload['renderProvenance'] = {'inputSHA256': 'sig', 'audioSHA256': sha256(audio)}
            save_json(out / 'abc.json', payload)
            self.assertFalse(reusable(out, 'abc', 'sig'))
