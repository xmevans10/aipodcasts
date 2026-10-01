import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from content_status import status
from export_usage import report
from pipeline import connect, reserve_call


class OperationsTests(unittest.TestCase):
    @patch('content_status.available')
    def test_coverage_collapses_cohosts_and_counts_only_approved_inventory(self, available):
        available.return_value = [(Path('a'), {'host': 'jax', 'evidence_tier': 'abstract'})]
        with tempfile.TemporaryDirectory() as tmp:
            result = status(Path(tmp), [{'id': 'one', 'hostID': 'kai', 'published': '2026-10-01'}])
        self.assertEqual(result['catalogShows'], 16)
        self.assertEqual(result['playableShows'], 1)
        self.assertEqual(result['approvedUnpublished'], 1)
        self.assertTrue(result['belowWeekBuffer'])
        row = next(r for r in result['shows'] if r['host'] == 'jax')
        self.assertEqual(row['publicEpisodes'], 1)
        self.assertEqual(row['approvedUnpublished'], 1)

    def test_duplicate_feed_fails(self):
        with self.assertRaises(ValueError):
            status(Path('.'), [{'id': 'same'}, {'id': 'same'}])

    def test_usage_preserves_unmeasured_attempts_as_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = connect(Path(tmp) / 'test.sqlite3')
            reserve_call(db, 'jev', 'failed')
            writer = reserve_call(db, 'openai', 'draft')
            db.execute('UPDATE calls SET input_tokens=100,output_tokens=20 WHERE id=?', (writer,))
            db.commit()
            result = report(db, '123')
            self.assertEqual(result['attempts'], 2)
            jev = next(r for r in result['usage'] if r['role'] == 'jev')
            self.assertIsNone(jev['inputTokens'])
            self.assertEqual(jev['tokenMeasuredAttempts'], 0)
            self.assertIsNone(result['actualChargeUSD'])
            self.assertNotIn('API_KEY', json.dumps(result))
            db.close()
