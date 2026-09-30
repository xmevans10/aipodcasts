import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from publish_feed import validate_rendered_episodes


class PublicationValidationTests(unittest.TestCase):
    def payload(self):
        return {"_file": "one.json", "story": {"id": "episode-one", "body": "Hello science."},
                "duration": 2.0, "transcript": [{"words": [
                    {"text": "Hello", "start": 0.0, "end": 0.9},
                    {"text": "science.", "start": 1.0, "end": 1.9}]}]}

    def test_valid_episode_and_corrupt_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one.m4a"
            path.write_bytes(b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 20)
            validate_rendered_episodes([self.payload()], Path(tmp))
            path.write_bytes(b"an error page instead of audio")
            with self.assertRaisesRegex(ValueError, "invalid M4A"):
                validate_rendered_episodes([self.payload()], Path(tmp))

    def test_mismatched_identity_script_and_timings_are_rejected(self):
        cases = []
        payload = self.payload(); payload["story"]["id"] = "episode-other"
        cases.append((payload, "identity"))
        payload = self.payload(); payload["story"]["body"] = "Unreviewed replacement"
        cases.append((payload, "differs"))
        payload = self.payload(); payload["duration"] = float("nan")
        cases.append((payload, "duration"))
        for start, end in [(-1, 0.9), (float("nan"), 0.9), (1, 0.5), (0, 3), (True, 0.9)]:
            payload = self.payload()
            payload["transcript"][0]["words"][0].update(start=start, end=end)
            cases.append((payload, "timing"))
        payload = self.payload(); payload["transcript"][0]["words"][1]["start"] = 0.5
        cases.append((payload, "timing"))
        payload = self.payload(); payload["transcript"] = []
        cases.append((payload, "differs"))
        with tempfile.TemporaryDirectory() as tmp:
            for payload, diagnostic in cases:
                with self.subTest(diagnostic=diagnostic, payload=payload):
                    with self.assertRaisesRegex(ValueError, diagnostic):
                        validate_rendered_episodes([payload], Path(tmp))

    def test_duplicate_episode_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "one.m4a").write_bytes(b"\x00\x00\x00\x18ftypM4A ")
            payload = self.payload()
            with self.assertRaisesRegex(ValueError, "duplicate"):
                validate_rendered_episodes([payload, copy.deepcopy(payload)], Path(tmp))
