"""Science Media Centre expert reactions: a checking source, never evidence.

The SMC publishes "Expert reaction to …" posts with named expert commentary and
statistical context. Zwicky uses them only to surface *caveats worth checking* against
the paper, in the verification step. They never enter the evidence packet, the evidence
selector or the script — see docs/editorial/story-discovery.md.

Feed verified live 2026-09-21: https://www.sciencemediacentre.org/feed/ (WordPress RSS,
20 items; reactions carry categories such as `sleep`, `brain & neuroscience`,
`climate change`).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED = "https://www.sciencemediacentre.org/feed/"
DATA = Path(os.environ.get("LILT_DATA", Path(__file__).resolve().parent / "data"))
CACHE = DATA / "cache" / "smc"
TTL_HOURS = 12

# Host beat -> SMC category/title keywords. Deliberately a small, explicit map: we only
# check the beats where the SMC regularly covers the literature (brain, sleep, climate,
# health-adjacent). Other beats pass through with no caveat questions.
HOST_TOPICS = {
    "ada": ("brain", "neuroscience", "mental health", "parkinson", "multiple sclerosis",
            "ptsd", "autism", "adhd"),
    "lena": ("sleep", "circadian"),
    "atlas": ("climate", "glacier", "flood", "water"),
    "tomas": ("heart", "weight loss", "exercise", "vitamins"),
    "rosa": ("microbiome", "microbiology", "microplastics"),
    "kenji": ("long covid", "microplastics"),
    "ines": ("statistical", "replication", "meta-analysis"),
}

REACTION_PREFIX = "expert reaction"


def get(url: str, fetch=None):
    """Return (kind, payload) with kind 'text'|'error', cached on disk."""
    if fetch is not None:
        return fetch(url)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
    if path.exists() and time.time() - path.stat().st_mtime < TTL_HOURS * 3600:
        return json.loads(path.read_text())
    request = urllib.request.Request(
        url, headers={"User-Agent": "ZwickyResearch/0.1 (smc check)"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = ("text", response.read().decode("utf-8", errors="replace"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return ("error", "network")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result))
    return result


def parse_feed(xml_text: str) -> list:
    """[{title, url, date, categories}] from the SMC RSS feed."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        items.append({
            "title": title,
            "url": (item.findtext("link") or "").strip(),
            "date": (item.findtext("pubDate") or "").strip(),
            "categories": [c.text.strip() for c in item.findall("category") if c.text],
        })
    return items


def is_expert_reaction(title: str) -> bool:
    return (title or "").lower().startswith(REACTION_PREFIX)


def expert_reactions(get_=None) -> list:
    """Only the expert-reaction posts, newest first, from the public feed."""
    get_ = get_ or get
    kind, payload = get_(FEED)
    if kind != "text":
        return []
    return [item for item in parse_feed(payload) if is_expert_reaction(item["title"])]


def reactions_for_host(host: str, reactions, limit: int = 2) -> list:
    """Reactions whose category or title matches the show's beat, capped per episode."""
    topics = HOST_TOPICS.get(host, ())
    if not topics:
        return []
    matched = []
    for reaction in reactions:
        haystack = " ".join([reaction.get("title", "")] + reaction.get("categories", [])).lower()
        if any(topic in haystack for topic in topics):
            matched.append(reaction)
        if len(matched) >= limit:
            break
    return matched
