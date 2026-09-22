# Milestone 1 — Co-hosted shows shipped end to end

Prepend [`00-shared-context.md`](00-shared-context.md), then paste:

```text
Goal: Ground Truth (Ines + Dev) and Star Bros (Jax, Kai, Benny, Chase) appear in the live R2 feed
with distinct, consistent per-host voices, correct speaker attribution, and working read-along.
Choose a narration engine that is licence-clear and runs free or cheap in CI without a paid key
(candidates already surveyed in docs/VOICE-OPTIONS.md: Kokoro per-turn splice, Higgs Audio v2, Dia2,
or a free managed option). The script's evidence still comes only from the paper.

Constraints: each presenter keeps a unique, stable voice; dialogue must satisfy the existing
dialogue contract (alternating turns, exact source_title and first author in the opening, both
sign-offs, verbatim limitations, verbatim claim quotes). No impersonation, no invented quotes.

Done when: render-episodes.yml produces both co-hosted shows and publishes them to R2 alongside the
14 solo shows; the feed exposes 16 shows; each sidecar carries per-turn, word-timed transcript (so
read-along highlights each speaker) and the envelope; the iOS app plays them and read-along works;
all three checks above pass; no paid key is required.
```
