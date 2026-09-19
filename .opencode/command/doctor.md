---
description: Show which API keys and host voices are configured (no network, no secrets).
subtask: true
---
Run `python3 backend/pipeline.py doctor` and summarise, for the user:

- the selected `VOICE_PROVIDER` and whether its key/url is present;
- whether the OpenAI writer key is set and which model;
- which of the 20 host voice variables are configured vs empty;
- the public origin and provider-call limits.

Then state exactly which keys are still needed to produce a real episode. $ARGUMENTS
