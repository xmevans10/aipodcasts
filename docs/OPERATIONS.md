# Engineering and editorial runbook

## Implemented architecture

SwiftUI iPhone client → HTTPS read-only JSON/audio server → SQLite publication records and local MP3 files. Operator-only Python CLI handles PLOS discovery, rights-checked XML import, OpenAI structured draft generation, evidence-quote validation, named editorial approval, ElevenLabs narration, publication and withdrawal. No API secrets or generation routes in the app. Public feed contains only published records. Audio supports HTTP ranges and is unavailable after withdrawal.

State machine: `ingested → review → approved → narrated → published`; any record may be withdrawn. Source text is stored separately from the generated draft; review records a SHA-256 of the draft. Publication checks that hash. Human approval is an actual editorial action, not automatically granted because an LLM supplied valid JSON. Exact quote matching checks provenance, not scientific entailment or completeness.

Run a single CLI operator/worker. The SQLite call-cap transaction handles budget reservation across processes, but generation jobs are not a distributed queue. Provider timeouts are ambiguous: check provider usage and local state before retrying. Calls are counted before execution, including failures. Daily cap is an attempt cap, not cost enforcement. There is no unattended scheduler installed.

## Local demo

Open `ios/ScienceBreak.xcodeproj`, select Sound Science and an iPhone simulator, Run. No API key is required. If using a real device, set your signing team and override `CODE_SIGNING_ALLOWED=YES`; the project is configured for unsigned simulator development by default.

Regenerate after source/config changes:
```
cd ios
xcodegen generate
```

Backend tests:
```
python3 -m unittest discover -s backend/tests -v
```

## A real editorial episode

From project root, export backend environment variables listed in `backend/.env.example`. Choose an available OpenAI model supporting Responses structured output; `OPENAI_MODEL` is deliberately explicit. Obtain licensed commercial ElevenLabs voice IDs for each host. The CLI reads allowlisted provider settings from backend/.env without shell execution; process environment values take precedence. Deployment paths and origin still use process environment variables. Never paste real keys into the iOS app or commit them.

```
python3 backend/pipeline.py discover
python3 backend/pipeline.py ingest 10.1371/journal.pbio.3003993 --host fern
python3 backend/pipeline.py list
python3 backend/pipeline.py draft STORY_ID
python3 backend/pipeline.py inspect STORY_ID
# Editor checks original, draft, evidence quotes and rights before this step:
python3 backend/pipeline.py approve STORY_ID --reviewer 'Editor Name'
python3 backend/pipeline.py narrate STORY_ID
# Listen to the MP3, check pronunciation and accidental omissions:
python3 backend/pipeline.py publish STORY_ID
```

The included live intake was imported on 2026-09-16 and remains unpublished in local `backend/data/`. No paid provider calls were made. Source article title: “Growth-rate coordination across the width of a leaf preserves its flatness.” The local record ID is `e94c833d4832dae56f3c`.

The first connector supports selected PLOS journals. It fetches explicit CC BY article XML, checks the requested DOI, retains authors and license URL, and imports text only. It does not republish images or assume an RSS feed grants reuse rights. It allows only PLOS’s verified corpus redirect. Other sources need separate adapters and rights decisions. A NASA informational page or open-access abstract does not make every included third-party work reusable.

## Editorial checklist

Check study date and retractions/corrections; establish whether this is research, commentary, or a preprint; verify source reuse rights and attribution. Match each substantive claim and number to the paper. Explain population/species and methods. Preserve uncertainty, correlation limits, sample limitations and the difference between observation and extrapolation. Avoid medical recommendations. Verify that the script includes the most important limitation. Review jargon and pronunciation. Hear the whole audio. Record reviewer identity. Do not publish if unsure.

For corrections, run `withdraw STORY_ID` immediately, then investigate. Current implementation keeps an audit record but has no in-place revision editor. Revisions require an explicit reviewed migration/new record; do not hand-edit a published draft. Production needs versioned correction notices, cache purge and listener-visible notices. `no-store` reduces caching in this beta; it cannot recall files a listener already obtained.

## Serving and deployment

```
export LILT_PUBLIC_ORIGIN=https://your-owned-domain.example
python3 backend/server.py
```

The server defaults to loopback on port 8787. Configure an HTTPS reverse proxy; then enter `https://your-owned-domain.example/v1/stories` in app Settings. iOS rejects plain HTTP feed/audio URLs. Dockerfile is supplied for a beta deployment, with a non-root user and `/data` persistent volume. No cloud service or domain has been provisioned.

Do not expose Python’s standard-library server directly as a production internet edge. Before public launch use a managed reverse proxy/ASGI service, request and connection limits, health monitoring, backups and restore tests. Move audio to object storage with signed URLs if premium content is introduced. Add structured error metrics without secrets or full source text. Maintain source license/retrieval records and backups. The current free feed needs no user identity; premium content requires authenticated entitlement checks.

## App Store and payments

Create an Apple Developer app record under your business; select bundle identifier and signing team. Publish real support, privacy and terms destinations. Set privacy disclosures from actual behavior. Add approved commercial voice rights and original source attribution. Fill age/content ratings accurately. Test on physical devices and submit via TestFlight before App Store release.

The Plus view is a guarded StoreKit SubscriptionStoreView integration point, not a complete paid system. Do not set `Sound ScienceSubscriptionProducts` until archive/offline functionality, Transaction.currentEntitlements, Transaction.updates, verification, server notifications, expiry/refund handling and access enforcement are implemented and tested. StoreKit supplies purchase UI/restore; it does not create your content entitlement backend. Paid rollout is explicitly blocked until this work is complete.

## Release gaps

Not yet implemented: paid entitlements; offline MP3 downloads; persistent live-feed cache; account sync; push notifications; analytics; correction UI; distributed worker scheduling; source connectors beyond PLOS; Android. Accessibility text-size/VoiceOver audit, interruptions/headphone routing and real-provider audio testing remain. No claim of App Store readiness.

## Verified references

- OpenAI native-web design guidance: https://developers.openai.com/apps-sdk/concepts/ui-guidelines
- UI kit and license: https://github.com/openai/apps-sdk-ui
- Responses structured output: https://developers.openai.com/api/docs/guides/structured-outputs
- ElevenLabs text-to-speech (text narration uses TTS, not their dubbing/localization endpoint): https://elevenlabs.io/docs/api-reference/text-to-speech/convert
- StoreKit merchandising: https://developer.apple.com/documentation/storekit/subscriptionstoreview
- PLOS reuse policy: https://journals.plos.org/plosone/s/content-license
- NASA media exclusions: https://www.nasa.gov/nasa-brand-center/images-and-media/

Consult these again before release; pricing, terms and APIs can change. Proposed prices/cost assumptions in PRODUCT.md are planning inputs, not quoted provider rates or legal advice.

## Evidence-packet update

Primary-author extraction now excludes peer-review sub-articles. Full source text is retained without the former 60,000-character truncation. The first paper was reimported with corrected attribution and 100,493 characters. Generation now uses a deterministic, section-aware evidence packet; see CONTENT-EFFICIENCY.md. Source refresh is allowed only before drafting. Thirty-four backend tests pass. The editorial sample in editorial/leaf-sample.md is assistant-authored, not a live API result, and is not published.

## Listening frontend

The app now persists queue order, current story, production-audio positions and completed stories locally. Today can queue an edition; the player and Library expose queue controls; Library separates saved, listening and finished stories. Sleep timers can be cancelled. Device-voice demos restart after relaunch because speech synthesis cannot seek. Queue restoration requires stories to be available in the loaded feed; offline feed caching is still pending. Full-name fictional presenters are shown throughout the app.

Validation: standalone listening-state checks and an unsigned simulator-SDK build. The simulator remains shut down at the user’s request; the new screens and real-audio continuation still need runtime verification.

## Sound design and direction (Eleven v3)

Effects can also be full-level stingers: an `effect_after` entry may be a dict with its own `gain_db`, fades and trailing gap, which is how Clara’s jingle now plays after her signature line rather than before the first word.

`backend/produce.py` synthesizes one directed beat at a time and caches by content hash, so retouching a line re-buys only that line. Per beat you can set `voice_settings` (v3 stability: 0.0 creative, 0.5 natural, 1.0 robust), `pause_after_seconds`, `effect_after` (a named clip from the plan's `assets` table) and `ambience` (a looping bed mixed under the speech at a given gain). Effects come from ElevenLabs sound generation (`/v1/sound-generation`); all music and effects are generated or user-supplied, never field recordings of the animals or places described, and the plan records that.

Direction runs hot on purpose: two to four tags per paragraph, written as intensity plus attitude ("[utterly delighted]", "[absolutely astonished]", "[stopping himself, firm]") rather than bare moods, with CAPS for emphasis and ellipses for breath. Narrative beats use creative stability (0.0) for range; beats carrying names, numbers or paper titles stay on natural (0.5), and each episode is split into 5-11 short beats so a bad take costs one beat.

Direction is expressed in `directed_text` only; the canonical `text` stays word-for-word identical, so transcripts, timings and the source check stay valid. A word-count assertion guards this. Creative stability (0.0) is more expressive but riskier: it slurred the dolphin's name "Bubbles" into "Bustles" in a takeaway beat, caught by `backend/evals/qa_episodes.py` and fixed by moving that beat to natural stability. v3 ignores the `speed` setting; pace comes from voice casting, ellipses and inter-beat pauses.

Also available on the current key and unused so far: text-to-dialogue (multi-speaker), music generation, voice design, forced alignment and speech-to-speech.

## Host personality configuration

`backend/hosts.py` is the single source of truth for each presenter: name, show, feed topic, beat, persona, delivery, opening style, exact sign-off, the domains their analogies may come from, what they must avoid, and the emotion palette used when directing narration. `writing_guide(host_id)` renders that profile into a block appended to the shared `PODCAST_INSTRUCTIONS`, so drafting is `shared editorial contract + one host personality` (prompt version `podcast-v2`). It also supplies the feed's topic label and the `ELEVENLABS_VOICE_*` variable name, so adding a host is one entry in one file.

Each profile ends with the rule that personality changes delivery only and never a finding, number, limitation or attribution. Drafts are checked against that: `validate_podcast` now requires the host's exact sign-off in the closing sixty words, alongside the existing headline, paper-title, first-author and verbatim-limitations checks. `python3 backend/pipeline.py hosts` prints the configured profiles.
