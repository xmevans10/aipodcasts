"""EurekAlert! as a signal-only press source.

EurekAlert exposes no public RSS or API. Its sitemap index lists per-month sitemaps, and
each entry carries a release URL, title and publication date. Release pages link to the
paper's DOI. This module reads the title transiently to resolve that DOI and keeps only
``(doi, date)``: it never persists, reproduces or narrates release text, because
EurekAlert's terms forbid reproducing or commercially reusing its content (see
``docs/editorial/story-discovery.md``).

The caller supplies a cached ``get(url) -> (kind, payload)`` so this module carries no
network policy of its own, and tests can inject a stub.
"""
from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET

from publicity import Release

SITEMAP_INDEX = "https://www.eurekalert.org/sitemap.xml"
DOI_URL = re.compile(r"https?://(?:dx\.)?doi\.org/(10\.[^\s\"'<>]+)", re.I)
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "news": "http://www.google.com/schemas/sitemap-news/0.9"}


def parse_sitemap_index(xml_text: str) -> list:
    """Per-month sitemap URLs listed by the index."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    return [loc.text.strip() for loc in root.findall(".//sm:sitemap/sm:loc", NS) if loc.text]


def parse_sitemap(xml_text: str) -> list:
    """[{url, title, date}] from a per-month sitemap's news entries."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    entries = []
    for url in root.findall(".//sm:url", NS):
        loc = url.find("sm:loc", NS)
        if loc is None or not loc.text:
            continue
        title = url.find("news:news/news:title", NS)
        date = url.find("news:news/news:publication_date", NS)
        entries.append({"url": loc.text.strip(),
                        "title": (title.text or "").strip() if title is not None else "",
                        "date": (date.text or "").strip() if date is not None else ""})
    return entries


def extract_doi(html: str) -> str:
    """First DOI linked from a release page, with trailing punctuation trimmed."""
    match = DOI_URL.search(html or "")
    return match.group(1).rstrip(").,;").lower() if match else ""


def _months(since: dt.date, today: dt.date):
    months, cursor = [], since.replace(day=1)
    while cursor <= today:
        months.append(f"{cursor.year:04d}-{cursor.month:02d}")
        cursor = dt.date(cursor.year + (cursor.month == 12), (cursor.month % 12) + 1, 1)
    return months


def releases(get, since: dt.date, today: dt.date | None = None, max_pages: int = 120) -> list:
    """Press releases in the window, as signal-only ``Release`` objects with DOIs.

    Fetches the sitemap index, the sitemaps for every month spanning ``since..today``,
    then up to ``max_pages`` release pages (newest sitemap order first) to extract DOIs.
    """
    today = today or dt.date.today()
    kind, payload = get(SITEMAP_INDEX)
    if kind != "text":
        return []
    index = set(parse_sitemap_index(payload))
    wanted = [url for month in sorted(_months(since, today))
              for url in index if f"/sitemap/{month}/" in url]

    entries = []
    for sitemap_url in wanted:
        sitemap_kind, sitemap = get(sitemap_url)
        if sitemap_kind == "text":
            entries.extend(parse_sitemap(sitemap))

    found, pages = [], 0
    windowed = [entry for entry in entries
                if not (entry["date"] and entry["date"][:10] < since.isoformat())]
    windowed.sort(key=lambda entry: entry["date"], reverse=True)
    for entry in windowed:
        if pages >= max_pages:
            break
        pages += 1
        date = (entry["date"] or "")[:10]
        page_kind, html = get(entry["url"])
        if page_kind != "text":
            continue
        doi = extract_doi(html)
        if doi:
            found.append(Release(source="eurekalert", title=entry["title"],
                                 url=entry["url"], date=date, doi=doi))
    return found
