# Build 10 listening and app QA

30 September 2026. TestFlight **1.0.0 (10)** uploaded and successfully processed.
This build includes onboarding/Home motion and the current character introductions.
Narration changes run in the backend. The fresh recordings below are private QA assets,
not published app episodes. The app still has six public episodes.

## Fresh delivery: listen in this order

Files are in `build/voice-qa-36746152616/voice-qa/`; approved scripts are beside them in
`qa-transcripts/`. All three passed independent factual and current audience review.
Audio format, durations, exact transcript words and monotone timing bounds passed.
Those checks do not prove natural delivery, exact acoustic word alignment or fidelity
of every spoken word. The times below come from the approximate sidecar alignment.

| Episode | Presenter / duration | Audio | Main listening check |
|---|---|---|---|
| When ChatGPT Misses Your Point | Noor / 3:29 | `50139e48b76fc738.m4a` | Does dry humour feel natural and warm? At ~1:08–2:16, can you hear a person reacting rather than reading? At ~2:18, does the uncertainty feel candid? |
| Birds Carry Plastic, Even When Released | Clara / 3:25 | `132500d7266bd69d.m4a` | Is she affectionate and curious without sounding theatrical? At ~0:37 and ~2:28, can you follow the samples and limitations by ear? |
| When Printed Lattices Lose Their Strength | Marek / 3:38 | `e41befbc366a72c2.m4a` | Is the tinkerer distinct from Noor and Clara? At ~1:17, do the technical measures lose you? At ~2:45, does the limitation revert to an academic paragraph? |

Listen once without reading. Afterwards, try to say the question, result and limit in
one sentence each. Flag exact moments that feel robotic, emotionally forced, too dense,
abrupt between paragraphs or uneven in volume. Minor reviewer advisories remain on
these candidates; they have not been silently edited after approval.

## Quick A/B calibration

`build/voice-qa-36745435418/voice-qa/` contains `atlas`, `fern` and `noor`, each with
`-baseline.m4a` and `-directed.m4a`. Same words and same voice per pair; the baseline uses
generic conversational direction, while the directed take uses the full character and
intonation brief. These are fictional 13–16 second calibration lines, not science episodes.
Listen for warmth and honest uncertainty in Theo, joy in Clara, and warmth beneath Noor's
sarcasm. A/B clips are samples of stochastic generations, not a controlled listening study.

## In-app QA on build 10

Use **What Forest Canopies Reveal About Birds** and **Can Solar Panels Save Their Own Power?**
from today's Home catalog. Their audio predates the new delivery direction; use them for
the app journey, not the character comparison.

- Fresh onboarding: entrances, choice feedback, transitions and first play. Repeat with
  iOS Reduce Motion enabled; the path should remain clear and comfortable.
- Home: refresh, card motion and episode opening. Confirm today's titles appear.
- Playback: play/pause, seek forwards/backwards, background/lock-screen controls and
  resume after interruption. Read-along should track the audible words after seeking.
- Open a listening-page link into the app; confirm the intended episode opens.

Both known physical phones were unavailable to the operator. No device walkthrough or
subjective full-audio sign-off is claimed. No simulator was launched.

## Release status — 1 October

Eight episodes are live across six shows. QA the actual app recordings of **When ChatGPT Misses Your Point** (Gradient) and **When Printed Lattices Lose Their Strength** (Layer by Layer), released today. Private recordings above are earlier renders, so do not assume identical intonation or timing. Latest independent health run `36833259337` passed.

Backfill `36831940287` passes the strict partial check with six approvals, including Webwork's **Can Silk Help a Wound Heal?**; four scripts remain unpublished after today's release. Star Stuff remains withheld. The fourteen-episode reserve target is not met. Build 11 changes the icon; playback and full listening sign-off remain required.

## Full-batch audio QA — 1 October

Generation `36835451105` produced nine strict approvals; private audio render `36844094932` uses speech-relative fades v2 and two-pass mastering. Follow-up `36844386557` preserves these approvals and attempts the other seven shows. Do not count pending results or label this sixteen-show coverage. Combined validated inventory currently contains twelve unique unpublished scripts (six days at two/day).

For every new recording: listen to the first ten seconds, both story-break cues and the final ten seconds. Check voice is foreground, cue attacks/releases are smooth, tails finish before speech, sentence endings and initial consonants remain intact, no digital clicks or unexpected level changes, and transcript timing remains correct. Compare headphones and phone speaker. Episode signatures vary; shared sampled material is CC0 Kenney audio.

Each export now records measured integrated loudness and true peak. Target is -16 LUFS ±1; final AAC true peak must be ≤-1 dBTP, with a -2 dBTP mastering target to allow codec headroom. Mastering may not shift the timeline by more than 10 ms. These measurements do not replace subjective listening sign-off. Mandatory real-encoder CI passed (318 tests); the local integration test is skipped because local FFmpeg is broken.
