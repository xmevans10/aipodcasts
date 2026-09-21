# API access requests (CORE, Semantic Scholar, NCBI, Unpaywall)

A reusable pack for requesting research-data API access for Zwicky. Replace every
`[…]` placeholder, then paste the relevant section into each provider's form or email.
Two framings are given where a provider asks about commercial use, so you can answer
honestly without rewriting from scratch.

---

## 1. Reusable boilerplate

### About the project — long

Zwicky is a science-listening app: short (3–5 minute) source-linked audio explainers of
recent research, read by clearly labelled synthetic hosts across a set of themed shows.
We are an early-stage, private-beta product with a small editorial team. For each
episode we identify a worthwhile recent paper, read its public metadata and abstract
(and its open-access full text only where the licence clearly permits reuse), then write
an original spoken summary that credits the authors, names the journal, states the
study's limitations, and links to the paper. We do not reproduce or redistribute source
articles; we summarise them and point listeners to the original.

### About the project — short

Zwicky turns recent research into short, source-linked science audio for a general
audience. We summarise papers and link to them; we do not redistribute articles.

### How we use your data

We use your API to look up a small number of records by DOI/identifier to retrieve
metadata, abstracts, open-access location, licence, and basic citation information. That
information feeds an attribution card and a draft spoken summary that a human editor
reviews. We request record-by-record, cache minimally, set a descriptive `User-Agent`
with a contact address, and stay far below published rate limits. We do not bulk
download, mirror, resell, or expose your data as a searchable corpus, and we do not use
it to train models.

### Our licence and attribution policy (we are happy to sign terms)

- We reuse full text only when the record's own licence permits it (CC BY, CC0 or public
  domain). We exclude NonCommercial, NoDerivatives and ShareAlike licences from reuse.
- Where a paper is not licence-clear, we use only its public abstract and metadata to
  write an original summary, and we never reproduce the article.
- Every episode shows author credit, journal, and a direct link to the source.

### Technical profile

- Server-side only, standard-library Python; no browser harvesting.
- `User-Agent: ZwickyResearch/0.1 (mailto:[your-email])`.
- Expected volume: `[e.g. a few thousand metadata lookups per month; dozens to low
  hundreds of full-text fetches]`; we cache responses and set timeouts.
- Contact: `[Your name]`, `[email]`, `[organisation / project URL]`.

---

## 2. Provider-specific requests

### 2a. CORE (`https://core.ac.uk/services/api`)

CORE asks who you are, what you are building, and how you will use the API (and often
about commercial use). Suggested wording:

> **What are you building?** Zwicky, a short-form science-listening app
> (`[project URL]`). We produce 3–5 minute source-linked audio explainers of recent
> research.
>
> **How will you use the CORE API?** To resolve open-access full text and metadata for a
> small set of recent papers we are already covering — primarily a per-record lookup of
> `fullText`, `downloadUrl`, `abstract`, authors, DOI and licence. CORE would let us
> ground summaries in open-access text instead of abstracts alone.
>
> **Volume and behaviour.** Low volume: `[N]` lookups per month, cached, rate-limited,
> with a descriptive User-Agent and contact email. We do not bulk download or mirror the
> corpus.
>
> **Licensing.** We will honour the licence of each CORE record and restrict reuse to
> CC BY / CC0 / public-domain items; where the licence is missing or restricted we fall
> back to metadata and abstract only. We are happy to discuss a commercial data licence
> if our use requires one.

Caveat to expect: CORE's per-record licences are sometimes missing. If a commercial
licence is required for your tier, ask; otherwise restrict to clearly CC-licensed items.

### 2b. Semantic Scholar (`https://www.semanticscholar.org/product/api#api-key-form`)

The form asks for a use case and sometimes commercial/affiliation details. Suggested
wording:

> **Use case.** Zwicky (`[project URL]`) produces short, source-linked science audio. We
> use the Semantic Scholar Graph API for per-paper metadata and abstracts to attribute
> and summarise recent research, and `tldr` as an internal signal for which papers are
> coverable. We request `paper/search`, `paper/{id}`, and batch lookups by DOI.
>
> **Volume.** `[N]` requests per month, cached and rate-limited; no bulk export, no
> mirroring, no model training on the corpus.
>
> **Commercial status.** Zwicky is `[an early-stage product / a not-for-profit
> prototype / a commercial product in private beta]`. We are glad to comply with your
> API terms and to discuss any commercial agreement your terms require.

Caveat: Semantic Scholar's terms restrict corpus mirroring and may restrict commercial
use; state your status honestly and ask which tier fits.

### 2c. NCBI E-utilities (`https://www.ncbi.nlm.nih.gov/account/settings/`)

NCBI mainly needs an account and a valid contact email; the key raises the limit from 3
to 10 requests/second. Provide the standard tool/email identification:

> **Tool:** `zwicky`
> **Email:** `[your-email]`
> **Usage:** server-side E-utilities (ESearch/ESummary/EFetch) to retrieve PubMed
> metadata and abstracts for individual recent papers we cover, one at a time. Low
> volume (`[N]` requests/day), cached, with a descriptive User-Agent; we honour the
> 10 requests/second and bulk-download limits and will not scrape the site.

### 2d. Unpaywall (no key — just a real email)

Unpaywall requires no application, only a valid `email=` on each request. Use:

> `email=[your-email]` (we already hold this as `LILT_CONTACT_EMAIL`)

Purpose to record in your notes: resolve the best open-access location and licence for
each DOI we cover, so we prefer licence-clear full text and fall back to abstracts
otherwise.

---

## 3. One-line blurbs (for short fields)

- **Project:** "Zwicky — short, source-linked science audio that summarises recent
  research and links to the paper (`[project URL]`)."
- **Use:** "Per-record metadata, abstracts and open-access text for papers we summarise;
  low volume, cached, rate-limited, no bulk download or mirroring."
- **Commercial:** "Early-stage product in private beta; happy to comply with your terms
  and to discuss any commercial licence your use requires."

---

## 4. Notes on honest framing

- Do **not** describe the project as non-commercial if it is intended as a paid product;
  answer the commercial question truthfully and ask which tier you need.
- Emphasise the behaviours that matter to providers: per-record requests, caching, a real
  contact email, a descriptive user agent, no mirroring, no model training, and a
  per-record licence policy.
- Keep a copy of what you submitted per provider, and of any terms you accepted, next to
  this file.
