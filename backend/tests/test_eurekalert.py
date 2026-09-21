import datetime as dt
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eurekalert import (SITEMAP_INDEX, extract_doi, parse_sitemap, parse_sitemap_index,
                        releases)

INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://www.eurekalert.org/sitemap/2026-09/sitemap.xml</loc></sitemap>
  <sitemap><loc>https://www.eurekalert.org/sitemap/2026-08/sitemap.xml</loc></sitemap>
</sitemapindex>"""

MONTH = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  <url>
    <loc>https://www.eurekalert.org/news-releases/1142182</loc>
    <news:news>
      <news:publication_date>2026-09-01</news:publication_date>
      <news:title>Breaking through AlphaFold's limits</news:title>
    </news:news>
  </url>
  <url>
    <loc>https://www.eurekalert.org/news-releases/1142000</loc>
    <news:news>
      <news:publication_date>2026-08-01</news:publication_date>
      <news:title>An old release from last month</news:title>
    </news:news>
  </url>
</urlset>"""

PAGE = """<html><head>
<meta property="og:title" content="Breaking through AlphaFold's limits">
</head><body>
<a href="http://dx.doi.org/10.1021/jacsau.6c00596">Read the paper</a>
</body></html>"""


def fetch(url):
    if url == SITEMAP_INDEX:
        return ("text", INDEX)
    if url.endswith("2026-09/sitemap.xml"):
        return ("text", MONTH)
    if url.endswith("2026-08/sitemap.xml"):
        return ("text", MONTH)
    if "1142182" in url:
        return ("text", PAGE)
    return ("error", 404)


class EurekAlertTests(unittest.TestCase):
    def test_parse_sitemap_index(self):
        self.assertEqual(parse_sitemap_index(INDEX),
                         ["https://www.eurekalert.org/sitemap/2026-09/sitemap.xml",
                          "https://www.eurekalert.org/sitemap/2026-08/sitemap.xml"])

    def test_parse_sitemap_extracts_news_fields(self):
        entries = parse_sitemap(MONTH)
        self.assertEqual(entries[0]["url"], "https://www.eurekalert.org/news-releases/1142182")
        self.assertEqual(entries[0]["date"], "2026-09-01")
        self.assertIn("AlphaFold", entries[0]["title"])
        self.assertEqual(entries[1]["date"], "2026-08-01")

    def test_extract_doi_trims_trailing_punctuation(self):
        self.assertEqual(extract_doi("see https://doi.org/10.1021/jacsau.6c00596)."),
                         "10.1021/jacsau.6c00596")
        self.assertEqual(extract_doi("<a href='http://dx.doi.org/10.1/X'>"), "10.1/x")
        self.assertEqual(extract_doi("no link here"), "")

    def test_releases_filters_by_window_and_keeps_doi(self):
        found = releases(fetch, dt.date(2026, 9, 1), dt.date(2026, 9, 21))
        self.assertEqual(len(found), 1)
        release = found[0]
        self.assertEqual(release.source, "eurekalert")
        self.assertEqual(release.doi, "10.1021/jacsau.6c00596")
        self.assertEqual(release.date, "2026-09-01")
        self.assertIn("AlphaFold", release.title)

    def test_releases_respects_page_cap(self):
        self.assertEqual(releases(fetch, dt.date(2026, 9, 1), dt.date(2026, 9, 21), max_pages=0), [])

    def test_releases_tolerates_bad_xml(self):
        self.assertEqual(parse_sitemap("<not-xml"), [])
        self.assertEqual(parse_sitemap_index("<not-xml"), [])


if __name__ == "__main__":
    unittest.main()
