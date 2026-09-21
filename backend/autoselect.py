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
  publicity    a press office judged the paper worth explaining (one event, however
               many syndicators carried the release; see publicity.py)
  editorial    presence and rank in independent human-edited feeds
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
from eurekalert import releases as eurekalert_releases
from hosts import HOSTS
from publicity import (INDEPENDENT, Release, cluster_releases, editorial_value,
                       event_index, publicity_value)

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
SIGNAL_WEIGHTS = {"publicity": 0.25, "editorial": 0.20, "community": 0.08,
                  "impact": 0.12, "reputation": 0.12, "studiness": 0.13,
                  "recency": 0.05, "fascination": 0.05}
PRIMARY_TYPES = {"article"}          # OpenAlex normalized type for peer-reviewed research
PREPRINT_TYPES = {"article", "preprint"}
# Shows allowed to draw from arXiv preprints: beats whose primary literature is
# physical or computational (astronomy, astrophysics, AI/ML, materials) and moves on
# arXiv ahead of journals. Every other show keeps the peer-reviewed default. The
# neuroscience show (ada) is deliberately left out: it is a life-science beat, not one
# of the physical/computational shows this change targets.
PREPRINT_SHOWS: set[str] = {"nova", "yusuf", "jax", "noor", "marek"}
ARXIV_LANDING = re.compile(r"arxiv\.org/abs/([^/?#\s]+)", re.I)
ARXIV_VERSION = re.compile(r"v\d+$", re.I)
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


def load_releases(fetch=None, editorial=None, since=None, today=None):
    """Structured feed releases, each with a DOI resolved by one Crossref title lookup.

    News headlines rarely share wording with the paper title, so fuzzy matching fails.
    Resolving the DOI makes the publicity signal a fact ("this release points at this
    paper") rather than a guess, and lets copies of one release on different sites
    collapse into a single event in publicity.cluster_releases. Returns (releases, lookups).

    When ``since`` is given, public EurekAlert releases in the window are appended as
    signal-only entries (see eurekalert.py). Set ``LILT_EUREKALERT=0`` to disable.
    """
    if editorial is None:
        editorial, _ = load_tastemakers(fetch)
    releases, lookups = [], 0
    for source, titles in editorial.items():
        for title in titles:
            release = Release(source=source, title=title)
            if len(_tokens(title)) >= 4:
                items = crossref_lookup(title, fetch)
                lookups += 1
                if items:
                    work = normalize(items[0])
                    if work and SequenceMatcher(None, title.lower(), work["title"].lower()).ratio() >= 0.45:
                        release.doi = work["doi"]
            releases.append(release)
    if since is not None and os.environ.get("LILT_EUREKALERT", "1").strip() != "0":
        # `fetch` stubs return a tuple too, so the same adapter serves tests and production.
        cached = fetch if fetch is not None else get
        try:
            releases.extend(eurekalert_releases(cached, since, today))
        except Exception:
            pass
    return releases, lookups


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


def arxiv_id_from_locations(work: dict) -> str:
    """First arXiv id in any location's landing page, version suffix stripped.

    OpenAlex reports arXiv ids in locations[].landing_page_url rather than in the
    doi field, so a submission with no registered DOI is otherwise invisible.
    """
    for location in work.get("locations") or []:
        match = ARXIV_LANDING.search((location or {}).get("landing_page_url") or "")
        if match:
            return ARXIV_VERSION.sub("", match.group(1)).lower()
    return ""


def normalize_openalex(work: dict):
    doi = (work.get("doi") or "").replace("https://doi.org/", "").replace("http://doi.org/", "").lower()
    title = clean(work.get("display_name") or "")
    arxiv_id = arxiv_id_from_locations(work)
    if not doi and arxiv_id:
        # No registered DOI: ingest_any routes the pseudo-DOI "arxiv:<id>" to ingest_arxiv.
        doi = "arxiv:" + arxiv_id
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
    return {"id": doi, "doi": doi, "arxiv_id": arxiv_id, "title": title,
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


def openalex_by_doi(doi: str, fetch=None):
    """Single-work OpenAlex lookup by DOI, for press-seeded discovery."""
    params = {"mailto": CONTACT}
    key = os.environ.get("LILT_OPENALEX_KEY", "").strip()
    if key:
        params["api_key"] = key
    url = (OPENALEX + "/https://doi.org/" + urllib.parse.quote(doi, safe="")
           + "?" + urllib.parse.urlencode(params))
    try:
        kind, payload = get(url, fetch)
    except RateLimited:
        return None
    if kind != "json" or not isinstance(payload, dict):
        return None
    return normalize_openalex(payload)


def crossref_by_doi(doi: str, fetch=None):
    params = {"mailto": CONTACT}
    url = CROSSREF + "/" + urllib.parse.quote(doi, safe="") + "?" + urllib.parse.urlencode(params)
    try:
        kind, payload = get(url, fetch)
    except RateLimited:
        return None
    if kind != "json" or not isinstance(payload, dict):
        return None
    return normalize(payload.get("message", {}))


def best_host(work):
    """The beat whose vocabulary best matches the paper, with that beat's terms."""
    best = None
    for raw_host, terms in BEATS.items():
        score = fit(work, terms)
        if best is None or score > best[2]:
            best = (normalize_host(raw_host), terms, score)
    return best


def seed_publicized(works, events_by_doi, exclude, fetch=None, source="crossref", cap=60,
                    since: dt.date | None = None):
    """Add papers a press office publicised even when no beat query surfaced them.

    Press attention is a lead, not an endorsement: the paper still clears the same fit,
    license, reputation and recency gates. Discovery metadata comes from the paper
    connector, never from the release text.
    """
    seeded, attempts = 0, 0
    for doi in events_by_doi:
        if attempts >= cap:
            break
        if doi in works or doi in exclude:
            continue
        attempts += 1
        work = openalex_by_doi(doi, fetch) if source == "openalex" else crossref_by_doi(doi, fetch)
        if work is None or (since is not None and work["date"] < since):
            continue
        match = best_host(work)
        if match is None or match[2] < FIT_GATE:
            continue
        host, terms, _ = match
        work["host"], work["show"], work["terms"] = host, HOSTS[host].show, terms
        work["discovered_by"] = "publicity"
        works[work["doi"]] = work
        seeded += 1
    return seeded


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


def is_preprint_show_work(work) -> bool:
    """A preprint on a show allowed to draw from preprints (arXiv or not)."""
    return (work.get("type") or "").lower() == "preprint" and work.get("host") in PREPRINT_SHOWS


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


# (signal, value getter, descending?, presence?) in the priority order from the plan.
# A presence signal is a *set* ("this outlet covered the paper"): candidates not in the
# set contribute nothing, exactly as a document absent from a retrieval list scores
# nothing in RRF. Treating absent candidates as a tied tail instead made the signal's
# effect shrink with the number of present candidates, which is not what we want.
SIGNALS = [
    ("publicity", lambda w: w["publicity"], True, True),
    ("editorial", lambda w: w["editorial"], True, True),
    ("community", lambda w: w["community"], True, True),
    ("impact", lambda w: math.log1p(w["cited"] / max(w["age"] / 30.0, 0.5)), True, False),
    ("reputation", venue_reputation, True, False),
    ("studiness", lambda w: w["studiness"], True, False),
    ("recency", lambda w: w["age"], False, False),
    ("fascination", lambda w: w["fascination"], True, False),
]


def fuse(candidates, weights=None):
    """Rank-aggregate: each signal contributes weight/(k+rank), so no axis dominates.

    Presence signals (publicity, editorial, community) only score the candidates that
    have them; graded signals score everyone and share a rank on ties, so equal values
    cannot be separated by list order. Exposed separately from `select` so the fusion can
    be measured directly (experiments/selection/publicity_effect.py) with no network.
    """
    weights = weights or SIGNAL_WEIGHTS
    for work in candidates:
        work["fusion"] = 0.0
    for signal, getter, reverse, presence in SIGNALS:
        ordered = sorted((w for w in candidates if not presence or getter(w) > 0),
                         key=getter, reverse=reverse)
        last_value, rank = None, 0
        for index, work in enumerate(ordered):
            value = getter(work)
            if index and value != last_value:
                rank = index
            last_value = value
            work["fusion"] += weights[signal] * rrf(rank)
    for work in candidates:
        work["score"] = round(work["fusion"], 5)
    return candidates


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
    releases, lookups = load_releases(fetch, editorial, since=dt.date.fromisoformat(since), today=today)
    events = cluster_releases(releases)
    events_by_doi = event_index(events)
    # Independent editorial is its own signal; syndicators (ScienceDaily, Phys.org)
    # only corroborate an event, so they are excluded from the fuzzy editorial match.
    independent = {source: titles for source, titles in editorial.items()
                   if source in INDEPENDENT}

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
                work["discovered_by"] = "beat"
                works[work["doi"]] = work

    # A publicized paper can be a candidate even when no beat query surfaced it; the
    # press release is a pointer, so the metadata still comes from the paper connector.
    seeded = seed_publicized(works, events_by_doi, exclude, fetch, source,
                             since=dt.date.fromisoformat(since))

    candidates = []
    retracted = non_primary = 0
    for work in works.values():
        if work.get("is_retracted"):
            retracted += 1
            continue
        # Peer-reviewed articles are the default everywhere. Preprints enter only on
        # the PREPRINT_SHOWS beats, unless the caller explicitly opted into preprints
        # by lowering min_reputation (the --include-preprints escape hatch).
        preprints_here = min_reputation < MIN_REPUTATION or work["host"] in PREPRINT_SHOWS
        allowed_types = PREPRINT_TYPES if preprints_here else PRIMARY_TYPES
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
        # Publicity is one event per paper, so a release repeated across EurekAlert,
        # ScienceDaily and Phys.org contributes one signal, not three. Independent
        # editorial (Quanta, Nature News, Science News) is a separate signal.
        event = events_by_doi.get(work["doi"])
        fuzzy, fuzzy_sources = _similarity(work["title"], independent)
        if event and event.independent:
            editorial_score = 1.0
            editorial_sources = sorted(source for source in event.sources if source in INDEPENDENT)
        elif fuzzy_sources:
            editorial_score = fuzzy
            editorial_sources = fuzzy_sources
        else:
            editorial_score = 0.0
            editorial_sources = []
        # Evidence tier: 'full' when the paper is license-clear (or an arXiv preprint on
        # a preprint show, re-checked at ingest); 'abstract' when only a public abstract
        # is available (any DOI); 'none' otherwise. Abstract-tier stories are written
        # from metadata + abstract only, never reproducing the article.
        full_tier = is_reusable(work["license"]) or (
            is_preprint_show_work(work) and bool(work.get("arxiv_id")))
        tier = "full" if full_tier else ("abstract" if work.get("abstract") else "none")
        work.update({
            "publicity": publicity_value(event),
            "publicity_sources": sorted(event.sources) if event else [],
            "editorial": editorial_score,
            "editorial_sources": editorial_sources,
            # Crossref subject is almost always empty; fall back to the matched beat
            # so the topic-diversity cap actually separates stories.
            "topic": (work["subject"] or [matched])[0],
            "community": _hf_similarity(work["title"], community),
            "age": max((today - work["date"]).days, 0),
            "fascination": fascinating(work),
            "studiness": round(work_studiness, 3),
            "fit": round(score, 3),
            "evidence_tier": tier,
            "reusable": tier != "none",
        })
        candidates.append(work)

    # Rank-aggregate: each signal contributes 1/(k+rank), so no axis dominates.
    fuse(candidates)

    ranked = sorted(candidates, key=lambda w: w["score"], reverse=True)
    selected, show_count, topic_count = [], {}, {}
    for work in ranked:
        # Preprints on the physical/computational shows are judged on license and fit,
        # not on journal reputation: a repository/preprint score is their norm.
        reputation_ok = venue_reputation(work) >= min_reputation or is_preprint_show_work(work)
        if not work["reusable"] or not reputation_ok:
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
            "publicity_events": len(events),
            "publicized_dois": len(events_by_doi),
            "publicized_candidates": sum(1 for w in ranked if w["publicity"]),
            "publicity_seeded": seeded,
            "editorial_titles": sum(len(v) for v in editorial.values()),
            "editorial_lookups": lookups}


def report(result: dict) -> str:
    lines = [f"# Autonomous selection (source: {result.get('source', '?')}, last {result['window_days']} days)",
             f"{result['papers_pulled']} papers pulled, {result['candidates']} scored, "
             f"{result['eligible']} license-eligible; {result['publicity_events']} publicity events "
             f"({result['publicized_dois']} with a DOI, {result['publicized_candidates']} candidate papers, "
             f"{result['publicity_seeded']} seeded); "
             f"{result['editorial_titles']} editorial headlines read", "",
             "| rank | score | show | title | venue | age | cited | publicized by | editorial from | reusable |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for index, work in enumerate(result["selected"], 1):
        venue = (work.get("venue_type") or work["journal"] or "")[:30]
        lines.append(f"| {index} | {work['score']} | {work['show']} | {work['title'][:60]} | "
                     f"{venue} | {work['age']}d | {work['cited']} | "
                     f"{','.join(work['publicity_sources']) or '-'} | "
                     f"{','.join(work['editorial_sources']) or '-'} | {work['reusable']} |")
    return "\n".join(lines)
