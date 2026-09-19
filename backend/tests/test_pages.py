import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages import render_episode, render_show

ENTRY = {
    "id": "a" * 20, "title": "A & B <script>alert(1)</script>", "dek": "Dek & more",
    "topic": "NATURE", "hostID": "fern", "minutes": 3, "isDemo": False,
    "body": "First paragraph.\n\nSecond paragraph.", "caveat": "Small sample & limits.",
    "audioURL": "https://example.com/audio/x.mp3",
    "sources": [{"title": "Paper <one>", "url": "https://doi.org/10.1/x", "attribution": "A, B", "license": "CC BY 4.0"}],
}


class PageTests(unittest.TestCase):
    def test_episode_page_has_preview_metadata(self):
        html = render_episode(ENTRY, "https://zwicky.app")
        self.assertIn('<link rel="canonical" href="https://zwicky.app/e/' + ENTRY["id"] + '">', html)
        self.assertIn('property="og:title"', html)
        self.assertIn('og:image" content="https://zwicky.app/icon.png"', html)
        self.assertIn('name="twitter:card" content="summary_large_image"', html)
        self.assertIn('https://example.com/audio/x.mp3', html)

    def test_episode_page_escapes_user_and_source_text(self):
        html = render_episode(ENTRY, "https://zwicky.app")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&amp;", html)
        self.assertIn("https://doi.org/10.1/x", html)

    def test_show_page_lists_episodes(self):
        html = render_show("fern", [ENTRY], "https://zwicky.app")
        self.assertIn("Wild Company", html)
        self.assertIn("https://zwicky.app/e/" + ENTRY["id"], html)

    def test_show_page_handles_no_episodes(self):
        html = render_show("noor", [], "https://zwicky.app")
        self.assertIn("Episodes are in production.", html)


if __name__ == "__main__":
    unittest.main()
