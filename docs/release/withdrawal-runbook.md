# Withdrawals, corrections and rollback

A withdrawal retains the old episode ID as a notice, blocks its playback, removes it from automatic release inventory and preserves it for saved records and old share links. A corrected recording uses a new ID, fresh factual/audience approvals and its own audio/transcript. Never replace an immutable public recording silently.

Prepare a local plan:

```sh
python3 tools/withdraw_episode.py --feed saved-feed.json --episode episode-ID \
  --notice 'A substantive explanation of the problem and its consequences.' --out withdrawal-plan.json
```

If a corrected episode is already published, add `--replacement-id episode-NEW-ID`. The replacement must be playable and belong to the same show. Review the exact notice, episode and complete before/after feed in the plan. A plan alone performs no writes.

An authorized operator applies the reviewed plan with the existing R2 environment:

```sh
python3 tools/withdraw_episode.py --apply-plan withdrawal-plan.json
```

The command checks that the feed still matches the plan, backs up the original assets, and uses the current feed ETag as a conditional write. R2 documents [conditional PutObject support](https://developers.cloudflare.com/r2/api/s3/api/). The withdrawal notice commits before public asset changes. If a later asset operation fails, the catalog stays blocked; create a fresh plan against the updated feed and retry the remaining withdrawal operations. Do not roll back a valid urgent withdrawal just to silence a failed job.

The command removes the public audio object after its backup. Previously cached clients then fail playback instead of receiving superseded science. Edge caches or an already buffered recording may not stop immediately; the native build stops when it receives the explicit withdrawal. A withdrawal is not a remote purge of downloaded/buffered bytes.

The release-drill workflow copies one existing recording into `v1-release-drill/RUN-ID`, proves stale-write rejection, withdrawal, replacement linking, audio removal and snapshot rollback, and records its result. It does not write or delete production keys. The storage drill does not prove queue/background playback behavior on an iPhone.

Production rollback remains an operator decision: inspect the saved original plan and backed-up audio/sidecar/page, verify that restoring the scientific content is appropriate, restore assets before the feed, and use a conditional feed write. Recheck the complete public catalog afterward. Normal daily publication must preserve tombstones; it cannot automatically resurrect a withdrawn paper from an old approved batch.
