"""Integrity of the audience-contract regression set.

These tests do not exercise product behaviour; they keep the shared calibration set
honest so stage-2 and stage-3 tests can rely on it.
"""
import unittest

import editorial_fixtures as fx


class FixtureIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.data = fx.load()
        self.cases = self.data["cases"]

    def test_ids_are_unique(self):
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_case_has_spoken_text(self):
        for case in self.cases:
            with self.subTest(case["id"]):
                self.assertTrue(fx.spoken(case).strip())

    def test_declared_checks_are_documented(self):
        known = set(self.data["deterministic_checks"])
        for case in self.cases:
            with self.subTest(case["id"]):
                self.assertLessEqual(set(case["deterministic"]), known)

    def test_verdicts_are_consistent(self):
        for case in self.cases:
            with self.subTest(case["id"]):
                self.assertIn(case["audience"], ("pass", "fail"))
                if case["deterministic"]:
                    # A deterministic defect is never an acceptable episode.
                    self.assertEqual(case["audience"], "fail")
                if case["audience"] == "pass":
                    self.assertEqual(case["severity"], "none")
                    self.assertIsNone(case["improvement"])
                else:
                    self.assertIn(case["severity"], ("blocker", "major"))
                    self.assertTrue(case["improvement"])

    def test_formats_are_covered(self):
        formats = {case["format"] for case in self.cases}
        self.assertEqual(formats, {"solo", "duo", "quad"})

    def test_positive_controls_exist_for_hard_science(self):
        """A gate must be able to pass a difficult subject, not just an easy one."""
        passing = {case["id"] for case in fx.cases(audience="pass")}
        self.assertIn("good_hard_term_explained", passing)
        self.assertIn("good_duo_progressive", passing)
        self.assertGreaterEqual(len(passing), 4)

    def test_failure_modes_are_covered(self):
        issues = " ".join(case["issue"] for case in fx.cases(audience="fail"))
        for expected in ("internal-instruction leakage", "incomprehensible", "causality",
                         "simulation presented as reality", "too many numbers",
                         "wrong show", "packet gap"):
            with self.subTest(expected):
                self.assertIn(expected, issues)


if __name__ == "__main__":
    unittest.main()
