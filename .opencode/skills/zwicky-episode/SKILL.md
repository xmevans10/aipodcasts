---
name: zwicky-episode
description: Produce a Zwicky episode through the editorial pipeline. Use when the user says episode, produce, draft, narrate, publish, pipeline, ingest, DOI, or names a host; covers discover/ingest/draft/approve/narrate/publish and voice providers.
---

# Produce a Zwicky episode

Operator CLI (stdlib Python). Human approval is a real gate; never auto-approve.

```bash
python3 backend/pipeline.py doctor                 # which keys/voices are configured
python3 backend/pipeline.py discover               # recent PLOS items
python3 backend/pipeline.py ingest <doi> --host <host_id>
python3 backend/pipeline.py draft <id>
python3 backend/pipeline.py inspect <id>           # review the draft + evidence
python3 backend/pipeline.py approve <id> --reviewer 'Name'   # human step
python3 backend/pipeline.py narrate <id>
python3 backend/pipeline.py publish <id>
```

Voice provider is chosen by `VOICE_PROVIDER`: `elevenlabs` (default), `openai`, or `local`
(a self-hosted HTTP TTS; no key). Co-hosted shows (Ground Truth, Star Bros) use
ElevenLabs text-to-dialogue automatically. See `docs/INTEGRATIONS.md`.

Hosts live in `backend/hosts.py`; dialogue shows in `DIALOGUE_SHOWS`. Validation lives in
`backend/dialogue.py` and `backend/podcast.py` and enforces headline, first-author credit,
verbatim limitations, host sign-offs and verbatim evidence quotes. Do not weaken it.
