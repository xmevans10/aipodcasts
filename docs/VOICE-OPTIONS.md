# Voice options for Zwicky

Decision record for synthetic narration, written after adding the two-host show
(Ground Truth: Ines Marlowe and Dev Raman). Production uses the free Kokoro cast; ElevenLabs remains an optional provider.

## What ElevenLabs actually offers

- **Text to Dialogue** (`POST /v1/text-to-dialogue`, model `eleven_v3`) renders
  multiple speakers **in one generation**. Pass `inputs: [{text, voice_id}]`; up
  to 10 unique voices, ~2,000 characters per request for reliability. So a
  two-host episode does **not** need per-voice splicing — chunk by turns and
  concatenate only to respect the request budget. Implemented in
  [`backend/pipeline.py`](../backend/pipeline.py) `_narrate_dialogue`.
- Each voice still needs a **voice ID**. **Cloning is a paid-plan feature** and
  needs sample audio plus consent. Our current key returns HTTP 402
  `paid_plan_required` for library voices, so real narration is blocked until a
  plan and voice IDs exist. The app ships a **device-voice two-host demo** that
  alternates two `AVSpeechSynthesisVoice`s turn by turn, which needs none of this.

## Open-source / self-hosted shortlist

Commercial-use licenses are marked. Popularity is a rough tie-breaker.

| Model | Repo | License | Cloning | Multi-speaker | Notes |
|---|---|---|---|---|---|
| **Chatterbox** | [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) | **MIT** | Yes (~5-10s) | No | Best license + cloning combo; MPS/CPU support; paralinguistic tags |
| **Higgs Audio v2** | [boson-ai/higgs-audio](https://github.com/boson-ai/higgs-audio) | Community (commercial under 100k users) | Yes | **Yes** | Only self-hosted option with cloning **and** native multi-speaker; wants ≥24GB VRAM |
| **Dia2** | [nari-labs/dia2](https://github.com/nari-labs/dia2) | **Apache-2.0** | Yes | **Yes** | Native `[S1]/[S2]` dialogue; English-only; lower fidelity than the top tier |
| **VoxCPM2** | [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) | **Apache-2.0** | Yes | No | 48kHz, style prompts, ~8GB VRAM |
| **Kokoro-82M** | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | Apache-2.0 | **No** | No | Tiny and fast; stable preset voices assigned per host |
| XTTS-v2 / F5-TTS / Fish S2 / Higgs v3 | — | **non-commercial** | — | — | Excluded on license |

## Cheaper commercial APIs

Prices are per 1M characters where the vendor bills by character.

| Provider | Quality | Cloning | Multi-speaker | ~Cost / 1M chars | Caveat |
|---|---|---|---|---|---|
| **Google Gemini-TTS** | Very high | Separate product | **Yes** | ~$15-30 nominal | Token billing can inflate; preview voices |
| **Inworld Realtime TTS-2** | Very high | Free instant + pro | No | ~$15 (at $300/mo) | Render each host, splice; younger API |
| **Cartesia Sonic** | Very high | Instant / pro | No | ~$37-50 | Credit math approximate |
| **Fish Audio** | High | Yes | Not documented | ~$15 | Thinner consent docs |
| OpenAI gpt-4o-mini-tts | High | No | No | ~$15 (tts-1) | Fixed presets, no cloning |
| Amazon Polly / Deepgram Aura | Good | No | No | ~$4-16 | Very mature, no cloning |

## Recommended free voice cast (implemented)

**Kokoro-82M** is the base for the free cast: Apache-2.0 for code *and* weights, 28
English fixed voicepacks (no cloning, no consent questions), 24 kHz, ~363 MB, CPU-viable.
`tools/tts/voice_cast.json` assigns each of the 20 presenters a distinct voice;
`tools/tts/kokoro_generate.py` renders them and the `tts-voice-cast` GitHub Action
produces QA samples. Piper was rejected for this purpose: the Blizzard-2013/Lessac
license taints most finetuned voices, and `hfc_*`, `ryan` and `l2arctic` are
non-commercial. Kokoro's only caveat is the GPL `espeak-ng` fallback used for
out-of-distribution text.

## Recommendation

1. **Production:** Kokoro-82M with the 20-voice cast above. Render co-hosted shows
   turn by turn with the same fixed voices, with no narration key or paid service.
2. **Optional:** ElevenLabs Text to Dialogue with licensed voice IDs.
3. **Free cloning path:** **Chatterbox** (MIT) with a short reference clip per host,
   generating each turn and stitching by speaker — the harness already exposes
   `turns_narration_inputs()` to drive this. Runs on Apple Silicon via MPS.
4. **True multi-speaker OSS:** **Higgs Audio v2** (community license, attribution)
   or **Dia2** (Apache) if we want one-pass dialogue without stitching.
5. **Cheapest managed multi-speaker:** **Google Gemini-TTS**, pending a real bill
   measurement on our scripts.

Compute cost at our volume is negligible (a 500-word episode is ~4 minutes of
audio); the real decisions are **licensing and voice consistency**, not GPU spend.

## Production path (implemented)

All 16 shows render with **Kokoro directly** — no cloning step. The
[model card](https://huggingface.co/hexgrad/Kokoro-82M) documents Apache-2.0 weights.
`tools/tts/bundle_shows.py` resolves each dialogue speaker through `backend/hosts.py`
and selects its stable voice by host ID from `voice_cast.json`. Each turn is synthesized
separately, with a 180 ms pause between turns. Paragraph word starts are estimated
within the measured turn duration and offset by the exact sample count, including pauses.
These are approximate word timings; forced alignment remains milestone 3.

Both rendering workflows require all 16 shows and retain the four older bundled
episodes in `ios/Zwicky/Episodes/`. They publish audio, speaker-labelled sidecars
and the feed to R2 when configured.
Every script must pass verification for its current content hash before any synthesis;
a failed, missing or stale approval aborts the batch without replacing the live feed.
Dialogue validation also requires every presenter to speak their own sign-off.

The iOS read-along shows the speaker above each turn and seeks/highlights using the
absolute word times. Legacy solo sidecars without speaker fields remain compatible.

## Provider seam (implemented)

`backend/dialogue.py` returns provider-agnostic `turns_narration_inputs`, and
`pipeline.narrate` branches single-host vs dialogue. A future
`backend/voice.py` can implement `ElevenLabs`, `Chatterbox` and `Gemini` behind
one `synthesize(inputs) -> bytes` call without touching the editorial pipeline.
