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
sys.path.insert(0, str(ROOT / "tools"))
from download_reviewed_batches import download_batches
from daily_release import select


class ReviewedBatchDownloadTests(unittest.TestCase):
    # Exercise the historic fixture under the review version that approved it.
    @patch("audience.REVIEW_VERSION", "audience-review-v1")
    def test_failed_run_supplies_only_its_strictly_approved_partial_scripts(self):
        downloaded = []

        def gh(command, **kwargs):
            if command[2] == "list":
                return SimpleNamespace(stdout=json.dumps([
                    {"databaseId": 9, "status": "completed", "conclusion": "success"},
                    {"databaseId": 11, "status": "in_progress", "conclusion": None},
                    {"databaseId": 12, "status": "completed", "conclusion": "failure"}]))
            downloaded.append(int(command[3]))
            shutil.copytree(ROOT / "experiments/full-run/stage4-2026-09-22", command[-1])
            return SimpleNamespace(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict(os.environ, {"LILT_REVIEWER": "openai"}):
            directory = Path(tmp) / "batches"
            report = download_batches(directory, 10, run=gh)
            picked = select(directory, [], "2026-09-30")
        self.assertEqual(downloaded, [12])
        self.assertEqual(report, {"runs": [12], "approved_scripts": 5})
        self.assertEqual([entry["show"] for _, entry in picked], ["Ground Truth", "Hive Mind"])

    def test_missing_and_unreviewed_artifacts_do_not_become_inventory(self):
        def gh(command, **kwargs):
            if command[2] == "list":
                return SimpleNamespace(stdout=json.dumps([
                    {"databaseId": i, "status": "completed", "conclusion": "failure"}
                    for i in (10, 11)]))
            if command[3] == "10":
                return SimpleNamespace(returncode=1, stderr="artifact expired")
            Path(command[-1]).mkdir()
            return SimpleNamespace(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "No usable reviewed"):
                download_batches(Path(tmp), 10, run=gh)

    def test_artifact_with_edited_approval_is_rejected(self):
        def gh(command, **kwargs):
            if command[2] == "list":
                return SimpleNamespace(stdout=json.dumps([
                    {"databaseId": 10, "status": "completed", "conclusion": "success"}]))
            target = Path(command[-1])
            shutil.copytree(ROOT / "experiments/full-run/stage4-2026-09-22", target)
            path = target / "transcripts/wild-company.json"
            artifact = json.loads(path.read_text())
            artifact["draft"]["body"] += " An unreviewed new sentence."
            path.write_text(json.dumps(artifact))
            return SimpleNamespace(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict(os.environ, {"LILT_REVIEWER": "openai"}):
            with self.assertRaisesRegex(ValueError, "No usable reviewed"):
                download_batches(Path(tmp), 10, run=gh)
