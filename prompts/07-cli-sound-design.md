# Milestone 7 — Headless sound design and daily audio QA

> Status (2026-09-25): experiment brief only. The daily renderer still uses the
> episode-ID melody and Kenney section effects in `tools/tts/sound_design.py`.
> Do not publish a replacement sound pack before listening to complete previews.

Prepend [`00-shared-context.md`](00-shared-context.md), then paste this prompt:

```text
Goal: create a distinctive, restrained sonic identity for Zwicky, entirely from
versioned source and CLI tools. Once a sound pack is approved, the daily 02:17,
03:17, and 04:17 Eastern preparation runs must assemble, master, and quality-check
episodes unattended before the 08:00 Eastern release. Produce evidence that the new
mix sounds better than both the present cues and a clean voice-only mix.

Current integration points (verify before editing):
- `tools/tts/sound_design.py` synthesizes eight notes from each episode ID, mixes in
  `steel-jingle.wav`, and inserts `soft-confirmation.wav` or `glass-accent.wav` at
  selected section breaks. `backend/tests/test_sound_design.py` tests this behavior.
- `tools/tts/bundle_shows.py` writes mono 24 kHz WAV, word timestamps and a level
  envelope, encodes M4A, and deletes the intermediate WAV. The audio fingerprint is
  written to the episode sidecar.
- `scripts/prepare-daily-episodes.sh` invokes the renderer for both the overnight
  `.github/workflows/prepare-daily-episodes.yml` job and the morning fallback in
  `.github/workflows/daily-episodes.yml`. `docs/AUDIO-PRODUCTION.md` describes it.
- This experiment must not call the Google TTS provider once for each candidate.
  Render a fixed voice take once and reuse its raw narration stems for every mix.

Experiment 1: Establish a blinded comparison set
1. Pick three representative approved scripts: a quiet solo story, a lively solo
   story, and a co-hosted story. Record source artifact IDs and TTS voice/model
   metadata. Estimate any Google TTS cost before making calls; prefer already
   available narration stems. Keep all experimental outputs under ignored `build/`.
2. Add a CLI option to save or load raw narration stems without changing the
   reviewed words, voices, timing schema, or production default. Render each script
   once. Create: A = current sound design; B = clean voice with intentional pauses
   and no effects; C = proposed new sound pack. Use the identical voice take for
   A/B/C, match playback loudness, and randomize preview filenames. Also export a
   short montage of each candidate's opening, first transition, and ending.
3. Record audio duration, integrated loudness, true peak, clipped samples, long
   unintended silence, cue-to-speech level, and actual cue positions. Verify every
   transcript word time against the final mix, including intro offsets.

Experiment 2: Build the sound pack from reproducible sources
1. Use a headless, open-source source renderer such as Csound `.csd` files for the
   authored musical material. The source and its render command must regenerate
   the exact release WAV files in CI. Use Python/Spotify Pedalboard only where it
   improves repeatable mixing; use FFmpeg for encoding and two-pass loudness
   measurement/normalization. Pin tool versions. Keep production CLI dependencies
   outside the standard-library-only `backend/` package.
2. Design one shared Zwicky motif and a small number of show color variants.
   Produce an opening, an ending, and at most two editorially justified transitions
   per episode. Let the show's profile or an explicit editorial cue sheet choose
   variants; never turn the episode ID into audible notes or select arbitrary UI
   sounds. Begin with no effects over speech. If an under-voice texture is tested,
   make it a separate candidate and measure intelligibility and ducking.
3. Commit the synthesis source, short final cue WAVs if practical, a JSON manifest
   with pack version, filenames, hashes, show mappings, gain and placement rules,
   and provenance/license for every external sample. Do not use noncommercial
   model weights or samples with unverified rights. A clean build must reproduce
   the manifest and fail on hash or format mismatch.
4. Keep the mixer deterministic. Preserve narration samples apart from documented
   mastering, exact spoken text, read-along word times, `levelHop`, and episode ID.
   Add a dry-voice fallback mode for a bad or unavailable pack, with an explicit
   sidecar record of which mix shipped. Do not silently ship the old cues.

Experiment 3: Listen, gate, and roll out
1. Present blind A/B/C full-episode previews and montages to the product owner
   and at least one other listener. Capture 1–5 scores and notes for identity,
   narration clarity, transitions, fatigue, and overall preference on headphones
   and a phone speaker. Test in a car if available. Choose C only if listeners
   prefer it over both baselines and nobody flags obscured speech or fatigue.
   Otherwise revise the pack and rerun the comparison; automation metrics alone
   cannot approve aesthetic quality.
2. Implement a CLI quality gate for pack integrity, finite PCM, clipping/true
   peak, integrated loudness tolerance, unintended silence, cue placement outside
   protected speech, transcript timing bounds, and sidecar/encoded-audio duration.
   Use deliberately broken fixtures to prove each blocking check. Report failures
   with episode and cue names.
3. Wire the approved pack and gate into `bundle_shows.py` and the shared preparation
   script. The prepared artifact must include the mix version, manifest hash, QC
   report, and cost estimate. The morning publisher must verify those artifacts
   before upload. Keep an explicit CLI switch for dry voice and a documented
   rollback path. Never rerender published audio in place without a release plan.
4. Update `docs/AUDIO-PRODUCTION.md` with one-command local regeneration, how to
   audition previews, dependency versions, expected runtime, the target loudness
   rationale for mono playback, and an operator response to a failed QC gate.

Done when: a clean checkout can regenerate the approved cues and produce the same
fixed-take candidate mixes from the CLI; blind listening favors the selected mix;
broken audio is blocked before publication; the daily and morning fallback paths
apply the same pack and QA; all tests pass. Keep the current production sound
design until the listening decision is recorded. Commit implementation in logical
increments and attach the preview/QC results to the review handoff.
```

Research starting points: [Csound CLI](https://csound.com/manual/invoke/the-csound-command/),
[Spotify Pedalboard](https://spotify.github.io/pedalboard/), and
[FFmpeg loudnorm](https://ffmpeg.org/ffmpeg-filters.html). Check tool versions and
licenses again during implementation.
