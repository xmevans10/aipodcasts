import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/tts'))
from select_voice_qa import select


class VoiceQaTests(unittest.TestCase):
    @patch.dict(os.environ, {'LILT_REVIEWER': 'openai'})
    @patch('audience.REVIEW_VERSION', 'audience-review-v1')
    def test_selects_three_contrasting_approved_scripts_without_editing(self):
        batch = ROOT / 'experiments/full-run/stage4-2026-09-22'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'selected'
            entries = select(batch, out)
            self.assertEqual([entry['host'] for entry in entries], ['fern', 'ines', 'amara'])
            self.assertEqual(len(list(out.glob('*.json'))), 3)
            for path in out.iterdir():
                self.assertEqual(path.read_bytes(), (batch / 'transcripts' / path.name).read_bytes())

    @patch.dict(os.environ, {'LILT_REVIEWER': 'openai'})
    def test_stale_scripts_are_rejected_before_any_qa_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'selected'
            with self.assertRaisesRegex(ValueError, 'stale'):
                select(ROOT / 'experiments/full-run/stage4-2026-09-22', out)
            self.assertFalse(out.exists())

    def test_daily_preparation_validates_with_the_detailed_reviewer(self):
        # Exercise the shared production shell handoff without network or synthesis.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / 'python3'
            binary.write_text(f'#!{sys.executable}\n' + '''import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['QA_HANDOFF_LOG'], 'a') as log:
    log.write(json.dumps({'args': args, 'reviewer': os.environ.get('LILT_REVIEWER')}) + '\\n')
if args[0] == '-c':
    print(0)
if args[0].endswith('daily_release.py') and '--out' in args:
    Path(args[args.index('--out') + 1]).mkdir(parents=True)
''')
            binary.chmod(0o755)
            log = root / 'calls.jsonl'
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                       QA_HANDOFF_LOG=str(log), LILT_REVIEWER='jev')
            result = subprocess.run(['bash', str(ROOT / 'scripts/prepare-daily-episodes.sh'),
                                     '2026-09-30', str(root / 'out')],
                                    cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            validations = [call for call in calls if call['args'][0].endswith(
                ('download_reviewed_batches.py', 'daily_release.py'))]
            self.assertEqual(len(validations), 3)
            self.assertTrue(all(call['reviewer'] == 'openai' for call in validations))
