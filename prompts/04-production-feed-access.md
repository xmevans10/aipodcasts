# Milestone 4 — Production feed: access control, versioning, analytics

Prepend [`00-shared-context.md`](00-shared-context.md), then paste:

```text
Goal: stop serving audio public-by-key. Only requests carrying a valid per-episode credential may
stream (presigned, expiring URLs, or a Cloudflare Worker gate), while feed.json stays public. Add
feed prefix versioning so a bad publish can be rolled back by pointing the app at the previous
prefix, and record privacy-preserving playback analytics (start, completion, skip, per show) with a
simple ops view of volume and cost.

Constraints: no PII; the opaque per-episode id stays the audio identity; the app must handle token
expiry gracefully (refresh the feed/sidecar, retry); the free tier must remain sufficient.

Done when: fetching an audio URL with no valid credential is denied; a valid, freshly-issued URL
streams; rollback to a prior prefix works; analytics are recorded and viewable; checks pass.
```
