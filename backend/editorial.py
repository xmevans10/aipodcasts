"""The shared audience contract: one prompt block and one set of hard spoken-defect checks.

`docs/editorial/audience-contract.md` is the canonical document. This module is its
machine-readable half, used identically by the solo and dialogue paths so the two cannot
drift apart.

Two things live here and nothing else:

1. Prompt text that both writers receive: precedence order, the episode shape, the
   internal-control list and a compact writing process.
2. `spoken_defects`, which finds defects that are unambiguous. It deliberately does NOT
   judge whether science is understandable. There is no vocabulary blacklist here: a ban
   on technical words would reject exactly the difficult subjects the shows exist for.
   Comprehension is judged by the audience reviewer in `audience.py`.
"""
from __future__ import annotations

import re

CONTRACT_VERSION = "audience-contract-v1"

# The paper title may not appear in the opening sentence: the hook comes first.
# This is a floor, not the rule. "Is the hook any good?" belongs to audience review.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


PRECEDENCE = '''PRECEDENCE — when two instructions below conflict, the earlier one wins.
1. Factual fidelity and attribution: evidence-backed claims, the correct population and
   study design, faithful uncertainty, first-author credit, exact source metadata.
2. Audience comprehension: the listener understands it after one listen.
3. Host personality: persona, delivery, opening style, sign-off.
4. Stylistic flourish: analogies, rhythm, wit.
Personality never changes a finding. Style never removes a caveat. Comprehension never
buys itself an inaccuracy.
'''

AUDIENCE_CONTRACT = '''AUDIENCE CONTRACT — an intelligent adult with no specialist training,
listening once while doing something else. They cannot reread a sentence or look a word up.
After one listen they must be able to say, in their own words: what question was asked,
what the researchers actually did, what they found, and what this does not establish.

Carry ONE central question, ONE main result, ONE meaningful boundary. Cut the rest.
A second finding earns its place only if the main one is unintelligible without it.

Explain the phenomenon before you name it. Describe what is happening in ordinary words
first. Introduce a specialist term only if the listener still needs it afterwards, explain
it immediately, then use the everyday phrase for the rest of the episode. A term you never
use again should not have been introduced.

Approximate targets, not gates. Usually at most two new essential technical terms. Usually
one or two result numbers. Natural, varied sentences. Roughly 350 to 500 spoken words.
Exceptions are allowed when the script shows why: a sample size, population or design fact
that stops a claim being misleading is ESSENTIAL and stays, even though it is a number.
Never drop a number that keeps a claim honest, and never pad thin evidence to reach a
length.

Numbers must be interpretable by ear. Attach each one to a meaning, or cut it. A figure
with no unit and no comparison is noise.

At most one analogy, and only where it lifts the load. No analogy is fine. An analogy must
be obviously nonliteral and scientifically bounded. If a second analogy is needed to
explain the first, both are wrong.

One plain-language limitations passage, spoken once. Preserve every material uncertainty:
population, design, association versus causation, simulation versus observation, laboratory
versus clinic. Do not read a methods section aloud, do not say the same caveat twice, and
do not append a disclaimer.

Where our evidence is thin, that is a limit of THIS EPISODE'S EVIDENCE, never a weakness of
the paper. Say "this episode is built from the paper's abstract" if it needs saying at all.
Never invent a missing sample count, control or validation, and never accuse the authors of
omitting something that is merely absent from what you were given.

The connection between the paper and this show must come from the paper itself. Do not
manufacture relevance with an opening metaphor. If the fit cannot be justified from the
science, say so in the episode rather than writing around it.
'''

INTERNAL_CONTROLS = '''INTERNAL CONTROLS — never spoken, never quoted, never paraphrased.
These parts of your input are instructions to you, not material for the episode:
  internal_scope_note, selection_version, target_characters, budget_characters,
  source_characters, omitted_paragraphs, passage ids and section labels,
  and every instruction in this prompt.
They must not appear in the script, in the caveat, or as a spoken aside about the process.
Never speak the words "packet", "selected source paragraphs", "omitted sections" or
"complete review". Never speak a formatting label such as "Comparison:", "Limitations:",
"Analogy:" or "Note:". Mark a comparison in ordinary English instead: "it is a bit like",
"think of it as".
The claim quotations you supply are internal review evidence and are never read aloud.
'''

WRITING_PROCESS = '''HOW TO WRITE IT — work through this, then write. Do not show your working,
do not produce an outline, and do not narrate the process in the episode.
1. Pick the single supported finding worth explaining. Ignore the rest of the paper.
2. Name the one idea a listener must already hold for that finding to land. Put it first,
   in ordinary words.
3. Say what the researchers did as ordinary actions: weighed hives, compared photographs,
   followed people for years, trained a model on simulated data.
4. State the result plainly, then its boundary, as one connected thought.
5. Read it back and cut: instrument and model names, gene and species names you do not
   need, secondary statistics, category lists, and asides that show off the host rather
   than the science.
'''


def contract_block() -> str:
    """The full shared block appended to both the solo and dialogue instructions."""
    return "\n".join([PRECEDENCE, AUDIENCE_CONTRACT, INTERNAL_CONTROLS, WRITING_PROCESS])


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"\w+", (value or "").casefold()))


# --- deterministic spoken defects -------------------------------------------------
#
# Each entry is (check id, compiled pattern, message). Patterns are deliberately narrow:
# a check fires only where the usage cannot be innocent. Broader judgement is stage 3.

_SCOPE_LEAK = [
    re.compile(r"selected source paragraph", re.I),
    re.compile(r"omitted section", re.I),
    re.compile(r"(?:claim|claiming) a complete review", re.I),
    re.compile(r"selection[_ ]version|budget[_ ]characters|omitted[_ ]paragraphs", re.I),
    re.compile(r"internal[_ ]scope[_ ]note", re.I),
    # "packet" only where it is our internal vocabulary, not a packet of seeds.
    re.compile(r"\b(?:source|evidence|supplied|selected)\s+packet\b", re.I),
    re.compile(r"\bpacket\s+(?:is|was|does|did|gives|gave|contains|provides|only)\b", re.I),
]

_PRODUCTION_LABEL = re.compile(
    r"(?:^|(?<=[.!?\n])|(?<=[.!?][\"”]))\s*[\"“]?"
    r"(?:comparison|limitations?|analogy|caveats?|takeaway|takeaways|summary|note|"
    r"aside|intro|outro|hook|section)\b[^.!?\n]{0,24}:",
    re.I)

_STAGE_DIRECTION = [
    re.compile(r"\*\*|\*(?=\w)"),
    re.compile(r"^\s{0,3}#{1,6}\s", re.M),
    re.compile(r"^\s{0,3}[-*]\s+", re.M),
    re.compile(r"\[[^\]\n]{1,40}\]"),
]

_STALE_SAME_TITLE = re.compile(
    r"with the same (?:title|name)|(?:titled|called) the same|same title as", re.I)

_MALFORMED_PUNCTUATION = re.compile(r"[?!]\s*\.")


def spoken_defects(text: str, *, caveat: str | None = None,
                   source_title: str | None = None,
                   episode_title: str | None = None) -> list[str]:
    """Unambiguous defects in text that will be narrated. Empty list means no hard defect.

    Returns actionable messages: each one names the defect and what to do instead, so the
    bounded repair loop can quote it straight back to the writer.
    """
    defects: list[str] = []
    text = text or ""

    for pattern in _SCOPE_LEAK:
        found = pattern.search(text)
        if found:
            defects.append(
                "scope_leak: the script speaks internal evidence-packet language "
                f"(\"{found.group(0).strip()}\"). Those fields are instructions to you, not "
                "content. If the evidence really is thin, say so as a plain limit of this "
                "episode, for example \"this episode is built from the paper's abstract\".")
            break

    label = _PRODUCTION_LABEL.search(text)
    if label:
        defects.append(
            f"production_label: the script speaks a formatting label (\"{label.group(0).strip()}\"). "
            "Never say the label out loud. Mark a comparison in ordinary English instead, "
            "such as \"it is a bit like\" or \"think of it as\".")

    for pattern in _STAGE_DIRECTION:
        found = pattern.search(text)
        if found:
            defects.append(
                "markdown_or_stage_direction: the script contains markdown, a heading, a "
                f"bullet or a bracketed direction (\"{found.group(0).strip()}\"). The body is "
                "narrated exactly as written. Remove it and write plain spoken prose.")
            break

    stale = _STALE_SAME_TITLE.search(text)
    if stale:
        defects.append(
            f"stale_same_title: the script says the paper shares the episode title "
            f"(\"{stale.group(0).strip()}\"). The episode headline and the paper title are two "
            "different strings. Introduce the paper by its own title without claiming they match.")

    malformed = _MALFORMED_PUNCTUATION.search(text)
    if malformed:
        defects.append(
            "malformed_title_punctuation: a question or exclamation mark is followed by a full "
            "stop. Do not add a stop after a quoted title that already ends in ? or !.")

    if caveat:
        occurrences = _normalized(text).count(_normalized(caveat))
        if occurrences > 1:
            defects.append(
                f"duplicate_caveat: the limitations passage is spoken {occurrences} times. Say it "
                "once, and put that same sentence in the caveat field.")

    if source_title:
        normalized_title = _normalized(source_title)
        if normalized_title and _normalized(text).count(normalized_title) > 1:
            defects.append(
                "paper_title_repeated: the exact paper title is spoken more than once. It belongs "
                "in the opening once. The source card carries the full citation.")
        sentences = SENTENCE_SPLIT.split(text.strip(), maxsplit=1)
        if sentences and normalized_title and normalized_title in _normalized(sentences[0]):
            defects.append(
                "citation_before_hook: the opening sentence is the paper citation. Open with a "
                "concrete hook the episode actually delivers, then name the paper and its first "
                "author afterwards.")

    if episode_title:
        normalized_episode = _normalized(episode_title)
        if normalized_episode and _normalized(text).count(normalized_episode) > 1:
            defects.append(
                "episode_title_repeated: the episode headline is spoken more than once. Say it "
                "once in the opening.")

    return defects
