# Content quality repair: implementation prompts

These prompts repair Zwicky's writing and editorial checks, then regenerate and publish
better episodes. They are implementation handoffs, not replacement episode-generation
system prompts. Creating these files does not run the work or authorize a new release.

Read [00-shared-context.md](00-shared-context.md) before each numbered prompt. Run the
prompts **in order, in one agent by default**. Finish and verify one stage before starting
the next; do not delegate automatically. A new agent should inspect the earlier stage's
commits and acceptance evidence rather than assume it was completed.

| Order | Prompt | Outcome |
|---|---|---|
| 1 | [Editorial contract and regression examples](01-editorial-contract.md) | A concrete audience standard, beat-fit policy, and representative failures to test against |
| 2 | [Generation and deterministic validation](02-generation-and-validation.md) | Solo and dialogue scripts that explain the science clearly without leaking internal instructions |
| 3 | [Audience review and bounded repair](03-audience-review-and-repair.md) | A calibrated comprehension check, separate from factual verification, enforced before publication |
| 4 | [Rewrite the latest sixteen episodes](04-rewrite-latest-episodes.md) | Source-grounded, reviewed scripts and synchronized artifacts for the entire latest batch |
| 5 | [Render, publish, and verify delivery](05-render-publish-verify.md) | Matching audio/text/timings, a verified live catalog, and honest iOS validation |

## One-task invocation

> Read `prompts/content-quality/00-shared-context.md`, then implement prompts 01–05 in
> order. Inspect current code and live state before relying on the dated handoff. Work
> in one agent, preserve unrelated changes, and make incremental commits. Complete the
> existing checks and each stage's acceptance criteria. Keep the exact spoken paper-title
> requirement unless I explicitly authorize moving it to the source card. Do not publish
> failed, stale, incomplete, or unreviewed work. Report concrete outcomes and any remaining
> blocker; distinguish code shipped, content published, and playback verified.

For a writing-system-only task, invoke stages 1–3. For a full content repair and release,
invoke stages 1–5. Stage 5 includes external publication; a review-only invocation does not.

## Important unresolved editorial decision

The existing contract requires the exact paper title in the spoken opening. That is a
real obstacle for a broad audience, but the user has **not yet selected** whether to drop
it. Default to retaining it once, after an accessible hook. The recommended alternative
is full exact citation in the source card, with first author and a natural description
spoken. Make that change only after an explicit decision, and update validators, tests,
and documentation together. Do not silently interpret a request for simpler prose as
permission to remove an attribution requirement.

## Snapshot: 2026-09-22

The latest 16 titles were improved, co-host rendering and iOS speaker labels were
implemented, and the changes were pushed through commit `b1c8f8b`. The content-quality
review then found serious script problems. The pending render was cancelled; that
release was not verified as published. These prompts describe the remaining repair.
Verify current state rather than restarting or blindly rerunning those workflows.
