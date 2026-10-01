import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiments/full-run'))
from repair_batch import candidate


class RepairCandidateTests(unittest.TestCase):
    def test_chooses_fixable_grounded_draft_and_excludes_published_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed = Path(tmp); (seed / 'withheld').mkdir()
            def write(name, doi, passed=True, rule='term_before_use', fit='grounded'):
                artifact = {'host': 'noor', 'doi': doi, 'verification': {'factual': {'pass': passed}},
                            'audience': {'decision': 'revise', 'beat_fit': fit,
                                         'issues': [{'severity': 'major', 'rule': rule}]}}
                (seed / 'withheld' / name).write_text(json.dumps(artifact))
            write('published.json', '10.1/published')
            write('science-risk.json', '10.1/risk', rule='limitations')
            write('fixable.json', '10.1/fixable')
            write('failed.json', '10.1/failed', passed=False)
            write('offbeat.json', '10.1/offbeat', fit='weak')
            self.assertEqual(candidate(seed, 'noor', {'10.1/published'})['doi'], '10.1/fixable')
            with self.assertRaisesRegex(ValueError, 'no grounded'):
                candidate(seed, 'jax', set())
