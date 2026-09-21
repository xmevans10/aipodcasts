import json
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import connect
from verify import Decision, Decider, verify_draft, verify_story, numeric_fidelity


class FakeDecider(Decider):
    name = "fake"

    def __init__(self, probability):
        self.probability = probability

    def ask(self, questions, state):
        return {q.id: Decision("boolean", self.probability >= 0.5, self.probability) for q in questions}


def fixtures(body="The crater is 222 metres wide.", quote="The crater is 222 metres wide",
             claim="The crater is 222 metres wide"):
    source = {"text": "The crater is 222 metres wide and formed recently."}
    packet = {"passages": [{"id": "p1", "text": source["text"]}], "source_title": "A source"}
    draft = {"title": "A Moon crater", "dek": "A short dek", "body": body, "caveat": "One limit",
             "claims": [{"claim": claim, "quote": quote}]}
    return source, packet, draft


class VerifyTests(unittest.TestCase):
    def test_numeric_fidelity_flags_invented_number(self):
        source, packet, draft = fixtures(body="The crater is 999 metres wide.")
        report = verify_draft(draft, source, packet, FakeDecider(0.99))
        self.assertFalse(report["pass"])
        self.assertTrue(any("numbers_not_in_evidence" in f for f in report["failures"]))

    def test_missing_quote_fails(self):
        source, packet, draft = fixtures(quote="Bananas orbit the Moon")
        report = verify_draft(draft, source, packet, FakeDecider(0.99))
        self.assertTrue(any("quote_not_in_source" in f for f in report["failures"]))

    def test_high_confidence_entailment_passes(self):
        source, packet, draft = fixtures()
        report = verify_draft(draft, source, packet, FakeDecider(0.95))
        self.assertTrue(report["pass"], report["failures"])
        self.assertEqual(report["backend"], "fake")

    def test_low_confidence_entailment_abstains(self):
        source, packet, draft = fixtures()
        report = verify_draft(draft, source, packet, FakeDecider(0.2))
        self.assertFalse(report["pass"])
        self.assertTrue(any("entail_0" in f for f in report["failures"]))

    def test_numeric_helper(self):
        self.assertEqual(numeric_fidelity("see 42 and 7", "nothing here"), ["42"])
        self.assertEqual(numeric_fidelity("only 3", "nothing"), [])

    def test_verify_story_reads_db(self):
        tmp = tempfile.TemporaryDirectory()
        db = connect(Path(tmp.name) / "t.sqlite3")
        source, packet, draft = fixtures()
        db.execute("INSERT INTO stories(id,source,host,draft,draft_input) VALUES(?,?,?,?,?)",
                   ("s1", json.dumps(source), "nova", json.dumps(draft), json.dumps(packet)))
        db.commit()
        report = verify_story(db, "s1", "deterministic")
        self.assertTrue(report["pass"], report["failures"])
        self.assertEqual(report["backend"], "deterministic")
        db.close()
        tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
