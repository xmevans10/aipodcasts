import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from publish_feed import add_share_urls, episode_page, merge_feed, upload  # noqa: E402


class SharePageTests(unittest.TestCase):
    def story(self):
        return {
            "id": "episode-webwork-1", "title": "Silk & science", "dek": 'A "small" story',
            "topic": "NATURE", "minutes": 3, "body": "First paragraph.\n\nSecond <paragraph>.",
            "caveat": "AI narration.", "audioURL": "https://cdn.example/v1/audio/one.m4a",
            "sources": [{"title": "Research", "url": "https://example.org/paper",
                         "attribution": "Researchers"}],
        }

    def test_page_is_shareable_and_escapes_episode_copy(self):
        story = add_share_urls([self.story()], "https://cdn.example/", "v1")[0]
        self.assertEqual(story["shareURL"],
                         "https://cdn.example/v1/listen/episode-webwork-1.html")
        page = episode_page(story).decode()
        self.assertIn('rel="canonical" href="' + story["shareURL"] + '"', page)
        self.assertIn("<audio controls", page)
        self.assertIn("Silk &amp; science", page)
        self.assertIn("Second &lt;paragraph&gt;.", page)
        self.assertNotIn("Second <paragraph>.", page)
        self.assertIn('href="https://example.org/paper"', page)

    def test_existing_feed_can_gain_share_link_without_changing_episode(self):
        old = {**self.story(), "published": "2026-09-22",
               "shareURL": "https://cdn.example/v1/listen/episode-webwork-1.html"}
        incoming = {key: value for key, value in old.items() if key != "shareURL"}
        merged = merge_feed([old], [incoming], day="2026-09-22")
        self.assertEqual(len(merged), 1)

    def test_pages_publish_before_feed(self):
        class Client:
            def __init__(self):
                self.keys = []

            def put_object(self, **kwargs):
                self.keys.append(kwargs["Key"])

        client = Client()
        story = add_share_urls([self.story()], "https://cdn.example", "v1")[0]
        with patch.dict(os.environ, {"R2_BUCKET": "test", "R2_PUBLIC_BASE": "https://cdn.example"}):
            with tempfile.TemporaryDirectory() as directory:
                upload([], [story], Path(directory), "v1", client=client)
        self.assertEqual(client.keys, ["v1/listen/episode-webwork-1.html", "v1/feed.json"])


if __name__ == "__main__":
    unittest.main()
