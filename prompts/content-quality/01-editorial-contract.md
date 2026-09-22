# Stage 1 — Define the editorial contract and regression set

Read `00-shared-context.md` first. Implement this stage; do not just write a plan.

## Goal

Turn the audience review into a clear, shared standard that generation and review can
apply. Establish concrete failing examples and a few passing examples without pretending
that a word blacklist can decide whether science is understandable.

## Inspect and diagnose

Read all 16 current spoken scripts, not only titles/deks or extracted metrics. Inspect
shared writing instructions, both schemas and validators, host persona instructions,
evidence packet construction, and the paths that approve/render/publish drafts.
Record a concise map of which code owns each requirement and where enforcement is absent.
Distinguish confirmed defects from editorial judgments.

Seed findings from the actual review:

| Show | Problem to verify and correct in the eventual rewrite |
|---|---|
| Ground Truth | Undefined replication forks, coupling, loop extrusion and PRIMPOL; duplicated paper credit; internal scope instructions read aloud |
| Star Bros | Diffusion models, N-body simulations, attention maps, Dice coefficient, cross-power spectra and non-Gaussian statistics pile up; internal instructions read aloud |
| Mycelium | Species name and technical developmental structures crowd out the simple wall-building story; an unrelated fungal-communication correction distracts |
| Old Bones | Reads, coverage, haplotypes, pangenome graphs and likelihood tools require too much background; vague “samples don't reach that far” may overstate a source gap |
| Marginal Gains | Tissue terminology, shear and correlations dominate; duplicated limitations; retitling left an incorrect “paper, with the same title”; eye biomechanics may not fit a sports show |
| Gradient | Several correlation numbers and a model identifier obscure the weak agreement with human reviewers |
| Common Ground | Category lists, precise label counts and multiple F1 scores overwhelm a useful glacier-mapping story |
| Layer by Layer | Opens with an ellipsoidal Kelvin lattice; alloy code and test dimensions compete with the roughness/cooling trade-off |
| The Long View | Long citation comes before the hook; isotope ranges and unexplained measures make the dust-origin result hard to follow |
| Signal & Noise | Several subgroup percentages, terminology and repeated caveats; retain the key population and observational limit |
| Star Stuff | Reads internal scope instructions; laboratory NMR is framed with a stars introduction despite a questionable astronomy connection |
| Webwork | “Dimensions” and mental maps stay abstract; does not make clear that the available evidence leaves the dimensions' meanings unspecified |
| Slow Wave | Mostly approachable, but image-statistics language and an elaborate analogy compete with a small effect; avoid exaggerating the title's promise |
| The Deep | Concrete subject, but taxonomy/statistics and a shipping-lane analogy need simplification |
| Hive Mind | Among the closest; daily weight comparisons can be more intuitive, with less method/caveat repetition |
| Wild Company | Among the closest; remove implied causal explanations that exceed an across-species association |

## Produce one editorial contract

Store a concise canonical document in `docs/editorial/` and link it from the relevant
prompt documentation. Reuse or update an existing document if one already owns this.
Specify:

- An intelligent nonspecialist listening once; no assumed biology, statistics or ML course.
- One central question, one main result, one meaningful boundary on that result.
- Explain the phenomenon before naming it. A specialist term earns its place only if the
  listener needs it; explain it immediately and then prefer the everyday phrase.
- Approximate targets, not crude universal gates: usually no more than two new essential
  technical terms, one or two important result numbers, natural short sentences, and
  roughly 3–5 minutes. Method/population numbers that prevent a misleading claim may be
  essential; define justified exceptions rather than forcing incorrect simplifications.
- What/how/result/limit should form a connected explanation. Avoid a mandatory repetitive
  template that makes every show sound identical.
- A hook supported by the actual episode, a short listener-facing title, and a concrete
  dek. Retain the improved shared title rules already implemented.
- At most one useful analogy when it actually helps. No required analogy, no spoken
  “Comparison:” label, no second analogy needed to explain the first.
- One plain-language limitations passage, matched by the caveat field. Preserve material
  uncertainty without reading an abstract's methods section or a legal disclaimer twice.
- Genuine conversational roles for co-hosts: questions, clarifications and explanations
  that build on one another, rather than splitting an academic monologue among names.
- Source gaps must be described as limits of the available evidence, not asserted as
  weaknesses of the entire study. No invented sample counts, missing dimensions or claims
  of absent validation when the packet merely does not include them.
- Beat fit must be grounded in the paper. Do not manufacture sports/astronomy relevance
  through an opening metaphor. Withhold or select a better paper if fit cannot be justified.

Document the spoken-citation decision explicitly. Default: exact paper title once in the
opening, after the accessible hook, with first author. Optional user-approved alternative:
exact title in source card, natural spoken topic plus first author/journal. Never silently
remove existing validators. Recommendations are not evidence that approval was granted.

## Regression examples and acceptance

Create a small offline fixture set with two-host, four-host, and solo examples. Include:
internal-instruction leakage; fluent but incomprehensible prose; accurate plain language;
simplification that wrongly introduces causality; simulation presented as reality; too many
numbers; a needed technical term clearly explained; insufficient evidence for an explanation;
and a science topic artificially attached to the wrong show.

Use short excerpts from our generated scripts and purpose-written fixtures. Do not copy
long paper passages or add raw private evidence to git. Annotate the expected issue and a
small illustrative improvement; improvements must remain grounded and must not be treated
as approved production scripts.

Done when the contract has concrete examples, all 16 have concise dispositions, ownership
of enforcement gaps is clear, the citation choice is recorded accurately, and subsequent
stages can test behavior against fixtures rather than another vague “write simply” slogan.
