# Zwicky social features: milestones

Planning baseline: 18 September 2026. This is a design record, not committed work.
It assumes the production backend from [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md)
M2 (ASGI + Postgres, authenticated writes); the current stdlib read-only server has no
accounts, sessions or write path, so every account-bearing milestone is blocked on it.

## Principles

1. **Local-first, account-free by default.** The free listening journey must work with no
   identity and offline. Social is an opt-in layer whose outage never blocks playback.
2. **Never upload listening by default.** History, saved items, minutes, positions, queue
   and followed shows stay on device unless a separate, clearly-worded toggle says otherwise.
3. **Content before community.** Stable sharing and distribution come first; accounts next;
   structured reactions before any free text; open comments are gated and probably not v1.
4. **Ship the smallest no-account slice first.**
5. **Trust and safety is a product surface, not an afterthought** once anything is UGC.

Recommended order: **sharing → identity → friends → reactions → (gated) comments**.
The no-account MVP is `SH0 + SH1 + SH2` plus nothing else.

## Workstream A — Sharing and distribution

Every shared thing already exists as reviewed content (a `Story` plus the newsletter
renderer). Render it to static HTML at publish time, give it a canonical URL, and share the
URL instead of the title string.

| ID | Milestone | Scope | Depends | Acceptance gate | Opt. |
|---|---|---|---|---|---|
| SH0 | Canonical identity & URL contract (`/e/<slug>`, `/s/<slug>`, configurable origin) | FE+BE | — | Versioned spec; every story id maps to a public slug; no hard-coded domain | no |
| SH1 | Static episode/show pages + OG/oEmbed/`twitter:` meta + canonical | BE+infra | SH0 | Pages work without JS; withdrawn/revised stories show a correction, not stale copy | no |
| SH2 | Native share: episode URL + `SharePreview`, excerpt quote card via `ImageRenderer` | FE | SH0 | Share works offline for bundled episodes; quote card renders at accessibility sizes | no |
| SH3 | Deep links / Universal Links + `zwicky://` scheme + Smart App Banner fallback | FE+infra | SH1 | Tapping a link opens `EpisodeView`; AASA served with no redirect; unknown slug falls back to web | no |
| SH4 | Web discovery + podcast RSS feed | BE+infra | SH1 | Valid RSS/iTunes feed and sitemap; free-vs-premium audio decision recorded | opt |
| SH5 | Newsletter cross-pollination (CTAs target canonical pages) | BE | SH1 | Newsletter tests still pass; no dead CTA domains | opt |
| SH6 | Privacy-preserving link attribution (coarse `src` tags, aggregate counts, no cookies/IP) | BE+infra | SH1 | No per-user tokens; App Privacy answers match; no ATT prompt needed | opt |
| SH7 | Home/Lock-screen widget | FE | SH3 | Deep-links Today's episode | opt |
| SH8 | Per-episode OG raster images (pre-generated static assets) | BE+infra | SH1 | 1200×630 assets or a documented default | opt |
| SH9 | App Clip | FE+infra | SH3 | Only after measured install lift; experience registered | opt |

Minimum viable sharing = **SH0 + SH1 + SH2**: no accounts, no cookies, no analytics SDK, no
new paid service.

## Workstream B — Identity and friends

Anonymous-first and upgradeable: every install can hold a Keychain-bound device identity
with no PII; claiming a handle or linking Sign in with Apple promotes that identity, never
gates the product. Read/write identity lives in Postgres, not `lilt.sqlite3`.

| ID | Milestone | Scope | Depends | Acceptance gate | Opt. |
|---|---|---|---|---|---|
| S0 | Identity ADR + schema spike + threat model | BE+design | M2 | Anonymous-first, optional Apple; migrations drafted; retention/privacy review | no |
| S1 | Anonymous device identity & sessions | BE+FE | S0 | Opaque hashed rotatable token, zero PII; in-app delete removes rows; free path unchanged | no |
| S2 | Profile & handle | FE+BE | S1 | Unique handle with reserved-word + profanity filters, change cooldown | no |
| S3 | Privacy defaults, block & report plumbing | FE+BE | S2 | Private by default; unilateral block; report path; 1.2 checklist signed off | no |
| S4 | One-way follows (people, not shows) | FE+BE | S3 | Rate-limited; follower lists per visibility; no listening data server-side | no |
| S5 | Friends (mutual) & requests | FE+BE | S4 | Single canonical edge; request caps; block cancels pending | opt |
| S6 | Sign in with Apple link/upgrade, export & delete | FE+BE | S1,S2 | Deterministic merge; delete revokes Apple token; JSON export | opt (required if any non-Apple login, 4.8) |
| S7 | Find friends (handle search, invite link/QR, no contacts upload) | FE+BE | S4,S5 | Discoverability respected; no address-book upload | opt |
| S8 | Age gate, safety, review & ops readiness | FE+BE+ops | S3–S7 | Age gate; filtered/reportable end-to-end; moderation SLA; reviewer demo; privacy labels updated | no |

Data model: `users`, `identities(anon|apple)`, `devices`, `profiles(handle, visibility,
discoverable)`, `follows(state)`, `friend_requests`, `friendships`, `blocks`, `reports`,
rate-limit counters. All visibility defaults private/unlisted; all social reads filter
blocks in both directions.

## Workstream C — Reactions, comments, moderation, notifications

Once anyone can post, App Review Guideline 1.2 makes filtering, reporting with timely
response, blocking and published contact mandatory. **Recommendation: do not ship text
comments in v1.** Ship opt-in notifications and a fixed-set, transcript-anchored reactions
surface (no free text, so not UGC under 1.2), build the moderation platform behind it, and
gate comments on demonstrated retention need.

| ID | Milestone | Scope | Depends | Acceptance gate | Opt. |
|---|---|---|---|---|---|
| C0 | Identity & account foundation (from workstream B) | BE+FE+T&S | M2 | Sign in/out; in-app delete removes authored data | no |
| N1 | Notification consent & APNs foundation | BE+FE+T&S | C0 | Contextual permission after value moment; tokens revocable; disclosures updated | no |
| R1 | Fixed-set transcript-anchored reactions (non-UGC) | BE+FE+T&S | C0 | Fixed enum only; one per account per moment, idempotent; server re-derives the anchor | no |
| N2 | In-app inbox & digest | BE+FE | N1 | Paginated read state; opt-in digest; neutral payloads; one-tap unsubscribe | no |
| M1 | Moderation & trust-and-safety platform | BE+FE(internal)+T&S | C0,R1 | Report/block/mute; internal queue with audit log; written SLA; kill switch tested | no |
| C1 | **Text comments — GATED** | BE+FE+T&S | N1,N2,M1 | All 1.2 controls live; staffed review with SLA; age posture; kill switch + deletion drill | gated |
| O1 | Community operations & scale | T&S+BE | C1 | SLA reported; cost per reviewed item measured; periodic drills | opt |

Do not enable comments until: identity with content-deleting account deletion exists; all
four 1.2 controls are live; a staffed review queue with a named owner and SLA exists; the
age posture is decided; notifications and an inbox exist; a kill switch works; and the
EULA/community standards/privacy policy are published and referenced in-app.

## Cross-cutting

- **App Store:** Guideline 1.2 (UGC), 4.8 (login services), 5.1.1 (data collection and
  account deletion), 2.3.6/1.3 (age rating / Kids), 1.5 (contact info).
- **Privacy:** no tracking SDKs, so no ATT prompt is expected; any server-side counter must
  avoid cookies and IP retention; profiles are not web-indexed by default.
- **Cost:** moderation is labour-dominant. A queue at 2–5 reviewer-minutes per item is a
  standing line well beyond the infrastructure reserve and cuts against "synthesize once,
  distribute many". This is the main reason comments are gated.

## What not to build yet

Comments/replies (before M1); DMs or messaging; presence/last-seen; contact-book upload;
user photo uploads; listening-history sharing or "friends are listening"; leaderboards or
comparative streaks; third-party analytics or attribution SDKs; App Clip and Live
Activities; public search-indexed profiles; referral dashboards; and anything on the
stdlib read-only server.

## Sources

- App Review Guidelines — https://developer.apple.com/app-store/review/guidelines/
- Account deletion — https://developer.apple.com/support/offering-account-deletion-in-your-app
- Associated domains / Universal Links — https://developer.apple.com/documentation/xcode/supporting-associated-domains
- ShareLink / SharePreview / ImageRenderer — https://developer.apple.com/documentation/swiftui/sharelink
- Registering with APNs — https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns
- App Privacy details — https://developer.apple.com/app-store/app-privacy-details/
- SKAdNetwork / AdAttributionKit — https://developer.apple.com/documentation/storekit/skadnetwork
