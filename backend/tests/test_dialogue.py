import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hosts import HOSTS, dialogue_hosts
from dialogue import validate_dialogue, turns_body, turns_narration_inputs


def build_draft(pad=200):
    ines, dev = HOSTS["ines"], HOSTS["dev"]
    return {
        "title": "The quiet achievement",
        "dek": "A second opinion on how a leaf stays flat.",
        "turns": [
            {"speaker": ines.name,
             "text": "Today: The quiet achievement. Kate Harline and colleagues ask how Growth across a leaf stays flat. " + "word " * pad},
            {"speaker": dev.name, "text": "Here is why it matters outside the lab, framed as one clearly marked comparison."},
            {"speaker": ines.name, "text": "The method is careful, and the sample was small. " + ines.sign_off},
            {"speaker": dev.name, "text": "That caveat does not spoil the finding, it sharpens it."},
            {"speaker": ines.name, "text": "Exactly. A small clear result still earns its place."},
            {"speaker": dev.name, "text": "And that is the whole story. " + dev.sign_off},
        ],
        "caveat": "The sample was small.",
        "claims": [{"claim": "Coordination keeps the leaf flat",
                    "quote": "Growth coordination keeps the leaf flat"}],
    }


SOURCE = {"title": "Growth across a leaf", "attribution": "Kate Harline, Brendan Lane",
          "text": "The sample was small. Growth coordination keeps the leaf flat. We imaged the leaves every day."}


class DialogueHostTests(unittest.TestCase):
    def test_member_host_returns_both_presenters(self):
        duo = dialogue_hosts("ines")
        self.assertEqual([host.id for host in duo or []], ["ines", "dev"])

    def test_single_host_show_returns_none(self):
        self.assertIsNone(dialogue_hosts("nova"))

    def test_unknown_host_is_none(self):
        self.assertIsNone(dialogue_hosts("nobody"))


class DialogueValidationTests(unittest.TestCase):
    def test_valid_dialogue_passes(self):
        duo = dialogue_hosts("ines")
        validate_dialogue(build_draft(), SOURCE, duo)

    def test_requires_both_presenters(self):
        duo = dialogue_hosts("ines")
        draft = build_draft()
        draft["turns"] = [turn for turn in draft["turns"] if turn["speaker"] != HOSTS["dev"].name]
        with self.assertRaisesRegex(ValueError, "turn"):
            validate_dialogue(draft, SOURCE, duo)

    def test_rejects_three_in_a_row(self):
        duo = dialogue_hosts("ines")
        draft = build_draft()
        name = HOSTS["ines"].name
        draft["turns"] = [
            {"speaker": name, "text": "One turn of reasonable length here."},
            {"speaker": name, "text": "Two turns of reasonable length here."},
            {"speaker": name, "text": "Three turns of reasonable length here."},
            {"speaker": HOSTS["dev"].name, "text": "A reply of reasonable length here."},
            {"speaker": HOSTS["dev"].name, "text": "Another reply of reasonable length."},
            {"speaker": HOSTS["ines"].name, "text": "And a closing line of length."},
        ]
        with self.assertRaisesRegex(ValueError, "twice in a row"):
            validate_dialogue(draft, SOURCE, duo)

    def test_rejects_missing_sign_off(self):
        duo = dialogue_hosts("ines")
        draft = build_draft()
        draft["turns"][-1]["text"] = "A vague ending with no sign-off at all."
        with self.assertRaisesRegex(ValueError, "sign-off"):
            validate_dialogue(draft, SOURCE, duo)

    def test_rejects_paraphrased_quote(self):
        duo = dialogue_hosts("ines")
        draft = build_draft()
        draft["claims"][0]["quote"] = "Growth coordination is what keeps a leaf nice and flat"
        with self.assertRaisesRegex(ValueError, "quote not found"):
            validate_dialogue(draft, SOURCE, duo)

    def test_rejects_missing_paper_title(self):
        duo = dialogue_hosts("ines")
        draft = build_draft()
        draft["turns"][0]["text"] = "Today: The quiet achievement. Kate Harline and colleagues explain a leaf. " + "word " * 200
        with self.assertRaisesRegex(ValueError, "paper title"):
            validate_dialogue(draft, SOURCE, duo)


class DialogueHelpersTests(unittest.TestCase):
    def test_body_joins_turns_and_inputs_map_voices(self):
        duo = dialogue_hosts("ines")
        draft = build_draft()
        body = turns_body(draft)
        self.assertIn(HOSTS["ines"].sign_off, body)
        inputs = turns_narration_inputs(draft, duo)
        self.assertEqual(inputs[0]["voice_env"], HOSTS["ines"].voice_env)
        self.assertEqual(inputs[1]["voice_env"], HOSTS["dev"].voice_env)


if __name__ == "__main__":
    unittest.main()
