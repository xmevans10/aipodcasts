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
OPENALEX = "https://api.openalex.org/works"

RRF_K = 60
SIGNAL_WEIGHTS = {"editorial": 0.30, "community": 0.10, "impact": 0.15,
                  "reputation": 0.15, "studiness": 0.15, "recency": 0.05,
                  "fascination": 0.10}
PRIMARY_TYPES = {"article"}          # OpenAlex normalized type for peer-reviewed research
PREPRINT_TYPES = {"article", "preprint"}
FINDING_CUES = ("we found", "we show", "we report", "we demonstrate", "our results",
                "results show", "we observed", "we identify", "we measured", "we tested",
                "experiment", "sample of", "participants", "dataset", "compared with",
                "we estimate", "we analysed", "we analyzed")
REVIEW_CUES = ("we review", "this review", "we summarize", "we summarise", "we argue",
               "we discuss", "we propose a framework", "perspective", "opinion",
               "commentary", "we survey", "we outline", "conceptual")
FIT_GATE = 0.25
MIN_REPUTATION = 0.5  # peer-reviewed journals; excludes preprints/repositories by default
MAX_PER_TOPIC = 2


def is_reusable(license_id: str) -> bool:
    """Commercial-safe reuse: attribution/CC0/public-domain, never NC or ND.

    CC BY-SA is excluded too: it would force our script and audio derivative to be
    share-alike, which we do not want on a paid product.
    """
    value = (license_id or "").lower()
    if not value:
        return False
    if any(marker in value for marker in ("by-nc", "by-nd", "by-sa", "/nc", "/nd", "-nc-", "-nd-")):
        return False
    return any(marker in value for marker in (
        "cc-by", "creativecommons.org/licenses/by", "cc0", "publicdomain",
        "public-domain", "public_domain"))

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
            "license": licenses, "subject": item.get("subject") or [],
            "type": "article" if item.get("type") in (None, "journal-article") else item.get("type"),
            "type_crossref": item.get("type") or "", "is_retracted": False,
            "fwci": None, "related_works": []}


def reconstruct_abstract(inverted) -> str:
    if not inverted:
        return ""
    positions = {}
    for word, indices in inverted.items():
        for index in indices:
            positions[index] = word
    return " ".join(positions[i] for i in sorted(positions))


def openalex_window(term: str, since: str, fetch=None, per_page: int = 50):
    """Open-access article/preprint/review works for a term, newest relevance first."""
    params = {"search": term,
              "filter": f"from_publication_date:{since},is_oa:true,type:article|preprint|review",
              "per-page": per_page, "mailto": CONTACT}
    key = os.environ.get("LILT_OPENALEX_KEY", "").strip()
    if key:
        params["api_key"] = key
    url = OPENALEX + "?" + urllib.parse.urlencode(params)
    try:
        kind, payload = get(url, fetch)
    except RateLimited:
        return []
    if kind != "json" or not isinstance(payload, dict):
        return []
    return payload.get("results", [])


def normalize_openalex(work: dict):
    doi = (work.get("doi") or "").replace("https://doi.org/", "").replace("http://doi.org/", "").lower()
    title = clean(work.get("display_name") or "")
    if not doi or not title:
        return None
    date_string = work.get("publication_date")
    if not date_string:
        return None
    try:
        date = dt.date.fromisoformat(date_string[:10])
    except ValueError:
        return None
    location = work.get("primary_location") or {}
    best = work.get("best_oa_location") or {}
    source = location.get("source") or {}
    return {"id": doi, "doi": doi, "title": title,
            "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
            "date": date, "journal": clean(source.get("display_name") or source.get("host_organization_name") or ""),
            "cited": work.get("cited_by_count", 0) or 0,
            "license": (best.get("license") or location.get("license") or ""),
            "subject": [(work.get("primary_topic") or {}).get("display_name")] if (work.get("primary_topic") or {}).get("display_name") else [],
            "type": work.get("type", ""), "venue_type": (source.get("type") or ""),
            "type_crossref": work.get("type_crossref") or "",
            "is_retracted": bool(work.get("is_retracted")),
            "fwci": (work.get("summary_stats") or {}).get("fwci"),
            "related_works": work.get("related_works") or []}


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


VENUE_REJECT = re.compile(r"\b(reviews?|commentary|opinion|perspective|magazine|newsletter|"
                          r"book review|media reviews?)\b", re.I)


def is_primary_venue(work):
    """Reject outlets that publish commentary/media reviews rather than research."""
    return not VENUE_REJECT.search(work.get("journal") or "")


def fit(work, terms):
    text = (work["title"] + " " + work["abstract"]).lower()
    return sum(1 for term in terms if term.lower() in text) / len(terms)


def venue_reputation(work):
    """Peer-reviewed journals outrank preprints and data repositories."""
    venue_type = (work.get("venue_type") or "").lower()
    if venue_type == "journal":
        return 1.0
    if venue_type in ("conference", "proceedings"):
        return 0.7
    if venue_type in ("repository", "preprint"):
        return 0.3
    return 0.6 if work.get("journal") else 0.4


def studiness(work):
    """Distinguish a study from commentary/review using abstract framing.

    Deterministic, no model: primary research says 'we measured / we found / sample',
    commentary says 'we review / we argue / perspective'. A media review has no
    methods, so this is what stops one winning a slot.
    """
    text = (work.get("abstract") or "").lower()
    if not text:
        return 0.4
    findings = sum(1 for cue in FINDING_CUES if cue in text)
    reviews = sum(1 for cue in REVIEW_CUES if cue in text)
    return max(0.0, min(1.0, 0.4 + 0.1 * findings - 0.2 * reviews))


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
           today: dt.date | None = None, fetch=None, source: str | None = None,
           min_reputation: float = MIN_REPUTATION):
    today = today or dt.date.today()
    since = (today - dt.timedelta(days=days)).isoformat()
    source = source or ("openalex" if os.environ.get("LILT_OPENALEX_KEY", "").strip() else "crossref")
    exclude = seen_dois(db)
    editorial, community = load_tastemakers(fetch)
    editorial_by_doi, lookups = editorial_dois(fetch)

    works: dict[str, dict] = {}
    for raw_host, terms in BEATS.items():
        host = normalize_host(raw_host)
        for term in terms:
            items = openalex_window(term, since, fetch) if source == "openalex" else crossref_window(term, since, fetch)
            for item in items:
                work = normalize_openalex(item) if source == "openalex" else normalize(item)
                if work is None or work["doi"] in exclude or work["doi"] in works:
                    continue
                work["host"], work["show"], work["terms"] = host, HOSTS[host].show, terms
                works[work["doi"]] = work

    candidates = []
    retracted = non_primary = 0
    allowed_types = PREPRINT_TYPES if min_reputation < MIN_REPUTATION else PRIMARY_TYPES
    for work in works.values():
        if work.get("is_retracted"):
            retracted += 1
            continue
        if work.get("type") not in allowed_types:
            non_primary += 1
            continue
        work_studiness = studiness(work)
        if min_reputation >= MIN_REPUTATION and not is_primary_venue(work):
            non_primary += 1
            continue
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
            "studiness": round(work_studiness, 3),
            "fit": round(score, 3),
            "reusable": is_reusable(work["license"]),
        })
        candidates.append(work)

    # Rank-aggregate: each signal contributes 1/(k+rank), so no axis dominates.
    for signal, getter, reverse in [
        ("editorial", lambda w: w["editorial"], True),
        ("community", lambda w: w["community"], True),
        ("impact", lambda w: math.log1p(w["cited"] / max(w["age"] / 30.0, 0.5)), True),
        ("reputation", venue_reputation, True),
        ("studiness", lambda w: w["studiness"], True),
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
        if not work["reusable"] or venue_reputation(work) < min_reputation:
            continue
        topic = work["topic"]
        if show_count.get(work["host"], 0) >= per_show or topic_count.get(topic, 0) >= MAX_PER_TOPIC:
            continue
        show_count[work["host"]] = show_count.get(work["host"], 0) + 1
        topic_count[topic] = topic_count.get(topic, 0) + 1
        selected.append({**work, "date": work["date"].isoformat()})
        if len(selected) >= limit:
            break
    selected_studiness = [w["studiness"] for w in selected]
    return {"source": source, "window_days": days, "papers_pulled": len(works), "candidates": len(ranked),
            "eligible": sum(1 for w in ranked if w["reusable"]), "selected": selected,
            "retracted_excluded": retracted, "non_primary_excluded": non_primary,
            "shows_filled": len({w["host"] for w in selected}),
            "mean_studiness": round(sum(selected_studiness) / len(selected_studiness), 3) if selected_studiness else 0,
            "editorial_titles": sum(len(v) for v in editorial.values()),
            "editorial_doi_links": len(editorial_by_doi), "editorial_lookups": lookups}


def report(result: dict) -> str:
    lines = [f"# Autonomous selection (source: {result.get('source', '?')}, last {result['window_days']} days)",
             f"{result['papers_pulled']} papers pulled, {result['candidates']} scored, "
             f"{result['eligible']} license-eligible; {result['editorial_titles']} editorial headlines read, "
             f"{result['editorial_doi_links']} joined to a paper by DOI", "",
             "| rank | score | show | title | venue | age | cited | editorial from | reusable |",
             "|---|---|---|---|---|---|---|---|---|"]
    for index, work in enumerate(result["selected"], 1):
        venue = (work.get("venue_type") or work["journal"] or "")[:30]
        lines.append(f"| {index} | {work['score']} | {work['show']} | {work['title'][:60]} | "
                     f"{venue} | {work['age']}d | {work['cited']} | "
                     f"{','.join(work['editorial_sources']) or '-'} | {work['reusable']} |")
    return "\n".join(lines)
