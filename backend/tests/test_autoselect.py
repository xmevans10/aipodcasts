import datetime as dt
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import connect
from autoselect import select, report

CC_BY = "https://creativecommons.org/licenses/by/4.0/"


def crossref_item(doi, title, *, license_url="", cited=0, abstract="", subject=("Topic",), date=(2026, 9, 10)):
    return {"DOI": doi, "title": [title], "abstract": abstract,
            "issued": {"date-parts": [list(date)]}, "container-title": ["Test Journal"],
            "subject": list(subject), "is-referenced-by-count": cited,
            "license": [{"URL": license_url}] if license_url else []}


def feed(*titles):
    items = "".join(f"<item><title>{title}</title></item>" for title in titles)
    return f"<rss><channel>{items}</channel></rss>"


class SelectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "test.sqlite3")
        self.today = dt.date(2026, 9, 20)
        self.crossref = {
            "moon": [
                crossref_item("10.1371/journal.pone.0000001", "A hidden young crater on the Moon",
                              license_url=CC_BY, cited=10, abstract="An unexpected crater surprises researchers."),
                crossref_item("10.9999/closed.1", "A routine survey of lunar dust", cited=2),
                crossref_item("10.1371/journal.pone.0000002", "A study of ordinary clouds",
                              license_url=CC_BY, subject=("Clouds",)),
            ],
            "sleep": [
                crossref_item("10.1371/journal.pone.0000003", "Sleep consolidates memory",
                              license_url=CC_BY, cited=3, subject=("Sleep research",)),
            ],
        }
        self.db.execute("INSERT INTO stories(id,source,host) VALUES(?,?,?)",
                        ("known", '{"doi": "10.1371/journal.pone.9999999"}', "nova"))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def fetch(self, url):
        if "quantamagazine.org" in url:
            return ("text", feed("A hidden young crater on the Moon"))
        if "huggingface.co" in url:
            return ("json", [{"paper": {"title": "A hidden young crater on the Moon"}}])
        if "api.crossref.org" in url:
            from urllib.parse import parse_qs, urlparse
            term = parse_qs(urlparse(url).query).get("query.bibliographic", [""])[0]
            return ("json", {"message": {"items": self.crossref.get(term, [])}})
        return ("text", feed())

    def select(self, **kwargs):
        return select(self.db, days=14, today=self.today, fetch=self.fetch, **kwargs)

    def test_only_license_eligible_are_selected(self):
        result = self.select(per_show=3, limit=10)
        dois = [work["doi"] for work in result["selected"]]
        self.assertIn("10.1371/journal.pone.0000001", dois)
        self.assertNotIn("10.9999/closed.1", dois)

    def test_fit_gate_drops_off_beat(self):
        result = self.select(per_show=3, limit=10)
        self.assertNotIn("A study of ordinary clouds", [work["title"] for work in result["selected"]])

    def test_editorial_signal_boosts_matched_paper(self):
        result = self.select(per_show=3, limit=10)
        by_doi = {work["doi"]: work for work in result["selected"]}
        self.assertIn("quanta", by_doi["10.1371/journal.pone.0000001"]["editorial_sources"])
        self.assertGreater(by_doi["10.1371/journal.pone.0000001"]["editorial"], 0.5)

    def test_per_show_cap(self):
        result = self.select(per_show=1, limit=10)
        nova = [work for work in result["selected"] if work["host"] == "nova"]
        self.assertLessEqual(len(nova), 1)

    def test_report_renders(self):
        self.assertTrue(report(self.select(per_show=2, limit=5)).startswith("# Autonomous selection"))


if __name__ == "__main__":
    unittest.main()
