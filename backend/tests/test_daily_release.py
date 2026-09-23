import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from daily_release import doi_from_url, select  # noqa: E402
from publish_feed import merge_feed  # noqa: E402
from verify_daily_feed import verify  # noqa: E402


class DailyReleaseTests(unittest.TestCase):
    def test_merge_preserves_archive_and_caps_daily_additions(self):
        older = {"id": "old", "published": "2026-09-21"}
        a = {"id": "a", "published": "2026-09-22"}
        b = {"id": "b", "published": "2026-09-22"}
        self.assertEqual({s["id"] for s in merge_feed([older], [a, b], day="2026-09-22")},
                         {"old", "a", "b"})
        self.assertEqual(len(merge_feed([older, a], [a, b], day="2026-09-22")), 3)
        with self.assertRaisesRegex(ValueError, "More than 2"):
            merge_feed([older, a, b], [{"id": "c", "published": "2026-09-22"}],
                       day="2026-09-22")

    def test_merge_refuses_to_replace_existing_story(self):
        with self.assertRaisesRegex(ValueError, "different metadata"):
            merge_feed([{"id": "a", "title": "Original", "published": "2026-09-22"}],
                       [{"id": "a", "title": "Changed", "published": "2026-09-22"}],
                       day="2026-09-22")

    def test_merge_replaces_older_edition_of_same_paper(self):
        older = {"id": "old", "hostID": "rosa", "published": "2026-09-22",
                 "sources": [{"url": "https://doi.org/10.1234/fungus"}],
                 "body": "old script"}
        revised = {**older, "id": "new", "published": "2026-09-23",
                   "body": "reviewed new script"}
        unrelated = {"id": "other", "hostID": "amara", "published": "2026-09-22",
                     "sources": [{"url": "https://doi.org/10.1234/hive"}]}
        merged = merge_feed([older, unrelated], [revised], day="2026-09-23")
        self.assertEqual({s["id"] for s in merged}, {"new", "other"})

    def test_selection_skips_published_doi_and_uses_oldest_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "100"; new = root / "200"
            for directory in (old, new):
                directory.mkdir()
                (directory / "transcripts").mkdir()
            (old / "manifest.json").write_text(json.dumps({"shows": [
                {"show": "Wild Company", "host": "fern", "doi": "10.1234/old"},
                {"show": "Mycelium", "host": "rosa", "doi": "10.1234/new"}]}))
            (new / "manifest.json").write_text(json.dumps({"shows": [
                {"show": "Hive Mind", "host": "amara", "doi": "10.1234/later"}]}))
            for directory, stem, body in ((old, "wild-company", "already published"),
                                           (old, "mycelium", "new episode"),
                                           (new, "hive-mind", "later episode")):
                (directory / "transcripts" / (stem + ".json")).write_text(
                    json.dumps({"draft": {"body": body}}))
            feed = [{"id": "published", "hostID": "fern", "published": "2026-09-22",
                     "sources": [{"url": "https://doi.org/10.1234/old"}],
                     "body": "already published"}]
            with patch("daily_release.check_batch", return_value=(16, 16)):
                picked = select(root, feed, "2026-09-22")
                first_day = select(root, [], "2026-09-22")
            self.assertEqual([(p.parent.parent.name, e["show"]) for p, e in picked],
                             [("100", "Mycelium")])
            self.assertEqual([e["show"] for _, e in first_day],
                             ["Wild Company", "Mycelium"])
            self.assertEqual(doi_from_url("https://doi.org/10.1038/ABC.1"), "10.1038/abc.1")

    def test_selection_requires_enough_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "need 2"):
                select(Path(tmp), [], "2026-09-22")

    def test_public_app_feed_must_contain_both_new_episodes(self):
        expected = [{"show": "Mycelium", "host": "rosa", "doi": "10.1234/fungus"},
                    {"show": "Hive Mind", "host": "amara", "doi": "10.1234/hive"}]
        feed = [{"id": str(i), "hostID": item["host"], "published": "2026-09-22",
                 "sources": [{"url": "https://doi.org/" + item["doi"]}],
                 "audioURL": "https://example.org/audio/" + str(i),
                 "detailURL": "https://example.org/episodes/" + str(i)}
                for i, item in enumerate(expected)]
        verify(feed, expected, "2026-09-22")
        with self.assertRaisesRegex(ValueError, "exactly two"):
            verify(feed[:1], expected, "2026-09-22")


if __name__ == "__main__":
    unittest.main()
