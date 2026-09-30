import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_content_health import todays_episodes


class PublicContentHealthTests(unittest.TestCase):
    def story(self, name, day):
        return {"id": name, "published": day,
                **{field: f"https://cdn.example/{name}/{field}"
                   for field in ("audioURL", "detailURL", "shareURL")}}

    def test_old_working_catalog_cannot_pass_todays_release_check(self):
        old = [self.story(str(i), "2026-09-25") for i in range(4)]
        with self.assertRaisesRegex(ValueError, "has 0"):
            todays_episodes(old, "2026-09-30")
        current = [self.story(str(i), "2026-09-30") for i in (4, 5)]
        self.assertEqual(todays_episodes(old + current, "2026-09-30"), current)

    def test_duplicate_ids_and_bad_asset_urls_fail_health(self):
        story = self.story("one", "2026-09-30")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            todays_episodes([story, story], "2026-09-30")
        story["audioURL"] = "http://cdn.example/audio"
        with self.assertRaisesRegex(ValueError, "invalid public asset"):
            todays_episodes([story], "2026-09-30")
