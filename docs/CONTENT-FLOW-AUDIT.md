# Content flow and launch audit

Audited 30 September 2026. Repository baseline: `2856389`. Companion: [product roadmap](PRODUCT-ROADMAP.md). Findings distinguish live observations, code defects and checks still needed. This is a code/operations audit with public endpoint probes, not a completed device or human listening audit.

**Remediation update, later on 30 September:** the publishing and partial-inventory repairs are deployed. [The recovery release succeeded](https://github.com/xmevans10/aipodcasts/actions/runs/36703861437): six episodes are now live, including two dated today. [Independent content health passed](https://github.com/xmevans10/aipodcasts/actions/runs/36704837615). Replenishment reached 14/16 strict approvals, leaving 12 unpublished scripts after today's release. Production reset protection, a shared Actions writer lock, rendered-artifact validation, prior-feed snapshots and app recovery improvements are deployed. The findings below describe the original baseline; current readiness and remaining gates are recorded in the roadmap.

## Why new episodes stopped

**Confirmed immediate cause:** the new staged-asset check in `tools/publish_feed.py:verify_staged_assets` uses urllib's default user agent. The current Cloudflare public edge returns **403** to that request. It returns **200** for the same existing asset with `User-Agent: curl/8.0`, which `verify_daily_feed.py` already uses. The publisher interprets this as missing audio and stops before updating `feed.json`.

Evidence:

- [29 September failed daily release](https://github.com/xmevans10/aipodcasts/actions/runs/36609209523): `episode-9937217f36e63bdb: staged audioURL is unavailable`, inside `verify_staged_assets` during `--assets-only`. Successful uploads precede the failure; feed commit is never reached.
- Read-only probes at approximately 12:08 Madrid time on 30 September: default Python HEAD returned 403 for both `/v1/feed.json` and `/v1/audio/9937217f36e63bdb.m4a`; the same requests with the verifier header returned 200. Audio length: 2,765,159 bytes. Its last modification was 29 September.
- [Public feed](https://pub-e19f5de621fd4b4ea01c0465d0251407.r2.dev/v1/feed.json): four episodes; two dated 23 September, two dated 25 September. Feed Last-Modified: 25 September, 15:39:21 UTC. Successful preparation does not mean successful publication.
- Recent Actions history shows repeated daily release failures on 26–29 September and successful preparation jobs over those days. The 25 September daily releases succeeded.

The local repair makes the staging probe use the existing verifier header and retains bounded retries and rejection of unavailable assets. It now includes the actual HTTP/network error in its final diagnostic. Regression tests reproduce the edge rejection and prove a real 404 still blocks release. A read-only run of the repaired function successfully checked the previously blocked audio, JSON sidecar and HTML page. **The fix has not been deployed and the live feed has not been changed by this audit.** This header is a compatibility repair for the present endpoint, not a production hosting strategy.

**Independent upstream problem:** [Monday's transcript run](https://github.com/xmevans10/aipodcasts/actions/runs/36476352229) generated 11 approved episodes out of 16. Its final complete-batch gate failed, although it uploaded the transcript artifact. `scripts/prepare-daily-episodes.sh` selects only runs whose conclusion is `success`. It therefore never downloads these 11 episodes. `daily_release.select` already supports partial batches with current individual approvals, but that capability is unreachable for this run through the shell handoff. Downloaded Monday's artifact and validated it using the current Jev reviewer policy: **11/16 pass the strict partial-batch check**. The five withheld shows remain withheld.

## Actual production path

1. Discovery: `backend/autoselect.py`, `shortlist.py`, `beats.py`; OpenAlex/Crossref, allowed preprints, publicity and editorial signals.
2. Intake: `pipeline.ingest_any`; PLOS/arXiv/Europe PMC, CORE fallback, then OpenAlex abstracts. SQLite records source and drafting/review state during generation.
3. Evidence/drafting: section-aware packet, host and dialogue contracts, deterministic editorial/provenance checks, bounded draft repairs.
4. Review: `verify.py` factual checks and `audience.py` comprehension/show-fit review, bound to the script fingerprint. `run_all_shows.py` exports approved JSON/Markdown and the complete batch manifest as an Actions artifact.
5. Selection/preparation: Actions artifacts → `daily_release.py` → remaining daily slots against the R2 feed → Google Cloud narration → alignment, sound design and M4A/sidecars → prepared artifact.
6. Publication: merge existing R2 catalog, stage audio/sidecars/share pages, check public availability, wait until the release time, commit feed, verify today's releases.
7. App: fixed feed URL → `Library.refresh` → last-good disk cache → show discovery/onboarding/library → AVPlayer streaming → on-demand sidecar/read-along → local listening state and browser sharing.

The local stdlib HTTP server is a separate supported path, **not the current public app serving architecture**. A PostgreSQL/API rewrite is not a prerequisite to repair this pipeline or ship a small free beta.

## Backend and editorial findings

Priority: P0 blocks restoring releases; P1 blocks an external/public launch; P2 improves the product after essential reliability is established. Proposed owners are roles, not assigned people.

| ID | Priority | Finding and evidence | Required outcome |
|---|---|---|---|
| C01 | P0 | Default urllib staging request receives 403 for existing objects; publication stops. | Deploy the tested compatibility repair; verify one current release through the default app feed. |
| C02 | P0 | Only successful full-run jobs are downloaded; 11 strictly approved Monday scripts are stranded. | Consume completed runs with artifacts, validate every batch and script strictly, preserve failed-run reporting and withheld episodes. Missing/expired artifacts get explicit diagnostics. |
| C03 | P1 | One weekly batch can provide at most 16 episodes against a two-per-day demand of 14; Monday's yield was only 11 before duplicate exclusions. No demonstrated buffer or automatic replenishment based on usable inventory. | Track approved unpublished inventory and show coverage; maintain 14 ready slots plus replenishment headroom. Trigger bounded targeted generation before inventory falls below the threshold. |
| C04 | P1 | `full-run.yml` fresh-release mode wipes the app feed and deletes audio/sidecars **before** generation/review/render succeed. It targets the app's live default origin. `wipe_app` leaves listening HTML pages behind. | Separate staging and production; disable production reset; require a recoverable feed snapshot and staged replacement before any catalog switch. Test old sharing URLs after withdrawal. |
| C05 | P1 | Publishers use read/merge/write without conditional update. Daily jobs serialize in their own group, but full-run/retitle/share-page tools can write the same feed independently. | One production publication lock or ETag compare-and-swap across every writer; conflicting writers must retry without losing episodes. |
| C06 | P1 | Episode key hashes show/date/DOI, not script or render version. Republishing a revision on a new date changes IDs; `merge_feed` removes older same-host/DOI editions. Re-rendering the same key can overwrite cached assets. | Stable episode identity with explicit revision and immutable audio/sidecar keys; retain listening progress and visible correction history. |
| C07 | P1 | Legacy SQLite withdrawal is not a complete R2/app correction flow. Cached/player content and old public links have no versioned withdrawal contract. | Production withdrawal/correction command, tombstones, cache rules, current-player handling and a drill that covers app, sidecar, audio and share page. |
| C08 | P1 | Fresh-release entertainment mode accepts a fresh audience `revise` verdict, including `weak` beat fit; implemented in approval, batch check and narration. Normal daily preparation does not set this override. | Make production review policy explicit and auditable. Default external releases to strict passing factual and audience reviews; surface any exceptional editorial override to the owner. Do not weaken gates to fill slots. |
| C09 | P1 | All 11 approved Monday artifacts use abstract-only evidence. Five carry `cc-by-nc-nd` metadata. One live episode also carries that string. This is a source-use/policy review question, not proof that an original summary is unlawful. CORE full-text fallback does not enforce the exact CC BY gate used by PLOS/JATS, and can label short-full-text/abstract input as full evidence. | Record actual evidence used, normalized rights basis and article status. Review CORE full-text eligibility separately; correct tier classification. Get an explicit commercial source policy decision before launch. |
| C10 | P1 | `story_for` drops evidence tier, evidence note, retrieval date, journal/status and review provenance from the public story. Listeners see a license string but cannot reliably distinguish abstract-based summaries or preprints. | Publish useful source/evidence/status metadata and honest client disclosures; retain review/source snapshots internally. |
| C11 | P1 | Script approvals are hash-bound before TTS, but the final publisher accepts rendered files without checking their originating approval chain. Public preflight checks HTTP success only; it does not check sidecar identity, timing validity or audio content. | Bind rendered manifest to reviewed script and audio hashes; validate sidecar schema/identity/timings and positive playable media before publication. |
| C12 | P1 | No demonstrated final-listening or speech-to-script QA gate on the daily Google Cloud path. The waveform aligner is a heuristic, not verified word-level forced alignment. | Human listening signoff for the initial catalog; pronunciation, missing/extra speech, clipping, silence and loudness QA. Measure alignment on representative solo/dialogue episodes before claiming precise word timing. |
| C13 | P1 | Provider-call cap uses local SQLite. Actions checkouts do not establish a cross-run daily ledger. Google Cloud retries and cost estimates are not a persistent pre-spend budget/reservation. | Persistent daily spend/call accounting across runs, idempotent render cache, bounded retries and operator-visible cost per approved minute including rejects. |
| C14 | P1 | Current default origin is `r2.dev`; scheduling uses Actions and can be delayed. Observed release jobs run well after the nominal morning time. | Custom production domain, native-client probes and an independent missing-release alert. Promise a morning edition until an exact-time service has been demonstrated. |
| C15 | P1 | Local Git remote configuration contains an embedded credential. Its value is omitted here. | Rotate the exposed credential, remove it from the remote URL, and use a credential helper/scoped automation credentials. Audit log redaction. |
| C16 | P2 | Daily selection traverses newest batches and manifest order, without a coverage/follow-demand fairness policy. Retractions can be rejected at discovery but there is no demonstrated ongoing published-catalog recheck. | Track show drought, paper reuse and age; rebalance selection and periodically recheck live sources for corrections/retractions. |

Cloudflare documents `r2.dev` as a rate-limited development endpoint and directs production traffic to a custom domain. This corroborates C14; the precise rule producing the observed 403 is not established by the probes. [Cloudflare public bucket documentation](https://developers.cloudflare.com/r2/buckets/public-buckets/).

## User-facing content findings

| ID | Priority | Finding and evidence | Required outcome |
|---|---|---|---|
| U01 | P1 | Sixteen shows are statically offered, while the live feed has four episodes across four hosts (`ada`, `atlas`, `fern`, `nova`). Most show pages have no episodes. | Make every promoted/onboarding show playable or label/hide unavailable shows. First play must use a currently available episode and a useful recommendation. |
| U02 | P1 | A successful fetch sets `feedCachedAt` to now, even when the server catalog is old. Cache refresh failures set `isOffline` for server/schema errors too; Home says "You're offline". | Distinguish network failure, service failure and stale publication. Expose last publication separately from last fetch; retry without blaming the listener's connection. |
| U03 | P1 | Feed is decoded as one `[Story]`; one invalid entry rejects the whole refresh. Unknown hosts fall back to the first host/show. Sidecar loads do not compare decoded story identity to the requested episode or validate timing bounds. | Validate feed/schema/IDs/hosts before publish and defensively on client; reject wrong sidecars and preserve the last valid catalog. Prevent incorrect host attribution. |
| U04 | P1 | Sidecars live only in an in-memory map. Fetch failure logs an error and read-along disappears; there is no explicit retry/error state. | Show plain transcript immediately, expose read-along loading/retry, persist validated sidecars if offline reading is promised. |
| U05 | P1 | Saved/history/queue persist IDs locally, but visible episode lists resolve against the current feed. Replacement/removal can make previously saved episodes disappear. Active AVPlayer also holds an old Story separately. | Define archive retention and correction behavior. Keep retained saved metadata and resume positions; explain unavailable/withdrawn episodes and stop unsafe playback. |
| U06 | P1 | Player implements resume, interruptions, route changes and remote controls, but failed-item handling is largely in the periodic time callback. These runtime paths have not been exercised in this audit. | Device-test bad URLs, stalled streams, retry, seeking while buffering, calls, Bluetooth, lock screen, background resume, sleep and queue completion; observe item failure independently of playback ticks. |
| U07 | P1 | Sources/caveats and synthetic-host disclosures exist. There is no visible episode correction/report destination or distinct evidence-tier/preprint field. | Add a report/correction route and concise evidence/status disclosure on episode and source views. Keep exact-title spoken citation policy unchanged unless explicitly approved. |
| U08 | P1 | Privacy UI is local prose. No tracked `PrivacyInfo.xcprivacy` was found. Delete-local-data clears listening/saved/history but retains profile fields and other preferences despite the broader wording. No production support destination is shown in Settings. | Inventory required-reason APIs and shipping binary; provide accurate privacy/support destinations and a deletion action whose scope matches its label. Do not infer manifest or App Store compliance from a successful build. |
| U09 | P2 | New-episode acknowledgement uses a maximum date, not episode IDs, and announcement is limited to once per launch. Same-day additions are missed after acknowledgement. This is an in-app sheet, not push delivery. | Use a feed revision/seen-ID cursor, follow-aware badges, and optional notifications only after cadence is reliable. |
| U10 | P2 | App uses local OSLog/signposts, with no product analytics SDK. Activation/retention targets in old documents are hypotheses, not measured outcomes. | Establish a consented beta measurement method with denominators; use TestFlight feedback/interviews before adding telemetry. |

Positive foundations to preserve: HTTPS default feed, last-good atomic disk cache, local account-free listening state, source and caveat views, escaped public listening pages, sharing/deep links, production AVPlayer, synthetic-host disclosure, and DEBUG-only Plus entry. There is no reason to add accounts, paid entitlements or a general backend rewrite to the free launch critical path.

## Validation and limits

- Backend: **278 passed**, including two new staged-asset regressions. The first sandboxed run had one loopback-bind permission failure; the same full suite passed with loopback access.
- iOS pure logic: **194 checks passed**, plus deep-link checks. These do not verify rendered SwiftUI or AVPlayer runtime.
- The previously failing staged episode's audio, sidecar and listening page all pass the repaired preflight against the live public endpoint. No uploads or feed mutations were performed.
- Strict partial-batch check of Monday's downloaded Actions artifact: **11/16**. This verifies current recorded gates, not human scientific/listening approval.
- All four published episodes: audio/sidecar/share-page HEAD returned 200; sidecar IDs matched feed IDs; audio range requests returned 206 for bytes 0–31. Sidecar durations were 205.28–215.20 seconds. A parallel urllib probe encountered a transient TLS EOF; the subsequent curl audit completed successfully. This does not establish native-device streaming reliability.
- Unsigned iOS Release build with simulator SDK: **BUILD SUCCEEDED**. The simulator was not launched.
- No simulator was launched. No physical-device walkthrough, full-audio listening, new paid generation, TestFlight upload, App Store submission, DNS change, invitation or marketing message occurred.

## Immediate recovery procedure

1. Review and deploy the C01 repair through normal main-branch CI. Keep the prior feed snapshot and do not run fresh-release reset.
2. Repair C02's artifact discovery and strictly validate the downloaded partial batch. Record individual approval/provenance; withheld scripts never enter selection.
3. Select two eligible current episodes with the existing daily allowance and origin checks. Stage/validate assets; commit and verify the public feed using the same publication date. A historical prepared artifact must not simply be relabeled today.
4. Confirm the updated feed and both episodes on an actual iPhone, including playback and read-along. If verification fails, restore the previous catalog while investigating the origin/client failure.
5. Observe the following releases and usable inventory. A green preparation job or two existing date labels alone is insufficient health evidence.

## Personality follow-up — 30 September

Two additional causes of flat delivery were found: a second style roster appended after
the character brief, with contradictory pacing/joke rules, and one generic Google TTS
performance prompt for every host. Both are replaced by directions derived from the
20 current profiles in [CHARACTERS.md](CHARACTERS.md). Reactions, natural imperfections,
modest vulnerability, brief earned chuckles and thoughtful breaths are permitted.

A spot-check of the first personality batch found lecture prose and unrelated pulsar,
mathematical-network and fuel-cell stories despite boolean audience approvals. Review v4
examines the middle explanation and literal beat using detailed span-based audience
feedback; factual Jev verification remains independent. Earlier approvals are stale.
The detailed-review replacement batch yielded zero eligible scripts. Minor-only revision
decisions and early retries also consumed its call budget. Review v4 clarifies that
minor advisories may pass; major/blocker comprehension, personality, honesty and beat
failures remain release gates. The subsequent v4 run used one candidate per show and produced 3/16 strict approvals; its complete-batch gate failed. Three full private QA recordings passed script/timing/container checks. The seeded follow-up failed; its extra automated approval was a non-episode withholding note, now blocked at the release boundary. The prior three valid scripts remain eligible; the one-week buffer remains below target.

Google narration now carries passage position and directions for meaningful emphasis,
pauses and uncertainty. Renderer checks preserve the supplied words and cover single-
and multi-passage episodes. Perceived improvement remains unverified until audio QA.

Two further release defects were repaired: daily preparation still demanded the former Jev audience reviewer, and SMC checking reactions were matched by show topic rather than paper identity. Preparation now accepts the current detailed audience reports; SMC checks require an exact DOI link in the reaction article and include the actual commentary. Claims and audience checks remain independent. Build 1.0.0 (10) has processed in TestFlight; final checks passed (302 backend tests, 202 iOS logic checks plus deep links, unsigned Release compilation). Both known iPhones remained unavailable.

The empty-show investigation identified three more structural defects: substring keyword matches (bee/been, rest/breast, star/start), ownership by first query rather than strongest beat, and rejected-paper exclusions applied after a one-candidate quota. These are corrected, with regression coverage. Publication now prioritises shows with the fewest public episodes; the actual dry-run selects Gradient and Layer by Layer. A 90-day bootstrap run is filling the remaining launch-show gaps. Four of sixteen shows currently have public episodes, so the full catalog is not ready to promise at launch. Latest checks: 307 backend tests, 202 iOS checks plus deep links, successful Release compilation.

## 1 October release update

The live feed now has eight episodes across six shows. Gradient and Layer by Layer published successfully; latest independent health run `36833259337` passed. Backfill `36831940287` yields six strict approvals, including Webwork, with four unpublished after today's release. Star Stuff remains withheld. A bounded, evidence-guided factual rewrite now complements targeted audience repair; fresh factual and audience checks remain mandatory. Required checks pass: 313 backend tests, 202 iOS checks plus deep links, Release compilation. Build 11 carries the revised textured olive/cream Z icon; physical-device and subjective listening QA remain open.
