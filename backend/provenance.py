"""Verbatim-quote matching, shared by the single-host and dialogue validators."""
from __future__ import annotations
import unicodedata


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
