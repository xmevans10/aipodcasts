# Zwicky: front-end plan

Planning baseline: 18 September 2026. Scope is the iPhone client and the
newsletter surface. It assumes no new backend services and no paid provider
calls; work is validated against published-feed and unit-test fixtures. Backend milestones remain
in [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md).

## Cleanup shipped on 23 September 2026

- The app reads only the official feed. Its offline cache is tied to that
  URL, and old pinned episode copies are removed on launch.
- Feed refreshes bypass the HTTP cache, coalesce while in flight, and run when the
  app returns to the foreground. Home no longer starts a second launch request.
- Empty and offline states distinguish loading from a failed fetch. Preview voice
  and review claims have been replaced with current product copy.
- Episode sharing and private profile fields are tracked in [SOCIAL-PLAN.md](SOCIAL-PLAN.md).
- Playback updates lock-screen elapsed-time metadata every ten seconds during
  steady playback, while transport and seek changes update immediately.
- Transcript, queue, and host screens have improved VoiceOver actions and
  layout at accessibility text sizes. A physical-device pass is still needed.
- A manual GitHub Actions TestFlight workflow is available once its signing
  secrets are configured; the existing iOS build workflow checks pushes.
- Newsletter HTML is now a separate template with semantic headings and a solid
  color fallback. Staged email requires a public HTTPS audio link; Apple Mail
  and Gmail rendering still need a visual pass before delivery.

## Baseline state (18 September 2026)

The notes below record the starting point for this plan. The newer cleanup above
supersedes the feed and copy items.

- One `AudioPlayer` ([`Player.swift`](../ios/Zwicky/Player.swift)) with
  `AVAudioSession.playback` and play/pause remote commands, and Now Playing set
  to title/artist only. No interruption or route-change handling.
- Persistence is `UserDefaults`/`@AppStorage` ([`Models.swift`](../ios/Zwicky/Models.swift),
  `Library`, `ListeningState`). Saved/history/queue survive relaunch; the feed
  is not cached to disk, so a rotating or offline feed loses stories.
- Placeholder surfaces remain: a "coming soon" line on device-voice samples
  ([`DetailViews.swift:36`](../ios/Zwicky/DetailViews.swift)) and a
  StoreKit preview behind a Settings membership entry (`DetailViews.swift:314`).
- Accessibility labels exist across screens but there has been no Dynamic Type
  or VoiceOver audit.
- `scripts/run-ios-tests.sh` runs 117 pure-logic checks with `swiftc`; UI
  behaviour still needs a device. The simulator is intentionally kept shut down.

## Phases

### Phase 1 — Remove misleading surfaces
- Drop the "coming soon" promise on device-voice samples; describe the sample
  factually.
- Gate the StoreKit preview (`PlusView`, membership entry) behind `#if DEBUG`
  so release builds expose no nonfunctional purchase flow.
- Done when: the release path has no dead or misleading paid/coming-soon UI.
- Files: `DetailViews.swift`, `YouView.swift`.

### Phase 2 — Audio session and player hardening
- Observe `AVAudioSession.interruptionNotification` and resume only when the
  system says to; pause on `routeChangeNotification` when the old device
  disappears (unplug/Bluetooth drop).
- Complete Now Playing: artwork, elapsed time, duration and rate; wire
  next/previous/skip/seek and `changePlaybackPosition` to the queue.
- Sleep-timer and device-voice resume edge cases (speech synthesis cannot seek).
- Files: `Player.swift`, `ListeningState.swift`, `Immersive.swift`.
- Done when, on a device: play → incoming call → resume; unplug pauses;
  lock-screen controls all work.

### Phase 3 — Persistent catalog and offline behaviour
- Cache the last good feed to Application Support with a timestamp; load cache
  first, refresh in the background, and show an explicit stale/offline state.
- Persist resolved story bodies for saved and queued items so they survive feed
  rotation.
- Add retry affordances and a clear "offline, showing saved episodes" state.
- Files: `Models.swift`, `ZwickyApp.swift`, new cache module,
  `HomeView.swift`, `ShowViews.swift`.
- Done when: with no network, relaunch still opens and plays saved/queued items.

### Phase 4 — States and accessibility
- Loading, error and empty states for Home, Browse, Show, Hosts and Library.
- Dynamic Type and VoiceOver audit of the player, transcript and queue; keep the
  editorial hero type legible at accessibility sizes and the primary action
  reachable.
- Respect Reduce Motion for new animation (`Motion.swift`); confirm 44pt
  interaction targets.
- Files: `HomeView.swift`, `ShowViews.swift`, `HostsView.swift`, `QueueView.swift`,
  `TranscriptView.swift`, `Typography.swift`, `Motion.swift`.
- Done when: an AX5 pass clips nothing and VoiceOver can complete the core
  journey.

### Phase 5 — Trust and sharing
- Correction/report link and a listener-visible correction notice.
- Stable per-episode share links; visible synthetic-host disclosure.
- Verify source cards always show attribution and license.
- Files: `DetailViews.swift`, `Player.swift`, `Models.swift`.
- Done when: the share sheet yields a working canonical link and the correction
  path is reachable.

### Phase 6 — Newsletter front-end
- Split the HTML out of [`backend/newsletter.py`](../backend/newsletter.py) into
  a template, make the audio URL and sender configuration explicit, and add a
  dark-email-safe fallback.
- Accessibility: alt text, semantic headings, sufficient contrast; verify in
  Apple Mail and Gmail.
- Files: `backend/newsletter.py`, `backend/tests/test_newsletter.py`.
- Done when: preview and `.eml` render cleanly and the audio CTA points at a real
  hosted URL once one exists.

## Order and verification

Order: **1 → 2 → 3 → 4 → 5 → 6**. Phases 1–4 are launch-blocking and need no
backend services. Validate each phase with `./scripts/run-ios-tests.sh` for logic
and an unsigned simulator-SDK build for compilation; record device-only checks
separately and never claim runtime verification from a compile.
