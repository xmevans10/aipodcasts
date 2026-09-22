#!/usr/bin/env python3
"""Run the full autonomous pipeline across every show and save the transcripts.

For each canonical show this selects candidates, ingests the first with usable evidence,
drafts the episode, and runs the automated verification gate. It writes one transcript per
show plus a manifest, and by default never narrates or publishes, so no audio provider or
public feed is touched.

    LILT_MAX_PROVIDER_CALLS_PER_DAY=64 python3 experiments/full-run/run_all_shows.py
    python3 experiments/full-run/run_all_shows.py --select-only   # no API calls
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from beats import BEATS, normalize_host  # noqa: E402
from pipeline import (HOSTS, approve_auto, connect, draft_story, ingest_any,  # noqa: E402
                      load_local_env, row, select_stories)

HERE = Path(__file__).resolve().parent


def canonical_hosts() -> list:
    """One canonical host id per show, in BEATS order; dialogue members collapse."""
    return list(dict.fromkeys(normalize_host(host) for host in BEATS))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "untitled"


def render(draft: dict, source: dict, host_id: str) -> str:
    lines = [f"# {draft.get('title', '')}", "", f"*{draft.get('dek', '')}*", ""]
    if "turns" in draft:
        for turn in draft["turns"]:
            lines.append(f"**{turn.get('speaker', '')}:** {turn.get('text', '')}")
            lines.append("")
    else:
        lines += [draft.get("body", ""), ""]
    lines += [f"**Caveat:** {draft.get('caveat', '')}", "", "## Claims", ""]
    for claim in draft.get("claims", []):
        lines += [f"- {claim.get('claim', '')}", f"  > {claim.get('quote', '')}"]
    source_line = " — ".join(part for part in (
        source.get("title", ""), source.get("attribution", ""),
        source.get("journal", ""), source.get("url", "")) if part)
    lines += ["", "## Source", source_line, "",
              f"Evidence tier: `{source.get('evidence_tier', '?')}` · "
              f"license: `{source.get('license', '?')}`"]
    return "\n".join(lines)


def word_count(draft: dict) -> int:
    if "turns" in draft:
        return sum(len(turn.get("text", "").split()) for turn in draft.get("turns", []))
    return len(draft.get("body", "").split())


def build(args):
    load_local_env()
    db = connect()
    today = dt.date.today()
    selection = select_stories(db, days=args.days, per_show=args.per_show, limit=args.limit,
                               today=today, fetch=None, source=None)

    by_host: dict[str, list] = {}
    for work in selection["selected"]:
        by_host.setdefault(work["host"], []).append(work)

    out = Path(args.out) if args.out else HERE / ("run-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    transcripts = out / "transcripts"
    transcripts.mkdir(parents=True, exist_ok=True)

    print(f"selection: {selection['papers_pulled']} papers, {selection['candidates']} scored, "
          f"{selection['publicity_events']} publicity events, {len(selection['selected'])} candidates")
    print(f"writing artifacts to {out}")
    print(f"provider call cap: {os.environ.get('LILT_MAX_PROVIDER_CALLS_PER_DAY', '12')}\n")

    entries = []
    for host in canonical_hosts():
        show = HOSTS[host].show
        candidates = by_host.get(host, [])
        entry = {"host": host, "show": show, "candidates": len(candidates),
                 "status": "no_candidate", "doi": "", "title": ""}
        if args.select_only:
            entry["candidate_dois"] = [w["doi"] for w in candidates]
            entry["candidate_titles"] = [w["title"][:80] for w in candidates]
            entries.append(entry)
            continue

        errors = []
        for work in candidates:
            try:
                story_id = ingest_any(db, work["doi"], host)
                draft = draft_story(db, story_id)
                record = row(db, story_id)
                source = json.loads(record["source"])
                verification = None
                if not args.no_verify:
                    verification = approve_auto(db, story_id, args.decider)
                stamp = slug(show)
                artifact = {"show": show, "host": host, "story_id": story_id,
                            "doi": work["doi"], "requested_by": work.get("discovered_by", "beat"),
                            "publicity_sources": work.get("publicity_sources", []),
                            "source": {k: source.get(k) for k in
                                       ("title", "attribution", "journal", "url", "license",
                                        "evidence_tier", "evidence_note")},
                            "words": word_count(draft), "verification": verification, "draft": draft}
                (transcripts / f"{stamp}.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False))
                (transcripts / f"{stamp}.md").write_text(render(draft, source, host))
                listener = (verification or {}).get("audience") or {}
                artifact["audience"] = listener or None
                (transcripts / f"{stamp}.json").write_text(
                    json.dumps(artifact, indent=2, ensure_ascii=False))
                entry.update({"status": verification.get("status", "drafted") if verification else "drafted",
                              "doi": work["doi"], "title": draft.get("title", ""),
                              "story_id": story_id, "words": word_count(draft),
                              "evidence_tier": source.get("evidence_tier"),
                              "verification_pass": (verification or {}).get("pass"),
                              "audience_pass": listener.get("pass"),
                              "audience_decision": listener.get("decision"),
                              "beat_fit": listener.get("beat_fit"),
                              "audience_repairs": (verification or {}).get("audience_repairs")})
                print(f"  {show:16} {entry['status']:24} {draft.get('title', '')[:52]}")
                break
            except Exception as error:  # one bad show must not abort the batch
                errors.append(f"{work['doi']}: {type(error).__name__}: {error}"[:200])
                continue
        else:
            entry["errors"] = errors
            print(f"  {show:16} FAILED                 {errors[-1] if errors else 'no candidates'}")
        entries.append(entry)

    manifest = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(),
                "window_days": args.days, "selection": {k: selection[k] for k in
                    ("papers_pulled", "candidates", "publicity_events", "publicized_candidates")},
                "shows": entries}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    lines = ["# Full-run transcripts", "",
             f"- Generated: {manifest['generated']}",
             f"- Window: {args.days} days · {sum(1 for e in entries if e['status'] not in ('no_candidate', 'FAILED'))}/{len(entries)} shows drafted", "",
             "| Show | Host | Status | Title | Words | Tier | Factual | Audience | Beat fit |",
             "|---|---|---|---|---|---|---|---|---|"]
    for entry in entries:
        lines.append(f"| {entry['show']} | {entry['host']} | {entry['status']} | "
                     f"{entry.get('title', '')[:60]} | {entry.get('words', '')} | "
                     f"{entry.get('evidence_tier', '')} | {entry.get('verification_pass', '')} | "
                     f"{entry.get('audience_decision') or entry.get('audience_pass', '')} | "
                     f"{entry.get('beat_fit', '')} |")
    approved = sum(1 for e in entries if e["status"] == "approved")
    lines += ["",
              f"**{approved}/{len(entries)} shows approved.** A show that is not `approved` is "
              "not part of a release: it is withheld or blocked, and must be reported as such.",
              ""]
    (out / "manifest.md").write_text("\n".join(lines) + "\n")

    db.close()
    drafted = sum(1 for e in entries if e["status"] not in ("no_candidate", "FAILED"))
    approved = sum(1 for e in entries if e["status"] == "approved")
    print(f"\n{drafted}/{len(entries)} shows drafted, {approved}/{len(entries)} approved -> {out}")
    for entry in entries:
        if entry["status"] != "approved":
            print(f"  NOT APPROVED  {entry['show']:16} {entry['status']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--per-show", type=int, default=3)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--out", default="")
    parser.add_argument("--decider", default="auto")
    parser.add_argument("--select-only", action="store_true", help="candidates only; no API calls")
    parser.add_argument("--no-verify", action="store_true")
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
