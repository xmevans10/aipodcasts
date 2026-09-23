"""Blind AI judge for draft scripts.

Collects every valid draft from the A/B runs plus the bundled (baseline)
transcripts, strips provenance, and scores each one pointwise against a shared
rubric. Two DeepSeek judges are used so a single model's self-preference cannot
decide the result; the deterministic `anti_slop` penalty is reported alongside.

Run from the project root:
    python3 backend/evals/ai_judge.py
    python3 backend/evals/ai_judge.py --judges pro
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))
from anti_slop import analyze, penalty
from evidence import evidence_text
from hosts import HOSTS

AB = HERE / "ab"
EPISODES = ROOT / "ios" / "ScienceBreak" / "Episodes"
LEAF_PACKET = ROOT / "docs" / "editorial" / "leaf-evidence-packet.json"
CACHE = AB / "judge-cache.json"
API = "https://api.deepseek.com/chat/completions"

JUDGES = {"pro": "deepseek-v4-pro", "flash": "deepseek-flash"}
DIMENSIONS = ("hook", "clarity", "fidelity", "spoken_rhythm", "human_voice", "host_fit", "overall")

RUBRIC = """You are a blind editorial judge for Sound Science, a spoken science show and newsletter.
You are given the host's profile, the source evidence packet (which may be marked as not provided), and one
candidate script. Judge only the script. Do not try to guess which system wrote it. Do not reward length.

Score each dimension with an integer 1-10 (10 is best):
- hook: does the opening earn attention with something concrete, not throat-clearing?
- clarity: is the study, what was done and the finding explained in plain spoken language?
- fidelity: is every factual claim traceable to the evidence packet? Penalize invented facts, numbers,
  quotations or experiences. If the packet is not provided, return null for this dimension.
- spoken_rhythm: does it read naturally aloud, with varied sentence length and no metronomic or staccato rhythm?
- human_voice: does it sound like a person with a point of view, free of AI-slop phrasing and staged reveals?
- host_fit: does the delivery match this specific host's personality?
- overall: your holistic judgment of whether a listener would stay and trust it.

Also list short strings in ai_tells for any machine-sounding tics you notice, and give a one-sentence rationale.
Return only JSON: {"hook":int,"clarity":int,"fidelity":int or null,"spoken_rhythm":int,"human_voice":int,
"host_fit":int,"overall":int,"ai_tells":[string],"rationale":string}"""


def read_env():
    env = {}
    path = ROOT / "backend" / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env.setdefault(key.strip(), value.strip().strip("'\""))
    return env


def leaf_evidence():
    if not LEAF_PACKET.exists():
        return None
    return evidence_text(json.loads(LEAF_PACKET.read_text()))


def add_ab_candidates(candidates, evidence):
    seen = {}
    for results_path in sorted(AB.glob("*/results.json")):
        run_dir = results_path.parent.name
        for record in json.loads(results_path.read_text()).get("results", []):
            draft = record.get("draft")
            if not draft or not draft.get("body"):
                continue
            body = draft["body"]
            key = hashlib.sha256(body.encode()).hexdigest()[:12]
            label = record.get("variant", "unknown") + "--" + key
            if label in seen:
                continue
            seen[label] = True
            candidates.append({
                "label": label, "condition": record.get("variant", "unknown"),
                "source": "leaf", "host_id": "fern",
                "title": draft.get("title", ""), "dek": draft.get("dek", ""), "body": body,
                "evidence": evidence, "style_penalty": record.get("style_penalty"),
                "valid_draft": record.get("valid_draft"), "valid_podcast": record.get("valid_podcast"),
                "origin": run_dir + "#r" + str(record.get("run")),
            })
    return candidates


def add_bundled_candidates(candidates):
    for path in sorted(EPISODES.glob("*.json")):
        document = json.loads(path.read_text())
        story = document.get("story", document)
        body = story.get("body")
        if not body:
            continue
        candidates.append({
            "label": "bundled-baseline--" + path.stem, "condition": "bundled-baseline",
            "source": "bundled", "host_id": story.get("hostID", "fern"),
            "title": story.get("title", ""), "dek": story.get("dek", ""), "body": body,
            "evidence": None, "style_penalty": penalty(analyze(body)),
            "valid_draft": None, "valid_podcast": None, "origin": "rendered-episodes/" + path.name,
        })
    return candidates


def host_brief(host_id):
    host = HOSTS.get(host_id)
    if host is None:
        return {"name": host_id, "show": "", "persona": "", "delivery": ""}
    return {"name": host.name, "show": host.show, "persona": host.persona, "delivery": host.delivery}


def call_judge(model, key, payload, max_tokens=1600):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError("HTTP " + str(error.code) + ": " + error.read().decode()[:300]) from error
    content = data["choices"][0]["message"].get("content") or ""
    parsed = json.loads(content)
    parsed["_usage"] = data.get("usage", {})
    return parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judges", default="pro,flash", help="comma-separated judge keys")
    parser.add_argument("--out", default=str(AB))
    args = parser.parse_args()

    env = read_env()
    key = env.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("Set DEEPSEEK_API_KEY in backend/.env")

    evidence = leaf_evidence()
    candidates = add_bundled_candidates([])
    add_ab_candidates(candidates, evidence)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    judge_names = [j.strip() for j in args.judges.split(",") if j.strip()]
    print(f"{len(candidates)} candidates | judges: {', '.join(judge_names)}")

    for candidate in candidates:
        payload = {
            "host": host_brief(candidate["host_id"]),
            "evidence_packet": candidate["evidence"] or "NOT PROVIDED. Return null for fidelity.",
            "candidate_script": {"title": candidate["title"], "dek": candidate["dek"], "body": candidate["body"]},
        }
        for judge_name in judge_names:
            model = JUDGES[judge_name]
            cache_key = hashlib.sha256(("|".join([model, candidate["body"], candidate["evidence"] or ""])).encode()).hexdigest()
            if cache_key not in cache:
                print("  judging", candidate["label"], "with", judge_name, "...", flush=True)
                try:
                    cache[cache_key] = call_judge(model, key, payload)
                    CACHE.write_text(json.dumps(cache, indent=1))
                except Exception as error:
                    print("    ERROR:", error)
                    cache[cache_key] = {"_error": str(error)}
                    CACHE.write_text(json.dumps(cache, indent=1))
            candidate.setdefault("scores", {})[judge_name] = cache[cache_key]

    aggregate(candidates, judge_names, Path(args.out))


def _mean(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return round(sum(values) / len(values), 2) if values else None


CRAFT_DIMENSIONS = ("hook", "clarity", "spoken_rhythm", "human_voice", "host_fit", "overall")


def candidate_composite(candidate, judge_names):
    """Mean craft score across judges, excluding fidelity (not always available)."""
    per_judge = []
    for judge_name in judge_names:
        score = candidate.get("scores", {}).get(judge_name) or {}
        dims = [score[d] for d in CRAFT_DIMENSIONS if isinstance(score.get(d), (int, float))]
        if dims:
            per_judge.append(sum(dims) / len(dims))
    return _mean(per_judge)


def aggregate(candidates, judge_names, out_dir):
    by_condition = {}
    for candidate in candidates:
        condition = by_condition.setdefault(candidate["condition"], {"composite": [], "fidelity": [], "style": [], "n": 0})
        condition["n"] += 1
        condition["style"].append(candidate["style_penalty"])
        composite = candidate_composite(candidate, judge_names)
        candidate["composite"] = composite
        if composite is not None:
            condition["composite"].append(composite)
        for judge_name in judge_names:
            score = candidate.get("scores", {}).get(judge_name) or {}
            if isinstance(score.get("fidelity"), (int, float)):
                condition["fidelity"].append(score["fidelity"])

    rows = []
    for condition, data in by_condition.items():
        rows.append({
            "condition": condition, "n": data["n"],
            "composite": _mean(data["composite"]),
            "fidelity": _mean(data["fidelity"]),
            "style_penalty": _mean(data["style"]),
        })
    # Rank on craft composite, then on fewer AI tells; fidelity is reported but not
    # comparable across the bundled scripts (different papers, no packet).
    rows.sort(key=lambda r: (r["composite"] or 0, -(r["style_penalty"] or 0)), reverse=True)

    lines = ["# Blind AI judge — leaf draft A/B", "",
             "Judges: " + ", ".join(judge_names) + " (DeepSeek, thinking disabled, temp 0). "
             "`composite` is the mean of hook, clarity, spoken rhythm, human voice, host fit and overall across both judges. "
             "`bundled-baseline` scripts cover different papers, so their `fidelity` is null and only craft dimensions are comparable. "
             "Note: `backend/data/baseline-2026-09-17/manifest.json` records the bundled scripts as assistant-authored, "
             "not a live Luna API run, so treat `bundled-baseline` as a human/assistant quality reference, not API output.",
             "", "| rank | condition | n | composite | fidelity | det. style penalty |", "|---|---|---|---|---|---|"]
    for index, row in enumerate(rows, 1):
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            index, row["condition"], row["n"], row["composite"], row["fidelity"], row["style_penalty"]))
    winner, runner_up = (rows[0], rows[1]) if len(rows) > 1 else (rows[0] if rows else None, None)
    lines += ["", "## Verdict", ""]
    if rows:
        best = rows[0]["composite"] or 0
        tier = [r for r in rows if (r["composite"] or 0) >= best - 0.15]
        practical = sorted(tier, key=lambda r: (r["style_penalty"] if r["style_penalty"] is not None else 99,
                                                -(r["fidelity"] or 0)))[0]
        lines.append(f"Raw craft leader: **{rows[0]['condition']}** ({rows[0]['composite']}/10). "
                     f"Conditions within 0.15 (treated as a tie): {', '.join(r['condition'] for r in tier)}.")
        lines.append("")
        lines.append(f"Practical winner on equal craft with the fewest AI tells: **{practical['condition']}** — "
                     f"composite {practical['composite']}, style penalty {practical['style_penalty']}, fidelity {practical['fidelity']}.")
    if runner_up:
        lines.append("")
        lines.append(f"Margin between raw leader and runner-up is only {round((winner['composite'] or 0) - (runner_up['composite'] or 0), 2)}, "
                     "so trust the tie-break on AI tells rather than the ordering.")
    lines += ["", "## Per-sample detail", "", "| candidate | condition | composite | overall | fidelity | style penalty | judge tells |", "|---|---|---|---|---|---|---|"]
    for candidate in sorted(candidates, key=lambda c: (c["condition"], c["label"])):
        scores = candidate.get("scores", {})
        overall = _mean([(scores.get(j) or {}).get("overall") for j in judge_names])
        fidelity = _mean([(scores.get(j) or {}).get("fidelity") for j in judge_names])
        tells = "; ".join(sorted({t for j in judge_names for t in ((scores.get(j) or {}).get("ai_tells") or [])}))
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            candidate["label"], candidate["condition"], candidate.get("composite"), overall,
            fidelity, candidate["style_penalty"], tells[:160]))
    report = out_dir / "JUDGE.md"
    report.write_text("\n".join(lines) + "\n")
    (out_dir / "judge-results.json").write_text(json.dumps(
        {"generated": dt.datetime.now(dt.timezone.utc).isoformat(), "judges": judge_names,
         "aggregate": rows, "candidates": candidates}, indent=1))
    print("\n" + "\n".join(lines[:20]))
    print("\nWrote", report)


if __name__ == "__main__":
    main()
