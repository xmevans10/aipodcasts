#!/usr/bin/env python3
"""Add failed batch papers to a JSON DOI exclusion list before a retry."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DOI = re.compile(r"10\.\d{4,9}/[^\s,;]+", re.I)


def failed_dois(manifest: dict) -> set[str]:
    excluded = set()
    for entry in manifest.get("shows", []):
        if entry.get("status") == "approved":
            continue
        doi = entry.get("doi", "")
        if doi:
            excluded.add(str(doi).rstrip(".,:)]").casefold())
        for error in entry.get("errors", []):
            if "Named author metadata is required before generation" in str(error):
                continue
            for match in DOI.findall(str(error)):
                excluded.add(match.rstrip(".,:)]").casefold())
    return excluded


def metadata_retry_dois(manifest: dict) -> set[str]:
    """Do not permanently exclude papers whose only ingest failure is missing author data."""
    retry = set()
    for entry in manifest.get("shows", []):
        for error in entry.get("errors", []):
            if "Named author metadata is required before generation" not in str(error):
                continue
            retry.update(match.rstrip(".,:)]").casefold() for match in DOI.findall(str(error)))
    return retry


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("exclusions", type=Path)
    args = parser.parse_args()
    current = json.loads(args.exclusions.read_text())
    manifest = json.loads(args.manifest.read_text())
    if not isinstance(current, list) or any(not isinstance(doi, str) for doi in current):
        raise ValueError("DOI exclusion list is malformed")
    result = sorted(({doi.casefold() for doi in current} - metadata_retry_dois(manifest))
                    | failed_dois(manifest))
    args.exclusions.write_text(json.dumps(result) + "\n")
    print(f"Added {len(result) - len(set(current))} failed paper DOI exclusions")


if __name__ == "__main__":
    main()
