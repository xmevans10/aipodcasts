# The audience review gate

Operational reference for `backend/audience.py`. The standard it enforces is
[the audience contract](audience-contract.md).

Version: `audience-review-v1`, against `audience-contract-v1`.

## What it is, and what it is not

It asks one question: **could an intelligent nonspecialist, listening once, recover the
question, the method, the finding and the limitation?**

It is not a factual check. `verify.py` decides whether the script is true; this decides
whether it is understandable. The two are independent, and deliberately so: a strong
audience report never rescues a failed evidence result, and a passed evidence check never
substitutes for comprehension.

It is not a measurement of real listeners. It is a structured model review calibrated
against `backend/tests/fixtures/editorial_cases.json`. Saying "audience review passed" is
a claim about the gate, not about people.

It is not a readability score. There is no grade-level bar. Several of the worst scripts
in the 2026-09-21 batch had short sentences, plain syntax and no jargon vocabulary, and
were still unintelligible.

## Why it is a separate provider call

`verify.Decider` (Jev, or an OpenAI-compatible endpoint) answers booleans, choices and
scores. That interface cannot return the quoted spans, severity tags and repair
instructions a writer needs, and a probability attached to "is this understandable" would
be a number with no referent.

So review is one structured-output call against the **already configured writer provider**
(`OPENAI_API_KEY`, `OPENAI_MODEL`, overridable with `LILT_REVIEW_MODEL`). No new service,
no new dependency, no readability package.

## The decision

The reviewer returns a decision, severity-tagged issues each with a short quoted span and
one concrete instruction, the first sentence that lost the listener, unexplained terms, a
beat-fit judgement, and a listener-style paraphrase of the question, method, finding and
limit.

A report passes only when **all** of the following hold:

- the reviewer's own decision is `pass`;
- no issue is tagged `blocker` or `major` (`minor` issues are recorded, not blocking);
- beat fit is not `unfounded`;
- the paraphrase recovers all four listener questions.

Anything else fails, and the reviewer's own instructions become the repair text.

The paraphrase is a **diagnostic, not an oracle**. Numbers appearing in the paraphrase but
in neither the script nor the evidence are recorded as
`paraphrase_numbers_not_in_script`, which means the reviewer supplied knowledge of its own
and its judgement should be read with that in mind.

## Failure semantics

Every one of these leaves the story **pending**, never approved:

| Situation | Result |
|---|---|
| No `OPENAI_API_KEY` or model configured | `pending` |
| Network error, timeout, HTTP error | `pending` |
| Provider returns `status != completed` | `pending` |
| No output, or a refusal | `pending` |
| Output is not JSON | `pending` |
| Output is missing a required field | `pending` |
| Output has an unknown decision, severity or beat-fit value | `pending` |

A pending review never triggers a writer rewrite: re-rolling the writer cannot fix an
unreachable reviewer, and re-rolling the reviewer against unchanged text until it happens
to agree is explicitly not allowed.

## Freshness

Every report is bound to three things: the exact `draft_sha256`, the contract version, and
the review version. If any of them differs, the report is stale and the gate fails closed.

Editing a title, a body, a turn or a caveat changes the fingerprint. There is no polishing
after approval. A redraft clears the stored report, the reviewer name and the review hash
in the same statement that writes the new draft.

An unchanged draft with a valid report is **reused without a call**. Resuming an
interrupted batch costs nothing.

## Where the gate is enforced

| Path | Enforcement |
|---|---|
| `pipeline.py approve-auto` | both gates; evidence first, then audience |
| `pipeline.py narrate` | fresh passing report, or a recorded override |
| `pipeline.py publish` | re-checked, because a story can be narrated and then edited |
| `pipeline.py produce-auto` | inherits `approve_auto` |
| `experiments/full-run/run_all_shows.py` | records the decision per show and prints every show that is not approved |
| `tools/tts/bundle_shows.py` | refuses to render a transcript without a fresh passing report |

Legacy rows predating 2026-09-22 have `audience_report = NULL`. They are **not** approved
for narration; a missing field does not satisfy the gate. The migration policy is to
re-review them, or to record an override.

`override-audience STORY_ID --reviewer NAME --reason "..."` lets a named person ship
without a passing review, on the record, with a reason of at least twenty characters. It
exists so an urgent correction is possible when the reviewer is down. It is not a way to
skip the gate quietly, and it is stored on the story.

## Cost

| Event | Provider calls |
|---|---|
| First review of a draft | 1 (`audience`) |
| Re-check of an unchanged draft | 0 |
| One audience-driven repair round | 1 writer + 1 review |
| Forced re-review (`--force`) | 1 |

Every call is reserved through `reserve_call` **before** it is made, so failures count too,
and all of it sits inside the same `LILT_MAX_PROVIDER_CALLS_PER_DAY` cap as generation.
Repair rounds are capped by `LILT_AUDIENCE_REPAIRS`, default `1`.

Budgeting a full sixteen-show batch: 16 generations, up to 16 verifications, 16 reviews,
plus one repair round for each show that fails. A batch where half the shows need one
repair round costs roughly 16 + 16 + 8 + 8 = 48 writer-and-review calls on top of
verification. The default cap of 12 per day is a single-episode cap; a batch run needs the
operator to raise it deliberately for that run, exactly as
`experiments/full-run/run_all_shows.py` already documents.
