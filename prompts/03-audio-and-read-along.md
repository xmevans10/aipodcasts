# Milestone 3 — Professional audio and precise read-along

> Status (2026-09-22): waveform-guided alignment is implemented in `tools/tts/align.py`
> and wired into `bundle_shows.py` (Kokoro segment anchors + phoneme-weighted energy DP),
> with `TranscriptWord.end` now carried into the app. Loudness normalisation, per-host
> pronunciation for names/terms, and the automated alignment-confidence gate remain open.

Prepend [`00-shared-context.md`](00-shared-context.md), then paste:

```text
Goal: every published episode meets a quality bar, and highlighting tracks the actual voice. Replace
the length-weighted word timings with forced alignment against the rendered audio (open tooling, no
paid API), add per-host pronunciation for names and scientific terms, and normalise loudness across
episodes. Add an automated QA gate that fails a render if alignment confidence, clipping, silence,
or duration fall outside bounds, so a bad episode never reaches the feed.

Constraints: audio and transcript must stay word-for-word identical to the reviewed body; the
envelope and timing schema (transcript[].words[].start, levelHop) must not change the app contract;
all tooling runs on free CI.

Done when: timings are derived from the audio and verified (spot-check that highlighted words match
spoken words); a deliberately broken render is blocked by the gate; loudness is consistent across
shows; checks pass.
```
