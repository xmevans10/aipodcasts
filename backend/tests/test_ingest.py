from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import parse_jats

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


if __name__ == "__main__":
    unittest.main()
