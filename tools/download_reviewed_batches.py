#!/usr/bin/env python3
"""Recover individually approved scripts from completed Actions runs.

A failed complete-batch gate must not strand safe partial inventory. Every downloaded
artifact still passes the current strict script/review checks before it can be selected.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "full-run"))
from check_batch import check_batch  # noqa: E402


def download_batches(directory: Path, baseline: int, *, run=subprocess.run) -> dict:
    response = run(["gh", "run", "list", "--workflow", "full-run.yml", "--status", "completed",
                    "--limit", "100", "--json", "databaseId,status,conclusion"],
                   check=True, capture_output=True, text=True)
    runs = json.loads(response.stdout)
    ids = sorted({entry["databaseId"] for entry in runs
                  if entry.get("status") == "completed"
                  and isinstance(entry.get("databaseId"), int)
                  and entry["databaseId"] >= baseline})
    directory.mkdir(parents=True, exist_ok=True)
    usable, approved = [], 0
    for run_id in ids:
        target = directory / str(run_id)
        if target.exists():
            raise ValueError(f"Batch download directory must start fresh: {target}")
        result = run(["gh", "run", "download", str(run_id), "--name", "full-run-transcripts",
                      "--dir", str(target)], capture_output=True, text=True)
        if result.returncode:
            print(f"Skipping unavailable artifact from run {run_id}: {result.stderr.strip()}",
                  file=sys.stderr)
            continue
        try:
            count, total = check_batch(target, require_all=False)
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"Skipping invalid batch {run_id}: {error}", file=sys.stderr)
            continue
        print(f"Run {run_id}: {count}/{total} strictly approved scripts")
        if count:
            usable.append(run_id)
            approved += count
    if not usable:
        raise ValueError(f"No usable reviewed batch artifacts after baseline {baseline}")
    return {"runs": usable, "approved_scripts": approved}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(download_batches(args.out, args.baseline)))


if __name__ == "__main__":
    main()
