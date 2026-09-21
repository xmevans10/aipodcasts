"""One press release is one signal, however many sites republish it.

EurekAlert, ScienceDaily and Phys.org all carry institutional material, and the same
university release commonly appears on all three. Counting each occurrence would let a
single press office manufacture three independent endorsements. This module collapses
those copies into one *publicity event*, and keeps genuinely independent editorial
outlets (Quanta, Nature News, Science News) as their own signal.

A release is only ever a pointer. Its DOI identifies the paper; the episode's evidence
still comes from the paper connectors, never from release text.

Usage:
    from publicity import Release, cluster_releases, event_index, publicity_value
    events = cluster_releases([Release("eurekalert", "…", doi="10.1/x"),
                               Release("sciencedaily", "…")])
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

# Sites that republish institutional material. They corroborate an event but never cast
# an independent vote, so a release on all three is still one event.
SYNDICATORS = {"sciencedaily", "physorg"}
# Outlets that apply their own editorial judgement: each one is an independent signal,
# not syndication of a press release.
INDEPENDENT = {"quanta", "nature", "science"}
# Press-release origins. Presence here is the tier-1 publicity signal.
PRESS = {"eurekalert", "pressoffice", "university", "journal"}

FUZZY_MATCH = 0.72  # title similarity required to merge releases that lack a DOI


def _normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (title or "").lower()).strip()


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]{4,}", (text or "").lower()))


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    overlap = len(left_tokens & right_tokens) / max(len(left_tokens), 1)
    return max(SequenceMatcher(None, left.lower(), right.lower()).ratio(), overlap)


@dataclass
class Release:
    """A single feed item: a pointer, never evidence."""
    source: str
    title: str
    url: str = ""
    date: str = ""
    doi: str = ""


@dataclass
class Event:
    """All releases judged to be the same publicity event."""
    key: str
    title: str
    doi: str = ""
    date: str = ""
    sources: set = field(default_factory=set)

    @property
    def press(self) -> bool:
        """A press office released this, so a human already judged it explainable."""
        return bool(self.sources & PRESS)

    @property
    def independent(self) -> bool:
        return bool(self.sources & INDEPENDENT)

    @property
    def is_syndicated_only(self) -> bool:
        return self.sources <= SYNDICATORS


def cluster_releases(releases) -> list:
    """Group releases into events, merging by DOI first and fuzzy title second.

    A release with a DOI opens (or joins) a DOI-keyed event. A release without one joins
    an existing event whose title is similar enough, so a syndicated copy that never
    resolves to a DOI still collapses into the origin instead of voting on its own.
    """
    events: list = []
    for release in releases:
        doi = (release.doi or "").lower()
        match = next((e for e in events if doi and e.doi == doi), None)
        if match is None:
            match = next((e for e in events
                          if _similarity(release.title, e.title) >= FUZZY_MATCH), None)
        if match is None:
            match = Event(key=doi or "title:" + _normalize(release.title),
                          title=release.title, doi=doi, date=release.date)
            events.append(match)
        match.sources.add(release.source)
        if doi and not match.doi:
            match.doi = doi
        if release.date and not match.date:
            match.date = release.date
    return events


def event_index(events) -> dict:
    """doi(lower) -> Event, for joining the publicity signal to a candidate paper."""
    return {event.doi.lower(): event for event in events if event.doi}


def publicity_value(event) -> float:
    """Collapsed press signal: any press origin is 1.0, however many sites carried it."""
    return 1.0 if event and event.press else 0.0


def editorial_value(event) -> float:
    """Independent editorial signal: a judged outlet, not a syndicated republish."""
    return 1.0 if event and event.independent else 0.0
