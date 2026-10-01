# Integrations and API keys

One place for every external credential and what it unlocks. Nothing here is
committed; values live in `backend/.env` (git-ignored) or the process environment.
Run the doctor to see what is currently configured (presence only, no network, no
secret values):

```
python3 backend/pipeline.py doctor
```

## Active production route — 1 October 2026

The deployed Actions pipeline writes with OpenAI `gpt-5.6-luna` at low reasoning effort, uses the same configured OpenAI model for detailed audience review, verifies facts with TypeSafe/Jev, and narrates with Google Cloud `gemini-2.5-flash-tts` through GitHub workload identity. R2 serves the feed/audio. The optional `pipeline narrate` providers below are separate paths; ElevenLabs is not the current production narrator. App icon edits in this session used the built-in image tool, not the application's OpenAI key.

| Service | Active purpose | Billing visibility |
|---|---|---|
| OpenAI | Writer and audience review | Organization billing dashboard; organization Costs API requires admin access, not just the application key |
| TypeSafe/Jev | Factual verification | Signed-in TypeSafe billing console; inference-key presence is not a credit balance |
| Google Cloud | Production narration | Cloud Billing dashboard/export; service-account synthesis permission does not establish billing visibility |
| DeepSeek | Optional verifier fallback | Read-only `/user/balance` endpoint; not the writer |
| ElevenLabs | Optional alternate narration | Subscription endpoint; local key authentication needs repair before using this path |
| OpenAlex / CORE | Research discovery/evidence | Separate account/rate limits; do not infer their quotas from generation balances |
| Cloudflare R2 | Feed/audio storage and delivery | Cloudflare billing dashboard; separate from model credits |

The 96-call cap applies to the full-run job's local provider ledger. It is not a persistent account-wide dollar ceiling across Actions runs. The renderer emits an audio-only estimate; retries, text input, writing and factual/audience reviews require actual provider billing for a total spend figure.

## The short list (what to hand over)

| # | Credential | What it unlocks | Required now? |
|---|---|---|---|
| 1 | `OPENAI_API_KEY` (+ `OPENAI_MODEL`) | Drafts scripts with the Zwicky writing contract; icon/OG image generation | Yes, for real drafting |
| 2 | `ELEVENLABS_API_KEY` + one `ELEVENLABS_VOICE_<HOST>` per show | Produced narration (single-host and text-to-dialogue) | Only for produced audio |
| 3 | `LILT_PUBLIC_ORIGIN` | The HTTPS feed/audio origin the app points at | Only to go live |
| 4 | `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD` | Newsletter delivery (`backend/newsletter.py send --deliver`) | Only to email |
| 5 | App Store Connect API key (key id, issuer id, `.p8`) | Archive/upload to TestFlight | Already in use |

The free `VOICE_PROVIDER=local` path, device-voice demos and tests need no inference key. Production verification and cloud narration use the separate services above.

## Narration providers

`VOICE_PROVIDER` chooses the backend; `pipeline narrate` calls it and concatenates audio.

| Provider | Env | Notes |
|---|---|---|
| `elevenlabs` (default) | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_<HOST>`, `ELEVENLABS_DIALOGUE_MODEL` | `eleven_v3` text-to-dialogue for co-hosted shows; `ELEVENLABS_MODEL` for single-host. Cloning needs a paid plan and consent. |
| `openai` | `OPENAI_API_KEY`, `OPENAI_TTS_MODEL` (default `gpt-4o-mini-tts`), `OPENAI_TTS_VOICE`, `VOICE_OPENAI_<HOST>` | Preset voices, no cloning; one call per turn, concatenated. |
| `local` | `VOICE_LOCAL_URL` | Any self-hosted server accepting `{"inputs":[{speaker,text,voice}]}` and returning audio bytes — the seam for the open-source models in [VOICE-OPTIONS.md](VOICE-OPTIONS.md) (Chatterbox MIT, Higgs v2, Dia2). No key. |

Host voice variables follow each presenter id: `ELEVENLABS_VOICE_NOVA`, `_FERN`, `_ADA`,
`_ATLAS`, `_INES`, `_DEV`, and the new shows `ELEVENLABS_VOICE_SPINNER`, `_YUSUF`, `_NOOR`,
`_MAREK`, `_TOMAS`, `_LENA`, `_ROSA`, `_AMARA`, `_KENJI`, `_FREYA`, `_JAX`, `_KAI`,
`_BENNY`, `_CHASE`. `doctor` lists them and flags which are empty.

## Writing, images, feed, newsletter

- **Writing:** `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-5.6-luna`),
  `OPENAI_REASONING_EFFORT`. Anti-slop rules are in the prompt; see
  [OPERATIONS.md](OPERATIONS.md).
- **Images:** the same `OPENAI_API_KEY` powers `gpt-image-2` (used for the app icon).
- **Feed/audio origin:** `LILT_PUBLIC_ORIGIN` (HTTPS; iOS rejects plain HTTP). Serve with
  `python3 backend/server.py` behind a TLS proxy.
- **Newsletter:** SMTP variables above; otherwise `newsletter.py send` stages `.eml` files
  locally with no key.
- **Data/limits:** `LILT_MAX_PROVIDER_CALLS_PER_DAY`, `LILT_MAX_SOURCE_CHARS`,
  `LILT_DATA`, `PORT`.

## Episode delivery: public Cloudflare R2

Rendered episodes are served, not bundled. `tools/publish_feed.py` uploads the audio and
a `feed.json` to R2's S3-compatible API; the app's Settings → feed field points at
`<R2_PUBLIC_BASE>/<prefix>/feed.json`. At 02:17 America/New_York,
`prepare-daily-episodes.yml` selects up to two approved, unpublished episodes and
renders them with Google Cloud TTS into a dated Actions artifact. It retries at
03:17 and 04:17 if the artifact is missing. The release workflow starts at 07:17,
07:43, and 08:13 Eastern; it renders a missing artifact itself, waits until 08:00
when early, and merges the audio into the feed once. It never replaces the archive
with only that day's episodes. GitHub scheduled jobs can still start late or be
dropped, so 08:00 is a target rather than a hard guarantee.

The weekly `full-run.yml` checks complete review before marking a batch successful.
The overnight Action checks the batch again before rendering. An incomplete or edited
transcript batch cannot reach the R2 publish step. The weekly Action can resume a
partially approved batch from a committed `seed_dir` or a prior `seed_run_id`; see
[story discovery](editorial/story-discovery.md#weekly-full-run).

The preparation artifact includes `cost-estimate.json` with a per-episode audio
duration upper bound at Google's public Gemini 2.5 Flash TTS rate. It excludes
text input and retries; actual charges require Cloud Billing export.

| Secret | Value |
|---|---|
| `R2_ENDPOINT` | `https://<account-id>.r2.cloudflarestorage.com` |
| `R2_BUCKET` | bucket name; required for the daily publisher |
| `R2_ACCESS_KEY_ID` | R2 API token access key |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_PUBLIC_BASE` | public origin for the bucket (`https://<hash>.r2.dev` or a custom domain) |

The bucket needs public read for `audio/*`, `episodes/*` and `feed.json`. `R2_PREFIX`
(default `v1`) versions a feed so a bad publish can be rolled back by pointing the app at
the old prefix.

Each episode has an **opaque 16-hex id** (`bundle_shows.episode_key`, derived from show +
date + DOI): the audio key and the feed's `audioURL` use it, so audio can't be guessed
from the show name. The feed story also carries a `detailURL` sidecar
(`episodes/<id>.json`) with the word-timed transcript and cover envelope, which the app
fetches on demand so **read-along works for streamed episodes**, not just bundled ones.
(True per-listener restriction would need presigned URLs or a Worker gate; r2.dev is
public-by-key.)

## Story discovery (no keys)

Selection fuses publicity/metadata signals; see
[editorial/story-discovery.md](editorial/story-discovery.md) for the priority order and
verification log.

| Source | Env | Notes |
|---|---|---|
| OpenAlex discovery | `LILT_OPENALEX_KEY`, `LILT_CONTACT_EMAIL` | Key raises the shared free rate limit; contact email is polite-pool identification. |
| EurekAlert press releases | `LILT_EUREKALERT` (default `1`) | Signal-only: sitemap + transient DOI extraction, `(doi, date)` kept. No release text is stored or narrated. Set `0` to skip. |
| Science Media Centre | `LILT_SMC` (default `0`) | Enables one extra verifier caveat question per episode for brain/sleep/climate/health beats. Never evidence. |
| Quanta / Nature News / Science News / ScienceDaily / Phys.org, arXiv, HF Daily Papers | *(none)* | RSS/JSON feeds; syndicated press copies collapse into one event. |

`python3 backend/pipeline.py doctor` reports which of these are active.

## App Store Connect (TestFlight)

Uses a team API key (key id, issuer id, and a `.p8` file) with manual signing:

```
xcodebuild archive -project ios/Zwicky.xcodeproj -scheme Zwicky -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/release/Zwicky.xcarchive \
  CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM=8K5ZVPCQ42 \
  PROVISIONING_PROFILE_SPECIFIER="Zwicky App Store" CODE_SIGN_IDENTITY="Apple Distribution"
xcodebuild -exportArchive -archivePath build/release/Zwicky.xcarchive \
  -exportOptionsPlist build/release/ExportOptions.plist -exportPath build/release/export \
  -authenticationKeyPath /absolute/path/AuthKey_XXXX.p8 \
  -authenticationKeyID XXXX -authenticationKeyIssuerID xxxx-...
```

The App Store Connect API cannot create app records (`apps` is GET/UPDATE only), so the
`Zwicky` record must exist in the web UI first (bundle `com.xmevans10.Zwicky`).

## Deliberately not needed

No analytics SDK, no push, no accounts, no database service. Social and accounts are
planned in [SOCIAL-PLAN.md](SOCIAL-PLAN.md) and will add providers (Sign in with Apple,
Postgres, APNs) when they are built — the doctor will be extended to report them.
