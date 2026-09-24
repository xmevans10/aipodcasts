import sys
import tempfile
import json
import unittest
from types import SimpleNamespace
from email import policy
from email.parser import BytesParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import newsletter
from newsletter import render_episode, build_message, available_episodes


class NewsletterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.episodes = self.out / "episodes"
        self.episodes.mkdir()
        newsletter.EPISODES = self.episodes
        story = {"id": "clara", "title": "Test episode", "dek": "Test dek", "topic": "NATURE",
                 "hostID": "fern", "minutes": 2, "body": "A test transcript.\n\nSecond paragraph.",
                 "caveat": "Test caveat", "sources": [], "audioURL": None}
        (self.episodes / "clara.json").write_text(json.dumps({"story": story}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_rendered_episode_fixture(self):
        ids = available_episodes()
        self.assertTrue(ids, "expected rendered fixture")
        for episode_id in ids:
            rendered = render_episode(episode_id, self.out, copy_audio=False)
            story = rendered["story"]
            self.assertIn(story["title"], rendered["html"])
            self.assertIn(story["title"], rendered["subject"])
            self.assertIn("More stories from Zwicky", rendered["html"])
            self.assertIn("Transcript", rendered["html"])
            self.assertIn(story["body"].split("\n\n")[0][:40], rendered["html"])

    def test_message_has_text_and_html_alternatives(self):
        rendered = render_episode("clara", self.out, copy_audio=False)
        message = build_message(rendered, sender="a@b.c", recipient="d@e.f")
        parts = [part.get_content_type() for part in message.walk()]
        self.assertIn("text/plain", parts)
        self.assertIn("text/html", parts)
        self.assertEqual(message["To"], "d@e.f")

    def test_missing_episode_is_rejected(self):
        with self.assertRaises(SystemExit):
            render_episode("does-not-exist", self.out, copy_audio=False)

    def test_staged_email_uses_hosted_audio_and_semantic_headings(self):
        story_path = self.episodes / "clara.json"
        data = json.loads(story_path.read_text())
        data["story"]["audioURL"] = "https://audio.example.org/clara.m4a"
        story_path.write_text(json.dumps(data))
        args = SimpleNamespace(out=str(self.out), episodes="clara", to="reader@example.org",
                               audio_url=None, attach_audio=False, deliver=False)
        newsletter.command_send(args)
        message = BytesParser(policy=policy.default).parsebytes(
            (self.out / "outbox" / "clara--reader_example_org.eml").read_bytes())
        html = message.get_body(preferencelist=("html",)).get_content()
        self.assertIn('href="https://audio.example.org/clara.m4a"', html)
        self.assertIn("<h1", html)
        self.assertIn(">Transcript</h2>", html)
        self.assertNotIn("<audio", html)
        self.assertIn("unsubscribe?token=preview", html)

    def test_staging_rejects_missing_public_audio(self):
        args = SimpleNamespace(out=str(self.out), episodes="clara", to="reader@example.org",
                               audio_url=None, attach_audio=False, deliver=False)
        with self.assertRaisesRegex(SystemExit, "public HTTPS audio URL"):
            newsletter.command_send(args)
        self.assertEqual(list((self.out / "outbox").glob("*.eml")), [])


if __name__ == "__main__":
    unittest.main()
