"""Rank recent publications into a per-show shortlist for editorial review.

Deterministic and key-free. It reads OpenAlex discovery metadata for a date window,
scores each candidate on four explainable axes, gates on show fit, and returns a
ranked list the operator can act on. It never ingests or publishes; the rights gate
in `pipeline.ingest` still decides what can actually be used.

Signals (all 0-1 before weighting):
  importance  field-weighted citation impact + cited-by percentile + journal impact
  momentum    citations per month since publication (a proxy for current attention)
  interest    title/abstract heuristics: surprise, concrete numbers, a question hook,
              short readable words, minus jargon density
  fit         how well the paper matches a show's beat vocabulary (beats.py)

`attention` (Altmetric) is enriched best-effort for the top candidates only, since it
is a separate per-DOI request; it is reported, not required.

Usage:
    python3 backend/pipeline.py shortlist --days 7 --per-host 3
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from beats import BEATS, normalize_host
from hosts import HOSTS

OPENALEX = "https://api.openalex.org/works"
ALTMETRIC = "https://api.altmetric.com/v1/doi/{doi}"
TIMEOUT = 40
DATA = Path(os.environ.get("LILT_DATA", Path(__file__).resolve().parent / "data"))
CACHE = DATA / "cache" / "openalex"
CACHE_TTL_HOURS = 12


class RateLimited(RuntimeError):
    """OpenAlex's shared free budget is exhausted; a key or a wait is required."""

WEIGHTS = {"importance": 0.28, "momentum": 0.22, "interest": 0.28, "fit": 0.22}
FIT_GATE = 0.12
MAX_PER_TOPIC = 2

SURPRISE = ("unexpected", "surprising", "surprise", "paradox", "counterintuitive",
            "counter-intuitive", "challenge", "overturn", "contradict", "despite",
            "for the first time", "never", "rare", "hidden", "mysterious",
            "unprecedented", "reveals", "unravel", "enigma")
JARGON = ("signaling", "pathway", "expression", "receptor", "transcript", "in vitro",
          "in vivo", "genome-wide", "differential", "quantitative", "molecular",
          "mechanistic", "knockout", "phenotype", "allele", "downstream")


def _norm(value, low, high):
    if value is None:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def abstract_of(work) -> str:
    inverted = work.get("abstract_inverted_index")
    if not inverted:
        return ""
    positions: dict[int, str] = {}
    for word, indices in inverted.items():
        for index in indices:
            positions[index] = word
    return " ".join(positions[i] for i in sorted(positions))


def days_old(date_string, today: dt.date):
    if not date_string:
        return None
    try:
        published = dt.date.fromisoformat(date_string[:10])
    except ValueError:
        return None
    return (today - published).days


def doi_of(work) -> str:
    return (work.get("doi") or "").replace("https://doi.org/", "").replace("http://doi.org/", "")


def rights(work, doi: str):
    location = work.get("primary_location") or {}
    license_id = location.get("license") or (work.get("best_oa_location") or {}).get("license") or ""
    oa_status = (work.get("open_access") or {}).get("oa_status") or "closed"
    reusable = doi.startswith("10.1371/") and "cc-by" in license_id.lower()
    return {"oa_status": oa_status, "license": license_id,
            "reusable": reusable,
            "rights": "PLOS CC BY; ingestable" if reusable else "needs rights review"}


def score(work, host: str, terms: list[str], today: dt.date) -> dict:
    title = work.get("display_name") or work.get("title") or ""
    abstract = abstract_of(work)
    text = f"{title} {abstract}".lower()
    stats = work.get("summary_stats") or {}
    fwci = stats.get("fwci") or 0
    mean_cited = stats.get("2yr_mean_citedness") or 0
    percentile = (work.get("cited_by_percentile_year") or {}).get("min") or 0
    importance = (0.5 * _norm(fwci, 0, 5) + 0.3 * _norm(mean_cited, 0, 20)
                  + 0.2 * _norm(percentile, 0, 100))

    age_days = days_old(work.get("publication_date"), today) or 1
    months = max(age_days / 30.0, 0.5)
    velocity = (work.get("cited_by_count") or 0) / months
    momentum = _norm(math.log1p(velocity), 0, math.log1p(50))

    surprises = sum(text.count(term) for term in SURPRISE)
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    title_words = re.findall(r"[a-z']+", title.lower())
    average_word = sum(len(word) for word in title_words) / len(title_words) if title_words else 9
    jargon = sum(text.count(term) for term in JARGON)
    interest = max(0.0, 0.35 * min(1.0, surprises / 3)
                   + 0.2 * min(1.0, numbers / 6)
                   + 0.1 * (1.0 if "?" in title else 0.0)
                   + 0.35 * _norm(14 - average_word, 0, 6)
                   - 0.3 * min(1.0, jargon / 3))

    hits = sum(1 for term in terms if term.lower() in text)
    topic_conf = ((work.get("primary_topic") or {}).get("score") or 0)
    fit = min(1.0, 0.7 * (hits / len(terms) if terms else 0) + 0.3 * topic_conf)

    total = (WEIGHTS["importance"] * importance + WEIGHTS["momentum"] * momentum
             + WEIGHTS["interest"] * interest + WEIGHTS["fit"] * fit)
    topic = (work.get("primary_topic") or {}).get("display_name") or "unclassified"
    reasons = []
    if importance >= 0.5:
        reasons.append("high field impact")
    if momentum >= 0.6:
        reasons.append("fast-cited")
    if surprises >= 2:
        reasons.append("counterintuitive framing")
    if fit >= 0.5:
        reasons.append("strong beat fit")
    return {
        "score": round(total, 4), "importance": round(importance, 4),
        "momentum": round(momentum, 4), "interest": round(interest, 4), "fit": round(fit, 4),
        "hits": hits, "topic": topic, "host": host, "show": HOSTS[host].show,
        "reason": "; ".join(reasons) or "beat match",
    }


def get_json(url: str, fetch=None) -> dict | None:
    if fetch is not None:
        return fetch(url)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
    if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL_HOURS * 3600:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    request = urllib.request.Request(url, headers={"User-Agent": "ZwickyResearch/0.1 (story shortlist)"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise RateLimited(error.read(200).decode(errors="replace"))
        return None
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    except OSError:
        pass
    return data


def openalex_window(term: str, days: int, contact: str, today: dt.date, fetch=None,
                    per_page: int = 25):
    since = (today - dt.timedelta(days=days)).isoformat()
    params = {
        "search": term,
        "filter": f"from_publication_date:{since},type:article,is_retracted:false",
        "per-page": per_page,
        "mailto": contact,
    }
    key = os.environ.get("LILT_OPENALEX_KEY", "").strip()
    if key:
        params["api_key"] = key
    data = get_json(OPENALEX + "?" + urllib.parse.urlencode(params), fetch)
    return (data or {}).get("results", [])


def altmetric_attention(doi: str, fetch=None):
    if not doi:
        return None
    data = get_json(ALTMETRIC.format(doi=urllib.parse.quote(doi, safe="")), fetch)
    if not data:
        return None
    return _norm(data.get("score", 0), 0, 100), data.get("score")


def seen_dois(db) -> set[str]:
    found = set()
    for row in db.execute("SELECT source FROM stories WHERE source IS NOT NULL"):
        try:
            found.add((json.loads(row["source"]).get("doi") or "").lower())
        except (json.JSONDecodeError, TypeError):
            continue
    return {doi for doi in found if doi}


def rank(db, days: int = 7, per_host: int = 3, limit: int = 25,
         contact: str = "zwicky-research@example.com", today: dt.date | None = None,
         fetch=None, enrich: bool = True) -> dict:
    today = today or dt.date.today()
    exclude = seen_dois(db)
    candidates: dict[str, dict] = {}
    query_count = 0
    rate_limited = 0
    empty = 0

    for raw_host, terms in BEATS.items():
        host = normalize_host(raw_host)
        for term in terms:
            query_count += 1
            try:
                works = openalex_window(term, days, contact, today, fetch)
            except RateLimited:
                rate_limited += 1
                works = []
            if not works:
                empty += 1
            for work in works:
                key = (work.get("id") or doi_of(work)).rsplit("/", 1)[-1]
                if not key:
                    continue
                doi = doi_of(work)
                if doi.lower() in exclude:
                    continue
                scored = score(work, host, terms, today)
                # Require a real beat-term hit; topic confidence alone misroutes
                # (an archaeology paper must not become a materials show).
                if scored["fit"] < FIT_GATE or scored["hits"] < 1:
                    continue
                existing = candidates.get(key)
                if existing is None or scored["score"] > existing["score"]:
                    candidates[key] = {"work": work, **scored, "doi": doi,
                                       "title": work.get("display_name") or "",
                                       "journal": ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
                                       "date": work.get("publication_date", ""),
                                       "days_old": days_old(work.get("publication_date"), today),
                                       "cited_by": work.get("cited_by_count", 0),
                                       **rights(work, doi)}

    ranked = sorted(candidates.values(), key=lambda item: item["score"], reverse=True)

    if enrich and ranked:
        for item in ranked[:25]:
            attention = altmetric_attention(item["doi"], fetch)
            if attention:
                score_value, raw = attention
                item["attention"] = round(score_value, 4)
                item["altmetric"] = raw
                item["score"] = round(item["score"] * 0.9 + score_value * 0.1, 4)

    selected, host_count, topic_count = [], {}, {}
    for item in sorted(ranked, key=lambda entry: entry["score"], reverse=True):
        host, topic = item["host"], item["topic"]
        if host_count.get(host, 0) >= per_host:
            continue
        if topic_count.get(topic, 0) >= MAX_PER_TOPIC:
            continue
        host_count[host] = host_count.get(host, 0) + 1
        topic_count[topic] = topic_count.get(topic, 0) + 1
        selected.append(item)
        if len(selected) >= limit:
            break
    result = {"window_days": days, "queries": query_count, "candidates": len(ranked),
              "excluded_known": len(exclude), "rate_limited": rate_limited,
              "empty_queries": empty, "shortlist": selected}
    if not selected and rate_limited:
        result["warning"] = ("OpenAlex free budget exhausted. Set LILT_OPENALEX_KEY "
                             "(free at openalex.org) or retry after midnight UTC.")
    return result


def report(result: dict) -> str:
    lines = [f"# Story shortlist (last {result['window_days']} days)",
             f"{result['candidates']} candidates from {result['queries']} beat queries; "
             f"{result['excluded_known']} already-ingested DOIs excluded", "",
             "| rank | score | show | host | title | date | topic | rights | why |",
             "|---|---|---|---|---|---|---|---|---|"]
    for index, item in enumerate(result["shortlist"], 1):
        title = item["title"][:70].replace("|", "/")
        lines.append(f"| {index} | {item['score']} | {item['show']} | {item['host']} | {title} | "
                     f"{item['date']} | {item['topic']} | {item['rights']} | {item['reason']} |")
    return "\n".join(lines)
