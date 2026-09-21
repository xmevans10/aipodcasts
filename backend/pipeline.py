"""Zwicky's local editorial pipeline. Python 3.11+, standard library only.
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
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from evidence import extract_passages, build_packet, evidence_text
from hosts import HOSTS as HOST_PROFILES, writing_guide, dialogue_hosts
from anti_slop import ANTI_SLOP_GUIDE
from dialogue import DIALOGUE_INSTRUCTIONS, DIALOGUE_SCHEMA, dialogue_guide, validate_dialogue, turns_body, turns_narration_inputs
from provenance import provenance_text, quotes_in_source
from language_clues import LANGUAGE_CLUES
import verify as verifier
from autoselect import select as select_stories, report as select_report
from shortlist import rank as shortlist_rank, report as shortlist_report
from voice import synthesize, status as voice_status
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
               "ELEVENLABS_DIALOGUE_MODEL", "VOICE_PROVIDER", "VOICE_LOCAL_URL", "OPENAI_TTS_MODEL", "OPENAI_TTS_VOICE",
               "LILT_MAX_PROVIDER_CALLS_PER_DAY", "LILT_MAX_SOURCE_CHARS",
               "LILT_OPENALEX_KEY", "LILT_CONTACT_EMAIL", "TYPESAFE_AI_API_KEY", "JEV_API_KEY", "CORE_API_KEY",
               "TYPESAFE_BASE_URL", "JEV_MODEL", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL",
               *[h.voice_env for h in HOSTS.values()], *["VOICE_OPENAI_" + h.id.upper() for h in HOSTS.values()]}
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
                return urllib.request.Request(newurl, headers={"User-Agent": "ZwickyResearch/0.1"})
            return None
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "ZwickyResearch/0.1", **(headers or {})})
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


EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPEPMC_XML = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


def parse_jats(data: bytes, doi: str, license_hint: str = "") -> dict:
    """Parse JATS full text (Europe PMC) into the same source dict as parse_plos_xml."""
    if b"<!ENTITY" in data.upper() or re.search(br"<!DOCTYPE[^>]*\[", data, re.I):
        raise ValueError("XML entity declarations are not supported")
    root = ET.fromstring(re.sub(br"<!DOCTYPE[^>]*>", b"", data, flags=re.I))
    license_nodes = root.findall("./front/article-meta/permissions/license")
    raw_license = ET.tostring(license_nodes[0], encoding="unicode") if license_nodes else license_hint
    match = re.search(r"https?://creativecommons.org/licenses/by/(\d\.\d)/?", raw_license)
    if not match:
        raise ValueError("No explicit CC BY license URL found; needs rights review")
    actual_doi = next((text(n) for n in root.findall("./front/article-meta/article-id")
                       if n.get("pub-id-type") == "doi"), "")
    if actual_doi and actual_doi.lower() != doi.lower():
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
    return {"title": text(root.find("./front/article-meta/title-group/article-title")),
            "url": "https://doi.org/" + doi, "doi": doi,
            "attribution": ", ".join(authors) or "Authors listed at source",
            "journal": text(root.find("./front/journal-meta/journal-title-group/journal-title")),
            "license": "CC BY " + match.group(1), "licenseURL": match.group(0),
            "text": content, "passages": extract_passages(root, text),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat()}


def europepmc_source(doi: str) -> dict | None:
    """Full text for a CC BY open-access paper indexed by Europe PMC, else None."""
    query = urllib.parse.quote('DOI:"' + doi + '"')
    found = json.loads(request(EUROPEPMC_SEARCH + "?query=" + query + "&resultType=core&format=json"))
    results = found.get("resultList", {}).get("result", [])
    if not results:
        return None
    record = results[0]
    if record.get("isOpenAccess") != "Y" or not record.get("pmcid"):
        return None
    return parse_jats(request(EUROPEPMC_XML.format(pmcid=record["pmcid"])), doi,
                      str(record.get("license") or ""))


ARXIV_API = "https://export.arxiv.org/api/query"


ARXIV_CHROME = re.compile(r"(HTML conversions sometimes|Report GitHub Issue|Back to top|"
                          r"Content selection saved|Describe the issue below|"
                          r"arXiv:\d|This article has an erratum)", re.I)
ARXIV_STOP = re.compile(r"^(references|bibliography|acknowledg)", re.I)


def parse_arxiv_html(html: bytes):
    """Extract section-labelled paragraphs from an arXiv HTML (LaTeXML) page."""
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html.decode("utf-8", "replace"),
                  flags=re.S | re.I)
    passages, section = [], "Body"
    for match in re.finditer(r"<(h[1-6]|p)\b[^>]*>(.*?)</\1>", body, re.S | re.I):
        value = " ".join(re.sub(r"<[^>]+>", " ", match.group(2)).split())
        if not value:
            continue
        if match.group(1).lower().startswith("h"):
            if ARXIV_STOP.match(value):
                break
            if ARXIV_CHROME.search(value):
                continue
            section = value[:80]
        elif len(value) >= 40 and not ARXIV_CHROME.search(value):
            passages.append({"id": f"p{len(passages) + 1}", "section": section, "text": value})
    return "\n\n".join(p["text"] for p in passages), passages


def arxiv_license(arxiv_id: str) -> str:
    page = request("https://arxiv.org/abs/" + arxiv_id).decode("utf-8", "replace")
    match = re.search(r"creativecommons\.org/licenses/([a-z0-9-]+)/([\d.]+)", page)
    return match.group(0) if match else ""


def is_cc_by(license_url: str) -> bool:
    value = (license_url or "").lower()
    return "/by/" in value and "nc" not in value and "nd" not in value


def arxiv_source(arxiv_id: str, license_url: str) -> dict:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(request(ARXIV_API + "?id_list=" + urllib.parse.quote(arxiv_id) + "&max_results=1"))
    entry = root.find("a:entry", ns)
    if entry is None:
        raise ValueError("arXiv id not found: " + arxiv_id)
    title = " ".join(text(entry.find("a:title", ns)).split())
    authors = [text(a.find("a:name", ns)) for a in entry.findall("a:author", ns)]
    abstract = " ".join(text(entry.find("a:summary", ns)).split())
    full_text, passages = parse_arxiv_html(request("https://arxiv.org/html/" + arxiv_id))
    if len(full_text) < 400:
        raise ValueError("arXiv full text unavailable or too short: " + arxiv_id)
    match = re.search(r"creativecommons\.org/licenses/by/([\d.]+)", license_url)
    return {"title": title, "url": "https://arxiv.org/abs/" + arxiv_id, "doi": "arxiv:" + arxiv_id,
            "attribution": ", ".join(authors) or "Authors listed at source", "journal": "arXiv",
            "license": "CC BY " + match.group(1), "licenseURL": license_url,
            "text": abstract + "\n\n" + full_text,
            "passages": [{"id": "p0", "section": "Abstract", "text": abstract}] + passages,
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat()}


def ingest_arxiv(db: sqlite3.Connection, arxiv_id: str, host: str, refresh: bool = False) -> str:
    if host not in HOSTS:
        raise ValueError("Unknown host")
    story_id = hashlib.sha256(("arxiv:" + arxiv_id + ":" + host).encode()).hexdigest()[:20]
    existing = db.execute("SELECT state FROM stories WHERE id=?", (story_id,)).fetchone()
    if existing and not refresh:
        return story_id
    if existing and existing["state"] != "ingested":
        raise ValueError("Only an undrafted source can be refreshed")
    license_url = arxiv_license(arxiv_id)
    if not is_cc_by(license_url):
        raise ValueError("arXiv paper is not CC BY; not commercially reusable: " + arxiv_id)
    source = arxiv_source(arxiv_id, license_url)
    with db:
        if existing:
            db.execute("UPDATE stories SET source=? WHERE id=?", (json.dumps(source), story_id))
        else:
            db.execute("INSERT INTO stories(id,source,host) VALUES(?,?,?)", (story_id, json.dumps(source), host))
    return story_id


CORE_API = "https://api.core.ac.uk/v3/search/works"
# CORE sits behind Cloudflare bot management, which blocks default library user
# agents (error 1010); a browser-like UA and a followed redirect are required.
CORE_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def paragraphs_from_text(text: str) -> list:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    if len(parts) <= 1:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text or "") if s]
        parts = [" ".join(sentences[i:i + 4]) for i in range(0, len(sentences), 4)]
    return [{"id": f"p{i + 1}", "section": "Body", "text": p} for i, p in enumerate(parts)]


def source_from_core(work: dict, doi: str):
    """Normalize a CORE record into a source dict, preferring full text over abstract."""
    if not work or (work.get("doi") or "").lower() != doi.lower():
        return None
    full = work.get("fullText") or ""
    abstract = work.get("abstract") or ""
    text = full if len(full.split()) >= 200 else abstract
    if len(text.split()) < 40:
        return None
    authors = [a.get("name") for a in (work.get("authors") or []) if a.get("name")]
    return {"title": work.get("title") or "", "url": work.get("downloadUrl") or ("https://doi.org/" + doi),
            "doi": doi, "attribution": ", ".join(authors) or "Authors listed at source",
            "journal": work.get("publisher") or "", "license": work.get("license") or "CORE record",
            "licenseURL": "", "text": text, "passages": paragraphs_from_text(text),
            "evidence_tier": "full" if full else "abstract",
            "evidence_note": "CORE open-access record." if full else "CORE abstract only.",
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat()}


def core_source(doi: str):
    """Best-effort CORE full text/abstract for a DOI; None on any failure or miss."""
    key = os.environ.get("CORE_API_KEY", "").strip()
    if not key:
        return None
    query = urllib.parse.quote('doi:"' + doi + '"')
    request_ = urllib.request.Request(
        CORE_API + "?q=" + query + "&limit=1",
        headers={"Authorization": "Bearer " + key, "Accept": "application/json",
                 "User-Agent": CORE_UA})
    try:
        with urllib.request.urlopen(request_, timeout=60) as response:
            data = json.loads(response.read(MAX_SOURCE_BYTES))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None
    results = data.get("results") or []
    return source_from_core(results[0], doi) if results else None


def fetch_public(url: str) -> bytes:
    """General HTTPS GET that follows redirects (unlike the PLOS-hardened `request`)."""
    req = urllib.request.Request(url, headers={"User-Agent": "ZwickyResearch/0.1"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read(MAX_SOURCE_BYTES + 1)


def reconstruct_abstract(inverted) -> str:
    if not inverted:
        return ""
    positions = {}
    for word, indices in inverted.items():
        for index in indices:
            positions[index] = word
    return " ".join(positions[i] for i in sorted(positions))


def openalex_source(doi: str) -> dict:
    """Abstract-tier evidence: metadata + abstract for any DOI, no full-text reuse.

    A paper whose full text is not licence-clear can still become an episode: we use
    only the public abstract and metadata, write our own script, and never reproduce
    the article. The source is marked evidence_tier='abstract' so the review trail is
    explicit; fidelity is bounded by the abstract, which the validators and Jev
    entailment enforce.
    """
    key = os.environ.get("LILT_OPENALEX_KEY", "").strip()
    url = "https://api.openalex.org/works/doi:" + doi
    if key:
        url += "?api_key=" + key
    work = json.loads(fetch_public(url))
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    if len(abstract.split()) < 40:
        raise ValueError("No usable public abstract on OpenAlex for " + doi)
    location = work.get("primary_location") or {}
    best = work.get("best_oa_location") or {}
    source = location.get("source") or {}
    authors = []
    for authorship in work.get("authorships") or []:
        name = (authorship.get("author") or {}).get("display_name")
        if name:
            authors.append(name)
    return {"title": work.get("display_name") or "", "url": "https://doi.org/" + doi, "doi": doi,
            "attribution": ", ".join(authors) or "Authors listed at source",
            "journal": source.get("display_name") or "",
            "license": (best.get("license") or location.get("license") or "abstract only"),
            "licenseURL": best.get("license") or location.get("license") or "",
            "text": abstract, "passages": [{"id": "p0", "section": "Abstract", "text": abstract}],
            "evidence_tier": "abstract",
            "evidence_note": "Abstract-only evidence; no full-text reuse.",
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat()}


def ingest_any(db: sqlite3.Connection, doi: str, host: str, refresh: bool = False) -> str:
    """PLOS or arXiv full text, then Europe PMC full text, then an OpenAlex abstract."""
    if doi.startswith("arxiv:"):
        return ingest_arxiv(db, doi.split(":", 1)[1], host, refresh)
    if re.fullmatch(r"10\.1371/journal\.[a-z]+\.\d+", doi):
        return ingest(db, doi, host, refresh)
    if host not in HOSTS:
        raise ValueError("Unknown host")
    story_id = hashlib.sha256((doi + ":" + host).encode()).hexdigest()[:20]
    existing = db.execute("SELECT state FROM stories WHERE id=?", (story_id,)).fetchone()
    if existing and not refresh:
        return story_id
    if existing and existing["state"] != "ingested":
        raise ValueError("Only an undrafted source can be refreshed")
    try:
        source = europepmc_source(doi)
    except (ValueError, urllib.error.URLError):
        source = None
    if source is None:
        source = core_source(doi)  # CORE open-access full text, when indexed
    if source is None:
        source = openalex_source(doi)  # abstract-tier fallback; raises if no abstract
    with db:
        if existing:
            db.execute("UPDATE stories SET source=? WHERE id=?", (json.dumps(source), story_id))
        else:
            db.execute("INSERT INTO stories(id,source,host) VALUES(?,?,?)", (story_id, json.dumps(source), host))
    return story_id


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


def language_clue_block(duo, host_id: str) -> str:
    """Prompt block of observed speaking-style clues for this host (both, if dialogue)."""
    ids = [host.id for host in duo] if duo else [host_id]
    parts = [f"LANGUAGE CLUES for {i}:\n{LANGUAGE_CLUES[i]}" for i in ids if i in LANGUAGE_CLUES]
    return ("\n\n" + "\n\n".join(parts)) if parts else ""


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
    duo = dialogue_hosts(record["host"])
    clues = language_clue_block(duo, record["host"])
    if duo:
        instructions = DIALOGUE_INSTRUCTIONS + dialogue_guide(duo) + "\n\n" + ANTI_SLOP_GUIDE + clues
    else:
        instructions = PODCAST_INSTRUCTIONS + writing_guide(record["host"]) + "\n\n" + ANTI_SLOP_GUIDE + clues
    effort = os.environ.get("OPENAI_REASONING_EFFORT", "low")
    if effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
        raise ValueError("Unsupported reasoning effort")
    reasoning = {"reasoning": {"effort": effort}} if model.startswith("gpt-5.6-luna") else {}
    with db:
        db.execute("UPDATE stories SET draft_input=? WHERE id=?", (json.dumps(packet, ensure_ascii=False), story_id))

    # Validate-and-repair loop: a draft that fails one validator is retried with the
    # exact failure quoted back, instead of being dropped. Each attempt is reserved
    # against the daily provider-call cap, so repair cannot run away.
    attempts = max(1, int(os.environ.get("LILT_DRAFT_ATTEMPTS", "2")))
    last_error, draft = None, None
    for _ in range(attempts):
        attempt_instructions = instructions
        if last_error:
            attempt_instructions += ("\n\nREPAIR: the previous draft was rejected by the validator with: \""
                                     + last_error + "\". Rewrite it so it satisfies that exact requirement. Keep every "
                                     "fact, number and quotation traceable to the evidence packet; add no new facts.")
        call_id = reserve_call(db, "openai", story_id)
        response = json.loads(request("https://api.openai.com/v1/responses", payload={
            "model": model, "store": False, "instructions": attempt_instructions, **reasoning,
            "input": json.dumps(packet, ensure_ascii=False, separators=(",", ":")),
            "max_output_tokens": 4500 if duo else 3500,
            "text": {"format": {"type": "json_schema", "name": "science_story", "strict": True,
                                "schema": DIALOGUE_SCHEMA if duo else SCHEMA}}
        }, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}))
        usage = response.get("usage") or {}
        with db:
            db.execute("UPDATE calls SET input_tokens=?,output_tokens=? WHERE id=?",
                       (usage.get("input_tokens"), usage.get("output_tokens"), call_id))
        if response.get("status") != "completed":
            last_error = "generation incomplete"
            continue
        outputs = [c["text"] for item in response.get("output", []) for c in item.get("content", []) if c.get("type") == "output_text"]
        if not outputs:
            last_error = "no draft returned, possibly refused"
            continue
        try:
            candidate = json.loads("".join(outputs))
            if duo:
                # validate_dialogue checks the opening for the exact paper title and first
                # author, so it needs the metadata as well as the evidence text.
                validate_dialogue(candidate, {"text": evidence_text(packet),
                                              "title": source.get("title", ""),
                                              "attribution": source.get("attribution", "")}, duo)
            else:
                validate_draft(candidate, {"text": evidence_text(packet)})
                validate_podcast(candidate, source, HOSTS[record["host"]])
        except (json.JSONDecodeError, ValueError) as error:
            last_error = str(error)
            continue
        draft = candidate
        break
    if draft is None:
        raise ValueError("Draft failed after " + str(attempts) + " attempts: " + str(last_error))
    with db:
        db.execute("UPDATE stories SET draft=?,state='review' WHERE id=?", (json.dumps(draft), story_id))
    return draft


def review(db, story_id: str, reviewer: str):
    record = row(db, story_id)
    if record["state"] != "review" or not reviewer.strip():
        raise ValueError("Requires a draft awaiting review and a named reviewer")
    draft = json.loads(record["draft"])
    source = json.loads(record["source"])
    duo = dialogue_hosts(record["host"])
    if duo:
        validate_dialogue(draft, source, duo)
    else:
        validate_draft(draft, source)
        validate_podcast(draft, source, HOSTS[record["host"]])
    digest = hashlib.sha256(record["draft"].encode()).hexdigest()
    with db:
        db.execute("UPDATE stories SET state='approved',reviewer=?,review_hash=? WHERE id=?", (reviewer.strip(), digest, story_id))


def approve_auto(db, story_id: str, decider_mode: str = "auto"):
    """Replace the named human reviewer with the automated verification gate."""
    record = row(db, story_id)
    if record["state"] != "review":
        raise ValueError("Auto-approval requires a draft awaiting review")
    report = verifier.verify_story(db, story_id, decider_mode)
    if not report["pass"]:
        return {"story": story_id, "status": "abstained", **report}
    review(db, story_id, report["reviewer"])
    return {"story": story_id, "status": "approved", **report}


def produce_auto(db, days: int = 14, limit: int = 6, max_stories: int = 3,
                 narrate: bool = True, decider_mode: str = "auto"):
    """Fully autonomous chain: select -> ingest -> draft -> verify -> (narrate/publish).

    Only sources the current connector can parse are ingested; everything else is
    reported as skipped. A story that fails verification abstains and the next
    candidate is tried. No human approval is requested.
    """
    selection = select_stories(db, days=days, per_show=1, limit=limit)
    results, published = [], 0
    for work in selection["selected"]:
        if published >= max_stories:
            break
        try:
            story_id = ingest_any(db, work["doi"], work["host"])
        except ValueError as error:
            results.append({"doi": work["doi"], "show": work["show"],
                            "status": "no_ingestable_source", "error": str(error)[:160]})
            continue
        try:
            draft_story(db, story_id)
            report = approve_auto(db, story_id, decider_mode)
        except (ValueError, urllib.error.URLError, json.JSONDecodeError) as error:
            results.append({"doi": work["doi"], "show": work["show"], "story": story_id,
                            "status": "error", "error": str(error)[:200]})
            continue
        entry = {"doi": work["doi"], "show": work["show"], "story": story_id, **report}
        if report["status"] == "approved" and narrate:
            try:
                narrate(db, story_id)
                publish(db, story_id)
                entry["status"] = "published"
                published += 1
            except (ValueError, urllib.error.URLError) as error:
                entry["status"] = "approved_not_narrated"
                entry["narrate_error"] = str(error)[:200]
                published += 1
        elif report["status"] == "approved":
            published += 1
        results.append(entry)
    return {"window_days": days, "selected": len(selection["selected"]),
            "published": published, "results": results}


def doctor() -> dict:
    """Report which provider keys and settings are present. Makes no network calls."""
    return {
        "voice": voice_status(),
        "openai_writer": {"api_key": bool(os.environ.get("OPENAI_API_KEY")),
                          "model": os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL},
        "feed": {"public_origin": os.environ.get("LILT_PUBLIC_ORIGIN", ""),
                 "max_provider_calls_per_day": os.environ.get("LILT_MAX_PROVIDER_CALLS_PER_DAY", "12"),
                 "max_source_chars": os.environ.get("LILT_MAX_SOURCE_CHARS", "18000")},
        "selection_sources": {
            "openalex_key": bool(os.environ.get("LILT_OPENALEX_KEY")),
            "contact_email": bool(os.environ.get("LILT_CONTACT_EMAIL")),
            "eurekalert": os.environ.get("LILT_EUREKALERT", "1").strip() != "0",
            "smc_caveats": os.environ.get("LILT_SMC", "").strip().lower() in ("1", "true", "yes"),
        },
        "hosts": [{"id": host.id, "name": host.name, "show": host.show, "voice_env": host.voice_env,
                   "voice_configured": bool(os.environ.get(host.voice_env))} for host in HOSTS.values()],
    }


def narrate(db, story_id):
    record = row(db, story_id)
    if record["audio"]:
        return record["audio"]
    if record["state"] != "approved":
        raise ValueError("Editorial approval is required before narration")
    if hashlib.sha256(record["draft"].encode()).hexdigest() != record["review_hash"]:
        raise ValueError("Draft changed after review")
    draft = json.loads(record["draft"])
    source = json.loads(record["source"])
    duo = dialogue_hosts(record["host"])
    if duo:
        validate_dialogue(draft, source, duo)
        inputs = turns_narration_inputs(draft, duo)
    else:
        validate_podcast(draft, source)
        host = HOSTS[record["host"]]
        inputs = [{"speaker": host.name, "host": host.id, "voice_env": host.voice_env, "text": narration_script(draft)}]
    reserve_call(db, "elevenlabs", story_id)
    audio = synthesize(inputs, dialogue=bool(duo), fetch=request)
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
        duo = dialogue_hosts(r["host"])
        body = turns_body(draft) if duo else draft["body"]
        entry = {"id": r["id"], "title": draft["title"], "dek": draft["dek"],
            "topic": HOSTS[r["host"]].topic, "hostID": r["host"],
            "minutes": max(1, round(len(body.split()) / 150)),
            "body": body, "caveat": draft["caveat"], "isDemo": False,
            "sources": [{"title": source["title"], "url": source["url"],
                         "attribution": source["attribution"] + ". Adapted by Zwicky; changes made.",
                         "license": source["license"] + " · " + source["licenseURL"]}],
            "audioURL": origin.rstrip("/") + "/audio/" + r["audio"]}
        if duo:
            entry["turns"] = draft["turns"]
            entry["hostIDs"] = [host.id for host in duo]
        result.append(entry)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover")
    p = sub.add_parser("shortlist"); p.add_argument("--days", type=int, default=7); p.add_argument("--per-host", type=int, default=3); p.add_argument("--limit", type=int, default=25); p.add_argument("--no-enrich", action="store_true"); p.add_argument("--markdown", action="store_true")
    p = sub.add_parser("select"); p.add_argument("--days", type=int, default=14); p.add_argument("--per-show", type=int, default=2); p.add_argument("--limit", type=int, default=10); p.add_argument("--markdown", action="store_true"); p.add_argument("--include-preprints", action="store_true", help="allow preprints/repositories (lower reputation)")
    p = sub.add_parser("approve-auto"); p.add_argument("id"); p.add_argument("--decider", default="auto")
    p = sub.add_parser("produce-auto"); p.add_argument("--days", type=int, default=14); p.add_argument("--limit", type=int, default=6); p.add_argument("--max-stories", type=int, default=3); p.add_argument("--no-narrate", action="store_true"); p.add_argument("--decider", default="auto")
    p = sub.add_parser("ingest"); p.add_argument("doi"); p.add_argument("--host", choices=HOSTS, required=True); p.add_argument("--refresh", action="store_true")
    sub.add_parser("hosts")
    for command in ("draft", "inspect", "narrate", "publish", "withdraw", "packet"):
        p = sub.add_parser(command); p.add_argument("id")
    p = sub.add_parser("approve"); p.add_argument("id"); p.add_argument("--reviewer", required=True)
    sub.add_parser("list")
    sub.add_parser("usage")
    sub.add_parser("doctor")
    args = parser.parse_args(); load_local_env(); db = connect()
    try:
        if args.command == "discover": result = discover()
        elif args.command == "shortlist":
            result = shortlist_rank(db, days=args.days, per_host=args.per_host, limit=args.limit,
                                    contact=os.environ.get("LILT_CONTACT_EMAIL", "zwicky-research@example.com"),
                                    enrich=not args.no_enrich)
            if args.markdown:
                print(shortlist_report(result))
                return
        elif args.command == "select":
            result = select_stories(db, days=args.days, per_show=args.per_show, limit=args.limit,
                                    min_reputation=0.0 if args.include_preprints else 0.5)
            if args.markdown:
                print(select_report(result))
                return
        elif args.command == "approve-auto": result = approve_auto(db, args.id, args.decider)
        elif args.command == "produce-auto":
            result = produce_auto(db, days=args.days, limit=args.limit, max_stories=args.max_stories,
                                  narrate=not args.no_narrate, decider_mode=args.decider)
        elif args.command == "ingest": result = ingest(db, args.doi, args.host, args.refresh)
        elif args.command == "packet": result = build_packet(json.loads(row(db, args.id)["source"]), int(os.environ.get("LILT_MAX_SOURCE_CHARS", "18000")))
        elif args.command == "hosts": result = [{"id": h.id, "name": h.name, "show": h.show, "topic": h.topic,
            "beat": h.beat, "delivery": h.delivery, "sign_off": h.sign_off, "voice_env": h.voice_env} for h in HOSTS.values()]
        elif args.command == "usage": result = [dict(r) for r in db.execute("SELECT day,provider,count(*) AS attempts,sum(input_tokens) AS input_tokens,sum(output_tokens) AS output_tokens FROM calls GROUP BY day,provider")]
        elif args.command == "doctor": result = doctor()
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
