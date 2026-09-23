import hashlib
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/tts"))
from bundle_shows import SR, render_turns, solo_sections, wav_duration  # noqa: E402
from sound_design import ASSETS, SoundDesign, transition_positions  # noqa: E402


class SoundDesignTests(unittest.TestCase):
    def test_cc0_assets_match_recorded_hashes(self):
        expected = {
            "soft-confirmation.wav": "e3f6641f2895127509460b184bf1e05f980446034edf423541a381adaf331bd8",
            "glass-accent.wav": "9f79c406ca3d9965841d8c4a239415111e3477f3858dd8125e666be3dcbffc6f",
            "steel-jingle.wav": "36f4101d685c10483825fe6c366cd847f37fdf96798e14ab18f5e8611639941c",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((ASSETS / name).read_bytes()).hexdigest(), digest)

    def test_every_episode_id_changes_the_signature(self):
        first = SoundDesign("0000000000000000")
        second = SoundDesign("0100000000000000")
        third = SoundDesign("0000000000000001")
        self.assertEqual(first.fingerprint, SoundDesign("0000000000000000").fingerprint)
        self.assertEqual(len({first.fingerprint, second.fingerprint, third.fingerprint}), 3)
        with self.assertRaisesRegex(ValueError, "16 hex"):
            SoundDesign("not-an-id")

    def test_cues_are_limited_to_story_breaks(self):
        self.assertEqual(transition_positions(3), set())
        self.assertEqual(transition_positions(5), {2})
        self.assertEqual(transition_positions(8), {3, 5})
        design = SoundDesign("0123456789abcdef")
        self.assertNotEqual(design.between(2, 6).tobytes(), design.between(4, 6).tobytes())

    def test_solo_paragraphs_become_sections_without_changing_words(self):
        body = "First scene has a fact.\n\nSecond scene explains it.\n\nThird scene ends."
        sections = solo_sections(body)
        self.assertEqual(len(sections), 3)
        self.assertEqual(" ".join(" ".join(sections).split()), " ".join(body.split()))

    def test_mix_preserves_narration_and_shifts_word_times(self):
        design = SoundDesign("0123456789abcdef")
        inputs = [{"host": "rosa", "text": f"Section {i}.", "voice": "test"} for i in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "episode.wav"
            paragraphs = render_turns(inputs, output, 1.0,
                                      render=lambda *_: [0.1] * SR, sound_design=design)
            with wave.open(str(output), "rb") as stream:
                audio = stream.readframes(stream.getnframes())
                self.assertEqual(stream.getframerate(), SR)
            self.assertEqual(len(paragraphs), len(inputs))
            self.assertAlmostEqual(paragraphs[0]["words"][0]["start"], len(design.intro()) / SR, places=3)
            self.assertAlmostEqual(paragraphs[2]["words"][0]["start"] - paragraphs[1]["words"][0]["start"],
                                   1 + len(design.between(2, 6)) / SR, places=3)
            self.assertGreater(wav_duration(output), paragraphs[-1]["words"][-1]["end"])
            for paragraph in paragraphs:
                start = round(paragraph["words"][0]["start"] * SR)
                self.assertEqual(int.from_bytes(audio[start * 2 + 200:start * 2 + 202], "little", signed=True), 3277)


if __name__ == "__main__":
    unittest.main()
