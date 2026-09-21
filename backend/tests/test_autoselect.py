import datetime as dt
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import connect
from autoselect import select, report, is_reusable, normalize_openalex, studiness

CC_BY = "https://creativecommons.org/licenses/by/4.0/"


def crossref_item(doi, title, *, license_url="", cited=0, abstract="", subject=("Topic",), date=(2026, 9, 10), type="journal-article"):
    return {"DOI": doi, "title": [title], "abstract": abstract,
            "issued": {"date-parts": [list(date)]}, "container-title": ["Test Journal"],
            "subject": list(subject), "is-referenced-by-count": cited, "type": type,
            "license": [{"URL": license_url}] if license_url else []}


def feed(*titles):
    items = "".join(f"<item><title>{title}</title></item>" for title in titles)
    return f"<rss><channel>{items}</channel></rss>"


def openalex_work(title, *, arxiv_id=None, doi=None, work_type="preprint",
                  license_id="", source_type="repository", cited=1):
    work = {
        "display_name": title,
        "publication_date": "2026-09-10",
        "type": work_type,
        "cited_by_count": cited,
        "primary_location": {"source": {"display_name": "arXiv", "type": source_type},
                             "license": license_id},
        "best_oa_location": {"license": license_id},
        "primary_topic": {"display_name": "Planetary science"},
        "locations": [],
    }
    if doi:
        work["doi"] = "https://doi.org/" + doi
    if arxiv_id:
        work["locations"].append({"landing_page_url": f"https://arxiv.org/abs/{arxiv_id}"})
    return work


def openalex_fetch(work_by_term):
    def fetch(url):
        if "api.openalex.org" in url:
            from urllib.parse import parse_qs, urlparse
            term = parse_qs(urlparse(url).query).get("search", [""])[0]
            return ("json", {"results": work_by_term.get(term, [])})
        if "huggingface.co" in url:
            return ("json", [])
        if "api.crossref.org" in url:
            return ("json", {"message": {"items": []}})
        return ("text", feed())
    return fetch


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
        return select(self.db, days=14, today=self.today, fetch=self.fetch, source="crossref", **kwargs)

    def test_only_license_eligible_are_selected(self):
        result = self.select(per_show=3, limit=10)
        dois = [work["doi"] for work in result["selected"]]
        self.assertIn("10.1371/journal.pone.0000001", dois)
        self.assertNotIn("10.9999/closed.1", dois)

    def test_abstract_tier_selected_without_license(self):
        self.crossref["sleep"].append(crossref_item(
            "10.9999/abstract.2", "Sleep and memory in older adults", subject=("Sleep",),
            abstract="We measured sleep and found memory improved in a sample of 60 participants."))
        result = self.select(per_show=3, limit=10)
        by_doi = {work["doi"]: work for work in result["selected"]}
        self.assertIn("10.9999/abstract.2", by_doi)
        self.assertEqual(by_doi["10.9999/abstract.2"]["evidence_tier"], "abstract")

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

    def test_commentary_excluded(self):
        self.crossref["moon"].append(crossref_item(
            "10.1371/journal.pone.0000004", "A book review of recent lunar science",
            license_url=CC_BY, subject=("Reviews",), type="book-review"))
        result = self.select(per_show=3, limit=10)
        self.assertNotIn("A book review of recent lunar science", [work["title"] for work in result["selected"]])
        self.assertGreaterEqual(result["non_primary_excluded"], 1)

    def test_studiness_prefers_findings_over_reviews(self):
        finding = {"abstract": "We measured a sample of 40 participants and found a strong effect."}
        review = {"abstract": "We review the literature, discuss prior work and argue for a perspective."}
        self.assertGreater(studiness(finding), studiness(review))

    def test_license_rules(self):
        for good in ("cc-by", "https://creativecommons.org/licenses/by/4.0/", "cc0", "public-domain"):
            self.assertTrue(is_reusable(good), good)
        for bad in ("cc-by-nc", "cc-by-nd", "cc-by-sa", "", "https://creativecommons.org/licenses/by-nc/4.0/"):
            self.assertFalse(is_reusable(bad), bad)

    def test_arxiv_preprint_selectable_on_preprint_show(self):
        work = openalex_work("A hidden moon with an unexpected orbit", arxiv_id="2501.00001v2")
        result = select(self.db, days=14, today=self.today, source="openalex", per_show=2, limit=10,
                        fetch=openalex_fetch({"moon": [work]}))
        selected = next(w for w in result["selected"] if w["doi"] == "arxiv:2501.00001")
        self.assertEqual(selected["arxiv_id"], "2501.00001")
        self.assertEqual(selected["host"], "nova")

    def test_arxiv_preprint_excluded_on_non_preprint_show(self):
        work = openalex_work("A hidden bird with an unexpected song", arxiv_id="2501.00002")
        result = select(self.db, days=14, today=self.today, source="openalex", per_show=2, limit=10,
                        fetch=openalex_fetch({"bird": [work]}))
        self.assertEqual(result["selected"], [])
        self.assertGreaterEqual(result["non_primary_excluded"], 1)

    def test_journal_article_still_requires_min_reputation(self):
        work = openalex_work("A hidden moon in a repository", doi="10.5555/repo.1", work_type="article",
                             source_type="repository", license_id=CC_BY)
        fetch = openalex_fetch({"moon": [work]})
        default = select(self.db, days=14, today=self.today, source="openalex", per_show=2, limit=10,
                         fetch=fetch)
        self.assertEqual(default["selected"], [])
        relaxed = select(self.db, days=14, today=self.today, source="openalex", per_show=2, limit=10,
                         fetch=fetch, min_reputation=0.0)
        self.assertIn("10.5555/repo.1", [w["doi"] for w in relaxed["selected"]])

    def test_normalize_openalex(self):
        work = {"doi": "https://doi.org/10.1234/x", "display_name": "A surprising Moon crater",
                "publication_date": "2026-09-10", "abstract_inverted_index": {"A": [0], "crater": [2]},
                "cited_by_count": 3, "primary_location": {"source": {"display_name": "Icarus"}, "license": "cc-by"},
                "best_oa_location": {"license": "cc-by"}, "primary_topic": {"display_name": "Planetary science"},
                "type": "article"}
        normalized = normalize_openalex(work)
        self.assertEqual(normalized["doi"], "10.1234/x")
        self.assertEqual(normalized["journal"], "Icarus")
        self.assertTrue(normalized["abstract"])
        self.assertTrue(is_reusable(normalized["license"]))


if __name__ == "__main__":
    unittest.main()
