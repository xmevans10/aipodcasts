"""Sound Science's local editorial pipeline. Python 3.11+, standard library only.
No public endpoint can trigger paid generation. All mutations are operator CLI actions.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from evidence import extract_passages, build_packet, evidence_text
from hosts import HOSTS as HOST_PROFILES, writing_guide
from anti_slop import ANTI_SLOP_GUIDE
from podcast import DEFAULT_MODEL, PODCAST_INSTRUCTIONS, validate_podcast, narration_script

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("LILT_DATA", ROOT / "data"))
HOSTS = HOST_PROFILES  # personality config lives in hosts.py
MAX_SOURCE_BYTES = 4_000_000


def load_local_env(path: Path | None = None) -> None:
    path = path or ROOT / ".env"
    if not path.exists():
        return
    allowed = {"OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_REASONING_EFFORT", "ELEVENLABS_API_KEY", "ELEVENLABS_MODEL",
               "LILT_MAX_PROVIDER_CALLS_PER_DAY", "LILT_MAX_SOURCE_CHARS", *[h.voice_env for h in HOSTS.values()]}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or key not in allowed:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if value and not os.environ.get(key):
            os.environ[key] = value


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or DATA / "lilt.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS stories (
      id TEXT PRIMARY KEY, source TEXT NOT NULL, host TEXT NOT NULL,
      state TEXT NOT NULL DEFAULT 'ingested', draft TEXT, reviewer TEXT,
      review_hash TEXT, audio TEXT, error TEXT,
      created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS calls (
      id INTEGER PRIMARY KEY, day TEXT NOT NULL, provider TEXT NOT NULL,
      story_id TEXT NOT NULL, created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    for table, name, declaration in [('stories', 'draft_input', 'TEXT'),
                                     ('calls', 'input_tokens', 'INTEGER'),
                                     ('calls', 'output_tokens', 'INTEGER')]:
        if name not in {r[1] for r in db.execute('PRAGMA table_info(' + table + ')')}:
            db.execute('ALTER TABLE ' + table + ' ADD COLUMN ' + name + ' ' + declaration)
    db.commit()
    return db


def request(url: str, *, payload: dict | None = None, headers: dict | None = None,
            limit: int = MAX_SOURCE_BYTES) -> bytes:
    """Fixed provider endpoints; only PLOS-to-its-corpus redirects are permitted."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            old, new = urllib.parse.urlparse(req.full_url), urllib.parse.urlparse(newurl)
            if (req.data is None and old.hostname == "journals.plos.org"
                and new.scheme == "https" and new.netloc == "storage.googleapis.com"
                and new.path.startswith("/plos-corpus-prod/10.1371/")
                and new.path.endswith(".xml")):
                return urllib.request.Request(newurl, headers={"User-Agent": "Sound ScienceResearch/0.1"})
            return None
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Sound ScienceResearch/0.1", **(headers or {})})
    with urllib.request.build_opener(NoRedirect).open(req, timeout=90) as response:
        content = response.read(limit + 1)
        if len(content) > limit:
            raise ValueError("Response exceeded size limit")
        return content


def text(node: ET.Element | None) -> str:
    return " ".join("".join(node.itertext()).split()) if node is not None else ""


def parse_plos_xml(data: bytes, doi: str) -> dict:
    if b"<!ENTITY" in data.upper() or b"<!DOCTYPE" in data.upper():
        # PLOS JATS can have a DOCTYPE declaration; discard an external declaration,
        # but never accept internal entities or an internal DTD subset.
        if b"<!ENTITY" in data.upper() or re.search(br"<!DOCTYPE[^>]*\[", data, re.I):
            raise ValueError("XML entity declarations are not supported")
        data = re.sub(br"<!DOCTYPE[^>]*>", b"", data, flags=re.I)
    root = ET.fromstring(data)
    license_node = root.find("./front/article-meta/permissions/license")
    raw_license = ET.tostring(license_node, encoding="unicode") if license_node is not None else ""
    # Accept only the exact commercial derivatives license family, not BY-NC/ND/SA.
    match = re.search(r"https?://creativecommons.org/licenses/by/(\d\.\d)/?", raw_license)
    if not match:
        raise ValueError("No explicit CC BY license URL found; needs rights review")
    actual_doi = next((text(n) for n in root.findall("./front/article-meta/article-id") if n.get("pub-id-type") == "doi"), "")
    if actual_doi.lower() != doi.lower():
        raise ValueError("DOI mismatch")
    authors = []
    for n in root.findall("./front/article-meta/contrib-group/contrib"):
        if n.get("contrib-type") == "author":
            name = n.find("name")
            if name is not None:
                authors.append(" ".join(filter(None, [text(name.find("given-names")), text(name.find("surname"))])))
    paragraphs = [text(n) for n in root.findall("./front/article-meta/abstract//p") + root.findall("./body//p")]
    content = "\n\n".join(p for p in paragraphs if p)
    if len(content) < 400:
        raise ValueError("Source text too short")
    title = text(root.find("./front/article-meta/title-group/article-title"))
    return {"title": title, "url": "https://doi.org/" + doi, "doi": doi,
            "attribution": ", ".join(authors) or "Authors listed at source",
            "journal": text(root.find("./front/journal-meta/journal-title-group/journal-title")),
            "license": "CC BY " + match.group(1), "licenseURL": match.group(0),
            "text": content, "passages": extract_passages(root, text), "retrieved": dt.datetime.now(dt.timezone.utc).isoformat()}


def ingest(db: sqlite3.Connection, doi: str, host: str, refresh: bool = False) -> str:
    if not re.fullmatch(r"10\.1371/journal\.[a-z]+\.\d+", doi):
        raise ValueError("Only PLOS journal DOIs are supported in the first source connector")
    if host not in HOSTS:
        raise ValueError("Unknown host")
    story_id = hashlib.sha256((doi + ":" + host).encode()).hexdigest()[:20]
    existing = db.execute("SELECT state FROM stories WHERE id=?", (story_id,)).fetchone()
    if existing and not refresh:
        return story_id
    if existing and existing["state"] != "ingested":
        raise ValueError("Only an undrafted source can be refreshed")
    journal = doi.split("journal.")[1].split(".")[0]
    journal_path = {"pone": "plosone", "pbio": "plosbiology", "pgen": "plosgenetics", "pcbi": "ploscompbiol", "pmed": "plosmedicine"}.get(journal)
    if not journal_path:
        raise ValueError("Journal not yet enabled")
    url = "https://journals.plos.org/" + journal_path + "/article/file?id=" + urllib.parse.quote(doi, safe="") + "&type=manuscript"
    source = parse_plos_xml(request(url), doi)
    with db:
        if existing:
            db.execute("UPDATE stories SET source=? WHERE id=?", (json.dumps(source), story_id))
        else:
            db.execute("INSERT INTO stories(id,source,host) VALUES(?,?,?)", (story_id, json.dumps(source), host))
    return story_id


def discover(limit: int = 10) -> list[dict]:
    """Discovery metadata only. Full-text reuse is checked separately at ingestion."""
    raw = request("https://journals.plos.org/plosbiology/feed/atom")
    root = ET.fromstring(raw)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    results = []
    for entry in root.findall("a:entry", ns)[:min(max(limit, 1), 30)]:
        blob = ET.tostring(entry, encoding="unicode")
        match = re.search(r"10\.1371/journal\.[a-z]+\.\d+", blob)
        if match:
            results.append({"doi": match.group(0), "title": text(entry.find("a:title", ns))})
    return results


SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"title": {"type": "string"}, "dek": {"type": "string"},
                         "body": {"type": "string"}, "caveat": {"type": "string"},
                         "claims": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                           "properties": {"claim": {"type": "string"}, "quote": {"type": "string"}},
                           "required": ["claim", "quote"]}}},
          "required": ["title", "dek", "body", "caveat", "claims"]}


def provenance_text(value: str) -> str:
    """Normalize typography so a verbatim quote matches across encodings.

    Models routinely return straight quotes/dashes where JATS uses curly ones.
    This does not forgive paraphrasing: only punctuation and spacing differ.
    """
    value = unicodedata.normalize("NFKC", value)
    for source, target in (("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'),
                           ("\u2010", "-"), ("\u2011", "-"), ("\u2012", "-"), ("\u2013", "-"),
                           ("\u2014", "-"), ("\u2212", "-"), ("\u2026", "...")):
        value = value.replace(source, target)
    return " ".join(value.split())


def quotes_in_source(quote: str, normalized_source: str) -> bool:
    """A quote may omit interior text, but every retained fragment must be verbatim.

    Comparison is case- and typography-insensitive only: a model may capitalise the
    first word of a quote, but it may not change or reorder words.
    """
    fragments = [f.strip() for f in provenance_text(quote).split("...")]
    haystack = normalized_source.casefold()
    return bool(fragments) and all(fragment.casefold() in haystack for fragment in fragments)


def validate_draft(draft: dict, source: dict) -> None:
    if set(draft) != set(SCHEMA["required"]):
        raise ValueError("Draft has unexpected fields")
    for field, maximum in [("title", 120), ("dek", 220), ("body", 9000), ("caveat", 1800)]:
        if not isinstance(draft[field], str) or not 10 <= len(draft[field]) <= maximum:
            raise ValueError("Invalid " + field)
    if not 180 <= len(draft["body"].split()) <= 1000:
        raise ValueError("Narration must be between 180 and 1000 words")
    if not isinstance(draft["claims"], list) or not 1 <= len(draft["claims"]) <= 15:
        raise ValueError("Claim evidence is required")
    normalized = provenance_text(source["text"])
    for claim in draft["claims"]:
        if not isinstance(claim, dict) or set(claim) != {"claim", "quote"}:
            raise ValueError("Invalid claim format")
        if not all(isinstance(claim[key], str) and len(claim[key]) >= 15 for key in ("claim", "quote")):
            raise ValueError("Empty or insufficient evidence")
        if not quotes_in_source(claim["quote"], normalized):
            raise ValueError("Evidence quote not found in original source")


def reserve_call(db: sqlite3.Connection, provider: str, story_id: str) -> int:
    """Reserve before the call, including failed calls; shared across CLI processes."""
    day = dt.datetime.now(dt.timezone.utc).date().isoformat()
    maximum = int(os.environ.get("LILT_MAX_PROVIDER_CALLS_PER_DAY", "12"))
    db.execute("BEGIN IMMEDIATE")
    try:
        count = db.execute("SELECT count(*) FROM calls WHERE day=?", (day,)).fetchone()[0]
        if count >= maximum:
            raise ValueError("Daily provider-call cap reached")
        cursor = db.execute("INSERT INTO calls(day,provider,story_id) VALUES(?,?,?)", (day, provider, story_id))
        db.commit()
        return cursor.lastrowid
    except Exception:
        db.rollback()
        raise


def row(db, story_id):
    result = db.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    if result is None:
        raise ValueError("Unknown story")
    return result


def draft_story(db, story_id):
    record = row(db, story_id)
    if record["draft"]:
        return json.loads(record["draft"])
    if record["state"] != "ingested":
        raise ValueError("Story must be ingested first")
    key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL
    if not key or not model:
        raise ValueError("Set OPENAI_API_KEY and OPENAI_MODEL on the backend")
    source = json.loads(record["source"])
    if not source.get("attribution") or source["attribution"] == "Authors listed at source":
        raise ValueError("Named author metadata is required before generation")
    packet = build_packet(source, int(os.environ.get("LILT_MAX_SOURCE_CHARS", "18000")))
    instructions = PODCAST_INSTRUCTIONS + writing_guide(record["host"]) + "\n\n" + ANTI_SLOP_GUIDE
    effort = os.environ.get("OPENAI_REASONING_EFFORT", "low")
    if effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
        raise ValueError("Unsupported reasoning effort")
    reasoning = {"reasoning": {"effort": effort}} if model.startswith("gpt-5.6-luna") else {}
    with db:
        db.execute("UPDATE stories SET draft_input=? WHERE id=?", (json.dumps(packet, ensure_ascii=False), story_id))
    call_id = reserve_call(db, "openai", story_id)
    response = json.loads(request("https://api.openai.com/v1/responses", payload={
        "model": model, "store": False, "instructions": instructions, **reasoning,
        "input": json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
        "max_output_tokens": 3500,
        "text": {"format": {"type": "json_schema", "name": "science_story", "strict": True, "schema": SCHEMA}}
    }, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}))
    usage = response.get("usage") or {}
    with db:
        db.execute("UPDATE calls SET input_tokens=?,output_tokens=? WHERE id=?",
                   (usage.get("input_tokens"), usage.get("output_tokens"), call_id))
    if response.get("status") != "completed":
        raise ValueError("Generation incomplete; nothing published")
    outputs = [c["text"] for item in response.get("output", []) for c in item.get("content", []) if c.get("type") == "output_text"]
    if not outputs:
        raise ValueError("No draft returned, possibly refused")
    draft = json.loads("".join(outputs))
    validate_draft(draft, {"text": evidence_text(packet)})
    validate_podcast(draft, source, HOSTS[record["host"]])
    with db:
        db.execute("UPDATE stories SET draft=?,state='review' WHERE id=?", (json.dumps(draft), story_id))
    return draft


def review(db, story_id: str, reviewer: str):
    record = row(db, story_id)
    if record["state"] != "review" or not reviewer.strip():
        raise ValueError("Requires a draft awaiting review and a named reviewer")
    draft = json.loads(record["draft"])
    validate_draft(draft, json.loads(record["source"]))
    validate_podcast(draft, json.loads(record["source"]), HOSTS[record["host"]])
    digest = hashlib.sha256(record["draft"].encode()).hexdigest()
    with db:
        db.execute("UPDATE stories SET state='approved',reviewer=?,review_hash=? WHERE id=?", (reviewer.strip(), digest, story_id))


def narrate(db, story_id):
    record = row(db, story_id)
    if record["audio"]:
        return record["audio"]
    if record["state"] != "approved":
        raise ValueError("Editorial approval is required before narration")
    if hashlib.sha256(record["draft"].encode()).hexdigest() != record["review_hash"]:
        raise ValueError("Draft changed after review")
    key = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_" + record["host"].upper())
    if not key or not voice or not re.fullmatch(r"[A-Za-z0-9_-]+", voice):
        raise ValueError("Configure a licensed ElevenLabs voice and API key")
    draft = json.loads(record["draft"])
    validate_podcast(draft, json.loads(record["source"]))
    script = narration_script(draft)
    reserve_call(db, "elevenlabs", story_id)
    audio = request("https://api.elevenlabs.io/v1/text-to-speech/" + voice + "?output_format=mp3_44100_128", payload={
        "text": script, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.75}
    }, headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"}, limit=30_000_000)
    if len(audio) < 1000 or not (audio[:3] == b"ID3" or (audio[0] == 255 and audio[1] & 224 == 224)):
        raise ValueError("Provider did not return valid MP3 audio")
    audio_dir = DATA / "audio"; audio_dir.mkdir(parents=True, exist_ok=True)
    filename = story_id + ".mp3"
    with tempfile.NamedTemporaryFile(dir=audio_dir, delete=False) as f:
        f.write(audio); tmp = Path(f.name)
    tmp.replace(audio_dir / filename)
    with db:
        db.execute("UPDATE stories SET audio=?,state='narrated' WHERE id=?", (filename, story_id))
    return filename


def publish(db, story_id):
    record = row(db, story_id)
    if record["state"] != "narrated" or not record["audio"]:
        raise ValueError("Only approved, narrated stories can publish")
    if not (DATA / "audio" / record["audio"]).is_file():
        raise ValueError("Audio file is missing")
    if hashlib.sha256(record["draft"].encode()).hexdigest() != record["review_hash"]:
        raise ValueError("Draft no longer matches the approved version")
    with db:
        db.execute("UPDATE stories SET state='published' WHERE id=?", (story_id,))


def feed(db, origin: str) -> list[dict]:
    result = []
    for r in db.execute("SELECT * FROM stories WHERE state='published' ORDER BY created DESC, id"):
        source, draft = json.loads(r["source"]), json.loads(r["draft"])
        result.append({"id": r["id"], "title": draft["title"], "dek": draft["dek"],
            "topic": HOSTS[r["host"]].topic, "hostID": r["host"],
            "minutes": max(1, round(len(draft["body"].split()) / 150)),
            "body": draft["body"], "caveat": draft["caveat"], "isDemo": False,
            "sources": [{"title": source["title"], "url": source["url"],
                         "attribution": source["attribution"] + ". Adapted by Sound Science; changes made.",
                         "license": source["license"] + " · " + source["licenseURL"]}],
            "audioURL": origin.rstrip("/") + "/audio/" + r["audio"]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover")
    p = sub.add_parser("ingest"); p.add_argument("doi"); p.add_argument("--host", choices=HOSTS, required=True); p.add_argument("--refresh", action="store_true")
    sub.add_parser("hosts")
    for command in ("draft", "inspect", "narrate", "publish", "withdraw", "packet"):
        p = sub.add_parser(command); p.add_argument("id")
    p = sub.add_parser("approve"); p.add_argument("id"); p.add_argument("--reviewer", required=True)
    sub.add_parser("list")
    sub.add_parser("usage")
    args = parser.parse_args(); load_local_env(); db = connect()
    try:
        if args.command == "discover": result = discover()
        elif args.command == "ingest": result = ingest(db, args.doi, args.host, args.refresh)
        elif args.command == "packet": result = build_packet(json.loads(row(db, args.id)["source"]), int(os.environ.get("LILT_MAX_SOURCE_CHARS", "18000")))
        elif args.command == "hosts": result = [{"id": h.id, "name": h.name, "show": h.show, "topic": h.topic,
            "beat": h.beat, "delivery": h.delivery, "sign_off": h.sign_off, "voice_env": h.voice_env} for h in HOSTS.values()]
        elif args.command == "usage": result = [dict(r) for r in db.execute("SELECT day,provider,count(*) AS attempts,sum(input_tokens) AS input_tokens,sum(output_tokens) AS output_tokens FROM calls GROUP BY day,provider")]
        elif args.command == "draft": result = draft_story(db, args.id)
        elif args.command == "inspect": result = dict(row(db, args.id))
        elif args.command == "approve": review(db, args.id, args.reviewer); result = "Approved"
        elif args.command == "narrate": result = narrate(db, args.id)
        elif args.command == "publish": publish(db, args.id); result = "Published"
        elif args.command == "withdraw":
            with db: db.execute("UPDATE stories SET state='withdrawn' WHERE id=?", (args.id,))
            result = "Withdrawn from feed and audio access"
        else: result = [dict(r) for r in db.execute("SELECT id,host,state,created FROM stories")]
        print(json.dumps(result, indent=2))
    except (ValueError, urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        # Do not log HTTP request headers or provider bodies containing user data.
        parser.exit(1, f"Pipeline stopped: {type(e).__name__}: {e}\n")
    finally: db.close()

if __name__ == "__main__": main()
