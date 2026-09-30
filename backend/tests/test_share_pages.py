import os
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from publish_feed import add_share_urls, episode_page, main, merge_feed, upload, verify_staged_assets  # noqa: E402


class SharePageTests(unittest.TestCase):
    def test_staged_asset_checks_use_the_working_public_edge_headers(self):
        from io import BytesIO
        from types import SimpleNamespace
        story = {"id": "episode-one", **{field: f"https://cdn.example/{field}"
                 for field in ("audioURL", "detailURL", "shareURL")}}

        def edge(request, timeout):
            # Reproduce the live edge's refusal of default urllib requests.
            if request.get_header("User-agent") != "curl/8.0":
                raise HTTPError(request.full_url, 403, "Forbidden", {}, BytesIO())
            self.assertEqual(request.get_method(), "HEAD")
            self.assertEqual(request.get_header("Cache-control"), "no-cache")
            response = unittest.mock.MagicMock()
            response.__enter__.return_value = SimpleNamespace(status=200)
            return response

        with patch("publish_feed.urlopen", side_effect=edge) as fetch:
            verify_staged_assets([story])
        self.assertEqual(fetch.call_count, 3)

    def test_staged_asset_http_failure_still_blocks_with_diagnostic(self):
        story = {"id": "episode-one", "audioURL": "https://cdn.example/missing"}
        error = HTTPError(story["audioURL"], 404, "Not Found", {}, None)
        with patch("publish_feed.urlopen", side_effect=error) as fetch, \
             patch("publish_feed.time.sleep"):
            with self.assertRaisesRegex(ValueError, "staged audioURL.*HTTP Error 404"):
                verify_staged_assets([story])
        self.assertEqual(fetch.call_count, 4)

    def story(self):
        return {
            "id": "episode-webwork-1", "title": "Silk & science", "dek": 'A "small" story',
            "topic": "NATURE", "minutes": 3, "body": "First paragraph.\n\nSecond <paragraph>.",
            "caveat": "AI narration.", "audioURL": "https://cdn.example/v1/audio/one.m4a",
            "sources": [{"title": "Research", "url": "https://example.org/paper",
                         "attribution": "Researchers"}],
        }

    def test_page_is_shareable_and_escapes_episode_copy(self):
        story = add_share_urls([{**self.story(), "published": "2026-09-23"}],
                               "https://cdn.example/", "v1")[0]
        self.assertEqual(story["shareURL"],
                         "https://cdn.example/v1/listen/episode-webwork-1.html")
        page = episode_page(story).decode()
        self.assertIn('rel="canonical" href="' + story["shareURL"] + '"', page)
        self.assertIn("<audio controls", page)
        self.assertIn("Silk &amp; science", page)
        self.assertIn("Second &lt;paragraph&gt;.", page)
        self.assertNotIn("Second <paragraph>.", page)
        self.assertIn('href="https://example.org/paper"', page)
        self.assertIn('property="og:audio" content="https://cdn.example/v1/audio/one.m4a"', page)
        self.assertIn('href="zwicky://episode/episode-webwork-1"', page)
        self.assertIn('property="article:published_time" content="2026-09-23"', page)
        self.assertIn('<time datetime="2026-09-23">2026-09-23</time>', page)

    def test_rejects_malformed_public_urls_and_skips_unsafe_sources(self):
        with self.assertRaisesRegex(ValueError, "HTTPS origin"):
            add_share_urls([self.story()], "https:missing-host", "v1")
        story = add_share_urls([self.story()], "https://cdn.example", "v1")[0]
        story["sources"].append({"title": "Unsafe", "url": "https:missing-host"})
        self.assertNotIn("Unsafe", episode_page(story).decode())
        story["audioURL"] = "https:missing-host"
        with self.assertRaisesRegex(ValueError, "HTTPS share and audio URLs"):
            episode_page(story)
        story["audioURL"] = "https://cdn.example/v1/audio/one.m4a"
        story["id"] = "../unsafe"
        with self.assertRaisesRegex(ValueError, "URL-safe slug"):
            episode_page(story)

    def test_dry_run_validates_pages_before_reporting_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "one.json"
            path.write_text(json.dumps({"story": {**self.story(), "body": ["invalid"]}}))
            with patch.dict(os.environ, {"R2_PUBLIC_BASE": "https://cdn.example"}):
                with patch.object(sys, "argv", ["publish_feed.py", "--episodes", directory,
                                                "--dry-run"]):
                    with self.assertRaisesRegex(ValueError, "transcript must be text"):
                        main()

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

    def test_daily_release_skips_unchanged_archive_pages(self):
        class Client:
            def __init__(self):
                self.keys = []

            def put_object(self, **kwargs):
                self.keys.append(kwargs["Key"])

        client = Client()
        story = add_share_urls([self.story()], "https://cdn.example", "v1")[0]
        with patch.dict(os.environ, {"R2_BUCKET": "test", "R2_PUBLIC_BASE": "https://cdn.example"}):
            with tempfile.TemporaryDirectory() as directory:
                result = upload([], [story], Path(directory), "v1", client=client, page_ids=set())
        self.assertEqual(client.keys, ["v1/feed.json"])
        self.assertEqual(result["listening_pages"], 0)

    def test_staging_keeps_feed_hidden_until_commit(self):
        class Client:
            def __init__(self):
                self.keys = []

            def upload_file(self, path, bucket, key, ExtraArgs):
                self.keys.append(key)

            def put_object(self, **kwargs):
                self.keys.append(kwargs["Key"])

        client = Client()
        story = add_share_urls([{**self.story(), "published": "2026-09-25"}],
                               "https://cdn.example", "v1")[0]
        with patch.dict(os.environ, {"R2_BUCKET": "test", "R2_PUBLIC_BASE": "https://cdn.example"}):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "one.m4a").write_bytes(b"audio")
                payload = {"_file": str(root / "one.json"), "story": story}
                upload([payload], [story], root, "v1", client=client, assets_only=True)
                self.assertEqual(client.keys, ["v1/audio/one.m4a", "v1/episodes/one.json",
                                               "v1/listen/episode-webwork-1.html"])
                client.keys.clear()
                upload([payload], [story], root, "v1", client=client, feed_only=True)
        self.assertEqual(client.keys, ["v1/feed.json"])


if __name__ == "__main__":
    unittest.main()
