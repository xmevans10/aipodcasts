# Show-source audit — 2026-10-16

## Finding

The previous pipeline did not guarantee already-covered stories. It could discover
obscure papers through broad keyword queries and boost them using fuzzy headline
matches. Sharing a word with a show's subject was sometimes enough to route a paper.
The release path could also bypass a failed audience review.

The intended policy is simple: choose research that an established science outlet is
already covering, keep only stories whose central question fits a show, and explain
the primary evidence in everyday language. One credible outlet is enough. We do not
have readership data and do not claim a measured popularity threshold.

## Published inventory checked

Read the public app feed: **34 episodes across 16 shows**. Checked the newest episode
per show against its linked paper's Crossref metadata: **12 resolved**, **4 remained
unverified in this check**. Ten of the resolved records had abstracts; two provided
only titles/metadata. This was a source/niche triage, not a sentence-level factual audit.

| Show | Latest episode's primary source | Finding |
|---|---|---|
| Gradient | Nature — language models operating over bytes | Literal AI/ML fit |
| Signal & Noise | DOI 10.1016/j.visinf.2026.100367 | Metadata lookup failed; investigate before reuse |
| The Deep | DOI 10.1111/febs.70737 | Metadata lookup failed; investigate before reuse |
| Hive Mind | Honeybee pollen segmentation, Dokuz Eylül engineering journal | Bee-related, but primarily a computer-vision methods study; needs central-question review |
| Mycelium | Agribusiness — consumer preferences for fungus-resistant wine | Marketing/consumer behaviour, not fungal biology |
| Marginal Gains | Uzdanica — aerobic exercise and childhood coordination | Literal exercise fit; major-outlet coverage not established |
| Star Stuff | Astronomy & Astrophysics — sulfur in star-forming cores | Literal astrochemistry fit |
| Webwork | Ocean Engineering — a web-type mooring system | Clear mismatch: engineering geometry, not spiders |
| The Long View | DOI 10.3847/2041-8213/ae80a0 | Metadata lookup failed; investigate before reuse |
| Common Ground | Science Advances — Enceladus ice grains | Space/planetary research, not Earth's climate |
| Wild Company | Royal Society Interface — bird surveillance and virus modelling | Borderline: epidemiological modelling; needs central-question review |
| Layer by Layer | Tehnički glasnik — additively manufactured structures | Literal fabrication fit; major-outlet coverage not established |
| Ground Truth | DOI 10.1016/j.molcel.2026.08.003 | Metadata lookup failed; episode title suggests biological DNA replication, which is not statistical replication |
| Star Bros | Astronomy & Astrophysics — nearby radio galaxies | Literal astrophysics fit |
| Old Bones | Journal of Archaeological Science — ancient DNA lineage | Title-level fit; Crossref abstract absent |
| Slow Wave | Journal of Sleep Research — circadian preferences | Literal sleep/circadian fit |

An HTTP lookup failure does not prove a DOI or study is invalid. No recorded
major-outlet coverage trail was available in these published feed entries, so literal
fit alone does not establish that any particular story was already semi-popular.

## Discovery connectors checked live

Fetched the five configured feeds and inspected three current items per feed.
Quanta, Science, ScienceDaily and Phys.org returned feeds with 5, 10, 60 and 30 items
respectively. Nature's first response was not parsable by the audit; a subsequent
request returned valid RDF RSS with 75 items. Treat intermittent/empty responses as
visible source failures, never as permission to fill slots with uncovered papers.

The sample exposed two important linking problems. Quanta uses direct primary-publisher
links such as IOP and Nature, not just doi.org links. Science's feed can identify the
news article with its own DOI; that DOI must not be mistaken for the study it describes.
Some news articles contain no single identifiable study and should be skipped.

## Implemented controls

- Production starts from current dated major-source coverage, following explicit paper
  identifiers rather than guessing by headline. Retain outlet, headline, URL and feed
  position in selection reports and generation artifacts.
- Recognize DOI links on primary-publisher sites and canonical Nature research links;
  distinguish news identifiers from study identifiers. Unresolved links are skipped.
- Rank eligible covered stories before balancing shows. Coverage freshness controls
  timeliness; an older paper newly covered by an outlet can still qualify.
- Require literal niche fit, followed by a `grounded` audience-review judgment about the
  central question and measured outcome. Weak fit requires reselection, not a rewrite
  that manufactures an angle.
- Remove the entertainment-release bypass from approval, batch validation and rendering.
  Approved partial batches can supply the daily slots; missing niches stay empty.
- Incorporate avoid-ai-writing v3.38.0 preservation rules into writing and detailed
  review prompts. Keep scientific verification separate from clarity and personality.

Published episodes have not been regenerated or withdrawn by this code change. The
mismatches above need editorial disposition; older audience reports need fresh review
under v5 before reuse. Direct preprint-only links that cannot resolve to the current
paper connectors remain an abstention, not guessed coverage.

## Activation follow-up

The first production smoke batch (Actions 38954087182) exposed two additional
false fits despite audience approval: galaxy dark matter was assigned to Star Stuff,
and hippocampal plasticity to Gradient because it used a neural network. Neither
was published. Selection v2 now assigns the central source question and measured
outcome to a show before writing, without exposing the proposed host or script to
the classifier. Explicit scope boundaries also reach audience review v6.

Narration and publication reject legacy batches and prepared audio. Published
records carry matching source coverage, source-only show assignment, policy
versions and a hash of the delivered script. Generation runs daily before overnight
preparation; empty niches remain empty rather than receiving forced fits.

## Live adoption verified — 2026-10-16

- Reviewed generation: Actions `38958923899`; targeted numeric extraction recheck:
  `38960059976`. Two scripts passed current factual and audience reviews.
- Staged recordings and exact plan: `38960342826`. Applied successfully: `38961316669`.
- Plan SHA256: `ea88e0b66c26f52868f887b00f88b5feef1622dd7572184b729b769acf5673f6`.
- The public app feed contains **two active current-policy episodes** and **34 retirement
  notices**. All original feed records and legacy assets were backed up before the
  conditional feed switch. Old IDs remain available; their recordings are no longer public.
- Star Bros: **When Galaxy Stars Move Too Slowly**, DOI `10.3847/1538-4357/ae6b8d`,
  discovered through Quanta coverage. Public recording: 266.95 seconds.
- Signal & Noise: **Where Amyloid Clearance Looks Strongest**, DOI `10.1001/jama.2026.13058`,
  discovered through ScienceDaily coverage. Public recording: 213.75 seconds.
- Both public sidecars match the reviewed migration plan exactly, pass script-provenance
  validation and have valid word-timed read-along data. Both audio/detail endpoints resolve.
- A retired Webwork listening page returns 200 with its notice; its former audio returns 404.
- Final validation: 366 backend tests passed, one skipped; 205 iOS checks and deep-link
  checks passed; the Release simulator-target compile passed without launching a simulator.

The other niches intentionally have no active episodes yet. Daily generation and release
use the revised rules; gaps cannot be filled with unrelated papers or legacy prepared audio.

## Story-first reset and fresh batch — 2026-10-16

At the user's request, retirement run `38970879057` removed the two remaining v6
recordings from playback. All **36 pre-change episodes** now retain notices and backups.
Fresh generation `38970966705` approved one new script. After adding Science News
coverage and fixing the confirmed Neanderthal discovery vocabulary gap, expanded run
`38981027755` produced **five current v7-reviewed scripts** without reusing published papers.

Staging `38981781331` and successful application `38982577465` published **The Injured
Person of Shanidar Cave** (Old Bones) and **When Math Gets a Proof Checker** (Gradient).
The public feed, both audio/detail endpoints and both word-timed sidecars were verified;
the published text matches the reviewed plan exactly. Existing production voices were used.

Three reviewed scripts remain queued: **Pioneer 10’s Longest Near Miss**, **What the Brain
Does Without Awareness**, and **When Redwood Leaves Feel the Heat**. The ordinary two-per-day
release rule remains in force. Current checks: 373 backend tests passed, one skipped;
205 iOS checks and the Release compile passed.
