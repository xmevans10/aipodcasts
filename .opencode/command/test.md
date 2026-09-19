---
description: Run Zwicky's backend and iOS logic checks and report results.
subtask: true
---
Run the project checks and report pass/fail counts and any failures verbatim.

1. `python3 -m pytest -q backend/tests`
2. `./scripts/run-ios-tests.sh`
3. If any iOS source changed, also run the Release simulator compile from the `zwicky-test` skill.

Do not fix anything yet unless asked. Extra scope: $ARGUMENTS
