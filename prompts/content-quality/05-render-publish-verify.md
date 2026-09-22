# Stage 5 — Render and publish a coherent, verified release

Read `00-shared-context.md` and the preceding stage's actual results. Run this stage only
for a task that includes publication. A request for prompts or an editorial review alone
is not an instruction to deploy. Honor approval already given in the active task rather
than repeatedly requesting the same permission.

## Goal

Deliver the approved scripts as matching audio, feed text, speaker-labelled read-along and
envelope data. Prove public delivery and compatibility; keep on-device verification separate
from code/build checks. Complete the original co-host milestone where the environment allows.

## Preflight

- Inspect current git status, commit, branch, workflow runs and live feed. Do not restart
  the cancelled 2026-09-22 run from this handoff blindly. Check for newer work first.
- Verify all 16 intended show entries have current factual and audience approvals for the
  exact scripts/contracts being rendered. Check stable cast assignments and turn identities.
- Compare the current live catalog with intended output. Preserve existing older episodes
  unless removal is explicitly intended. At the handoff snapshot, four older bundled
  episodes should remain alongside the latest 16: 20 episodes across 16 shows.
- Inspect episode ID and published-date behavior. A correction to the same episode should
  not needlessly discard listening history or masquerade as a newly released episode.
  Determine an explicit content-version/cache strategy when replacing audio/sidecars at
  an existing ID; otherwise cached old audio can play against new word timings.
- Run required checks; distinguish permissions/environment failures from product failures.
  Never bypass scientific or audience review to obtain a green workflow.

## Render and publish

Use the existing no-paid-key Kokoro path and free CI, not a new narration provider.
Synthesize exact approved speech only; speaker labels, evidence quotes and review controls
must not be spoken. Each host keeps the cast voice mapped by stable ID.

Spoken edits require rerendering audio, per-turn word timings, total duration and envelope.
Do not update titles/body in the feed while pointing to an audio recording with different
spoken content. Text-only changes may avoid synthesis only when speech truly is unchanged
and the edit has been checked for approval/hash implications.

Keep timing claims honest: current Kokoro timing distributes words within each measured
turn; it is not forced alignment. Preserve exact turn offsets and inter-turn pauses.
Forced alignment remains a separate milestone unless explicitly included in the task.

Inspect upload failure behavior before replacing the live feed. Upload/validate all required
media and sidecars first, then switch the feed. A failed render/upload must not advertise a
complete new release. Retain enough prior metadata/objects to restore the last good feed
without deleting user content. Address cache/version consistency with the smallest change
needed for a coherent release, not an unsolicited hosting redesign.

Incrementally commit reviewed source/artifact metadata according to AGENTS.md. Do not commit
generated audio/build products or unrelated files. When pushing to main is authorized,
verify the remote base and avoid force pushes; handle intervening changes normally.

## Verify the public result

Wait for the exact render/publish run and inspect its final status/logs. Avoid rapid unchanged
polling. A successful artifact upload with a skipped R2 step is NOT a live release.

Fetch the actual public feed and sidecars, not only local output. At minimum confirm:
- All 16 shows, including Ground Truth and Star Bros, are represented; expected older
  entries remain; no duplicate replacements or stale titles appeared unintentionally.
- Latest titles, descriptions and full scripts match the approved artifacts.
- Audio/detail URLs return successfully and support the player's expected access pattern.
- Audio duration and decodability are valid, with no empty/silent render replacing speech.
- Every dialogue turn carries the right speaker/host ID, in order; all expected presenters
  participate and their sign-offs have their own voices.
- Transcript words reproduce the approved speech; timestamps are finite, monotonic, in
  bounds and anchored to actual turn offsets; five-band envelope/hop/duration are coherent.
- No internal evidence packets, supporting claim quotations, provider controls or private
  review metadata leaked into public narration or delivery payloads.

Decode real public sidecars with the app's actual Swift models. Preserve compatibility for
legacy solo paragraphs without speaker fields. Trace that an episode with audioURL streams
recorded audio even when it also has dialogue turns, rather than starting device speech.

## iOS and completion

Do not launch a simulator. If a connected iPhone is available, install the appropriate build
using the repository workflow and test both co-hosted shows: play, pause, seek to a turn,
follow read-along, speaker transitions, background/resume and a solo regression. Check that
long names and longer titles remain readable. Inspect actual UI output where tooling permits.

If no phone is available, finish all independent build, decode, public-media and transcript
checks, but explicitly leave on-device playback/UI acceptance unverified. Do not describe
milestone 1 as fully verified solely because the build passed. Do not silently expand into
TestFlight/App Store release work from a different milestone.

Content arrives through the live feed; it does not require rebundling the app. New speaker
label UI does require an updated app version. Explain that distinction in the handoff.

Update stale milestone status docs only after observing the outcomes. Final response should
state what code shipped, what content is live, which tests passed, whether playback was
actually exercised, and any remaining blocker. Link the actual workflow and relevant files;
do not leave the user to infer completion from a commit hash.
