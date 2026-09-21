# Story-discovery signals: publicity and expert reaction

How Zwicky decides *which* recently published paper is worth an episode, before the
rights gate and evidence selection decide what can actually be narrated. The paper
itself always supplies the script's evidence; publicity and expert reaction are used
only to *find* and *check* the paper, never as evidence.

## Priority order

| Priority | Source | How Zwicky uses it |
|---|---|---|
| 1 | **EurekAlert** + originating university/journal press office | Find papers someone already judged worth explaining publicly. Press-release presence improved media-coverage prediction in a study of 91,997 papers — evidence of likely interest, not scientific reliability. |
| 2 | **Quanta, Nature News, Science News** feeds | Independent editorial discovery signals. Follow their paper links, then retrieve evidence through the existing connectors. This is a recommendation, not a measured ranking. |
| 3 | **ScienceDaily, Phys.org** | Breadth only, and only to identify the originating release. One university release appearing on EurekAlert, ScienceDaily and Phys.org is **one publicity event**, not three endorsements. Both republish institutional material. |
| 4 | **OpenAlex → PLOS / Europe PMC / full-text connectors** | Discovery route for papers with no publicity. Prefer candidates with enough licence-clear evidence to verify the episode; press attention is never required. Coverage does not reliably favour stronger study designs. |
| 5 | **arXiv + Hugging Face Daily Papers**, selectively | AI, physics and astronomy beats. Community attention is a lead; preprint status is an explicit caveat. No evidence HF upvotes predict general-audience listening. |

**Checking source (not discovery):** the **Science Media Centre**'s public expert
reactions, especially for brain, sleep, climate and health-adjacent stories. It supplies
expert commentary and statistical context; use it to identify caveats worth checking
against the paper. It is not an endorsement and never enters the evidence packet.

## Live verification log (2026-09-21)

Checked with `curl` (short timeouts, descriptive User-Agent, no cache). Where a source
blocked, 404'd or had restrictive terms, that is stated rather than inferred from docs.

### EurekAlert has no public RSS or API

- `/rss/…`, `/rss.xml`, `/feed`, `/news-releases/rss` → **404**. The old
  `/api/v2/releases` route is decommissioned: it returns the site's Symfony 404 JSON.
- `api.eurekalert.org` does not resolve (`000`). `mediasvc.eurekalert.org` exists but
  serves only multimedia renditions (`/Api/v1/Multimedia/…`), not release metadata.
- The public discovery surface is the **sitemap**: `https://www.eurekalert.org/sitemap.xml`
  indexes per-month sitemaps (`/sitemap/2026-09/sitemap.xml`). The current month held
  **2,307** releases. Each `<url>` carries `<news:publication_date>`, `<news:title>` and
  `<news:keywords>`; genres are `PressRelease`.
- Individual release pages (`/news-releases/<id>`, e.g. `1142182`) return **200**,
  server-rendered, with `og:title`/`og:description` and the original paper DOI as a
  `dx.doi.org` link (sample: `http://dx.doi.org/10.1021/jacsau.6c00596`). No JSON-LD.
- `robots.txt` allows individual `/news-releases/<id>` (only `/news-releases/browse`,
  `/bysubject/`, `/pub_releases/` etc. are disallowed). Fetch sparsely and politely.

**Terms constraint (important).** EurekAlert's `/terms` forbids reproducing,
redistributing or commercially using Website Content without prior written permission.
The safe design is therefore **signal-only**: keep the DOI and publication date as a
derived "this paper was publicized" fact, read any title/description transiently to
resolve the DOI, and **do not persist, reproduce or narrate release text**. Evidence
still comes from the paper connectors.

### Science Media Centre (sciencemediacentre.org)

- Public WordPress RSS works: `https://www.sciencemediacentre.org/feed/` (**200**,
  `application/rss+xml`, ~309 KB, 20 items). A category feed exists but the
  `expert-reactions` slug returned empty.
- Expert reactions are identifiable by title prefix **"Expert reaction to …"** and by
  categories such as `brain & neuroscience`, `sleep`, `climate change`, `cancer`,
  `mental health`, `microplastics`, `long COVID`.
- No explicit reuse licence was found on the terms/about pages (only a copyright
  footer). Use reactions only to derive **caveats to check**, paraphrased as
  verification questions — never reproduce the commentary or treat it as evidence.

## Design implications

1. **One publicity event, one signal.** Collapse EurekAlert, ScienceDaily, Phys.org and
   press-office copies of the same release (same DOI, else originating URL/fuzzy title)
   into a single event. Event breadth must not raise the score — that is the whole point.
2. **Press can seed discovery.** A publicized DOI should be resolvable to a paper even
   when no beat query surfaced it. Fetch the paper from OpenAlex/Crossref by DOI.
3. **Independent editorial stays separate.** Quanta/Nature/Science News count as their
   own discovery signal, not as syndication of a press release.
4. **Evidence provenance is unchanged.** Releases and expert reactions never reach the
   evidence packet (`backend/evidence.py`) or the verifier's claim quotes
   (`backend/verify.py`). SMC only adds caveat questions.

## Implementation status

**Phase 1 — publicity events, one RRF signal (done).** `backend/publicity.py` clusters
feed releases into events: DOI match first, fuzzy title merge for copies that never
resolve to a DOI. Sources are classified `PRESS` / `INDEPENDENT` / `SYNDICATORS`;
`publicity_value()` is `1.0` for a press event regardless of how many syndicators
carried it, and `editorial_value()` is `1.0` only for an independent outlet.
`autoselect.select` now fuses an eighth signal, `publicity` (weight `0.25`), and scores
`editorial` (`0.20`) only from independent feeds — ScienceDaily and Phys.org still get
fetched to corroborate events but no longer cast an editorial vote. Weights:
`publicity .25 / editorial .20 / community .08 / impact .12 / reputation .12 /
studiness .13 / recency .05 / fascination .05` (sum `1.00`). Covered by
`backend/tests/test_publicity.py` and an autoselect integration test.

**Phase 2 — EurekAlert ingestion (done).** `backend/eurekalert.py` walks the sitemap index
and the per-month sitemaps, filters to the window (newest first), and reads up to
`max_pages` (default 120) release pages transiently to extract the DOI. Nothing but the
derived `(doi, date)` leaves the module — no release text is stored, reproduced or
narrated, per EurekAlert's terms. `autoselect.load_releases` appends these signal-only
releases when a window is supplied; disable with `LILT_EUREKALERT=0`. Press-seeded
discovery (`autoselect.seed_publicized`) fetches metadata for a publicized DOI from
OpenAlex/Crossref even when no beat query surfaced it, then assigns the best-matching
beat and re-applies the same fit/license/reputation gates. Verified live: sitemap parse
returned real releases with DOIs. Covered by `backend/tests/test_eurekalert.py` and a
seeding test.

**Phase 3 — tier ordering + measurement (done).** Weights order the sources
`publicity .25` (tier 1 press) `> editorial .20` (tier 2 independent) `> community .08`
(tier 5 HF), with impact/reputation/studiness/recency/fascination filling the middle.
`autoselect.fuse` is callable in isolation and treats `publicity`/`editorial`/`community`
as **presence signals**: a candidate without the signal gets no contribution, exactly as
a document absent from a retrieval list scores nothing in RRF. (Ranking absent
candidates as a tied tail made the boost shrink toward zero as the candidate pool grew.)
Ties among equal values share a rank, so list order cannot decide a signal.
`experiments/selection/publicity_effect.py` measures the effect on a synthetic corpus:
baseline order is `both > publicized > editorial > high-impact > fascinating > no-signal`,
turning publicity off drops the publicized paper to last, top-3 survives halving or
raising the publicity weight, and one publicized paper among 200 otherwise-equal ones
keeps its full boost. A live run exposed — and fixed — two more issues: seeded press
papers were bypassing the recency window, and the original tie handling let list position
outrank signal.

**Phase 4 — SMC caveats (done).** `backend/smc.py` reads the public
`sciencemediacentre.org/feed/`, keeps the `Expert reaction to …` posts, and maps the
show's beat to SMC categories (`HOST_TOPICS`) so only relevant reactions are surfaced
(brain, sleep, climate, health-adjacent). `verify.verify_draft` takes an optional
`caveats` list and adds one typed question — "does the script acknowledge the caveats
raised by these expert reactions?" — with the reactions in the verifier's state. It is
opt-in via `LILT_SMC=1` and best-effort: a feed failure fails open to no question.
Reactions never enter the evidence packet or the script. Verified live: 18 reactions
parsed; `lena` matched the REM-sleep reaction and `ada` the brain ones. Covered by
`backend/tests/test_smc.py`.

## Weekly full run

`experiments/full-run/run_all_shows.py` runs the whole chain — select → ingest → draft →
verify — for every show and writes one transcript per show plus a manifest. `.github/workflows/full-run.yml`
runs it every Monday (`0 13 * * 1`) and on demand, uploading `full-run-artifacts/` as a
build artifact. Required repo secrets: `OPENAI_API_KEY`, `LILT_OPENALEX_KEY`,
`LILT_CONTACT_EMAIL`; optional: `CORE_API_KEY`, `DEEPSEEK_API_KEY`, `TYPESAFE_AI_API_KEY`.
The per-run provider cap is raised to 96 because the run drafts every show. It never
narrates or publishes.

