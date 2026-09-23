"""The Actions handoff cannot render an incomplete or edited batch."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "full-run"))
sys.path.insert(0, str(ROOT / "tools"))
from check_batch import check_batch  # noqa: E402
import run_all_shows  # noqa: E402
from extend_doi_exclusions import failed_dois, metadata_retry_dois  # noqa: E402

SEED = ROOT / "experiments" / "full-run" / "stage4-2026-09-22"


class FullRunActionsTests(unittest.TestCase):
    def setUp(self):
        # These committed seed fixtures predate Jev audience judgments.
        self.reviewer_env = patch.dict(os.environ, {"LILT_REVIEWER": "openai"})
        self.reviewer_env.start()
        self.addCleanup(self.reviewer_env.stop)

    def test_net_new_generation_excludes_all_previously_published_dois(self):
        candidates = [{"doi": "10.1234/old"}, {"doi": "10.1234/new"}]
        result = run_all_shows.exclude_published(candidates, {"10.1234/OLD"})
        self.assertEqual(result, [{"doi": "10.1234/new"}])

    def test_retry_never_repeats_a_failed_seed_paper(self):
        candidates = [{"doi": "10.1234/failed"}, {"doi": "10.1234/alternate"}]
        result = run_all_shows.exclude_failed_seed(
            candidates, {"status": "abstained", "doi": "10.1234/failed"}, set())
        self.assertEqual(result, [{"doi": "10.1234/alternate"}])

    def test_retry_excludes_failed_candidate_but_not_approved_seed(self):
        manifest = {"shows": [
            {"status": "approved", "doi": "10.1234/approved"},
            {"status": "audience_rejected", "doi": "10.1234/rejected"},
            {"status": "no_candidate", "errors": ["10.5678/failed: no abstract"]},
        ]}
        self.assertEqual(failed_dois(manifest), {"10.1234/rejected", "10.5678/failed"})

    def test_metadata_only_failure_can_be_retried_after_author_fallback(self):
        manifest = {"shows": [{"status": "no_candidate", "errors": [
            "10.1234/no-authors: ValueError: Named author metadata is required before generation"]}]}
        self.assertEqual(failed_dois(manifest), set())
        self.assertEqual(metadata_retry_dois(manifest), {"10.1234/no-authors"})

    def test_rejected_candidate_does_not_block_next_candidate_for_show(self):
        draft = {"title": "A measured result", "dek": "A careful summary",
                 "body": "Three useful science words", "caveat": "Small sample size",
                 "claims": [{"claim": "A supported result", "quote": "The evidence supports this result."}]}
        source = {"title": "Paper title", "attribution": "Author Name",
                  "journal": "Journal", "url": "https://doi.org/10.1234/new",
                  "license": "cc-by", "evidence_tier": "abstract"}
        selection = {"selected": [{"host": "fern", "doi": "10.1234/rejected"},
                                   {"host": "fern", "doi": "10.1234/approved"}],
                     "papers_pulled": 2, "candidates": 2, "publicity_events": 0,
                     "publicized_candidates": 0}
        records = {"source": json.dumps(source), "draft": json.dumps(draft)}
        review_results = [{"status": "audience_rejected", "pass": False,
                           "audience": {"decision": "revise"}},
                          {"status": "approved", "pass": True}]
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(seed_dir="", days=14, per_show=3,
                                   limit=80, out=tmp, decider="auto",
                                   select_only=False, no_verify=False)
            with patch.object(run_all_shows, "canonical_hosts", return_value=["fern"]), \
                 patch.object(run_all_shows, "select_stories", return_value=selection), \
                 patch.object(run_all_shows, "connect", side_effect=lambda: __import__("sqlite3").connect(":memory:")), \
                 patch.object(run_all_shows, "ingest_any", side_effect=["story-1", "story-2"]), \
                 patch.object(run_all_shows, "draft_story", return_value=draft), \
                 patch.object(run_all_shows, "row", return_value=records), \
                 patch.object(run_all_shows, "approve_auto", side_effect=review_results):
                run_all_shows.build(args)
            artifact = json.loads((Path(tmp) / "transcripts" / "wild-company.json").read_text())
            self.assertEqual(artifact["doi"], "10.1234/approved")

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
