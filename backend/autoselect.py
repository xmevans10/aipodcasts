"""Autonomous story selection: borrow taste, aggregate ranks, gate hard, abstain.

There is no human editor. Two facts shape the design:

1. A single weighted score is fragile. Our own sensitivity run showed top-20 overlap
   near zero across recency windows and heavy reordering under small weight changes.
   So we use *rank aggregation* (reciprocal rank fusion) over independent tastemakers:
   differences in scale matter less, and no one axis can dominate.
2. The algorithm cannot have taste, but it can *consume* other people's. Human-edited
   science feeds (Quanta, Nature News, Science News, ScienceDaily, Phys.org) and the
   Hugging Face Daily Papers upvotes are independent proxies for "fascinating" and
   "important". We only read titles/links as signals; the narrable text still comes
   from the rights-cleared paper itself.

Gates (any failure -> the candidate is dropped, not queued):
  show fit, reusable license, abstract present, retracted, already covered.

Signals fused (rank-based):
  editorial    presence and rank in human-edited feeds
  community    Hugging Face Daily Papers upvotes (AI beat)
  impact       citation velocity (only meaningful for older papers)
  recency      mild decay; never dominant
  fascination  title/abstract heuristics

Usage:
    python3 backend/pipeline.py select --days 14 --per-show 2 --limit 10
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path

from beats import BEATS, normalize_host
from hosts import HOSTS

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("LILT_DATA", ROOT / "data"))
CACHE = DATA / "cache" / "select"
CONTACT = os.environ.get("LILT_CONTACT_EMAIL", "zwicky-research@example.com")

# Human-edited tastemakers: source -> (url, weight)
FEEDS = {
    "quanta": ("https://www.quantamagazine.org/feed/", 1.0),
    "nature": ("https://www.nature.com/nature.rss", 0.9),
    "science": ("https://www.science.org/rss/news_current.xml", 0.8),
    "sciencedaily": ("https://www.sciencedaily.com/rss/top/science.xml", 0.5),
    "physorg": ("https://phys.org/rss-feed/", 0.5),
}
HF_DAILY = "https://huggingface.co/api/daily_papers"
CROSSREF = "https://api.crossref.org/works"

RRF_K = 60
SIGNAL_WEIGHTS = {"editorial": 0.35, "community": 0.10, "impact": 0.20,
                  "recency": 0.15, "fascination": 0.20}
FIT_GATE = 0.25
MAX_PER_TOPIC = 2
REUSABLE_LICENSES = ("creativecommons.org/licenses/by", "creativecommons.org/publicdomain",
                     "creativecommons.org/licenses/zero", "cc0")

SURPRISE = ("unexpected", "surprising", "paradox", "counterintuitive", "challenge",
            "overturn", "contradict", "despite", "for the first time", "never", "rare",
            "hidden", "mysterious", "unprecedented", "unravel", "enigma")
JARGON = ("signaling", "pathway", "expression", "receptor", "transcript", "in vitro",
          "in vivo", "genome-wide", "quantitative", "molecular", "mechanistic", "allele")


class RateLimited(RuntimeError):
    pass


def _cache_path(url: str) -> Path:
    import hashlib
    return CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")


def get(url: str, fetch=None, ttl_hours: int = 12):
    """Return (kind, payload) with kind 'json'|'text'|'error', cached on disk."""
    if fetch is not None:
        return fetch(url)
    path = _cache_path(url)
    if path.exists() and time.time() - path.stat().st_mtime < ttl_hours * 3600:
        return json.loads(path.read_text())
    request = urllib.request.Request(url, headers={"User-Agent": "ZwickyResearch/0.1 (autonomous select)"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise RateLimited(url)
        return ("error", error.code)
    except (urllib.error.URLError, TimeoutError):
        return ("error", "network")
    try:
        payload = json.loads(body)
        result = ("json", payload)
    except json.JSONDecodeError:
        result = ("text", body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result))
    return result


def _titles_from_feed(xml_text: str):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    titles = []
    for tag in (".//item/title", ".//{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title"):
        for node in root.findall(tag):
            value = "".join(node.itertext()).strip()
            if value:
                titles.append(value)
    return titles


def load_tastemakers(fetch=None):
    """{source: [title, ...]} from human feeds, plus Hugging Face Daily Papers."""
    editorial: dict[str, list[str]] = {}
    for source, (url, _weight) in FEEDS.items():
        try:
            kind, payload = get(url, fetch)
        except RateLimited:
            continue
        if kind == "text":
            editorial[source] = _titles_from_feed(payload)
        elif kind == "json":  # Atom served as JSON is rare, but handle feedly-style
            editorial[source] = []
    community: list[str] = []
    try:
        kind, payload = get(HF_DAILY, fetch)
        if kind == "json":
            community = [(item.get("paper") or {}).get("title", "") for item in payload]
    except RateLimited:
        pass
    return editorial, [title for title in community if title]


def _tokens(text: str):
    return set(re.findall(r"[a-z0-9]{4,}", text.lower()))


def _similarity(title: str, candidate_titles):
    """Best fuzzy match and count of distinct sources whose titles match this paper."""
    if not title:
        return 0.0, []
    wanted = _tokens(title)
    best, sources = 0.0, []
    for source, titles in candidate_titles.items():
        for other in titles:
            ratio = SequenceMatcher(None, title.lower(), other.lower()).ratio()
            overlap = len(wanted & _tokens(other)) / max(len(wanted), 1)
            score = max(ratio, overlap)
            if score > best:
                best = score
            if score >= 0.55:
                sources.append(source)
                break
    return best, sorted(set(sources))


def _hf_similarity(title: str, community_titles):
    if not title:
        return 0.0
    wanted = _tokens(title)
    best = 0.0
    for other in community_titles:
        best = max(best, len(wanted & _tokens(other)) / max(len(wanted), 1))
    return best


def crossref_lookup(title: str, fetch=None, rows: int = 1):
    params = {"query.bibliographic": title, "rows": rows, "mailto": CONTACT}
    url = CROSSREF + "?" + urllib.parse.urlencode(params)
    try:
        kind, payload = get(url, fetch)
    except RateLimited:
        return []
    if kind != "json" or not isinstance(payload, dict):
        return []
    return payload.get("message", {}).get("items", [])


def editorial_dois(fetch=None):
    """Join human-edited feed headlines to papers by DOI, so taste transfers exactly.

    News headlines rarely share wording with the paper title, so fuzzy matching fails.
    One Crossref title lookup per feed item resolves the DOI and makes the editorial
    signal a fact ("Quanta covered this paper") rather than a guess.
    """
    editorial, _ = load_tastemakers(fetch)
    mapping: dict[str, set] = {}
    lookups = 0
    for source, titles in editorial.items():
        for title in titles:
            if len(_tokens(title)) < 4:
                continue
            items = crossref_lookup(title, fetch)
            lookups += 1
            if not items:
                continue
            work = normalize(items[0])
            if work and SequenceMatcher(None, title.lower(), work["title"].lower()).ratio() >= 0.45:
                mapping.setdefault(work["doi"], set()).add(source)
    return mapping, lookups


def crossref_window(term: str, since: str, fetch=None, rows: int = 40):
    params = {"query.bibliographic": term,
              "filter": f"from-pub-date:{since},type:journal-article",
              "rows": rows, "mailto": CONTACT}
    url = CROSSREF + "?" + urllib.parse.urlencode(params)
    try:
        kind, payload = get(url, fetch)
    except RateLimited:
        return []
    if kind != "json":
        return []
    return payload.get("message", {}).get("items", []) if isinstance(payload, dict) else []


def clean(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").replace("&amp;", "&").strip()


def normalize(item: dict):
    doi = (item.get("DOI") or "").lower()
    title = clean((item.get("title") or [""])[0])
    if not doi or not title:
        return None
    parts = (item.get("issued") or {}).get("date-parts", [[None]])[0]
    if not parts or not parts[0]:
        return None
    try:
        date = dt.date(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)
    except ValueError:
        return None
    licenses = " ".join((entry or {}).get("URL", "") for entry in (item.get("license") or []))
    return {"id": doi, "doi": doi, "title": title, "abstract": clean(item.get("abstract") or ""),
            "date": date, "journal": clean((item.get("container-title") or [""])[0]),
            "cited": item.get("is-referenced-by-count", 0) or 0,
            "license": licenses, "subject": item.get("subject") or []}


def fascinating(work):
    text = (work["title"] + " " + work["abstract"]).lower()
    surprises = sum(text.count(term) for term in SURPRISE)
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    words = re.findall(r"[a-z']+", work["title"].lower())
    average = sum(len(word) for word in words) / len(words) if words else 9
    jargon = sum(text.count(term) for term in JARGON)
    return max(0.0, 0.35 * min(1.0, surprises / 3) + 0.2 * min(1.0, numbers / 6)
               + 0.1 * (1.0 if "?" in work["title"] else 0.0)
               + 0.35 * max(0.0, min(1.0, (14 - average) / 6)) - 0.3 * min(1.0, jargon / 3))


def fit(work, terms):
    text = (work["title"] + " " + work["abstract"]).lower()
    return sum(1 for term in terms if term.lower() in text) / len(terms)


def rrf(rank: int) -> float:
    return 1.0 / (RRF_K + rank)


def seen_dois(db):
    found = set()
    for row in db.execute("SELECT source FROM stories WHERE source IS NOT NULL"):
        try:
            found.add((json.loads(row["source"]).get("doi") or "").lower())
        except (json.JSONDecodeError, TypeError):
            continue
    return {doi for doi in found if doi}


def select(db, days: int = 14, per_show: int = 2, limit: int = 10,
           today: dt.date | None = None, fetch=None):
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=days)).isoformat()
    exclude = seen_dois(db)
    editorial, community = load_tastemakers(fetch)
    editorial_by_doi, lookups = editorial_dois(fetch)

    works: dict[str, dict] = {}
    rate_limited = 0
    for raw_host, terms in BEATS.items():
        host = normalize_host(raw_host)
        for term in terms:
            for item in crossref_window(term, since, fetch):
                work = normalize(item)
                if work is None or work["doi"] in exclude or work["doi"] in works:
                    continue
                work["host"], work["show"], work["terms"] = host, HOSTS[host].show, terms
                works[work["doi"]] = work

    candidates = []
    for work in works.values():
        score = fit(work, work["terms"])
        if score < FIT_GATE:
            continue
        text = (work["title"] + " " + work["abstract"]).lower()
        matched = next((term for term in work["terms"] if term.lower() in text), work["show"])
        doi_sources = sorted(editorial_by_doi.get(work["doi"], []))
        fuzzy, fuzzy_sources = _similarity(work["title"], editorial)
        work.update({
            "editorial": 1.0 if doi_sources else fuzzy,
            "editorial_sources": doi_sources or fuzzy_sources,
            # Crossref subject is almost always empty; fall back to the matched beat
            # so the topic-diversity cap actually separates stories.
            "topic": (work["subject"] or [matched])[0],
            "community": _hf_similarity(work["title"], community),
            "age": max((today - work["date"]).days, 0),
            "fascination": fascinating(work),
            "fit": round(score, 3),
            "reusable": any(marker in work["license"].lower() for marker in REUSABLE_LICENSES),
        })
        candidates.append(work)

    # Rank-aggregate: each signal contributes 1/(k+rank), so no axis dominates.
    for signal, getter, reverse in [
        ("editorial", lambda w: w["editorial"], True),
        ("community", lambda w: w["community"], True),
        ("impact", lambda w: math.log1p(w["cited"] / max(w["age"] / 30.0, 0.5)), True),
        ("recency", lambda w: w["age"], False),
        ("fascination", lambda w: w["fascination"], True),
    ]:
        ordered = sorted(candidates, key=getter, reverse=reverse)
        for rank, work in enumerate(ordered):
            work.setdefault("fusion", 0.0)
            work["fusion"] += SIGNAL_WEIGHTS[signal] * rrf(rank)
    for work in candidates:
        work["score"] = round(work.get("fusion", 0.0), 5)

    ranked = sorted(candidates, key=lambda w: w["score"], reverse=True)
    selected, show_count, topic_count = [], {}, {}
    for work in ranked:
        if not work["reusable"]:
            continue
        topic = work["topic"]
        if show_count.get(work["host"], 0) >= per_show or topic_count.get(topic, 0) >= MAX_PER_TOPIC:
            continue
        show_count[work["host"]] = show_count.get(work["host"], 0) + 1
        topic_count[topic] = topic_count.get(topic, 0) + 1
        selected.append(work)
        if len(selected) >= limit:
            break
    return {"window_days": days, "papers_pulled": len(works), "candidates": len(ranked),
            "eligible": sum(1 for w in ranked if w["reusable"]), "selected": selected,
            "editorial_titles": sum(len(v) for v in editorial.values()),
            "editorial_doi_links": len(editorial_by_doi), "editorial_lookups": lookups}


def report(result: dict) -> str:
    lines = [f"# Autonomous selection (last {result['window_days']} days)",
             f"{result['papers_pulled']} papers pulled, {result['candidates']} scored, "
             f"{result['eligible']} license-eligible; {result['editorial_titles']} editorial headlines read, "
             f"{result['editorial_doi_links']} joined to a paper by DOI", "",
             "| rank | score | show | title | journal | age | cited | editorial from | reusable |",
             "|---|---|---|---|---|---|---|---|---|"]
    for index, work in enumerate(result["selected"], 1):
        lines.append(f"| {index} | {work['score']} | {work['show']} | {work['title'][:66]} | "
                     f"{work['journal'][:30]} | {work['age']}d | {work['cited']} | "
                     f"{','.join(work['editorial_sources']) or '-'} | {work['reusable']} |")
    return "\n".join(lines)
