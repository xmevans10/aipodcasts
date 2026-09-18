"""A/B experiments for the article/draft writing step, on DeepSeek.

Isolated from the production pipeline: this never writes to lilt.sqlite3 and
never publishes. It mirrors the real draft contract (same evidence packet, same
PODCAST_INSTRUCTIONS + host guide, same validators) so results are comparable.

Run from the project root, e.g.:
    python3 backend/evals/article_ab.py --n 2
    python3 backend/evals/article_ab.py --variants flash-baseline,flash-antislop
    python3 backend/evals/article_ab.py --packet docs/editorial/leaf-evidence-packet.json --host fern
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "backend"))
from anti_slop import ANTI_SLOP_GUIDE, analyze, penalty
from evidence import build_packet, evidence_text
from hosts import HOSTS
from podcast import PODCAST_INSTRUCTIONS, validate_podcast
from pipeline import SCHEMA, validate_draft

DEFAULT_PACKET = ROOT / "docs" / "editorial" / "leaf-evidence-packet.json"
API = "https://api.deepseek.com/chat/completions"
OPENAI_API = "https://api.openai.com/v1/responses"

JSON_SHAPE = (
    "Return only a JSON object (no markdown fence) with exactly these keys: "
    '{"title": string, "dek": string, "body": string, "caveat": string, '
    '"claims": [{"claim": string, "quote": string}]}'
)

# Off-peak standard rates, USD per 1M tokens. DeepSeek peak is 2x; Luna has no
# peak/off-peak split. Used only to compare variants.
RATES = {
    "deepseek-flash": {"in": 0.15, "out": 0.60, "peak_multiplier": 2},
    "deepseek-v4-pro": {"in": 0.66, "out": 1.98, "peak_multiplier": 2},
    "gpt-5.6-luna": {"in": 0.20, "out": 1.20, "peak_multiplier": 1},
}

VARIANTS = {
    "flash-baseline":    dict(model="deepseek-flash", prompt="baseline", provider="deepseek", thinking=False, temperature=0.8),
    "flash-antislop":    dict(model="deepseek-flash", prompt="antislop", provider="deepseek", thinking=False, temperature=0.8),
    "flash-antislop-think": dict(model="deepseek-flash", prompt="antislop", provider="deepseek", thinking=True, effort="high", temperature=None),
    "pro-baseline":      dict(model="deepseek-v4-pro", prompt="baseline", provider="deepseek", thinking=False, temperature=0.8),
    "pro-antislop":      dict(model="deepseek-v4-pro", prompt="antislop", provider="deepseek", thinking=False, temperature=0.8),
    "luna-baseline":     dict(model="gpt-5.6-luna", prompt="baseline", provider="openai", effort="low", max_tokens=3500),
    "luna-antislop":     dict(model="gpt-5.6-luna", prompt="antislop", provider="openai", effort="low", max_tokens=3500),
}


def read_env():
    env = {}
    for path in (ROOT / "backend" / ".env", ROOT / ".env"):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip("'\"")
            env.setdefault(key.strip(), value)
    return env


def load_packet(packet_path: Path | None, host_id: str, max_chars: int):
    if packet_path:
        packet = json.loads(packet_path.read_text())
    else:
        # Rebuild deterministically from the ingested source, like pipeline.draft_story.
        from pipeline import connect
        db = connect()
        row = db.execute("SELECT source FROM stories WHERE host=? ORDER BY created", (host_id,)).fetchone()
        if row is None:
            raise SystemExit("No ingested story for host " + host_id + "; pass --packet instead")
        packet = build_packet(json.loads(row["source"]), max_chars)
    source = {
        "title": packet["source_title"],
        "attribution": packet.get("source_attribution", ""),
        "journal": packet.get("source_journal", ""),
        "text": evidence_text(packet),
    }
    return packet, source


def instructions_for(prompt: str, host):
    base = PODCAST_INSTRUCTIONS + host.writing_guide()
    if prompt == "antislop":
        return base + "\n\n" + ANTI_SLOP_GUIDE
    return base


def call(keys: dict, variant: dict, instructions: str, packet: dict, max_tokens: int):
    provider = variant.get("provider", "deepseek")
    if provider == "openai":
        return call_openai(keys.get("OPENAI_API_KEY"), variant, instructions, packet, max_tokens)
    key = keys.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY")
    body = {
        "model": variant["model"],
        "messages": [
            {"role": "system", "content": instructions + "\n\n" + JSON_SHAPE},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False, separators=(",", ":"))},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "stream": False,
    }
    if variant.get("thinking"):
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = variant.get("effort", "high")
    else:
        body["thinking"] = {"type": "disabled"}
        body["temperature"] = variant.get("temperature", 0.8)
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode()[:600]
        raise RuntimeError("HTTP " + str(error.code) + ": " + detail) from error


def call_openai(key, variant, instructions, packet, max_tokens):
    if not key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    body = {
        "model": variant["model"], "store": False, "instructions": instructions,
        "input": json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": variant.get("effort", "low")},
        "text": {"format": {"type": "json_schema", "name": "science_story", "strict": True, "schema": SCHEMA}},
    }
    req = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode()[:600]
        raise RuntimeError("HTTP " + str(error.code) + ": " + detail) from error


def usage_of(response):
    usage = response.get("usage") or {}
    if "prompt_tokens" in usage or "completion_tokens" in usage:
        return {
            "input_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "cache_hit_tokens": usage.get("prompt_cache_hit_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens"),
        "cache_hit_tokens": (usage.get("input_tokens_details") or {}).get("cached_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def estimate_cost(model, usage, peak):
    rate = RATES.get(model, {"in": 0, "out": 0, "peak_multiplier": 1})
    multiplier = rate.get("peak_multiplier", 1) if peak else 1
    return ((usage["input_tokens"] or 0) / 1e6 * rate["in"]
            + (usage["output_tokens"] or 0) / 1e6 * rate["out"]) * multiplier


def is_peak(now):
    return now.weekday() < 5 and (1 <= now.hour < 4 or 6 <= now.hour < 10)


def run_variant(keys, name, variant, instructions, packet, source, host, max_tokens):
    record = {"variant": name, **{k: v for k, v in variant.items()}, "host": host.id}
    try:
        response = call(keys, variant, instructions, packet, max_tokens)
    except Exception as error:
        record["error"] = str(error)
        return record
    usage = usage_of(response)
    record["usage"] = usage
    record["cost_usd_offpeak"] = round(estimate_cost(variant["model"], usage, peak=False), 6)
    record["cost_usd_peak"] = round(estimate_cost(variant["model"], usage, peak=True), 6)
    if variant.get("provider") == "openai":
        content = "".join(c["text"] for item in response.get("output", [])
                          for c in item.get("content", []) if c.get("type") == "output_text")
        record["finish_reason"] = response.get("status")
        record["reasoning_chars"] = sum(len(c.get("text", "")) for item in response.get("output", [])
                                        for c in item.get("content", []) if c.get("type") == "reasoning_text")
    else:
        message = response["choices"][0]["message"]
        content = message.get("content") or ""
        record["finish_reason"] = response["choices"][0].get("finish_reason")
        record["reasoning_chars"] = len(message.get("reasoning_content") or "")
    try:
        draft = json.loads(content)
    except Exception:
        record["error"] = "unparseable JSON"
        record["raw"] = content[:2000]
        return record
    record["draft"] = draft
    report = analyze(draft.get("body", ""))
    record["style"] = report
    record["style_penalty"] = penalty(report)
    try:
        validate_draft(copy.deepcopy(draft), {"text": source["text"]})
        record["valid_draft"] = True
    except Exception as error:
        record["valid_draft"] = False
        record["draft_error"] = str(error)
    try:
        validate_podcast(copy.deepcopy(draft), source, host)
        record["valid_podcast"] = True
    except Exception as error:
        record["valid_podcast"] = False
        record["podcast_error"] = str(error)
    return record


def summary_table(results):
    lines = [
        "| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        if "error" in r and "draft" not in r:
            lines.append("| " + r["variant"] + " | " + str(r["run"]) + " | – | – | – | – | – | – | – | – | – | – | – | – |")
            continue
        s = r["style"]; f = s["findings"]; u = r.get("usage", {})
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["variant"], r["run"], s["stats"]["words"], r["style_penalty"],
            ",".join(f["tier1a_vocab"]) or "0", f["em_dash"], f["hedge_stack"],
            f["not_x_but_y"], f["staged_reveal"],
            r.get("valid_draft"), r.get("valid_podcast"),
            u.get("input_tokens"), u.get("output_tokens"), r.get("cost_usd_offpeak", ""),
        ))
    return "\n".join(lines)


def write_outputs(out_dir, results, meta):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=1))
    md = ["# Article generation A/B — " + meta["timestamp"], ""]
    md.append("Model(s): " + ", ".join(sorted({r["model"] for r in results})) + f". Host: {meta['host']}. Evidence: {meta['characters']} chars.")
    md.append("")
    md.append(summary_table(results))
    md += ["", "## Scripts", ""]
    for r in results:
        if "draft" not in r:
            md.append(f"### {r['variant']} run {r['run']} — ERROR\n\n{r.get('error')}\n")
            continue
        d = r["draft"]
        md.append(f"### {r['variant']} run {r['run']}  ·  penalty {r['style_penalty']}")
        md.append("")
        md.append(f"**Title:** {d.get('title','')}")
        md.append("")
        md.append(f"**Dek:** {d.get('dek','')}")
        md.append("")
        md.append(d.get("body", ""))
        md.append("")
        if r.get("draft_error"):
            md.append(f"> draft error: {r['draft_error']}")
        if r.get("podcast_error"):
            md.append(f"> podcast error: {r['podcast_error']}")
        md.append("")
    (out_dir / "report.md").write_text("\n".join(md))
    return out_dir / "report.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", default="flash-baseline,flash-antislop,flash-antislop-think,pro-baseline,pro-antislop")
    parser.add_argument("--runs", type=int, default=1, help="samples per variant")
    parser.add_argument("--packet", type=Path, default=None, help="evidence packet JSON (default: leaf packet)")
    parser.add_argument("--host", default="fern")
    parser.add_argument("--max-source-chars", type=int, default=18000)
    parser.add_argument("--max-tokens", type=int, default=6000)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    env = read_env()
    keys = {
        "DEEPSEEK_API_KEY": env.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_API_KEY"),
        "OPENAI_API_KEY": env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY"),
    }
    if not any(keys.values()):
        raise SystemExit("Set DEEPSEEK_API_KEY and/or OPENAI_API_KEY in backend/.env")

    host = HOSTS[args.host]
    packet_path = args.packet or (DEFAULT_PACKET if DEFAULT_PACKET.exists() else None)
    packet, source = load_packet(packet_path, args.host, args.max_source_chars)
    now = dt.datetime.now(dt.timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    out_dir = args.out or (HERE / "ab" / timestamp)

    names = [v.strip() for v in args.variants.split(",") if v.strip()]
    print("Evidence:", packet.get("source_title"))
    print("Chars:", len(json.dumps(packet, ensure_ascii=False)), "| host:", host.name, "| peak pricing:", is_peak(now))
    print("Output:", out_dir)

    results, run = [], 0
    for name in names:
        variant = VARIANTS[name]
        instructions = instructions_for(variant["prompt"], host)
        max_tokens = variant.get("max_tokens", args.max_tokens)
        for i in range(args.runs):
            run += 1
            print(f"[{run}] {name} sample {i+1}/{args.runs} ...", flush=True)
            record = run_variant(keys, name, variant, instructions, packet, source, host, max_tokens)
            record["run"] = i + 1
            if "draft" in record:
                print("    penalty", record["style_penalty"], "| valid", record.get("valid_draft"), record.get("valid_podcast"),
                      "| tokens", record["usage"].get("input_tokens"), record["usage"].get("output_tokens"))
            else:
                print("    ERROR:", record.get("error"))
            results.append(record)
    meta = {"timestamp": timestamp, "host": host.id, "title": packet.get("source_title"),
            "characters": len(json.dumps(packet, ensure_ascii=False)), "peak": is_peak(now)}
    report = write_outputs(out_dir, results, meta)
    print("\nWrote", report)


if __name__ == "__main__":
    main()
