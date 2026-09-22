# Milestone 2 — "New episodes are out", end to end

Prepend [`00-shared-context.md`](00-shared-context.md), then paste:

```text
Goal: listeners are told when episodes drop, without opening the app. Refresh the R2 feed in the
background (BGAppRefreshTask) and post a local notification when episodes are newer than the
listener's last-seen marker, deep-linking into the episode; add a Settings toggle and respect
quiet behaviour (one notification per drop, never repeat). Then make it work with the app fully
closed via a minimal push path (APNs + a tiny scheduler that reads feed.json), keeping the free
tier.

Constraints: no third-party analytics or tracking SDKs; notifications are local-first; the
last-seen marker and the in-app new-episodes sheet (already shipped) stay consistent; permission is
requested only with a clear prompt.

Done when: publishing a new episode to R2 results in a notification on a device within the
background window (and, for push, with the app terminated); tapping it opens that episode's player;
Settings can disable it; existing checks pass.
```
