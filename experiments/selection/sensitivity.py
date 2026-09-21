#!/usr/bin/env python3
"""Sensitivity analysis for paper selection: new / fascinating / reputable.

No human relevance labels exist, so this does not claim a "best" ranking. It measures
two things a designer can act on:

  1. SIGNAL AVAILABILITY: at which recency window do the axes actually have data?
     Citations are ~0 for a week-old paper, so "reputable" via citations only becomes
     meaningful as the window widens.
  2. ROBUSTNESS: how much does the top-K change when we perturb weights, recency
     half-life, gate threshold and source? A config whose top picks survive every
     perturbation is defensible without labels; one that reshuffles is not.

Corpus comes from Crossref (free, no key). Results print and are written as JSON+MD.

    python3 experiments/selection/sensitivity.py --windows 7,30,90,365
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from beats import BEATS, normalize_host  # noqa: E402
from hosts import HOSTS  # noqa: E402

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
CROSSREF = "https://api.crossref.org/works"
CONTACT = "zwicky-research@example.com"

SURPRISE = ("unexpected", "surprising", "surprise", "paradox", "counterintuitive", "challenge",
            "overturn", "contradict", "despite", "first time", "never", "rare", "hidden",
            "mysterious", "unprecedented", "reveals", "unravel", "enigma")
JARGON = ("signaling", "pathway", "expression", "receptor", "transcript", "in vitro", "in vivo",
          "genome-wide", "differential", "quantitative", "molecular", "mechanistic", "knockout",
          "phenotype", "allele", "downstream")
TIER1 = ("nature", "science", "cell", "pnas", "proceedings of the national academy",
         "physical review letters", "lancet", "new england journal", "jama", "bmj", "elife")


def norm(x, low, high):
    if x is None:
        return 0.0
    return max(0.0, min(1.0, (x - low) / (high - low)))


def clean(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").replace("&amp;", "&")


def fetch_crossref(term: str, since: str, rows: int = 40):
    params = {
        "query.bibliographic": term,
        "filter": f"from-pub-date:{since},type:journal-article",
        "rows": rows, "mailto": CONTACT,
    }
    url = CROSSREF + "?" + urllib.parse.urlencode(params)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
    if path.exists():
        return json.loads(path.read_text())
    request = urllib.request.Request(url, headers={"User-Agent": "ZwickyResearch/0.1 (selection sensitivity)"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            data = json.loads(response.read())["message"]["items"]
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError, KeyError):
        return []  # never cache a failure
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def normalize(item: dict) -> dict | None:
    doi = (item.get("DOI") or "").lower()
    title = clean((item.get("title") or [""])[0]).strip()
    if not doi or not title:
        return None
    parts = (item.get("issued") or {}).get("date-parts", [[None]])[0]
    if not parts or not parts[0]:
        return None
    try:
        date = dt.date(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)
    except ValueError:
        return None
    return {"id": doi, "doi": doi, "title": title, "abstract": clean(item.get("abstract") or ""),
            "date": date.isoformat(), "journal": clean((item.get("container-title") or [""])[0]),
            "subject": (item.get("subject") or []), "cited": item.get("is-referenced-by-count", 0) or 0,
            "references": item.get("reference-count", 0) or 0,
            "license": ((item.get("license") or [{}])[0] or {}).get("URL", "")}


# ---- axes -----------------------------------------------------------------
def axis_new(work, today, half_life):
    age = max((today - dt.date.fromisoformat(work["date"])).days, 0)
    return 0.5 ** (age / max(half_life, 1)), age


def axis_fascinating(work):
    text = (work["title"] + " " + work["abstract"]).lower()
    surprises = sum(text.count(term) for term in SURPRISE)
    numbers = len(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    words = re.findall(r"[a-z']+", work["title"].lower())
    average = sum(len(word) for word in words) / len(words) if words else 9
    jargon = sum(text.count(term) for term in JARGON)
    return max(0.0, 0.35 * min(1.0, surprises / 3) + 0.2 * min(1.0, numbers / 6)
               + 0.1 * (1.0 if "?" in work["title"] else 0.0)
               + 0.35 * norm(14 - average, 0, 6) - 0.3 * min(1.0, jargon / 3))


def axis_reputable(work, citation_p90):
    venue = work["journal"].lower()
    tier = 1.0 if any(name in venue for name in TIER1) else (0.6 if venue else 0.2)
    citations = norm(math.log1p(work["cited"]), 0, math.log1p(citation_p90 or 10))
    peer = 1.0
    return 0.5 * tier + 0.3 * citations + 0.2 * peer


def axis_fit(work, terms):
    text = (work["title"] + " " + work["abstract"]).lower()
    return sum(1 for term in terms if term.lower() in text) / len(terms)


def load_corpus(window: int, today: dt.date, per_show: int = 2):
    since = (today - dt.timedelta(days=window)).isoformat()
    works: dict[str, dict] = {}
    hits: dict[str, str] = {}
    for raw_host, terms in BEATS.items():
        host = normalize_host(raw_host)
        for term in terms[:per_show]:
            for item in fetch_crossref(term, since):
                work = normalize(item)
                if work is None:
                    continue
                work["host"] = host
                work["show"] = HOSTS[host].show
                work["terms"] = terms
                prior = works.get(work["id"])
                if prior is None or axis_fit(work, terms) > axis_fit(prior, prior["terms"]):
                    works[work["id"]] = work
    return list(works.values())


def spearman(a: list[str], b: list[str]):
    rank_a = {k: i for i, k in enumerate(a)}
    rank_b = {k: i for i, k in enumerate(b)}
    common = set(rank_a) & set(rank_b)
    if len(common) < 3:
        return None
    n = len(common)
    diff = sum((rank_a[k] - rank_b[k]) ** 2 for k in common)
    return round(1 - (6 * diff) / (n * (n * n - 1)), 4)


def jaccard(a, b):
    sa, sb = set(a), set(b)
    return round(len(sa & sb) / len(sa | sb), 3) if sa | sb else 1.0


def score_all(corpus, today, weights, half_life):
    cited = sorted((work["cited"] for work in corpus), reverse=True)
    p90 = cited[max(0, int(len(cited) * 0.1) - 1)] if cited else 10
    scored = []
    for work in corpus:
        new, age = axis_new(work, today, half_life)
        fascinating = axis_fascinating(work)
        reputable = axis_reputable(work, p90)
        fit = axis_fit(work, work["terms"])
        if fit < 0.25:
            continue
        total = (weights["new"] * new + weights["fascinating"] * fascinating
                 + weights["reputable"] * reputable + weights["fit"] * fit)
        scored.append({**work, "age": age, "new": round(new, 4), "fascinating": round(fascinating, 4),
                       "reputable": round(reputable, 4), "fit": round(fit, 4), "total": round(total, 4)})
    return sorted(scored, key=lambda entry: entry["total"], reverse=True)


BASELINE = {"new": 0.25, "fascinating": 0.35, "reputable": 0.30, "fit": 0.10}
HALF_LIFE = 30


def analyze(corpus, today, half_life=HALF_LIFE, top=20):
    baseline = score_all(corpus, today, BASELINE, half_life)
    base_ids = [w["id"] for w in baseline[:top]]
    report = {"corpus": len(corpus), "base_top": base_ids,
              "citation_coverage": round(mean(1 if w["cited"] >= 1 else 0 for w in corpus), 3) if corpus else 0,
              "abstract_coverage": round(mean(1 if w["abstract"] else 0 for w in corpus), 3) if corpus else 0,
              "perturbations": {}}
    for axis in ("new", "fascinating", "reputable", "fit"):
        for factor in (0.5, 1.5):
            weights = dict(BASELINE)
            weights[axis] = round(weights[axis] * factor, 3)
            ranked = score_all(corpus, today, weights, half_life)
            ids = [w["id"] for w in ranked[:top]]
            report["perturbations"][f"{axis}x{factor}"] = {
                "jaccard_top": jaccard(base_ids, ids),
                "spearman_all": spearman([w["id"] for w in baseline], [w["id"] for w in ranked]),
            }
    for life in (7, 90, 365):
        ranked = score_all(corpus, today, BASELINE, life)
        report["perturbations"][f"half_life_{life}"] = {
            "jaccard_top": jaccard(base_ids, [w["id"] for w in ranked[:top]]),
            "spearman_all": spearman([w["id"] for w in baseline], [w["id"] for w in ranked]),
        }
    # Robust picks: present in the top-`top` under every single perturbation.
    sets = []
    for config in report["perturbations"]:
        if config.startswith("half_life_"):
            ranked = score_all(corpus, today, BASELINE, int(config.split("_")[-1]))
        else:
            axis, factor = config.rsplit("x", 1)
            weights = dict(BASELINE); weights[axis] = round(weights[axis] * float(factor), 3)
            ranked = score_all(corpus, today, weights, half_life)
        sets.append({w["id"] for w in ranked[:top]})
    robust = set(base_ids)
    for s in sets:
        robust &= s
    report["robust_top"] = [w for w in base_ids if w in robust]
    report["robust_titles"] = [w["title"] for w in baseline if w["id"] in robust][:10]
    return report, baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows", default="7,30,90,365")
    parser.add_argument("--today", default=dt.date.today().isoformat())
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    today = dt.date.fromisoformat(args.today)
    windows = [int(w) for w in args.windows.split(",")]

    out = {"today": args.today, "baseline_weights": BASELINE, "half_life": HALF_LIFE, "windows": {}}
    print(f"today={today} baseline={BASELINE} half_life={HALF_LIFE}\n")
    corpora = {}
    for window in windows:
        corpus = load_corpus(window, today)
        corpora[window] = corpus
        report, baseline = analyze(corpus, today, top=args.top)
        out["windows"][str(window)] = {k: v for k, v in report.items() if k != "base_top"}
        out["windows"][str(window)]["top10"] = [
            {"title": w["title"][:80], "show": w["show"], "journal": w["journal"][:40],
             "age": w["age"], "cited": w["cited"], "new": w["new"], "fascinating": w["fascinating"],
             "reputable": w["reputable"], "total": w["total"]}
            for w in baseline[:10]]
        print(f"== window {window}d: {report['corpus']} papers | citation coverage {report['citation_coverage']} "
              f"| abstract coverage {report['abstract_coverage']}")
        print("   perturbations (top-20 Jaccard / rank correlation):")
        for name, values in report["perturbations"].items():
            print(f"     {name:22} {values['jaccard_top']:>5}  {values['spearman_all']}")
        print(f"   robust picks ({len(report['robust_top'])}):")
        for title in report["robust_titles"][:6]:
            print("     -", title[:80])
        print()

    # Cross-window overlap: does widening the window change the winners?
    print("== cross-window top-20 overlap ==")
    tops = {}
    for window in windows:
        ranked = score_all(corpora[window], today, BASELINE, HALF_LIFE)
        tops[window] = [w["id"] for w in ranked[:args.top]]
    for i, a in enumerate(windows):
        for b in windows[i + 1:]:
            print(f"   {a}d vs {b}d: {jaccard(tops[a], tops[b])}")
    out["cross_window_jaccard"] = {f"{a}v{b}": jaccard(tops[a], tops[b])
                                   for i, a in enumerate(windows) for b in windows[i + 1:]}
    (HERE / "sensitivity.json").write_text(json.dumps(out, indent=2))
    print("\nwrote", HERE / "sensitivity.json")


if __name__ == "__main__":
    main()
