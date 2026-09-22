# Milestone 5 — Cloud release and App Store readiness

Prepend [`00-shared-context.md`](00-shared-context.md), then paste:

```text
Goal: remove the local Mac from the release loop. A GitHub Actions macOS runner builds, signs, and
uploads TestFlight automatically on merge to main (or on a version tag), using the ASC key already
configured (key id G3X8K8ZRNJ); internal testers are notified with release notes per build. Prepare
the App Store submission: listing copy, screenshots from the release build, privacy details, age
rating, export-compliance answers, and a support/privacy URL — all reflecting the real app
(synthetic narration and editorial process disclosed).

Constraints: no secrets in logs; signing uses the existing distribution cert and "Zwicky App Store"
profile; a failed build must not upload; version/build numbers bump automatically.

Done when: merging a change produces a processed TestFlight build with no local steps; the App Store
submission checklist is complete and a reviewer-ready build is available; checks pass.
```
