# Stage 3 — Add audience review, bounded repair, and a real release gate

Read `00-shared-context.md` and stages 1–2. Implement a review path that can catch an
accurate but incomprehensible script without diluting evidence verification.

## Goal

A draft is publishable only when the current script passes scientific checks AND audience
review. Missing, unavailable, stale or inconclusive audience review is not a pass. Make
failures useful to the writer and cheap enough to run for weekly batches.

## Design and implement

Inspect `backend/verify.py`, provider interfaces, `reserve_call`, persistent state and the
batch runner before choosing the smallest compatible design. Reuse an existing configured
provider where it can perform the task adequately. Do not assume a boolean-only verifier
can provide rich sentence-level feedback; verify its actual interface. Do not invent
probabilities or interpret an arbitrary model score as measured reader comprehension.

Keep the factual report and audience report distinguishable. Reuse shared infrastructure
where sensible, but do not let a high style score compensate for a bad evidence result.

A structured audience review should cover:
- Can a nonspecialist recover the question, method, finding and limitation after one listen?
- Which exact sentence first demands unexplained knowledge? Quote short offending spans.
- Does each essential technical term get an explanation before it is used to explain another?
- Are numbers necessary, interpretable by ear and attached to meaning? Are essential sample,
  uncertainty or comparison details retained rather than erased for a lower reading grade?
- Is the result concrete, is the title honest, and does the episode fit its show's actual beat?
- Do analogies reduce the burden? Are they scientifically bounded, optional and nonliteral?
- Are limitations understandable and nonrepetitive? Does a missing detail in our packet stay
  a packet limitation rather than an accusation about the full paper?
- Does dialogue clarify the science instead of merely alternating expert-sounding speeches?

Request a compact decision, severity-tagged issues with evidence spans, actionable repair
instructions, and a short listener-style paraphrase of the core finding/limit. Check that
this paraphrase matches the script and evidence; it is a diagnostic, not an automatic truth
oracle. Keep provider response parsing strict and handle malformed responses explicitly.

## Calibration and failure semantics

Use the stage-1 fixture set. An accurate jargon-heavy negative must fail; an inaccurate but
smooth negative must fail scientific checks; an accessible accurate positive should pass.
Include technical subjects explained well so the gate does not learn “reject difficult
science.” Assess disagreements manually against the contract. Choose documented thresholds
from examples rather than declaring an untested number like “grade 8” to be a release bar.

Use deterministic metrics as supporting diagnostics only. Do not add a paid service or a
large readability package for a syllable counter. Avoid overfitting a blacklist to the
current sixteen scripts.

- Provider missing/error/timeout, malformed response, refused review and exhausted budget
  must leave an explicit pending/abstained state; never fabricate approval.
- Bind reports to the exact `draft_fingerprint`, relevant contract version and review
  version. Any title, body, turn or caveat edit invalidates applicable prior reports.
- Cache unchanged valid reviews where appropriate. Do not spend another call on a report
  just because an operator resumed a task.
- Account for reviewer and repair calls; never hide them outside generation's cost controls.
- Set a small documented maximum repair count. Give specific reviewer failures back to the
  writer, then rerun deterministic, factual and audience checks on the edited candidate.
  Do not re-roll reviewers until the same unchanged draft happens to pass.
- Preserve the last known-good approved/live episode when a replacement fails.

## Integrate every release path

Trace operator CLI, automated approval, batch export, narration, manual render workflow,
weekly workflow and publisher. Enforce equivalent approval requirements at their boundaries
without duplicating incompatible logic. Legacy approval records must have an explicit
migration/review policy; missing new fields must not silently satisfy the new gate.

A batch failure must be visible. If a candidate is rejected and another paper is considered,
that decision must respect show fit and budgets. Do not partially overwrite a live catalog
or advertise full coverage after quietly skipping a failed show. Separate renderable,
approved and published states in artifacts.

## Acceptance

Meaningful offline tests cover the provider failure matrix, exact-version/hash freshness,
repair success/exhaustion, cost caps, both script formats, and each reachable publish gate.
A small configured live pilot includes one accessible solo, one difficult solo and a
co-hosted show. Read their outputs yourself and document disagreements instead of trusting
a green badge. Do not expand to an unbounded benchmark.

Done when known bad examples are blocked, good examples can pass, explanations for rejection
are actionable, missing review fails closed, approved edits cannot reuse stale reports, and
required tests pass. Document the incremental call cost and operational failure behavior.
