# Handoff prompts: next milestones

Large, goal-oriented prompts to hand to a strong coding agent (e.g. GPT 6 in Codex). Each
file is self-contained except for the shared context, which you paste once at the top.

## How to use

1. Paste [`00-shared-context.md`](00-shared-context.md) into the agent first.
2. Paste one milestone prompt from the files below.
3. Point the agent at this repo and let it verify with the checks in the shared context.

## Milestones

| # | File | Goal | Depends on |
|---|---|---|---|
| 1 | [`01-cohosted-shows.md`](01-cohosted-shows.md) | Ground Truth + Star Bros narrated and live | — |
| 2 | [`02-new-episode-notifications.md`](02-new-episode-notifications.md) | Tell listeners when episodes drop (local, then push) | — |
| 3 | [`03-audio-and-read-along.md`](03-audio-and-read-along.md) | Forced-alignment timings, pronunciation, loudness, QA gate | — |
| 4 | [`04-production-feed-access.md`](04-production-feed-access.md) | Signed audio access, feed versioning, analytics | current R2 pipeline |
| 5 | [`05-cloud-release-app-store.md`](05-cloud-release-app-store.md) | Unattended macOS CI → TestFlight; App Store ready | — |

Suggested order: **1 → 3 → 2 → 4 → 5**. Milestones 1, 3 and 5 are independent; 2 needs
nothing new; 4 builds on the pipeline that already publishes to R2.

## Current state (for orientation)

- Weekly transcripts: `.github/workflows/full-run.yml` → `experiments/full-run/latest/`.
- Render + publish: `.github/workflows/render-episodes.yml` → `tools/tts/bundle_shows.py`,
  `tools/publish_feed.py` → Cloudflare R2 (`R2_*` secrets).
- Live feed: `https://pub-e19f5de621fd4b4ea01c0465d0251407.r2.dev/v1/feed.json`.
- 14 solo shows live; co-hosted shows deferred (milestone 1).
- App defaults to the feed; read-along fetches `detailURL` sidecars.
