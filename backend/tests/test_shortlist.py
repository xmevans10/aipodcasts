import datetime as dt
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import connect
from shortlist import rank, report


def inverted(text):
    index = {}
    for position, word in enumerate(text.split()):
        index.setdefault(word, []).append(position)
    return index


def work(wid, title, abstract, *, doi="", fwci=0, percentile=0, cited=0, mean_cited=0,
         date="2026-09-15", topic="Planetary science", topic_score=0.9, license=None, journal="Test Journal"):
    return {
        "id": "https://openalex.org/W" + wid,
        "doi": ("https://doi.org/" + doi) if doi else None,
        "display_name": title,
        "abstract_inverted_index": inverted(abstract),
        "summary_stats": {"fwci": fwci, "2yr_mean_citedness": mean_cited},
        "cited_by_percentile_year": {"min": percentile, "max": percentile},
        "cited_by_count": cited,
        "publication_date": date,
        "primary_topic": {"display_name": topic, "score": topic_score},
        "primary_location": {"source": {"display_name": journal}, "license": license},
        "open_access": {"oa_status": "gold" if license else "closed"},
    }


class ShortlistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "test.sqlite3")
        self.today = dt.date(2026, 9, 20)
        self.works = {
            "moon": [
                work("A", "The Moon has a hidden young crater", "An unexpected new crater on the Moon surprises researchers with 222 metres.",
                     doi="10.1371/journal.pone.0000001", fwci=8, percentile=99, cited=12, mean_cited=15, license="cc-by"),
                work("B", "A routine survey of lunar dust", "We measured dust on the Moon with standard methods.",
                     fwci=0.2, percentile=10, cited=0),
                work("D", "A study of ordinary clouds", "Nothing in this text matches the show vocabulary at all.",
                     topic_score=0.0),
                work("E", "The Moon changed while we slept", "A surprising new crater on the Moon.",
                     doi="10.1371/journal.pone.9999999", fwci=9, percentile=99, license="cc-by"),
            ],
            "sleep": [
                work("C", "Why sleep repairs the brain", "Sleep is important and here is a careful study.",
                     fwci=3, percentile=70, cited=4, mean_cited=6, topic="Sleep research"),
            ],
        }
        self.db.execute("INSERT INTO stories(id,source,host) VALUES(?,?,?)",
                        ("known", '{"doi": "10.1371/journal.pone.9999999"}', "nova"))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def fetch(self, url):
        if "openalex.org" not in url:
            return None
        from urllib.parse import parse_qs, urlparse
        term = parse_qs(urlparse(url).query).get("search", [""])[0]
        return {"results": self.works.get(term, [])}

    def shortlist(self, **kwargs):
        return rank(self.db, days=7, today=self.today, fetch=self.fetch, enrich=False, **kwargs)

    def test_ranking_prefers_impact_and_interest(self):
        result = self.shortlist(per_host=3, limit=10)
        titles = [item["title"] for item in result["shortlist"]]
        self.assertIn("The Moon has a hidden young crater", titles)
        self.assertLess(titles.index("The Moon has a hidden young crater"),
                        titles.index("A routine survey of lunar dust"))

    def test_fit_gate_drops_off_beat(self):
        result = self.shortlist(per_host=3, limit=10)
        self.assertNotIn("A study of ordinary clouds", [item["title"] for item in result["shortlist"]])

    def test_known_doi_excluded(self):
        result = self.shortlist(per_host=3, limit=10)
        self.assertEqual(result["excluded_known"], 1)
        self.assertNotIn("The Moon changed while we slept", [item["title"] for item in result["shortlist"]])

    def test_rights_flag(self):
        result = self.shortlist(per_host=3, limit=10)
        by_title = {item["title"]: item for item in result["shortlist"]}
        self.assertTrue(by_title["The Moon has a hidden young crater"]["reusable"])
        self.assertFalse(by_title["Why sleep repairs the brain"]["reusable"])

    def test_per_host_cap(self):
        result = self.shortlist(per_host=1, limit=10)
        nova = [item for item in result["shortlist"] if item["host"] == "nova"]
        self.assertLessEqual(len(nova), 1)

    def test_report_renders_markdown(self):
        self.assertTrue(report(self.shortlist(per_host=2, limit=5)).startswith("# Story shortlist"))


if __name__ == "__main__":
    unittest.main()
