# Ingestion sources: free academic-metadata / full-text APIs

Survey of free (or freemium) sources we can add to the paper-ingestion surface for
Zwicky episodes. Verified live with `curl` on 2026-09-21 (short timeouts, no cache,
no keys except where noted). Where a source blocked, timed out, or required an email
we did not have, that is stated rather than inferred from docs.

Per paper we want: title, authors, abstract, full text (ideally), publication date,
journal/venue, license, DOI/ids, and citation/attention signals.

We already use PLOS, arXiv, Europe PMC (`fullTextXML`), OpenAlex, and Crossref.

## Prioritized table

| Source | Auth | What it unlocks | License / risk | Effort | Field coverage |
|---|---|---|---|---|---|
| **Unpaywall** | none, **email required** | OA resolver for any DOI: best OA location, `url_for_pdf`, `license`, `oa_status`, version | License comes from the OA location; safe if we honor the per-record `license`. No key. | **Low** | All fields |
| **CORE** (core.ac.uk) | **free key** (anon works at ~10/min) | Full-text aggregator: `fullText`, `downloadUrl`, abstract, authors, DOI, `citationCount`, `fieldOfStudy`, journal | Per-item license is **not always present** — must resolve/verify before commercial reuse. Some items all-rights-reserved. | Low–Med | All fields |
| **Semantic Scholar Graph** | **free key** (no-key 1 rps, batch 429s) | `abstract`, `tldr`, `openAccessPdf` (+`license`), `citationCount`, `influentialCitationCount`, venues, authors | API free; honor returned license; S2 API terms restrict bulk redistribution. | Low | All fields |
| **bioRxiv / medRxiv** | none | Preprint metadata + `abstract`, `jatsxml` full-text link, `license`, published-journal DOI link | Per-preprint `license` (often CC BY/CC BY-NC-ND). | Low | Life sciences |
| **PubMed E-utilities** | none (3 rps) or **free NCBI key** (10 rps) | Biomedical abstracts (efetch XML), MeSH, ids; no full text | US Gov public domain metadata; abstracts per publisher terms. | Low | Biomedicine |
| **OpenAIRE** | none | OA aggregation: `bestaccessright`, OA color, `license`/rights, full-text links, funding | Aggregated rights; verify per record. | Med | All fields |
| **DOAJ** | none | OA journal + article metadata: abstract, authors, fulltext link, journal license, subjects | Only vetted OA journals; journal license is explicit. | Low | All fields |
| **HAL** | none | French/institutional OA: title, `abstract_s`, `uri_s`, DOI, license | Per-record; mixed. | Low | All fields |
| **OSF Preprints / PsyArXiv** | none | Preprint metadata, description, license, subjects (OSF HTTP API) | Per-record license; full text via OSF storage. | Med | Social/psych + all |
| **eLife** | none | Journal metadata + CC BY articles; full text via their site | CC BY. | Low | Life sciences |
| **PMC OA subset** | none (legacy oa.fcgi **404**) | Bulk OA packages via AWS S3 `pmc-oa-opendata` (HTTP 200); or Europe PMC (already integrated) | Per-article; subset licenses vary (some NC). | Med | Biomedicine |
| **Crossref** | none (polite `mailto`) | Metadata, sometimes abstract, license URLs, references | Metadata is open; abstracts often absent. | done | All fields |
| **OpenAlex** | **free key** | Metadata, abstract (inverted index), topics, citations | CC0 metadata. | done | All fields |
| SSRN | none | — | **Unverified (403) and terms hostile to commercial scraping. Deprioritize.** | — | Social/business |
| Research Square | none | — | **Could not connect (000). Commercial reuse unclear. Deprioritize.** | — | Life sciences |
| SciELO | none | ArticleMeta/OAI exists but probes **404/403** | **Unverified.** | Med | Latin America / all |
| Internet Archive Scholar / fatcat | none | — | **Unverified:** scholar.archive.org redirects to bot-check; `api.fatcat.wiki` times out. | — | All fields |
| F1000 / Wellcome Open Research | none | Articles are CC BY, but our guessed API URLs failed (000/404) | **Unverified endpoint.** | Med | Life sciences |

## Live verification log (what actually happened)

- `api.unpaywall.org/v2/...?email=test@example.com` → **422** ("use your own email");
  with a real-looking address → **200**, returns `best_oa_location`, `license: cc-by`,
  `url_for_pdf`. Confirmed email-only, no key.
- `api.core.ac.uk/v3/search/works/?q=test` → **301 → 200**, 6.5M+ hits; no key needed,
  `x-ratelimit-limit: 10`. Bogus `Authorization: Bearer` → **401**, so keys are honored.
  Result fields include `fullText`, `downloadUrl`, `sourceFulltextUrls`, `abstract`,
  `citationCount`, `fieldOfStudy`; **no license field** on the sample we pulled.
- `api.openalex.org/...` without key → **429** (`$0` shared daily budget on this IP).
  We already hold a free key, so this is only an unauthenticated-probe artifact.
- `api.crossref.org/works/...` → **200**; abstract absent for both samples; license URL
  present. `is-referenced-by-count` available.
- `api.semanticscholar.org/graph/v1/paper/...` → **200** with `abstract`, `tldr`,
  `openAccessPdf{url,status,license}`, `citationCount`, `publicationDate`. Single-paper
  no-key works; **batch POST without key → 429**.
- `eutils.ncbi.nlm.nih.gov/esummary|efetch` → **200** XML/JSON abstracts.
- `api.openaire.eu/search/publications` → **200**; Graph v1 needs `pageSize` (not
  `size`) and aggregate-by-id path returned 405. Fields include `bestaccessright`,
  `openaccesscolor`, `license`, `fulltext`.
- `doaj.org/api/search/articles/...` and `/api/v2/...` → **200**; no key; `bibjson`
  has abstract, authors, `link[type=fulltext]`, journal. Journal license was `null`
  on our sample.
- `api.biorxiv.org/details/biorxiv|medrxiv/...` → **200** with `abstract`, `license`,
  `jatsxml`, `doi`; published link appears in the `published` field when available.
- `api.archives-ouvertes.fr/search/` (HAL) → **200**, `title_s`, `abstract_s`, `uri_s`.
- `api.osf.io/v2/preprints/` → **200**, metadata + `description`, `license_record`.
- `api.elifesciences.org/search` → **200** (limited fields returned). Article-by-DOI
  path we tried → **404** (wrong scheme, not necessarily unavailable).
- `pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi` and `www.../pmc/utils/oa/oa.fcgi` → **404**
  for every id tried (including known OA ids); FTP `oa_file_list.csv` → **404**. Legacy
  OA Web Service appears decommissioned at these paths. `pmc-oa-opendata.s3.amazonaws.com`
  → **200** (current bulk route).
- `search.scielo.org` → **403**; `old.scielo.br` → **000**; `articlemeta.scielo.org`
  article path → **404**.
- `api.ssrn.com/...` → **403**.
- `api.researchsquare.com/...`, `api.f1000research.com/...`, `api.fatcat.wiki/...` →
  **000** (connection failure/timeout). `scholar.archive.org` → 302 to `/verify`.
- `export.arxiv.org/api/query` → **200**; Europe PMC `fullTextXML` → **200** (existing).

## Recommended connector roadmap

Customer value per unit effort is highest for these three, in order:

1. **Unpaywall (no key, email only).** Normalizes OA resolution and license for *every*
   DOI we already touch via Crossref/OpenAlex. Fastest win, and the `license` field is
   the cleanest signal we can gate commercial summarization on. Low risk.
2. **CORE (free key).** The only free source here that returns raw `fullText` at scale
   across physical/social sciences, plus a PDF `downloadUrl`. This is our main lever to
   move from abstract-only to full-text episodes beyond PLOS/Europe PMC. Must resolve
   per-item license (often missing) before reuse.
3. **Semantic Scholar Graph (free key).** Adds `tldr` (a ready-made hook signal) and
   `citationCount`/`influentialCitationCount` (attention), plus another OA PDF source.
   Complements OpenAlex metrics and gives us a second abstract when Crossref lacks one.

Secondary/backlog: **bioRxiv/medRxiv** (preprint freshness for life-science shows),
**PubMed E-utilities** (deep biomedical abstracts; free NCBI key for 10 rps),
**DOAJ/OpenAIRE/HAL/OSF** (breadth for OA and non-US/EU venues). **PMC OA** is best
consumed through Europe PMC (already integrated) or the S3 bulk bucket, not the dead
`oa.fcgi` endpoint. **Avoid SSRN** (403 + restrictive terms). Keep Research Square,
SciELO, IA Scholar/fatcat, and F1000 on an unverified watchlist until endpoints and
terms are confirmed.

## Free keys to obtain

| Key | Signup URL | What it unlocks |
|---|---|---|
| **CORE API key** | https://core.ac.uk/services/api | Raw `fullText` + `downloadUrl`, higher rate limits than the ~10/min anonymous tier |
| **Semantic Scholar API key** | https://www.semanticscholar.org/product/api#api-key-form | Higher rate limits, including the batch endpoint that 429s anonymously |
| **NCBI API key** | https://www.ncbi.nlm.nih.gov/account/settings/ | E-utilities at 10 req/s instead of 3 (PubMed, PMC) |
| **OpenAlex key** | https://openalex.org/settings/api | Already configured; keeps our own budget instead of the shared `$0` pool |
| Unpaywall | *(no key)* | Supply a real contact email in every request; `email=test@example.com` is rejected (422) |
| Crossref | *(no key)* | Add `mailto=` for the polite pool |
| DOAJ, OpenAIRE, bioRxiv/medRxiv, HAL, OSF, eLife, arXiv | *(no key)* | None needed |

## Commercial-use cautions

- **SSRN** (Elsevier): blocked us (403) and its terms do not permit commercial scraping
  or republication. Do not build on it without a license.
- **CORE:** excellent reach, but license is frequently absent from the record. Treat
  "no license" as all-rights-reserved and do not narrate until checked.
- **Semantic Scholar:** the API is free, but its terms restrict wholesale
  redistribution of the corpus; use it to enrich, not to mirror.
- **PMC:** the OA subset contains some non-commercial licenses; filter on license.
- **Unpaywall/DOAJ/OpenAIRE/HAL/OSF/bioRxiv/eLife:** rely on the returned `license`
  field per item and only summarize CC-licensed or explicitly reusable content.

## Could not verify

- **SciELO** (403/404/000), **SSRN** (403), **Research Square** (000),
  **F1000 / Wellcome Open Research** (000/404 on guessed endpoints),
  **Internet Archive Scholar / fatcat** (302 bot-check; `api.fatcat.wiki` timed out),
  and the **legacy PMC OA Web Service** (all ids 404).
- We also could not exercise **CORE with a real key** or **Semantic Scholar with a real
  key**, so the rate limits above are the anonymous observations.
