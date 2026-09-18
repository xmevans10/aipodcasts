# Zwicky: full-stack launch milestones

Planning baseline: 17 September 2026. This plan supersedes the fixed six-week engineering sequence in LAUNCH.md; that document remains the positioning and marketing reference. Estimates are working ranges for one focused builder with an available editorial/product owner, not deadlines. Allow roughly 7–11 weeks to a free public release, including overlapping work and a two-week beta. Apple review, credentials and editorial turnaround can extend that range.

## Release decision

Ship an English-language iPhone app with a finite weekday edition, four original fictional presenters, reliable listening, transcripts and source attribution. Launch free; ship paid archive/offline value once validated. Start at one reviewed episode per weekday, increasing toward three only when production capacity supports it. No forced account, ads, social feed, generated-on-demand episodes or Android in version 1.

Hosts: Mira Vale (space), Clara Rowan (nature), Elias Reed (mind/technology), Theo Mercer (Earth). These are fictional synthetic presenters, not researchers with invented qualifications. One assigned voice per episode; synthesize once and distribute to many listeners.

## What exists today

- SwiftUI onboarding, Today, Discover, host selection, article/source pages, player and Library. Recent work adds queue ordering/autoplay, local listening state, resume for production audio and completion states. Runtime verification remains outstanding.
- Python CLI for PLOS discovery, licensed XML import, evidence selection, structured drafts, explicit editorial approval, narration, publication and withdrawal. SQLite and local audio storage; simple read-only HTTP service.
- Deterministic backend checks and one-paper evidence comparison. Compact evidence saves estimated input tokens; broader quality evaluation and actual API usage measurement remain outstanding.
- No deployed service, live provider-generated episode, production voice configuration, signed release, billing backend or complete editorial console. Demo speech is not ElevenLabs audio.

## Architecture to build toward

SwiftUI app → versioned HTTPS API → managed PostgreSQL for catalog, editions, publication history and jobs. Audio lives in private object storage behind controlled delivery/CDN. A separate Python worker runs ingestion, drafting and TTS; a small authenticated internal editorial console handles review, approval, publishing and corrections. Retain the useful existing pipeline logic rather than rewriting it wholesale. A database-backed job queue is sufficient initially; no microservices or separate queue cluster required.

Staging and production have separate secrets, data and storage. CI runs tests/builds; deployments support migrations, rollback and restore. End-user accounts remain out of scope for the free release; internal editors require authenticated access. Provider keys never enter the app.

## Milestones at a glance

| Milestone | Rough effort | Dependency | Demonstrable outcome |
|---|---|---|---|
| M0 — Release foundations | 2–3 days plus external setup | None | Signed device build, scoped backlog, service/rights decisions |
| M1 — Real episode end to end | 4–7 days | Provider access from M0 | One reviewed paper becomes licensed audio playing on iPhone |
| M2 — Production backend and editorial desk | 7–12 days | M0; integrates M1 | Secure staging, repeatable publication and correction workflow |
| M3 — Launch-quality iPhone experience | 7–12 days | Starts after M0; real audio from M1/API from M2 | Complete listening journey survives real-world failures |
| M4 — Content operation and closed beta | 10–14 calendar days | M1–M3 | Two weeks of real listening and sustainable publishing |
| M5 — Store submission and public release | 3–5 working days plus review | M4 gate | Approved, supported free public app |
| M6 — Plus and paid launch | 7–12 days plus review | M4 demand evidence; normally after M5 | Working archive/offline subscription with verified access |

Critical path: M0 → M1 → M2/M3 integration → M4 → M5. M2 and M3 can proceed in separate work areas once their API contract is agreed. M6 is optional for the first public release; if paid launch is required on day one, it becomes a dependency of M4 and M5.

## M0 — Release foundations

Work: inventory the implementation; choose minimum supported iOS/device matrix; settle release scope; check app name/domain availability; configure business-owned Apple Developer/App Store Connect access and signing. Record hosting region, provider access, commercial voice permissions, source policy, editorial owner and spending limits. Define API/episode schema and publication states. Create a release checklist and CI foundation. Move arbitrary feed configuration and demos behind development configuration for release builds.

Gate: a signed build runs on a physical iPhone; account/credential blockers have explicit owners; the release scope and contract are documented. No unverified model ID or voice license is treated as production-ready.

**Dispatch prompt**

> Work in /Users/xanderevans/Documents/ScienceBreak. Implement M0 from docs/IMPLEMENTATION-PLAN.md. First inspect applicable AGENTS.md, ios/project.yml, README.md and docs/OPERATIONS.md; verify existing behavior before changing it. Produce a concise release backlog and app/API contract, add suitable CI, and prepare development/staging/production configuration and signing. Keep secrets out of source and output. Validate a build; install on a physical device only when available and authorized. Record external account, naming and voice-rights dependencies with owners rather than claiming them solved. Do not purchase services or publish. Return changed files, checks, gate status and precise blockers. Do not spawn further agents unless authorized.

## M1 — A real episode, source to headphones

Work: configure an available, inexpensive writing model; preserve the requested Luna preference only if it is actually available through the production API. Use the existing evidence packet to write an engaging podcast: hook/headline, paper title and authors, explanation, meaningful numbers, limitations and source credit. Review against the complete paper; generate with licensed ElevenLabs TTS and check pronunciation. Benchmark full versus slim evidence on at least 20 varied papers, including long papers and ones dependent on figures/tables. Fall back to fuller evidence or manual review when material is missing. Record actual input/output tokens, provider cost, editorial minutes and audio cost; do not extrapolate the one-paper estimate as a universal saving.

Gate: one complete reviewed episode plays on a physical device; representative evaluation has no unresolved material omissions in approved scripts, and documents failure/fallback cases. No automatic publication based on quote matching alone.

**Dispatch prompt**

> Implement M1 in /Users/xanderevans/Documents/ScienceBreak. Read backend/pipeline.py, evidence.py, podcast.py, backend/evals and docs/CONTENT-EFFICIENCY.md. Preserve explicit human editorial approval. Wire a real provider run if credentials and spending authorization are available; otherwise finish the integration and identify the exact blocked command. Verify production model availability instead of assuming the Codex Luna name is an API model. Build a varied full-versus-slim evaluation set, include difficult evidence, log actual token/cost usage, and add a conservative fallback for insufficient evidence. Prepare an engaging attributed script and licensed TTS episode for human review. Validate pipeline tests and source-to-device playback where possible. Report measured results separately from estimates; never claim provider output or editorial approval you did not obtain.

## M2 — Production backend and editorial desk

Work: move serving to a production Python ASGI service, managed PostgreSQL and object storage. Add migrations, stable episode IDs/versioning, editions, archive pagination, health checks and a documented API contract. Run retryable jobs with idempotency, bounded retries and safe handling of ambiguous paid calls. Add authenticated editor views for source/evidence/script comparison, pronunciation/audio preview, revision history, approval and scheduled publishing. Corrections must withdraw or replace an episode, invalidate delivery caches and expose notices to clients. Add secret management, log redaction, rate limits, backups, restore drills, failure alerts and cost ceilings. Expand sources only when rights are explicit and editorial breadth warrants it.

Gate: staging publishes, revises and withdraws an episode; unauthorized publication fails; retrying a job does not duplicate paid work/publication; restore and rollback are demonstrated. No infrastructure purchase assumed by the plan.

**Dispatch prompt**

> Implement M2 in /Users/xanderevans/Documents/ScienceBreak using the agreed API contract. Reuse pipeline logic; isolate API, worker and internal editor access. Build migrations, PostgreSQL job/publication persistence, object-storage integration and a minimal secure editorial console. Preserve approval hashes/audit history and separate draft content from public routes. Cover job retries, duplicate requests, failed provider calls, rights rejection, authorization and corrections with targeted integration tests. Add deploy configuration, health/metrics, backup/restore and rollback instructions. Keep secrets server-side; do not expose the current stdlib server as the public production edge. Deploy only within authorized infrastructure. Return a reviewable staging flow, operating instructions and unresolved gates.

## M3 — Launch-quality iPhone experience

Work: finish the queue/player/Library experience and full-name host presentation; improve loading/error/empty states, Dynamic Type and VoiceOver. Add persistent catalog/story storage so saved items survive feed rotation; synchronize revisions/withdrawals. Harden streaming, retry, seeking, resume, interruptions, lock-screen metadata/controls, Bluetooth/headphone changes and sleep. Use real duration metadata. Add stable story sharing links, correction/report links and clear synthetic-host disclosures. Remove nonfunctional purchase/coming-soon controls from the release experience. Instrument only the minimal approved diagnostic/product events with documented retention. Offline downloads belong to M6; graceful offline behavior belongs here.

Gate: onboard → discover → listen → queue → interrupt → resume → save → reopen works on physical devices; bad networks, missing audio and withdrawn stories have correct states. No launch-blocking crashes, inaccessible critical controls or misleading paid features.

**Dispatch prompt**

> Implement M3 in /Users/xanderevans/Documents/ScienceBreak. Inspect existing SwiftUI screens, Player.swift and ListeningState.swift before adding new structures. Complete the core journey with persistent feed/story storage, correction handling and production audio reliability. Integrate the agreed API; keep the distinctive Zwicky visual language and fictional full-name hosts. Test queue/resume across lifecycle events, feed rotation, audio errors and withdrawals; audit small screens, Dynamic Type and VoiceOver. Update Now Playing and interruption/routing behavior. Do not launch the simulator without renewed authorization: the user asked to keep it shut down. Build and use an available physical device when authorized; clearly separate compile checks from runtime validation. Avoid placeholder paid features and avoid a frontend rewrite. Return evidence for each release gate and remaining device checks.

## M4 — Content operation and closed beta

Work: curate at least 15 launch-ready episodes across the supported beats; exercise the pipeline on 30 editorially reviewed episodes, revising defects before release. Establish daily selection/review/audio-QA ownership, corrections SLA and a one-week publication buffer. Recruit 20–30 target walkers/commuters and observe two weeks of usage through TestFlight. Run core-device, poor-network, installation/upgrade and deletion tests. Capture playback success, first-story completion, week-one returns and qualitative trust feedback. Measure real production cost per approved minute, including rejected drafts and editorial labor.

Gate: zero unresolved material science errors or critical technical defects; two weeks of sustainable cadence; clear evidence that listeners understand and return to the product. Targets (not statistical proof): 60% activation, 65% first-story completion, 25% week-one retention; document denominators and interview dropouts. If weak, fix content/onboarding before scaling acquisition. External TestFlight distribution requires Apple's beta review [1].

**Dispatch prompt**

> Execute M4 preparation in /Users/xanderevans/Documents/ScienceBreak. Assemble the content readiness checklist, representative device/network test matrix, beta feedback flow and minimal measurement definitions. Prepare a signed TestFlight candidate when credentials allow, and draft tester instructions and recruitment copy. Do not send invitations/messages without explicit authorization. Track real cohort denominators, editorial defects, listening failures and per-episode costs; do not fabricate retention or compress a two-week observation period into a tool run. Work with the designated human editor for signoff. Fix reproducible launch blockers, report observed gate status, and recommend release or a focused iteration based on evidence.

## M5 — App Store submission and public release

Work: production deployment and restore/rollback check; final device regression; App Store screenshots from the release build; accurate listing, age rating, content-rights answers, support/privacy/terms pages, review notes and export-compliance answers. Audit privacy manifests/required-reason APIs and App Privacy answers against actual code and SDKs. Disclose synthetic narration and editorial process. Verify any applicable business/trader details for selected storefronts. Keep backend available during review. Prepare launch-page copy, captioned story excerpts, support triage and a small voluntary tester rollout; no paid acquisition until retention supports it.

Gate: App Review approval, production health checks, live support and content buffer. Monitor first-release crashes, playback failures, editorial issues and costs daily; pause publication or distribution when necessary. Store metadata must match the binary [2]. A first release uses a controlled launch; Apple's phased-release feature is not assumed for an initial version.

**Dispatch prompt**

> Prepare M5 for Zwicky at /Users/xanderevans/Documents/ScienceBreak. Verify current Apple requirements from official documentation and inspect the actual release binary/configuration. Finish store assets, accurate metadata, privacy manifest/disclosure inventory, support/privacy/terms destinations, reviewer instructions and operational rollback checklist. Run final release/device checks and validate the live backend if deployed. List account-holder/legal inputs that cannot be inferred. Deliver a concrete submission package; submit/publish or send marketing messages only with explicit authorization. After authorized release, report actual health and support findings without claiming guaranteed Apple approval or growth.

## M6 — Zwicky Plus and paid launch

Work: validate pricing (existing $5.99/month and $39.99/year are hypotheses). Deliver a browsable premium archive and offline audio with download progress, retry, storage limits, deletion and expiration rules. Implement StoreKit products, current/updated transactions, restore and subscription management. Verify transactions on the server; handle server notifications, renewals, grace period, refunds/revocation and reconciliation. Define a tested account-free purchase/restore identity strategy; avoid adding user accounts merely for billing. Protect premium API/audio access, with a documented offline entitlement policy. If account creation is later introduced, provide in-app account deletion [3].

Gate: sandbox purchase/renewal/expiry/refund/restore tests pass on device; premium access cannot be enabled with a client flag; offline behavior survives relaunch and matches the disclosed entitlement policy. Paid features, pricing and terms are ready for review before charging.

**Dispatch prompt**

> Implement M6 in /Users/xanderevans/Documents/ScienceBreak after reviewing beta demand and pricing evidence. Build the actual archive and offline listening value, then integrate StoreKit and server-verified entitlements. Document account-free purchase binding/restore and offline expiry behavior. Test purchase cancellation, pending transactions, renewal, grace, expiration, refunds, duplicate/out-of-order notifications and reinstall/restore. Verify access enforcement on both metadata and audio delivery. Do not activate charges or publish purchase claims until all gates pass and release is authorized. Return a tested billing matrix, unit-cost assumptions and the remaining commercial configuration steps.

## Dispatch and ownership rules

Dispatch each prompt as a bounded task; providing these prompts does not dispatch agents. Give each agent this file, the latest relevant contract and the previous milestone handoff. Require a short handoff: changed files, checks actually run, gate status, blockers and next commands. No blanket “done” when device, provider or editorial checks are missing. Run M2/M3 separately only with clear file ownership and an integration owner; the same intelligence can complete them sequentially to conserve tokens.

Engineering owns implementation and verification. The founder/account holder owns business accounts, commercial commitments, spending and release authorization. A designated human editor owns scientific and audio approval. An agent can prepare these decisions and artifacts but cannot invent credentials, licenses, metrics or human signoff.

## Official release references

[1] [Apple TestFlight](https://developer.apple.com/testflight/) — external testing/review workflow.

[2] [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) — release completeness, purchases, privacy, accurate metadata and live review access. Recheck before submission.

[3] [Offering account deletion](https://developer.apple.com/support/offering-account-deletion-in-your-app) — requirements when apps support account creation.
