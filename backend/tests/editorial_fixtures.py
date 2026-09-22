"""Loader for the audience-contract regression cases.

The fixture file is the shared calibration set for deterministic validation (stage 2)
and audience review (stage 3). Cases carry the spoken text plus the expected verdict, so
both layers can be tested against the same examples rather than against a slogan.

`improvement` strings are illustrative rewrites for calibration. They are not approved
production scripts and must never be published or used as generation output.
"""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "editorial_cases.json"


def load() -> dict:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def cases(*, format: str | None = None, audience: str | None = None,
          deterministic: str | None = None) -> list[dict]:
    """Cases, optionally filtered by script format, audience verdict or expected check."""
    selected = load()["cases"]
    if format is not None:
        selected = [c for c in selected if c["format"] == format]
    if audience is not None:
        selected = [c for c in selected if c["audience"] == audience]
    if deterministic is not None:
        selected = [c for c in selected if deterministic in c["deterministic"]]
    return selected


def spoken(case: dict) -> str:
    """The spoken text of a case, whether it is a solo body or a list of turns."""
    if "turns" in case:
        return " ".join(turn["text"] for turn in case["turns"])
    return case["text"]
