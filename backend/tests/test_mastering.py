import array
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/tts'))
from mastering import measure, master, validate_encoded
from bundle_shows import to_m4a, wav_duration


class MasteringTests(unittest.TestCase):
    @patch('mastering.subprocess.run')
    def test_bad_encoded_levels_stop_release(self, run):
        base = {'input_i': '-16', 'input_tp': '-2', 'input_lra': '4',
                'input_thresh': '-26', 'target_offset': '0'}
        for field, bad in [('input_i', '-20'), ('input_tp', '0'), ('input_i', '-inf')]:
            run.return_value = subprocess.CompletedProcess([], 0, '', json.dumps({**base, field: bad}))
            with self.assertRaises(ValueError):
                validate_encoded(Path('episode.m4a'))
        run.return_value = subprocess.CompletedProcess([], 0, '', json.dumps(base))
        self.assertEqual(validate_encoded(Path('episode.m4a'))['integratedLUFS'], -16)

    def test_real_master_and_aac_keep_timing_and_meet_levels(self):
        if not shutil.which('ffmpeg') or subprocess.run(
                ['ffmpeg', '-version'], capture_output=True).returncode:
            if os.environ.get('REQUIRE_AUDIO_MASTERING_TEST') == '1':
                self.fail('Working FFmpeg is required in production CI')
            self.skipTest('Working FFmpeg unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / 'speech.wav'
            samples = array.array('h', (round(1400 * math.sin(2 * math.pi * 220 * i / 24000)
                                             * (0.7 + 0.3 * math.sin(i / 24000)))
                                        for i in range(24000 * 8)))
            with wave.open(str(wav), 'wb') as stream:
                stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(24000)
                stream.writeframes(samples.tobytes())
            master(wav)
            self.assertAlmostEqual(wav_duration(wav), 8, places=2)
            encoded = wav.with_suffix('.m4a')
            to_m4a(wav, encoded)
            levels = validate_encoded(encoded)
            self.assertLessEqual(levels['truePeakDBTP'], -1)
            self.assertAlmostEqual(levels['integratedLUFS'], -16, delta=1)
