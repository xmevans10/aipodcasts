# Episode sound design

The daily and full-batch GitHub Actions renderers use `tools/tts/bundle_shows.py`. Each approved solo script is rendered by editorial paragraph; co-hosted scripts are rendered by speaker turn. `tools/tts/sound_design.py` then adds:

- An approximately 1.6-second opening signature generated from the episode's 16-hex-digit ID. Eight notes each encode one byte as pitch, duration, and brightness, so different IDs yield different stinger audio while re-renders of the same episode remain stable.
- Up to two quiet effects at section breaks, alternating two [Kenney CC0](../assets/audio/kenney/SOURCES.md) recordings. No effect plays over speech. Short episodes receive no internal cue.
- A soft closing jingle after the last word.

The three source recordings and their hashes are recorded in [SOURCES.md](../assets/audio/kenney/SOURCES.md). Legacy demo effects under `assets/audio/` are not used by this renderer because their rights records are missing.

Word timestamps include the opener and transition gaps, so read-along highlights stay aligned with the final audio. The episode JSON records a SHA-256 fingerprint of the opening signature. The mixing step is local and uses only Python's standard library; the GitHub Actions renderers already provide FFmpeg for AAC encoding.

For a quick check, run `python3 -m pytest -q backend/tests/test_sound_design.py backend/tests/test_bundle_shows.py`. Before publishing a new mix, listen to the opening, both section cues, and ending on the rendered artifact, and check that speech remains clear at normal phone volume.
