"""Anti-AI-slop writing rules and a lightweight detector.

Distilled for spoken science scripts from the pattern catalog in
conorbronsdon/avoid-ai-writing (MIT), itself adapted from blader/humanizer and
others. The guide is prompt text: it constrains surface style and rhythm only.
It never overrides factual fidelity, the exact headline, the first-author credit,
the verbatim limitations paragraph, or the host sign-off.

`analyze` is a deterministic review aid, not a verdict. Flags are candidates;
context and intent decide whether an edit is warranted.
"""
from __future__ import annotations
import re

ANTI_SLOP_GUIDE = '''WRITING SURFACE — sound like a person, not a model.
These rules change only how the script sounds. They never change a finding, a
number, a limitation, an attribution or the exact wording of the paper title.

Vocabulary to avoid (use the plain word or cut it):
- delve, leverage, harness, robust, comprehensive, cutting-edge, pivotal,
  underscore, meticulous, seamless, game-changer, landmark, testament to,
  realm, tapestry, paradigm, embark, beacon, nestled, vibrant, thriving,
  bustling, intricate, holistic, actionable, impactful, synergy, interplay,
  streamline, bolster, spearhead, resonate, facilitate, underpin, nuanced,
  multifaceted, myriad, plethora, encompass, catalyze, reimagine, illuminate,
  elucidate, juxtapose, cornerstone, paramount, poised, burgeoning, nascent,
  quintessential, overarching, utilize, commence, ascertain, endeavor,
  serves as, features (as a verb), boasts.

Constructions to avoid:
- "It's not X, it's Y" (including split across two sentences) and stacked
  negations before a reveal. State the positive claim directly.
- "Imagine a world...", "In today's...", "In a world where..." openers.
- "Here's the thing", "The catch?", "Plot twist:", "What surprised me most",
  "Here's what's interesting" and other staged reveals. Just say the thing.
- Empty hedging stacks: "could potentially", "may eventually", "might ultimately".
- "This matters because..." when it restates importance instead of a consequence.
- Vague attribution: "experts believe", "studies show" with no named source.
- Generic closers: "the future looks bright", "only time will tell".
- Significance inflation: "changes everything", "a watershed moment",
  "revolutionary", "unprecedented" without naming the precedent.
- Transition filler: "Moreover", "Furthermore", "Additionally", "In conclusion",
  "When it comes to", "At the end of the day", "That said".
- Copula avoidance: prefer "is" and "has" over "serves as", "features", "boasts".
- Rule-of-three lists and "X and Y and Z" rhythms when the content has two or
  four real items; let the evidence set the count.
- Superficial -ing glosses ("symbolizing...", "reflecting...", "showcasing...").

Rhythm:
- Vary sentence length. Do not chop ordinary sentences into fragments for drama,
  and do not march out same-shaped sentences. One short sentence that lands a
  point is good; three in a row is a drumroll.
- No em dashes. Use commas, full stops or parentheses. This is spoken; write for
  the ear, with contractions and natural breath.
- No markdown, bold, bullet points or section headings. Do not read numbers as
  digits unless they are conventionally spoken that way.
- Keep the host's voice specific. Do not invent personal experience, fieldwork,
  reactions or quotations to sound human. The source supplies the facts; the
  host supplies the attitude, not new evidence.
'''

TIER1A = {
    "delve", "leverage", "harness", "robust", "comprehensive", "cutting-edge",
    "pivotal", "underscore", "meticulous", "seamless", "game-changer",
    "game-changing", "landmark", "testament", "realm", "tapestry", "paradigm",
    "embark", "beacon", "nestled", "vibrant", "thriving", "bustling",
    "intricate", "holistic", "actionable", "impactful", "synergy", "interplay",
    "streamline", "bolster", "spearhead", "resonate", "facilitate", "underpin",
    "nuanced", "multifaceted", "myriad", "plethora", "encompass", "catalyze",
    "reimagine", "illuminate", "elucidate", "juxtapose", "cornerstone",
    "paramount", "poised", "burgeoning", "nascent", "quintessential",
    "overarching", "utilize", "commence", "ascertain", "endeavor", "watershed",
}
TIER1B = {"serves", "features", "boasts", "presents", "represents"}
SIGNIFICANCE = {
    "changes everything", "change everything", "revolutionary", "unprecedented",
    "the future looks bright", "only time will tell", "one thing is certain",
    "important to note", "at the end of the day", "when it comes to",
}
TRANSITIONS = {"moreover", "furthermore", "additionally"}
CHATBOT = {
    "i hope this helps", "great question", "certainly!", "absolutely!",
    "let's dive in", "let's explore", "let's take a look", "let's break this down",
}

RE_NOT_X_BUT_Y = re.compile(r"\b(?:isn't|is not|wasn't|was not|it's not|it is not)\b[^.!?]{0,80}\b(?:it'?s|it is|but)\b", re.I)
RE_HEDGE_STACK = re.compile(r"\b(?:could|may|might|would|will)\s+(?:potentially|eventually|ultimately|possibly|conceivably|perhaps)\b", re.I)
RE_IMAGINE = re.compile(r"\b(?:imagine a world|picture a (?:future|world)|in today's|in an era where|in a world where)\b", re.I)
RE_STAGED = re.compile(r"\b(?:here'?s the thing|the catch\??|plot twist|here'?s what'?s interesting|what surprised me most|the kicker)\b", re.I)
RE_MATTERS = re.compile(r"\bthis matters because\b", re.I)
RE_VAGUE_ATTR = re.compile(r"\b(?:experts believe|studies show|research suggests|scientists say|industry leaders agree)\b", re.I)
RE_EMDASH = re.compile(r"—|(?<!-)--(?!-)")
RE_RHET_Q = re.compile(r"\?")


def _words(text):
    return re.findall(r"[a-z][a-z'-]*", text.lower())


def analyze(text):
    """Return deterministic style findings and rhythm stats for a script body."""
    words = _words(text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    lengths = [len(_words(s)) for s in sentences]

    def density(term_set):
        return sum(1 for w in words if w in term_set)

    findings = {
        "tier1a_vocab": sorted({w for w in words if w in TIER1A}),
        "tier1b_copula": sorted({w for w in words if w in TIER1B}),
        "significance_phrases": [p for p in SIGNIFICANCE if p in text.lower()],
        "transition_words": sorted({w for w in words if w in TRANSITIONS}),
        "chatbot_artifacts": [p for p in CHATBOT if p in text.lower()],
        "not_x_but_y": len(RE_NOT_X_BUT_Y.findall(text)),
        "hedge_stack": len(RE_HEDGE_STACK.findall(text)),
        "scenario_opener": len(RE_IMAGINE.findall(text)),
        "staged_reveal": len(RE_STAGED.findall(text)),
        "this_matters_because": len(RE_MATTERS.findall(text)),
        "vague_attribution": len(RE_VAGUE_ATTR.findall(text)),
        "em_dash": len(RE_EMDASH.findall(text)),
        "rhetorical_questions": len(RE_RHET_Q.findall(text)),
        "markdown_or_bold": len(re.findall(r"\*\*|^#+\s|^- ", text, re.M)),
    }
    stats = {
        "words": len(words),
        "sentences": len(sentences),
        "mean_sentence_len": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "sentence_len_stdev": round((sum((x - sum(lengths) / len(lengths)) ** 2 for x in lengths) / len(lengths)) ** 0.5, 1) if len(lengths) > 1 else 0,
        "longest_sentence": max(lengths) if lengths else 0,
        "em_dash_per_1k": round(len(RE_EMDASH.findall(text)) / max(len(words), 1) * 1000, 2),
    }
    return {"findings": findings, "stats": stats}


def penalty(report):
    """A single comparable score; lower is cleaner. Rough, for A/B ranking only."""
    f = report["findings"]
    return (
        len(f["tier1a_vocab"])
        + 0.5 * len(f["tier1b_copula"])
        + len(f["significance_phrases"])
        + len(f["transition_words"])
        + 2 * len(f["chatbot_artifacts"])
        + 2 * f["not_x_but_y"]
        + 2 * f["hedge_stack"]
        + 2 * f["scenario_opener"]
        + 2 * f["staged_reveal"]
        + f["this_matters_because"]
        + 2 * f["vague_attribution"]
        + f["em_dash"]
        + 0.5 * f["rhetorical_questions"]
        + 5 * f["markdown_or_bold"]
    )
