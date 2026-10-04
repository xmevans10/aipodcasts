# Supabase account foundation

Prepared 4 October 2026; not deployed or connected to the app. The target project and
sign-in providers still need to be identified. Upgrading the plan does not configure
an auth provider or migrate local listener state automatically.

## Service boundaries

Cloudflare R2 remains the public origin for the feed, audio, transcripts and sharing
pages. Existing Actions generation, review, mastering and publishing continue. Do not
copy these assets into Supabase Storage or require sign-in to listen.

Supabase Auth identifies listeners; Postgres stores private account data. The prepared
migration adds listener profiles, followed shows and per-episode saved/listened/progress
state. All client operations require authentication and are restricted to the JWT's
user ID. Account deletion cascades these rows. No public profiles or analytics ingestion
are enabled. Cloudflare episode/show IDs are references, not duplicated content.

Migration: `supabase/migrations/202610040001_listener_data.sql`.
Isolation check: `supabase/tests/listener_isolation.sql`. Run on staging after applying
that migration; it rolls back test rows. It covers ownership, cross-account denial and
anonymous grants. It has not been executed against Postgres in this workspace; neither
the Supabase CLI nor psql is installed. Do not call the schema production-validated yet.

Policies follow the official [row-level security guide](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Auth setup to complete once the project is identified

1. Link the intended project and apply the migration to staging. Run the isolation
   check before exposing any account state through the Data API.
2. Enable the agreed providers. Email OTP is a small starting option that avoids an
   OAuth callback; use a production SMTP sender and confirm delivery/rate limits.
   Apple sign-in additionally needs the Apple/Supabase provider configuration.
3. Put only the project URL and publishable key in app configuration. Secret/service-role
   keys belong only on a trusted server; never in the IPA. Use the maintained Supabase
   Swift SDK, persist sessions in Keychain, refresh sessions and handle revoked tokens.
4. Keep guest listening. Add explicit account UI, sign-out and in-app account deletion.
   Deletion needs a trusted endpoint; deleting profile rows alone is not account deletion.
   If that endpoint is needed, use a Cloudflare Worker rather than moving the app backend.
5. Add opt-in sync with clear scope. Keep the existing local library until the first
   authenticated sync succeeds. Isolate caches/queues by account; never upload one
   listener's state after switching accounts. Design per-item conflict handling and
   removal/tombstones before enabling multi-device sync. The schema alone does not
   implement these behaviors.
6. Test first sign-in, expired OTP, refresh/relaunch, sign-out, account switch, offline
   playback, local-state import and account deletion on real devices. Update privacy
   wording/App Privacy declarations when personal state actually leaves the device.

See [passwordless email authentication](https://supabase.com/docs/guides/auth/auth-email-passwordless)
for the supported email flow. No auth settings, production migration, SMTP credentials
or Apple capabilities have been changed by this preparation.
