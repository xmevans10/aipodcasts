# Episode sound design

The daily and full-batch GitHub Actions renderers use `tools/tts/bundle_shows.py`. Each approved solo script is rendered by editorial paragraph; co-hosted scripts are rendered by speaker turn. The daily workflow supports Google Cloud Gemini TTS (`--tts-provider google-cloud`); the full-batch workflow defaults to Kokoro. Google rendering uses the stable `gemini-2.5-flash-tts` model through Cloud Text-to-Speech, requests EU-region mono 24 kHz PCM, and retries transient 429/500/503 responses up to three times. Host voice assignments live in `tools/tts/voice_cast.json`; both providers use the same timing, stinger, packaging, and feed steps. The GitHub OIDC provider is configured, but the daily workflow still needs a least-privilege service-account impersonation binding before it can authenticate.

The daily workflow can render with Google Cloud Gemini TTS (`--tts-provider google-cloud`). It uses the stable `gemini-2.5-flash-tts` model through Cloud Text-to-Speech, authenticates with GitHub OIDC/Workload Identity Federation, and requests EU-region mono 24 kHz PCM. Host voice assignments live in `tools/tts/voice_cast.json`; the existing timing, stinger, packaging and feed steps are shared with Kokoro. The provider retries transient 429/500/503 responses up to three times.

- An approximately 1.6-second opening signature generated from the episode's 16-hex-digit ID. Eight notes each encode one byte as pitch, duration, and brightness, so different IDs yield different stinger audio while re-renders of the same episode remain stable.
- Up to two quiet effects at section breaks, alternating two [Kenney CC0](../assets/audio/kenney/SOURCES.md) recordings. No effect plays over speech. Short episodes receive no internal cue.
- A soft closing jingle after the last word.

The three source recordings and their hashes are recorded in [SOURCES.md](../assets/audio/kenney/SOURCES.md). Legacy demo effects under `assets/audio/` are not used by this renderer because their rights records are missing.

Word timestamps include the opener and transition gaps, so read-along highlights stay aligned with the final audio. The episode JSON records a SHA-256 fingerprint of the opening signature. The mixing step is local and uses only Python's standard library; the GitHub Actions renderers already provide FFmpeg for AAC encoding.

For a quick check, run `python3 -m pytest -q backend/tests/test_sound_design.py backend/tests/test_bundle_shows.py`. Before publishing a new mix, listen to the opening, both section cues, and ending on the rendered artifact, and check that speech remains clear at normal phone volume.
