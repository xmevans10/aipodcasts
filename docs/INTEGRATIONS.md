# Integrations and API keys

One place for every external credential and what it unlocks. Nothing here is
committed; values live in `backend/.env` (git-ignored) or the process environment.
Run the doctor to see what is currently configured (presence only, no network, no
secret values):

```
python3 backend/pipeline.py doctor
```

## The short list (what to hand over)

| # | Credential | What it unlocks | Required now? |
|---|---|---|---|
| 1 | `OPENAI_API_KEY` (+ `OPENAI_MODEL`) | Drafts scripts with the Zwicky writing contract; icon/OG image generation | Yes, for real drafting |
| 2 | `ELEVENLABS_API_KEY` + one `ELEVENLABS_VOICE_<HOST>` per show | Produced narration (single-host and text-to-dialogue) | Only for produced audio |
| 3 | `LILT_PUBLIC_ORIGIN` | The HTTPS feed/audio origin the app points at | Only to go live |
| 4 | `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD` | Newsletter delivery (`backend/newsletter.py send --deliver`) | Only to email |
| 5 | App Store Connect API key (key id, issuer id, `.p8`) | Archive/upload to TestFlight | Already in use |

Everything else is local and needs no key: the free `VOICE_PROVIDER=local` path, the
device-voice demos in the app, and all tests.

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
`<R2_PUBLIC_BASE>/<prefix>/feed.json`. `render-episodes.yml` runs it automatically after
rendering when the secrets exist.

| Secret | Value |
|---|---|
| `R2_ENDPOINT` | `https://<account-id>.r2.cloudflarestorage.com` |
| `R2_BUCKET` | bucket name (leave unset to skip publishing) |
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
