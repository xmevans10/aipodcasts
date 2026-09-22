"""Stage-3 behaviour: audience review, its failure matrix, and the release gates.

The point of these tests is that nothing here can produce an approval by accident. Every
way the reviewer can fail to deliver a verdict must leave the story pending, and every
path that reaches a listener must ask the gate.
"""
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import audience
import editorial_fixtures as fx
import pipeline as p
from hosts import HOSTS

SOURCE = {"title": "A source article about leaves",
          "text": "This is a measured result with considerable uncertainty. " * 250,
          "url": "https://doi.org/10.1371/journal.pbio.123",
          "attribution": "A. Researcher, B. Other", "license": "CC BY 4.0",
          "licenseURL": "https://creativecommons.org/licenses/by/4.0/"}

DRAFT = {
    "title": "A little scientific wonder", "dek": "An accessible explanation.",
    "body": ("How does a leaf stay flat? Today's episode is A little scientific wonder. "
             "The paper is A source article about leaves, by A. Researcher and colleagues. "
             + "Evidence is interesting and uncertainty matters. " * 40
             + "This result has considerable uncertainty. " + HOSTS["nova"].sign_off),
    "caveat": "This result has considerable uncertainty.",
    "claims": [{"claim": "The result has uncertainty.",
                "quote": "This is a measured result with considerable uncertainty."}]}

CLEAN_REVIEW = {
    "decision": "pass", "issues": [], "first_hard_sentence": "",
    "unexplained_terms": [], "beat_fit": "grounded",
    "listener_paraphrase": {
        "question": "how does a leaf stay flat",
        "method": "they watched leaves grow and measured the shape",
        "finding": "growth is coordinated across the leaf",
        "limit": "it is one measurement with a lot of uncertainty"}}

FAILING_REVIEW = {
    "decision": "revise",
    "issues": [{"severity": "blocker", "rule": "term_before_use",
                "span": "loop extrusion",
                "instruction": "Describe the clamping in ordinary words before naming it."}],
    "first_hard_sentence": "Loop-forming cohesin reduced direct coupling.",
    "unexplained_terms": ["loop extrusion", "PRIMPOL"], "beat_fit": "grounded",
    "listener_paraphrase": {"question": "why does copying stall",
                            "method": "they removed a protein and watched",
                            "finding": "something gathers at the stall",
                            "limit": "this was cells in a dish"}}


def provider_response(review):
    return json.dumps({"status": "completed", "output": [
        {"content": [{"type": "output_text", "text": json.dumps(review)}]}]}).encode()


class VerdictTests(unittest.TestCase):
    """Threshold behaviour, decided against the fixture set rather than a guessed number."""

    def test_a_clean_review_passes(self):
        report = audience.verdict(CLEAN_REVIEW, DRAFT, SOURCE["text"])
        self.assertTrue(report["pass"])
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["contract_version"], audience.CONTRACT_VERSION)

    def test_a_blocker_fails_even_when_the_reviewer_says_pass(self):
        review = {**CLEAN_REVIEW, "issues": FAILING_REVIEW["issues"]}
        report = audience.verdict(review, DRAFT, SOURCE["text"])
        self.assertFalse(report["pass"])
        self.assertTrue(any("term_before_use" in f for f in report["failures"]))

    def test_a_minor_issue_is_recorded_but_does_not_block(self):
        review = {**CLEAN_REVIEW, "issues": [
            {"severity": "minor", "rule": "analogy", "span": "like a bridge",
             "instruction": "Trim the second clause."}]}
        report = audience.verdict(review, DRAFT, SOURCE["text"])
        self.assertTrue(report["pass"])
        self.assertEqual(len(report["issues"]), 1)

    def test_unfounded_beat_fit_blocks_and_says_to_reselect(self):
        review = {**CLEAN_REVIEW, "beat_fit": "unfounded"}
        report = audience.verdict(review, DRAFT, SOURCE["text"])
        self.assertFalse(report["pass"])
        self.assertTrue(any("Reselect" in f for f in report["failures"]))

    def test_an_incomplete_paraphrase_blocks(self):
        review = {**CLEAN_REVIEW,
                  "listener_paraphrase": {**CLEAN_REVIEW["listener_paraphrase"], "limit": ""}}
        report = audience.verdict(review, DRAFT, SOURCE["text"])
        self.assertFalse(report["pass"])
        self.assertTrue(any("listener_paraphrase_incomplete" in f for f in report["failures"]))

    def test_paraphrase_numbers_are_a_diagnostic_not_an_oracle(self):
        """A reviewer supplying its own numbers is recorded, and does not silently pass."""
        review = {**CLEAN_REVIEW, "listener_paraphrase": {
            **CLEAN_REVIEW["listener_paraphrase"], "method": "they measured 417 leaves"}}
        report = audience.verdict(review, DRAFT, SOURCE["text"])
        self.assertIn("417", report["paraphrase_numbers_not_in_script"])

    def test_repair_instructions_carry_the_spans_and_terms(self):
        report = audience.verdict(FAILING_REVIEW, DRAFT, SOURCE["text"])
        text = audience.repair_instructions(report)
        self.assertIn("term_before_use", text)
        self.assertIn("PRIMPOL", text)
        self.assertIn("Loop-forming cohesin", text)
        self.assertIn("do not remove a number", text)


class MalformedResponseTests(unittest.TestCase):
    """Strict parsing: an unparseable review is not a verdict, and never a pass."""

    def _call(self, body):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "k", "OPENAI_MODEL": "m"}):
            return audience.review_script(DRAFT, SOURCE, "evidence", "The Long View", "space",
                                          fetch=lambda *a, **k: body)

    def test_incomplete_status(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            self._call(json.dumps({"status": "incomplete", "output": []}).encode())

    def test_no_output(self):
        with self.assertRaisesRegex(RuntimeError, "no review"):
            self._call(json.dumps({"status": "completed", "output": []}).encode())

    def test_not_json(self):
        with self.assertRaisesRegex(RuntimeError, "malformed JSON"):
            self._call(json.dumps({"status": "completed", "output": [
                {"content": [{"type": "output_text", "text": "not json"}]}]}).encode())

    def test_missing_fields(self):
        with self.assertRaisesRegex(RuntimeError, "missing fields"):
            self._call(provider_response({"decision": "pass"}))

    def test_unknown_decision(self):
        with self.assertRaisesRegex(RuntimeError, "unknown decision"):
            self._call(provider_response({**CLEAN_REVIEW, "decision": "looks fine to me"}))

    def test_unknown_severity(self):
        bad = {**CLEAN_REVIEW, "issues": [
            {"severity": "catastrophic", "rule": "r", "span": "s", "instruction": "i"}]}
        with self.assertRaisesRegex(RuntimeError, "unknown severity"):
            self._call(provider_response(bad))

    def test_transport_failure(self):
        def boom(*args, **kwargs):
            raise urllib.error.URLError("no route")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "k", "OPENAI_MODEL": "m"}):
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                audience.review_script(DRAFT, SOURCE, "e", "s", "b", fetch=boom)

    def test_no_provider_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(audience.available())
            with self.assertRaisesRegex(RuntimeError, "no provider configured"):
                audience.review_script(DRAFT, SOURCE, "e", "s", "b", fetch=lambda *a, **k: b"")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.db = p.connect(self.data / "test.sqlite3")
        self.id = "c" * 20
        self.db.execute("INSERT INTO stories(id,source,host) VALUES(?,?,?)",
                        (self.id, json.dumps(SOURCE), "nova"))
        self.db.commit()
        self.env = {"OPENAI_API_KEY": "k", "OPENAI_MODEL": "m"}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def staged(self, draft=None):
        self.db.execute("UPDATE stories SET state='review', draft=? WHERE id=?",
                        (json.dumps(draft or DRAFT), self.id))
        self.db.commit()

    def approved(self):
        self.staged()
        p.review(self.db, self.id, "Test Editor")

    def test_missing_review_fails_closed(self):
        self.approved()
        permitted, why = p.audience_ok(self.db, self.id)
        self.assertFalse(permitted)
        self.assertIn("never run", why)

    def test_legacy_rows_without_a_report_cannot_narrate(self):
        self.approved()
        with self.assertRaisesRegex(ValueError, "Audience review gate"):
            p.narrate(self.db, self.id)

    def test_publish_asks_the_gate_too(self):
        self.approved()
        audio = self.data / "audio"
        audio.mkdir()
        (audio / (self.id + ".mp3")).write_bytes(b"ID3" + b"x" * 2000)
        self.db.execute("UPDATE stories SET state='narrated', audio=? WHERE id=?",
                        (self.id + ".mp3", self.id))
        self.db.commit()
        with patch.object(p, "DATA", self.data):
            with self.assertRaisesRegex(ValueError, "Audience review gate"):
                p.publish(self.db, self.id)

    def test_a_pending_review_is_not_a_pass(self):
        self.staged()
        with patch.dict(os.environ, self.env):
            def boom(*args, **kwargs):
                raise urllib.error.URLError("down")
            with patch.object(p, "request", side_effect=boom):
                result = p.audience_check(self.db, self.id)
        self.assertEqual(result["status"], "pending")
        self.assertFalse(result["pass"])
        permitted, _ = p.audience_ok(self.db, self.id)
        self.assertFalse(permitted)

    def test_a_pass_unlocks_narration(self):
        self.approved()
        with patch.dict(os.environ, self.env):
            with patch.object(p, "request", return_value=provider_response(CLEAN_REVIEW)):
                result = p.audience_check(self.db, self.id)
        self.assertTrue(result["pass"])
        permitted, _ = p.audience_ok(self.db, self.id)
        self.assertTrue(permitted)

    def test_an_unchanged_draft_reuses_its_report_without_a_call(self):
        self.staged()
        with patch.dict(os.environ, self.env):
            with patch.object(p, "request",
                              return_value=provider_response(CLEAN_REVIEW)) as request:
                p.audience_check(self.db, self.id)
                second = p.audience_check(self.db, self.id)
                self.assertEqual(request.call_count, 1)
        self.assertEqual(second["status"], "cached")
        self.assertTrue(second["pass"])

    def test_an_edit_invalidates_the_report(self):
        self.staged()
        with patch.dict(os.environ, self.env):
            with patch.object(p, "request", return_value=provider_response(CLEAN_REVIEW)):
                p.audience_check(self.db, self.id)
        edited = {**DRAFT, "body": DRAFT["body"].replace("How does", "So how does")}
        self.db.execute("UPDATE stories SET draft=? WHERE id=?",
                        (json.dumps(edited), self.id))
        self.db.commit()
        permitted, why = p.audience_ok(self.db, self.id)
        self.assertFalse(permitted)
        self.assertIn("stale", why)

    def test_a_contract_version_change_invalidates_the_report(self):
        self.staged()
        with patch.dict(os.environ, self.env):
            with patch.object(p, "request", return_value=provider_response(CLEAN_REVIEW)):
                p.audience_check(self.db, self.id)
        stored = json.loads(self.db.execute(
            "SELECT audience_report FROM stories WHERE id=?", (self.id,)).fetchone()[0])
        stored["contract_version"] = "audience-contract-v0"
        self.db.execute("UPDATE stories SET audience_report=? WHERE id=?",
                        (json.dumps(stored), self.id))
        self.db.commit()
        permitted, why = p.audience_ok(self.db, self.id)
        self.assertFalse(permitted)
        self.assertIn("stale", why)

    def test_review_calls_are_charged_to_the_daily_cap(self):
        self.staged()
        with patch.dict(os.environ, {**self.env, "LILT_MAX_PROVIDER_CALLS_PER_DAY": "1"}):
            with patch.object(p, "request", return_value=provider_response(CLEAN_REVIEW)):
                p.audience_check(self.db, self.id)
                edited = {**DRAFT, "dek": "A different dek entirely."}
                self.db.execute("UPDATE stories SET audience_report=NULL, draft=? WHERE id=?",
                                (json.dumps(edited), self.id))
                self.db.commit()
                with self.assertRaisesRegex(ValueError, "cap reached"):
                    p.audience_check(self.db, self.id)
        rows = self.db.execute("SELECT provider FROM calls").fetchall()
        self.assertEqual([r["provider"] for r in rows], ["audience"])

    def test_an_override_is_explicit_and_recorded(self):
        self.approved()
        with self.assertRaisesRegex(ValueError, "named reviewer"):
            p.override_audience(self.db, self.id, "", "short")
        with self.assertRaisesRegex(ValueError, "reason of real substance"):
            p.override_audience(self.db, self.id, "Editor", "fine")
        p.override_audience(self.db, self.id, "Editor",
                            "Reviewer provider is down and this correction is urgent.")
        permitted, why = p.audience_ok(self.db, self.id)
        self.assertTrue(permitted)
        self.assertIn("Editor", why)


class ApproveAutoTests(unittest.TestCase):
    """Both gates, independently, plus a bounded audience-driven rewrite."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.db = p.connect(self.data / "test.sqlite3")
        self.id = "d" * 20
        self.db.execute("INSERT INTO stories(id,source,host,state,draft) VALUES(?,?,?,?,?)",
                        (self.id, json.dumps(SOURCE), "nova", "review", json.dumps(DRAFT)))
        self.db.commit()
        self.env = {"OPENAI_API_KEY": "k", "OPENAI_MODEL": "m",
                    "LILT_MAX_PROVIDER_CALLS_PER_DAY": "20"}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_a_failed_evidence_check_is_not_rescued_by_a_good_audience_report(self):
        with patch.object(p.verifier, "verify_story",
                          return_value={"pass": False, "failures": ["quote_not_in_source"],
                                        "reviewer": "auto-verifier:test"}):
            with patch.object(p, "request") as request:
                result = p.approve_auto(self.db, self.id)
        self.assertEqual(result["status"], "abstained")
        request.assert_not_called()  # no audience call once the science has failed

    def test_a_passed_evidence_check_does_not_substitute_for_comprehension(self):
        with patch.dict(os.environ, {**self.env, "LILT_AUDIENCE_REPAIRS": "0"}):
            with patch.object(p.verifier, "verify_story",
                              return_value={"pass": True, "failures": [],
                                            "reviewer": "auto-verifier:test"}):
                with patch.object(p, "request",
                                  return_value=provider_response(FAILING_REVIEW)):
                    result = p.approve_auto(self.db, self.id)
        self.assertEqual(result["status"], "audience_rejected")
        self.assertFalse(result["pass"])
        self.assertEqual(
            self.db.execute("SELECT state FROM stories WHERE id=?", (self.id,)).fetchone()[0],
            "review")

    def test_a_pending_review_does_not_spend_a_writer_call(self):
        """Re-rolling the writer cannot fix an unreachable reviewer."""
        def boom(*args, **kwargs):
            raise urllib.error.URLError("down")
        with patch.dict(os.environ, {**self.env, "LILT_AUDIENCE_REPAIRS": "2"}):
            with patch.object(p.verifier, "verify_story",
                              return_value={"pass": True, "failures": [],
                                            "reviewer": "auto-verifier:test"}):
                with patch.object(p, "request", side_effect=boom) as request:
                    result = p.approve_auto(self.db, self.id)
        self.assertEqual(result["status"], "audience_pending")
        self.assertEqual(result["audience_repairs"], 0)
        self.assertEqual(request.call_count, 1)

    def test_a_rejected_draft_is_rewritten_once_and_re_reviewed(self):
        better = {**DRAFT, "dek": "A clearer explanation of the same result."}
        responses = [
            provider_response(FAILING_REVIEW),                       # first review: reject
            json.dumps({"status": "completed", "output": [           # writer rewrite
                {"content": [{"type": "output_text", "text": json.dumps(better)}]}]}).encode(),
            provider_response(CLEAN_REVIEW),                         # second review: pass
        ]
        with patch.dict(os.environ, {**self.env, "LILT_AUDIENCE_REPAIRS": "1"}):
            with patch.object(p.verifier, "verify_story",
                              return_value={"pass": True, "failures": [],
                                            "reviewer": "auto-verifier:test"}):
                with patch.object(p, "request", side_effect=responses) as request:
                    result = p.approve_auto(self.db, self.id)
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["audience_repairs"], 1)
        writer_prompt = request.call_args_list[1].kwargs["payload"]["instructions"]
        self.assertIn("AUDIENCE REVIEW rejected", writer_prompt)
        self.assertIn("term_before_use", writer_prompt)
        record = self.db.execute("SELECT state, draft FROM stories WHERE id=?",
                                 (self.id,)).fetchone()
        self.assertEqual(record["state"], "approved")
        self.assertEqual(json.loads(record["draft"])["dek"], better["dek"])

    def test_repairs_are_bounded(self):
        writer = json.dumps({"status": "completed", "output": [
            {"content": [{"type": "output_text", "text": json.dumps(DRAFT)}]}]}).encode()
        with patch.dict(os.environ, {**self.env, "LILT_AUDIENCE_REPAIRS": "1"}):
            with patch.object(p.verifier, "verify_story",
                              return_value={"pass": True, "failures": [],
                                            "reviewer": "auto-verifier:test"}):
                with patch.object(p, "request", side_effect=[
                        provider_response(FAILING_REVIEW), writer,
                        provider_response(FAILING_REVIEW)]) as request:
                    result = p.approve_auto(self.db, self.id)
        self.assertEqual(result["status"], "audience_rejected")
        self.assertEqual(result["audience_repairs"], 1)
        self.assertEqual(request.call_count, 3)


class FixtureCalibrationTests(unittest.TestCase):
    """The fixture set is the calibration reference for a live reviewer pilot.

    Offline we can only assert the shape of the contract these cases encode. A real
    reviewer is exercised against them in a bounded live pilot; a green run here is not
    evidence that listeners understood anything.
    """

    def test_every_failing_case_names_a_rule_the_reviewer_is_asked_about(self):
        rules = audience.REVIEW_INSTRUCTIONS
        for keyword in ("one_question", "term_before_use", "numbers", "packet_gap",
                        "beat_fit", "dialogue", "analogy", "limitations", "title_honest"):
            with self.subTest(keyword):
                self.assertIn(keyword, rules)

    def test_the_reviewer_is_told_not_to_punish_difficulty(self):
        self.assertIn("Difficulty is not a defect", audience.REVIEW_INSTRUCTIONS)
        self.assertIn("flag its REMOVAL", audience.REVIEW_INSTRUCTIONS)

    def test_fixtures_cover_both_sides_of_the_gate(self):
        self.assertTrue(fx.cases(audience="fail"))
        self.assertTrue(fx.cases(audience="pass"))


if __name__ == "__main__":
    unittest.main()
