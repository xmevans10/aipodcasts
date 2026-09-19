---
description: Commit the working tree incrementally, one logical change per commit, with explanations.
---
Commit the current work using the repo's rule: incremental, one logical change per commit,
with a clear imperative subject and a body explaining what changed and why.

1. Inspect `git status`, `git diff` and `git log --oneline -5` first.
2. Group the changes into logical commits (not one grab-bag). Stage only the files for
   each change; never stage secrets or generated output (`backend/.env`, `*.p8`, `build/`).
3. After each commit, `git push origin main`.
4. Report each commit hash and what it does.

Scope/notes: $ARGUMENTS
