# Zwicky product roadmap and launch gates

Planning baseline: **30 September 2026**. Based on the [content-flow audit](CONTENT-FLOW-AUDIT.md), live feed and Actions evidence, rather than the older demo-era inventory. This replaces `IMPLEMENTATION-PLAN.md` as the current sequencing document; `LAUNCH.md` remains useful for positioning and draft marketing copy.

**Public launch decision: still gated; content recovery is deployed.** The catalog now contains six episodes, including two new releases on 30 September. Independent public health checks pass. The unpublished inventory is being regenerated under the stricter personality and audience review; earlier approvals are stale and do not count toward the one-week buffer. Signed build 9 has successfully processed in internal TestFlight. External TestFlight and public launch follow source/audio review, real-device QA and a two-week listener cohort.

## Product promise and scope

For English-speaking curious walkers and commuters: a short, understandable science episode that works on the first tap, offers a useful next listen, and lets the listener inspect the source and uncertainty. Hosts are fictional synthetic presenters. Success means listeners understand what they heard and voluntarily return.

Launch free on iPhone, iOS 17+. Preserve the current sixteen-show design, but promote only shows with approved playable inventory. Support first play, discovery/following, queue/resume, saved episodes, readable transcripts, sources and browser sharing. Keep two episodes per day as the current operational target; do not advertise an exact 08:00 release until scheduling performance supports it. Any reduction in cadence must be an explicit product decision reflected in copy and operations.

Defer subscriptions, paid offline downloads, accounts, social feeds, Android, multilingual episodes and on-demand generation. Runtime resilience and honest unavailable states belong in the free launch; paid functionality does not.

## Sequence and effort

Effort estimates are working days for one builder with an available founder/editor. They are planning ranges, not commitments or observed completion. Budget approximately 5–7 calendar weeks including a genuine two-week beta; review, domain/account setup and content remediation can extend this. Sequence work in one agent unless separately authorized.

| Stage | Effort | Depends on | Product outcome | Exit gate |
|---|---|---|---|---|
| R0 Restore releases | 1–2 days | Existing infrastructure | New approved episodes reach the app again | Current-date release verified in public feed and on iPhone; no feed reset or weakened reviews |
| R1 Make content operation reliable | 4–7 days | R0 | Sustainable, recoverable content supply | At least 14 eligible unpublished slots; observed seven-day cadence; replenishment, alerts and correction drill |
| R2 Complete the listener journey | 4–7 days | R0; R1 contract | First play and continued listening survive failures | Core journey passes device/network/accessibility matrix; every promoted show is playable |
| R3 Prepare external beta | 2–4 days | R1/R2 essentials | Installable, supported free TestFlight build | Signed build, external beta review, accurate privacy/support setup, reviewed launch catalog |
| R4 Validate with listeners | 14 calendar days | R3 | Evidence of understanding and a repeat use occasion | Cohort gates below; resolve science/playback defects and interview dropouts |
| R5 Submit and release | 2–4 days + Apple review | R4 | Supported free public app | App Review approval, live production checks, content buffer and rollback owner |
| R6 Improve retention and test paid value | After launch evidence | Stable R5 | Better recommendations and validated offline/archive value | Measured demand; paid access and purchase lifecycle proven before charging |

Critical path: repair publication → restore usable inventory and safe delivery → prove real-device first play → signed external beta → two weeks of observation → public submission. Infrastructure and product improvements are scoped around that path.

## Executable backlog

Owners: **Engineering** implements and verifies; **Editorial** owns source policy, scientific/listening review and correction decisions; **Founder** owns accounts, commercial choices, release and recruitment. One person may fill multiple roles, but each release needs named ownership. Audit IDs link each item to evidence.

| Item | Stage / priority | Owner | Work and acceptance criterion |
|---|---|---|---|
| L01 Publishing recovery | R0 / P0 | Engineering | Deploy tested C01 header/diagnostic fix. Fresh release exposes the intended two IDs; audio, sidecar, share page and iPhone playback pass. Recovery must append to the archive. |
| L02 Salvage strict approvals | R0 / P0 | Engineering | Repair C02 discovery to download available completed-run artifacts regardless of overall job conclusion. Invalid/missing artifacts are diagnosed; strict per-script approval remains mandatory. Regression: 11-approved/5-withheld batch contributes only eligible approved scripts. |
| L03 Inventory and replenishment | R1 / P1 | Engineering + Editorial | Ledger/dashboard reports approved unpublished count, age, evidence tier and per-show coverage. Maintain 14 slots plus generation headroom at two/day; alert below seven slots. Replenish low inventory using bounded targeted runs and alternatives for rejected papers. |
| L04 Production origin | R1 / P1 | Founder + Engineering | Configure owned custom domain and staging origin; update app/publisher/verification consistently. Test native URLSession, AVPlayer, browser, byte ranges and cache behavior. Preserve old installed-client access during migration. C14. |
| L05 Safe publication and rollback | R1 / P1 | Engineering | Isolate live secrets, remove production wipe route, snapshot feed, serialize all writers/CAS, make asset keys immutable and validate final manifests. Failed render/upload/probe leaves prior catalog intact. Two-writer and rollback tests pass. C04–C06/C11. |
| L06 Corrections and withdrawals | R1 / P1 | Engineering + Editorial | Stable ID/revision/tombstone contract; operator withdrawal/correction, listener-visible notice and report route. Demonstrate correction and urgent withdrawal on staging across catalog, active player, saved/queued records and old links. C07/U05/U07. |
| L07 Evidence and editorial policy | R1 / P1 | Editorial + Engineering | Review abstract-only, CORE and restrictive-license handling; normalize source rights/evidence/status metadata. Keep strict release reviews and record exceptions explicitly. Sample approved beat fit and calibrate factual/audience reviewers against the audience contract. C08–C10/C16. |
| L08 Final audio quality | R1 / P1 | Editorial + Engineering | Listen to every launch episode; record pronunciation and completeness signoff. Add final audio/script provenance, corruption/silence/clipping/loudness checks and representative timing evaluation. Failures return to render/repair. C11/C12. |
| L09 Costs and secrets | R1 / P1 | Engineering + Founder | Rotate/remove credential embedded in local remote; verify log redaction. Establish persistent call/spend ledger and cache keyed to script/voice/settings; retries cannot silently exceed the agreed budget. Count rejected content and human effort. C13/C15. |
| L10 Release health | R1 / P1 | Engineering | Health reports include last publication, expected daily count, usable inventory and asset checks. Alert an identified operator on missing release, invalid feed, failed playback probe or low buffer; include a documented recovery action. C03/C14. |
| L11 Playable onboarding and discovery | R2 / P1 | Engineering + Founder | Offer playable shows/episodes, useful first recommendation and finite latest edition. Test empty feed, chosen show with no episode and returning listener. Avoid promoting a catalog that is mostly empty. U01. |
| L12 Feed and transcript resilience | R2 / P1 | Engineering | Distinguish stale catalog from offline/service errors, validate IDs/hosts/sidecars/timing bounds, show plain text and retry when read-along fails. One corrupt item cannot silently misattribute a host or erase a usable catalog. U02–U04. |
| L13 Listening and saved-state reliability | R2 / P1 | Engineering | Exercise queue, resume, sleep, completion and saved items across lifecycle, buffering, deletion and revisions. Add direct player failure/stall observation where the tests expose gaps. U05/U06. |
| L14 Accessibility and trust | R2 / P1 | Engineering + Editorial | VoiceOver order/labels, largest Dynamic Type, reduced motion, contrast and small-screen controls verified on release build. Show limitations, evidence tier/article status, synthetic narration and correction/support route. U07. |
| L15 Privacy and support | R3 / P1 | Founder + Engineering | Audit actual APIs and host logs, add required privacy-manifest declarations, accurate App Privacy responses and reachable privacy/support pages. Align delete-local-data behavior with its label; verify clean install and upgrade. U08. |
| L16 Signed release and store package | R3/R5 / P1 | Founder + Engineering | Prove existing TestFlight workflow with real scoped credentials; signing/provisioning and versioning pass. Capture release screenshots, prepare beta/store descriptions, review notes, age/content/rights and applicable business details. Remove outdated placeholder claims. |
| L17 Beta learning | R4 / P1 | Founder + Editorial | Recruit 20–30 target listeners once distribution is authorized; record first play, comprehension, completion, return and trust feedback. Use consented diaries/interviews/TestFlight feedback initially; no fabricated analytics. |
| L18 Seen episodes and reminders | R6 / P2 | Engineering | Replace date-only new marker with seen IDs/revision; followed-show relevance and opt-in reminders tested. Push is optional and follows reliable supply. U09. |
| L19 Better catalog relevance | R6 / P2 | Founder + Engineering | Tune show coverage and next-episode recommendation from beta evidence; reduce empty searches and show drought. Measure episode starts/completions rather than scroll volume. C16/U10. |
| L20 Paid value experiment | R6 / P2 | Founder + Engineering | Validate offline/archive demand and price before implementation. Deliver downloads plus server-verified StoreKit lifecycle, refunds/expiry/restore and protected premium audio before charging. No paid claims in free-release metadata. |

## Content readiness gate

Each launch episode must have an attributable primary source, actual evidence tier and rights basis, correct article/preprint status, script hash and current factual/audience reviews. Preserve the audience contract's hook-first, exact spoken paper-title policy. Material uncertainty must survive simplification.

For the first cohort, Editorial listens to the entire rendered episode and verifies claims, pronunciation, speaker consistency, limitations and the four comprehension questions. Store that disposition with script/audio hashes. Test representative solo and co-hosted episodes and difficult names/numbers. An automated pass is an aid, not evidence that a real listener understands.

Every promoted show needs a playable entry. If all sixteen are promoted, all sixteen need approved content; otherwise clearly expose the smaller available launch catalog. Maintain a week of ready inventory against the chosen cadence, with no withheld/revise scripts counted as ready. Review correction/retraction status and stale evidence before releasing buffered scripts.

## Device and failure acceptance matrix

Run on the actual signed release build. Minimum matrix: a small supported iPhone, a current iPhone, iOS 17 and the latest supported iOS available to the team; physical-device results required for AVPlayer/audio behavior. A compile or pure-logic test is insufficient.

| Journey / failure | Expected result |
|---|---|
| Clean install → choose available show → first play | Understandable onboarding; real audio starts; no empty dead end |
| Home/Browse/show → play → read → source → share | Correct episode/host/citation; link works in browser and installed app |
| Stream on Wi-Fi/cellular/poor network | Loading/buffering is visible; failures offer retry/plain transcript; no false completion |
| Seek, rate change, queue next/previous, sleep timer | Correct position, duration, order and end/sleep behavior |
| Call, unplug headphones, switch Bluetooth, lock screen | Correct pause/resume and remote metadata; no unwanted autoplay |
| Force quit/relaunch; reinstall/upgrade | Resume/saved/queue semantics match the disclosed local-storage policy |
| Launch with no network and with cached feed | Honest catalog availability; does not imply cached audio is downloaded |
| 403/404/5xx, malformed feed, wrong sidecar, expired assets | Last-good feed retained where applicable; clear service/error state; no wrong transcript |
| Correction/withdrawal while saved, queued or playing | Visible notice, preserved safe progress, correct playback stop/replacement behavior |
| Largest text/VoiceOver/reduced motion/landscape | All critical controls reachable and labeled; no clipped first-play/source actions |
| Delete local data | Exactly the disclosed fields removed; no stale player/Now Playing or leaked cache state |
| New feed revision with same-day episodes | New badge/announcement behaves correctly without repeat spam |

## Beta measurements and release decision

North-star: weekly listeners completing at least three episodes. These are proposed gates, not achieved metrics or statistical guarantees:

| Measure | Definition | Working gate |
|---|---|---|
| Activation | New installed testers starting a real episode in their first session / observed new installed testers | ≥60% |
| First-episode completion | Activated testers reaching ≥90% of first episode / activated testers with observable playback | ≥65% |
| Week-one return | Activated testers listening again on days 2–7 / activated testers with full seven-day observation | ≥25% |
| Comprehension | Interviewed listeners who can explain question, method, result and limitation after one listen | At least 8 of an initial 10; investigate each material misunderstanding |
| Use occasion | Interviewees naming a repeatable occasion / interviewed cohort | ≥10 of 20 |
| Reliability | Playback attempts with usable audio and no terminal failure / observed playback attempts | ≥99% target; all critical reproducible defects fixed |
| Editorial trust | Unresolved material science errors or misleading attribution in the release catalog | Zero |
| Sustainable operation | Publication, inventory and correction logs over the observation period | Two weeks at the disclosed cadence, within the founder's approved spend and editorial capacity |

Record denominators and missing observations. A small cohort can expose defects; it does not prove these percentages at population scale. If users cannot understand the episodes, prioritize content. If they cannot start them, fix discovery/playback. If they understand but do not return, test show relevance and the listening occasion before paid acquisition.

External TestFlight distribution requires the appropriate beta setup and review; Apple describes that process in its [TestFlight documentation](https://developer.apple.com/testflight/). Submission preparation must reflect the real binary, accurate metadata, support/privacy information and current review requirements. [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), [privacy manifest documentation](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files).

## Operational release checklist

Before external beta: identify founder/editor/operator; approve source/voice policy and spending ceiling; restore publication; validate production origin; review playable catalog and buffer; complete device journey; demonstrate correction/rollback; produce signed build and live support/privacy destinations. Never run the dev-feed wipe against production.

Before public release: complete the actual two-week cohort; resolve critical issues; verify version/build, store screenshots and descriptions; validate live assets and today's edition; confirm operator coverage and restore drill; obtain App Review approval and release authorization. Domain changes, invitations, store submission, public release and purchases remain concrete external actions, not completed checklist items.

After release: operator checks cadence, inventory, audio errors, source corrections and cost daily. On missing content, preserve the last-good catalog and investigate; on material science error, withdraw the affected episode and notify through the correction path. Review the first cohort and support findings before expanding show count, acquisition or monetization.

## Readiness evidence at this audit

| Gate | Observed status |
|---|---|
| Publishing code repair | Deployed; current-date recovery release and independent content-health jobs succeeded |
| Actual new publication | Six live episodes; today's two releases verified through public audio, sidecars and sharing |
| Latest usable batch | No eligible replacement scripts yet; [v4 replenishment](https://github.com/xmevans10/aipodcasts/actions/runs/36743990186) is running; earlier v1/v2/v3 approvals are stale |
| Backend checks | 293 passed after the character, narration and audience-review changes |
| iOS logic | 202 checks passed plus deep-link checks |
| iOS release compile | Unsigned Release build succeeded with simulator SDK; simulator not launched |
| Published assets | All four episodes: audio/sidecar/share-page 200; matching sidecar IDs; byte-range 206 |
| Device/listening QA | Not performed in this audit |
| Signed TestFlight | Build 1.0.0 (9) signed, uploaded and successfully processed by App Store Connect (app 6813660087); release notes set; external beta not distributed |
| Source/voice commercial policy, privacy/store package | Requires owner review and verification |
| Real listener outcomes | Unmeasured; cohort has not been run |

## Deployed recovery and operating instructions

Completed on 30 September: L01 publication restored; L02 consumes strictly reviewed partial artifacts; L03 exposes deduplicated inventory and buffer in preparation logs/job summaries. Production resets are blocked and Actions catalog writers share a concurrency group. Rendered script/sidecar/audio validation and prior-feed snapshots are deployed. Independent `content-health` checks run after publication and each morning; failures appear as failed Actions runs (confirm the operator's GitHub notification settings).

The app has playable first-listen fallbacks, honest cached service-error wording, validated read-along identity/timings and visible loading/retry. Newly rendered episodes retain abstract evidence metadata for source cards. Build 7 includes local-preferences/performance privacy reasons and accurate deletion wording. These improvements are compile/logic verified; physical-device behavior remains unverified.

Normal operation: run `prepare-daily-episodes.yml`; it selects/reviews existing inventory and renders at most the remaining two daily slots. Successful preparation arms `daily-episodes.yml`, which stages assets and waits until 08:00 Eastern. For an incident recovery only, dispatch `daily-episodes.yml` with `publish_now=true` to use today's prepared artifact immediately. Re-running after two releases is a no-op, not another paid render. Never relabel a historical prepared artifact as today.

For replenishment, use `full-run.yml` with `release_fresh_batch=false`. A seed Actions run can reuse approved scripts while finding alternatives for withheld shows. Batch completeness may report failure even when approved partial inventory is usable; preparation checks those approvals itself. Do not turn on entertainment overrides or lower review standards to fill a buffer.

Each catalog commit through `publish_feed.py` first saves the previous catalog under `v1/.release/feed-snapshots/<sha256>.json`; its exact key appears in the job result. A snapshot write failure blocks the feed commit. The deployed sharing-page backfill was exercised successfully and saved a snapshot of the current six-episode catalog. For rollback, stop/serialize publishers, inspect the selected snapshot and its asset availability, then restore that exact JSON to `v1/feed.json` using the operator's R2 credentials with `Cache-Control: no-cache`. Run `content-health` and device checks afterwards. This audit has verified snapshot creation, not an intentional live rollback drill.

The embedded credential was removed from the local Git remote URL; invalidating the old credential still requires its owner to revoke/rotate it. Production domain and support destinations await the founder's domain choice. CI TestFlight signing secrets/environment are not configured; the existing local signing setup successfully uploaded and processed build 9. Its stale key-file location was repaired in the ignored local configuration, without changing the key. The distributed IPA contains the privacy manifest.

At the recovery handoff, GitHub backend CI, iOS compile CI, `content-health` and snapshot/backfill runs were green. The two bounded replenishment runs produced 14/16 approvals and failed the complete-sixteen gate; Signal & Noise and Marginal Gains remain withheld. Those approvals predate personality review v4; the old inventory is now withheld pending fresh review. Native Foundation URLSession returned HTTP 200 and decoded all six episodes; this is a macOS networking probe, not iPhone playback QA. Both known physical iPhones remain unavailable.

Next: source/final-audio review, persistent cost accounting and correction/withdrawal handling; reach a full week of inventory; verify the updated beta on an available physical iPhone; configure the production domain/support pages and external TestFlight package. Public release remains gated on these checks and actual listener evidence.

## Host personality follow-up — 30 September

All 20 original characters now have distinct attitudes, conversational rhythms, emotional
range and cadence examples in [the character bible](CHARACTERS.md). Writing and Google
Gemini performance directions share these profiles. Host summaries are updated in build 9;
build 8 introduced native motion in onboarding and Home. Device listening/timing QA remains
open.

The first personality batch recorded 12/16 automated approvals, but human spot-checks
found lecture-like middle sections and off-topic metaphor bridges. Those reports cannot
release under v4. Removed the second, contradictory language-clue roster and switched
production to detailed span-based audience review while retaining separate Jev factual
verification. The [replacement batch](https://github.com/xmevans10/aipodcasts/actions/runs/36738352796)
produced zero approvals: real comprehension/beat failures were caught, but minor-only
advisories also triggered revision and early retries exhausted the call budget before
the whole roster was attempted. Review v4 explicitly permits a pass with minor
advisories; substantive failures still require repair. The [new bounded run](https://github.com/xmevans10/aipodcasts/actions/runs/36743990186)
uses one candidate per show within the existing call budget. Its scripts are not yet
counted as eligible inventory.

Narration now receives opening/body/closing context and sentence-level direction for
emphasis, pauses, questions and uncertainty. This is implemented and tested, but improved
intonation has not yet been confirmed by listening. Private Google calibration previews
await export approval after automatic approval review rejected the request.
