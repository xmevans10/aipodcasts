# Experiments

Isolated, non-production tooling. Nothing here is imported by the app, the
server or the editorial pipeline. It makes paid provider calls only when run.

- `article_ab.py` — generates a labelled matrix of draft scripts over models,
  prompt variants and thinking on/off. Mirrors the production draft contract
  (same evidence packet, `PODCAST_INSTRUCTIONS` + host guide, same validators)
  but never writes to `lilt.sqlite3` and never publishes.
- `ai_judge.py` — collects every valid draft from `ab/` plus the bundled
  baseline scripts, strips provenance, and scores each one blind with two
  DeepSeek judges. Results are cached in `ab/judge-cache.json`.
- `ab/` — run outputs: `results.json`, readable `report.md` per run, and the
  aggregate `JUDGE.md` / `judge-results.json`.

Run from the project root:

```
python3 experiments/article_ab.py --runs 2
python3 experiments/ai_judge.py
```

The anti-AI-slop writing guide and detector (`backend/anti_slop.py`) are now
part of the production draft prompt; see `docs/OPERATIONS.md`.

Requires `DEEPSEEK_API_KEY` (and `OPENAI_API_KEY` for the `luna-*` variants) in
`backend/.env`. Never commit that file.
