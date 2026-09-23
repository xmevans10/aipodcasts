#!/usr/bin/env python3
"""Fail closed before a transcript batch can be rendered or published.

Also used to validate approved seed artifacts when a GitHub Actions run resumes
the stage 4 batch. This performs no network calls and needs no credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tools" / "tts"))

from beats import BEATS, normalize_host  # noqa: E402
from bundle_shows import load_cast, narration_inputs  # noqa: E402
from hosts import HOSTS  # noqa: E402
from run_all_shows import render, slug, word_count  # noqa: E402


def check_artifact(artifact: dict, entry: dict, transcripts: Path, cast: dict) -> None:
    """Check an approved JSON/Markdown pair against the manifest and release gate."""
    show = entry["show"]
    host = entry["host"]
    if (artifact.get("show"), artifact.get("host"), artifact.get("story_id")) != (
        show, host, entry.get("story_id")
    ):
        raise ValueError(f"{show}: artifact identity differs from manifest")
    if host not in HOSTS or HOSTS[host].show != show:
        raise ValueError(f"{show}: unknown or mismatched host")
    draft = artifact.get("draft") or {}
    if not artifact.get("doi") or not artifact.get("source", {}).get("title"):
        raise ValueError(f"{show}: missing paper metadata")
    if draft.get("title") != entry.get("title") or word_count(draft) != entry.get("words"):
        raise ValueError(f"{show}: title or word count differs from manifest")
    if artifact.get("words") != entry["words"]:
        raise ValueError(f"{show}: artifact word count differs from manifest")
    if entry.get("verification_pass") is False or entry.get("factual") not in (None, "pass"):
        raise ValueError(f"{show}: manifest records a failed factual review")
    listener = artifact.get("audience") or {}
    relaxed_revise = (os.environ.get("LILT_ENTERTAINMENT_RELEASE") == "1"
                      and listener.get("decision") == "revise"
                      and listener.get("beat_fit") in ("grounded", "weak"))
    if entry.get("audience_pass") is False and not relaxed_revise:
        raise ValueError(f"{show}: manifest records a failed audience review")
    narration_inputs(artifact, cast)
    expected_md = render(draft, artifact["source"], host).strip()
    actual_md = (transcripts / (slug(show) + ".md")).read_text().strip()
    if actual_md != expected_md:
        raise ValueError(f"{show}: Markdown differs from approved JSON script")


def check_batch(directory: Path, *, require_all: bool = True) -> tuple[int, int]:
    manifest = json.loads((directory / "manifest.json").read_text())
    entries = manifest["shows"]
    expected = {HOSTS[normalize_host(host)].show for host in BEATS}
    names = [entry["show"] for entry in entries]
    if len(names) != len(set(names)) or set(names) != expected:
        raise ValueError(f"Manifest show set differs from canonical batch: {sorted(expected - set(names))}")
    transcripts = directory / "transcripts"
    cast = load_cast(ROOT / "tools" / "tts" / "voice_cast.json")
    approved = [entry for entry in entries if entry.get("status") == "approved"]
    if manifest.get("approved") is not None and manifest["approved"] != len(approved):
        raise ValueError("Manifest approved count is inconsistent")
    for entry in approved:
        path = transcripts / (slug(entry["show"]) + ".json")
        check_artifact(json.loads(path.read_text()), entry, transcripts, cast)
    actual_json = {p.stem for p in transcripts.glob("*.json")}
    if actual_json != {slug(e["show"]) for e in approved}:
        raise ValueError("Transcript directory contains missing or unapproved JSON artifacts")
    if require_all and len(approved) != len(expected):
        pending = [e["show"] for e in entries if e.get("status") != "approved"]
        raise ValueError(f"Only {len(approved)}/{len(expected)} approved; withheld: {', '.join(pending)}")
    if require_all and manifest.get("release_ready") is False:
        raise ValueError("Manifest explicitly marks this batch as not release ready")
    return len(approved), len(expected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-partial", action="store_true", help="validate approved seed artifacts")
    args = parser.parse_args()
    approved, total = check_batch(args.directory, require_all=not args.allow_partial)
    print(f"Checked {approved}/{total} approved episodes")


if __name__ == "__main__":
    main()
