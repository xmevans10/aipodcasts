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
do not produce an outline, and do not narrate the writing/generation process in the episode.
This does NOT mean hiding the host's curiosity, momentary confusion or change of understanding.
1. Pick the single supported finding worth explaining. Ignore the rest of the paper.
2. Name the one idea a listener must already hold for that finding to land. Put it first,
   in ordinary words.
3. Say what the researchers did as ordinary actions: weighed hives, compared photographs,
   followed people for years, trained a model on simulated data.
4. State the result plainly, then its boundary, as one connected thought.
5. Read it back and cut: instrument and model names, gene and species names you do not
   need, secondary statistics and category lists. Keep an aside when it reveals what the
   host finds funny, troubling or surprising and carries the listener into the next idea.
'''

HUMAN_STORY_GUIDE = '''THINKING AND FEELING OUT LOUD — storytelling, not a miniature paper review.
Build around a supported tension: an intuitive expectation, what was actually tested,
and the detail that changes how the host understands it. Let that question pull us through
the MIDDLE, instead of marching through an inventory of methods and results. Do not imply
an expected outcome was the researchers' hypothesis unless the source says so.
Use tangible actions/objects the source supplies. An explicitly imagined everyday analogy
can help; invented lab scenes, dialogue, memories and researcher feelings cannot.
The fictional host may want a simpler answer, feel unsettled, get excited about a detail,
notice their own mistaken intuition or briefly search for better words. Make the reason
audible. A generic 'wow, fascinating' pasted onto a summary does not do this.
Let a sentence change direction when the thought changes. Fragments, a brief reaction,
self-correction or a warm aside can stay when they make understanding easier. Do not
insert ums, fake confusion, laughs or vulnerability on a schedule. Never pretend to be
confused about a basic fact just to stage an explanation. Express laughter through earned
humor and performance direction, never bracketed stage notes or a canned laugh track.
In dialogue, let the last speaker's actual words provoke the next turn: question,
pushback, recognition, playful disagreement or a more useful analogy. Neither speaker
should be a permanently clueless audience surrogate. Both can notice and revise things.
Keep personality inside the explanation: one host lingers fondly on a living detail,
another punctures a seductive claim, another gets absorbed in how something was built.
An emotional arc need not end in excitement. Honest disappointment or an unresolved
question can be the ending. Preserve the finding and every material limit.
Before returning JSON, silently ask: what did THIS host initially expect or want, what
specific detail moved them, and why does the next thought follow? If the body is still
an abstract with contractions, rewrite its narrative spine. Do not add a reaction quota.
'''


OPENING_CHECKLIST = '''OPENING CHECKLIST — check these before you return the JSON. They are
structural requirements, not style advice, and a draft that misses one is rejected.
1. The FIRST sentence is a hook. It is not the paper citation and not a greeting.
2. Somewhere in the opening, after that hook, the `title` field appears WORD FOR WORD in
   the spoken script. Copy it exactly; do not paraphrase it, shorten it or reword it.
3. Somewhere in the opening, the `source_title` appears WORD FOR WORD, with the first
   named author from `source_attribution` and "and colleagues" if there are several.
4. Each of those two titles is spoken EXACTLY ONCE in the whole script, and the paper is
   credited once, not once per presenter.
5. Write the limitation in your own plain spoken words, then copy that paragraph into
   both `caveat` and the spoken script WORD FOR WORD, exactly once. This is a match
   between your two output fields, NOT an instruction to quote the source paper.
6. The closing carries each presenter's exact sign-off, in that presenter's own words.
Requirements 2, 3 and 5 are verbatim string matches. Cutting for clarity never means
cutting these; trim elsewhere.
'''


def contract_block() -> str:
    """The full shared block appended to both the solo and dialogue instructions.

    The opening checklist goes last on purpose. The structural requirements are exact
    string matches that a validator rejects outright, and a writer that has just read four
    paragraphs about cutting for clarity will otherwise paraphrase the headline away.
    """
    return "\n".join([PRECEDENCE, AUDIENCE_CONTRACT, INTERNAL_CONTROLS, WRITING_PROCESS, HUMAN_STORY_GUIDE,
                       OPENING_CHECKLIST])


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

_BRACKET_DIRECTION = re.compile(r"\[[^\]\n]{1,40}\]")
_STAGE_DIRECTION = [
    re.compile(r"\*\*|\*(?=\w)"),
    re.compile(r"^\s{0,3}#{1,6}\s", re.M),
    re.compile(r"^\s{0,3}[-*]\s+", re.M),
    _BRACKET_DIRECTION,
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

    if re.search(r'\bthis episode (?:therefore )?(?:should|must) be withheld\b', text, re.I):
        defects.append('editorial_non_episode: the script says this episode should be withheld. '
                       'An editorial rejection is not a playable science episode; choose an on-beat paper.')

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

    # The required paper credit can contain real notation such as [O III]. Only
    # that exact title span is exempt; directions elsewhere are still rejected.
    outside_credit = re.sub(re.escape(source_title), '', text, flags=re.I) if source_title else text
    for pattern in _STAGE_DIRECTION:
        found = pattern.search(outside_credit if pattern is _BRACKET_DIRECTION else text)
        if found:
            defects.append(
                "markdown_or_stage_direction: the script contains markdown, a heading, a "
                f"bullet or a bracketed direction (\"{found.group(0).strip()}\"). The body is "
                "narrated exactly as written. Remove it and write plain spoken prose. "
                "Bracketed scientific notation is allowed only inside the exact paper title credit; "
                "use ordinary spoken names elsewhere.")
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
