from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import parse_jats, parse_arxiv_html, is_cc_by, paragraphs_from_text, source_from_core

LONG = ("We measured many samples across sites and found a strong consistent effect. " * 8)


def jats(license_text="https://creativecommons.org/licenses/by/4.0/", doi="10.1234/x"):
    return f'''<?xml version="1.0"?>
<article><front>
<journal-meta><journal-title-group><journal-title>Test Journal</journal-title></journal-title-group></journal-meta>
<article-meta>
  <title-group><article-title>A surprising finding</article-title></title-group>
  <contrib-group><contrib contrib-type="author"><name><given-names>Ada</given-names><surname>Lovelace</surname></name></contrib></contrib-group>
  <permissions><license><license-p>{license_text}</license-p></license></permissions>
  <article-id pub-id-type="doi">{doi}</article-id>
  <abstract><p>{LONG}</p></abstract>
</article-meta></front>
<body><p>{LONG}</p></body></article>'''.encode()


class IngestTests(unittest.TestCase):
    def test_parse_jats_cc_by(self):
        source = parse_jats(jats(), "10.1234/x")
        self.assertEqual(source["doi"], "10.1234/x")
        self.assertTrue(source["license"].startswith("CC BY"))
        self.assertIn("Ada Lovelace", source["attribution"])
        self.assertEqual(source["journal"], "Test Journal")
        self.assertGreater(len(source["passages"]), 0)
        self.assertGreater(len(source["text"]), 400)

    def test_parse_jats_rejects_non_cc(self):
        with self.assertRaises(ValueError):
            parse_jats(jats(license_text="All rights reserved."), "10.1234/x")

    def test_parse_jats_rejects_doi_mismatch(self):
        with self.assertRaises(ValueError):
            parse_jats(jats(), "10.9999/other")

    def test_is_cc_by(self):
        self.assertTrue(is_cc_by("https://creativecommons.org/licenses/by/4.0/"))
        self.assertFalse(is_cc_by("https://creativecommons.org/licenses/by-nc-nd/4.0/"))
        self.assertFalse(is_cc_by(""))

    def test_paragraphs_from_text(self):
        many = paragraphs_from_text("One. Two. Three. Four. Five. Six. Seven. Eight.")
        self.assertGreater(len(many), 1)
        blocks = paragraphs_from_text("First block.\n\nSecond block with more text.")
        self.assertEqual(len(blocks), 2)

    def test_source_from_core_prefers_full_text_and_checks_doi(self):
        work = {"doi": "10.1/x", "title": "A study", "fullText": "Sentence here. " * 150,
                "abstract": "short", "authors": [{"name": "Ada Lovelace"}], "publisher": "Repo",
                "license": "cc-by", "downloadUrl": "https://example.org/paper.pdf"}
        source = source_from_core(work, "10.1/x")
        self.assertEqual(source["evidence_tier"], "full")
        self.assertEqual(source["attribution"], "Ada Lovelace")
        self.assertGreater(len(source["passages"]), 1)
        self.assertIsNone(source_from_core(work, "10.9/other"))

    def test_parse_arxiv_html_drops_chrome_and_references(self):
        html = (b"<html><body><h2>1 Introduction</h2><p>" + b"meaningful paper sentence " * 6 +
                b"</p><h2>Report GitHub Issue</h2><p>Content selection saved. Describe the issue below:</p>"
                b"<h2>References</h2><p>a reference paragraph that is long enough to be captured normally.</p>"
                b"</body></html>")
        _text, passages = parse_arxiv_html(html)
        self.assertEqual(len(passages), 1)
        self.assertIn("Introduction", passages[0]["section"])


if __name__ == "__main__":
    unittest.main()
