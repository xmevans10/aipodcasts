"""The Actions handoff cannot render an incomplete or edited batch."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "full-run"))
from check_batch import check_batch  # noqa: E402
import run_all_shows  # noqa: E402

SEED = ROOT / "experiments" / "full-run" / "stage4-2026-09-22"


class FullRunActionsTests(unittest.TestCase):
    def test_partial_stage4_seed_is_valid_but_cannot_release(self):
        self.assertEqual(check_batch(SEED, require_all=False), (5, 16))
        with self.assertRaisesRegex(ValueError, "Only 5/16 approved"):
            check_batch(SEED)

    def test_edited_approved_script_fails_seed_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "seed"
            shutil.copytree(SEED, copy)
            path = copy / "transcripts" / "wild-company.json"
            artifact = json.loads(path.read_text())
            artifact["draft"]["body"] = artifact["draft"]["body"].replace(
                "A bird flips a leaf", "A bird hides a leaf", 1)
            path.write_text(json.dumps(artifact))
            with self.assertRaisesRegex(ValueError, "stale"):
                check_batch(copy, require_all=False)

    def test_resuming_reuses_only_approved_scripts(self):
        empty_selection = {"selected": [], "papers_pulled": 0, "candidates": 0,
                           "publicity_events": 0, "publicized_candidates": 0}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            args = SimpleNamespace(seed_dir=str(SEED), days=14, per_show=3,
                                   limit=80, out=str(out), decider="auto",
                                   select_only=False, no_verify=False)
            with patch.object(run_all_shows, "select_stories", return_value=empty_selection), \
                 patch.object(run_all_shows, "connect", side_effect=lambda: __import__("sqlite3").connect(":memory:")):
                run_all_shows.build(args)
            self.assertEqual(check_batch(out, require_all=False), (5, 16))
            self.assertEqual(len(list((out / "transcripts").glob("*.json"))), 5)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertFalse(manifest["release_ready"])
            star = next(e for e in manifest["shows"] if e["show"] == "Star Stuff")
            self.assertEqual(star["excluded_dois"], ["10.1038/s42004-026-01968-x"])

    def test_export_uses_draft_after_automatic_repair(self):
        old = {"title": "Old draft", "dek": "A result", "body": "old words here",
               "caveat": "small sample", "claims": []}
        revised = {**old, "title": "Revised draft", "body": "new words here"}
        source = {"title": "Paper title", "attribution": "Author Name",
                  "journal": "Journal", "url": "https://example.org/paper",
                  "license": "cc-by", "evidence_tier": "abstract"}
        selection = {"selected": [{"host": "fern", "doi": "10.1/example"}],
                     "papers_pulled": 1, "candidates": 1, "publicity_events": 0,
                     "publicized_candidates": 0}
        records = [{"source": json.dumps(source), "draft": json.dumps(old)},
                   {"source": json.dumps(source), "draft": json.dumps(revised)}]
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(seed_dir="", days=14, per_show=3,
                                   limit=80, out=tmp, decider="auto",
                                   select_only=False, no_verify=False)
            with patch.object(run_all_shows, "canonical_hosts", return_value=["fern"]), \
                 patch.object(run_all_shows, "select_stories", return_value=selection), \
                 patch.object(run_all_shows, "connect", side_effect=lambda: __import__("sqlite3").connect(":memory:")), \
                 patch.object(run_all_shows, "ingest_any", return_value="story-1"), \
                 patch.object(run_all_shows, "draft_story", return_value=old), \
                 patch.object(run_all_shows, "row", side_effect=records), \
                 patch.object(run_all_shows, "approve_auto", return_value={"status": "approved", "pass": True}):
                run_all_shows.build(args)
            artifact = json.loads((Path(tmp) / "transcripts" / "wild-company.json").read_text())
            self.assertEqual(artifact["draft"], revised)
            self.assertEqual(artifact["words"], 3)


if __name__ == "__main__":
    unittest.main()
