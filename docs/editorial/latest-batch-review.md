# Latest-batch review and enforcement map

Diagnosis of `experiments/full-run/latest/` (generated 2026-09-21, `podcast-v4`,
16/16 shows drafted, all 16 passed factual verification).

Read with [the audience contract](audience-contract.md). Every script below was read in
full. Factual verification passed for all sixteen; that is not in dispute here. What
follows is audience quality only.

## 1. Confirmed defects, mechanically verified

Counted over the spoken body (solo `body`, or the concatenated dialogue `turns`):

| Defect | Episodes affected |
|---|---|
| Packet `scope` instruction spoken aloud | Ground Truth, Star Bros, Star Stuff, The Deep, The Long View, Webwork |
| Literal `"Comparison:"` label spoken | Ground Truth, Hive Mind, Layer by Layer, Marginal Gains, Mycelium, Old Bones, The Deep, The Long View, Webwork, Wild Company |
| Literal `"Limitations:"` label spoken | Signal & Noise |
| Stale "The paper, with the same title" after retitling | Marginal Gains |
| Malformed `?.` inside a quoted episode title | Marginal Gains |
| Paper title spoken before any hook | Ground Truth, The Long View |

Star Bros reads the scope instruction aloud and then comments on it in character
("That sentence is a little stern, but it keeps our scoreboard honest"), which is the
clearest possible evidence that internal controls are reaching the writer as content.

These are objective and belong to deterministic validation (stage 2).

## 2. Per-show dispositions

`repair` = rewrite from the existing paper. `reselect` = beat fit is not defensible from
the paper; obtain a better candidate or withhold.

| Show | Disposition | Why |
|---|---|---|
| Ground Truth | **repair** | Undefined replication forks, coupling, loop extrusion, PRIMPOL. Paper credit given twice (turn 1 and turn 2). Scope instruction spoken. Paper title precedes the hook. Dialogue alternates two monologues rather than one host answering the other. |
| Star Bros | **repair** | Diffusion models, N-body simulations, attention maps, Dice coefficient, cross-power spectra and non-Gaussian statistics stack up unexplained. Scope instruction spoken and then joked about. 611 words, longest in the batch, across four hosts each performing expertise. |
| Mycelium | **repair** | *Rhizoclosmatium globosum*, saprotrophic chytrid, thalli, sporangium, apophysis, beta-glucan crowd out a simple and appealing wall-building story. The unprompted "wood-wide web" correction is a distraction from the actual finding. 514 words. |
| Old Bones | **repair** | Reads, coverage, haplotypes, pangenome graphs, likelihood-based tools and diploid genotypes need too much background. "The samples don't reach that far" asserts a study weakness where the packet simply omits error rates — a §9 violation. |
| Marginal Gains | **reselect** | Lamina cribrosa, peripapillary sclera, shear strain and radius of curvature dominate. Duplicated limitations (two consecutive caveat paragraphs). Stale same-title phrase and `?.`. Beat fit is keyword-level only: "biomechanics" matches the discovery term, but donor-eye glaucoma mechanics is not a sports-performance story and cannot be made into one with a bicycle metaphor. |
| Gradient | **repair** | Four correlation values (0.34, 0.22, 0.33, 56%) and the model identifier "Gemma 3 27b" obscure the actual finding, which is that agreement with human reviewers is weak. The closing caveat sentence is lifted in the abstract's register and clashes with the rest. |
| Common Ground | **repair** | Eight-class category list, 137,592 labelled points, three F1 values and a percentage spread bury a genuinely good glacier-mapping story. |
| Layer by Layer | **repair** | Opens on "an ellipsoidal Kelvin lattice" before any plain-language footing. AlSi10Mg, strut dimensions and test-piece dimensions compete with the real story, which is the roughness-versus-cooling trade-off. |
| The Long View | **repair** | Paper title precedes the hook. Isotope values in parts per thousand, then "Two nickel measures were seven plus or minus three, and minus six plus or minus nine" — unitless and uninterpretable by ear. |
| Signal & Noise | **repair** | Six subgroup percentages, spoken `"Limitations:"` label, and the caveat repeated across two consecutive paragraphs. The 90+ population and the observational limit must both survive the rewrite. |
| Star Stuff | **reselect** | Scope instruction spoken. Pure shift NMR, chemical shifts, nuclear interactions. The stars framing is an opening metaphor bolted onto a laboratory chemistry method paper; §11 does not allow it. "Spectroscopy" as a beat keyword is not beat fit. |
| Webwork | **repair** | "Five dimensions" and "mental representations" stay abstract throughout; the episode never says what the dimensions turned out to be, and does not make clear that the packet simply does not report them. Scope language spoken. |
| Slow Wave | **repair (light)** | Mostly approachable. Image-statistics language ("three groups of image features accounted for 59 percent"), and the train/station analogy is elaborate for a 22-millisecond effect. The title promises more bending of time than 22 ms delivers. |
| The Deep | **repair (light)** | Concrete and readable. Needs taxonomy and statistics trimmed, the shipping-lane analogy simplified (it currently needs a sentence to disclaim itself), and the scope language removed. 504 words. |
| Hive Mind | **repair (light)** | Among the closest. Daily weight figures (0.76 / 0.47 / 0.50 kg) can be made intuitive rather than listed. Method and caveat material repeats, and the paper's own limitation sentence is read aloud as a quotation. |
| Wild Company | **repair (light)** | Among the closest. Remove the implied causal explanations ("a bird eating a wider range of things may meet more opportunities") that exceed an across-species association. |

Summary: 12 repair, 2 reselect (Marginal Gains, Star Stuff), 2 light repair counted within
the 12 — no episode in the batch is publishable as written.

## 3. Root causes in the prompt set

These are editorial judgements about why the batch came out this way.

1. **Contradictory opening requirements.** `TITLE_GUIDE` says the title is "a reason to
   press play, not a paper citation", while `validate_podcast` requires the exact paper
   title inside the first 180 words and `validate_dialogue_contract` inside the first 220.
   The cheapest way for a writer to satisfy both is to open with the citation. Two
   episodes did exactly that.
2. **"Mark analogies as comparisons" reads as a formatting instruction.** Both
   `PODCAST_INSTRUCTIONS` and `Host.writing_guide` say "mark it as a comparison", while
   `ANTI_SLOP_GUIDE` bans headings. Ten of sixteen scripts resolved this by speaking the
   word "Comparison:".
3. **The evidence packet's `scope` field is indistinguishable from content.** It arrives
   in the same JSON object as the passages, with no marker saying it is a control. Six
   episodes spoke it.
4. **"Verbatim limitations" pushes toward copying.** The requirement that `caveat` appear
   verbatim in the body, combined with a packet that contains caveat-like prose, produced
   duplicated limitation paragraphs and one quoted source sentence.
5. **"No jargon" is asserted, never checked.** `GENERAL_AUDIENCE_GUIDE` already says
   exactly the right thing. Nothing downstream measures whether it happened, so a draft
   that passes factual verification is approved regardless.
6. **Beat fit is keyword matching.** `BEATS` maps a show to search terms. A paper matching
   one term is eligible, and nothing asks whether the show's audience is served.

## 4. Enforcement ownership map

| Requirement | Owner today | Enforced? |
|---|---|---|
| Episode title distinct from paper title, ≤72 chars / ≤12 words | `podcast.validate_episode_title` | yes |
| Exact paper title + episode title + first author in opening | `podcast.validate_podcast`, `dialogue.validate_dialogue_contract` | yes |
| Hook precedes the paper citation | `editorial.spoken_defects` (`citation_before_hook`) | yes, floor only |
| Caveat spoken verbatim, once | validators + `editorial.spoken_defects` (`duplicate_caveat`) | yes |
| Host sign-off, own presenter, own turn | `validate_podcast`, `validate_dialogue_contract` | yes |
| Speaker names, turn count, run limit, participation | `validate_dialogue_contract` | yes |
| Claim quotes verbatim in source | `provenance.quotes_in_source`, `verify.verify_draft` | yes |
| Numeric fidelity against the packet | `verify.numeric_fidelity` | yes |
| Entailment, primary finding, no overstatement | `verify.verify_draft` typed questions | yes, when a decider is reachable |
| Word count / structural bounds | `pipeline.validate_draft`, `validate_dialogue_contract` | yes |
| Internal `scope` text absent from speech | `editorial.spoken_defects` (`scope_leak`); packet field renamed `internal_scope_note` | yes |
| Production labels ("Comparison:", "Limitations:") absent from speech | `editorial.spoken_defects` (`production_label`) | yes |
| Markdown / stage directions absent from speech | `editorial.spoken_defects` (`markdown_or_stage_direction`) | yes |
| Stale "the paper, with the same title" | `editorial.spoken_defects` (`stale_same_title`) | yes |
| Malformed `?.` / `!.` inside quoted titles | `editorial.spoken_defects` (`malformed_title_punctuation`) | yes |
| Surface style (slop vocabulary, em dashes, staged reveals) | `anti_slop.analyze` / `penalty` | advisory only |
| **Comprehensibility after one listen** | nobody | **no** |
| **Term-before-use ordering** | nobody | **no** |
| **Number load and interpretability** | nobody | **no** |
| **Packet gap stated as packet gap** | nobody | **no** |
| **Beat fit grounded in the paper** | `beats.BEATS` keyword match | keyword only |
| **Progressive dialogue** | run/participation limits only | **no** |

Rows in the first block are stage-2 work: unambiguous defects that deterministic checks
can catch. Rows in bold at the bottom are stage-3 work: judgements that need structured
audience review.

**Stage-2 status (2026-09-22).** The deterministic rows above are now enforced by
`backend/editorial.py`, called from `podcast.validate_podcast` and
`dialogue.validate_dialogue_contract`, so failures reach the bounded repair loop with an
actionable message. Re-run against the 2026-09-21 batch, fifteen of the sixteen episodes
now fail at least one deterministic check; Gradient is the exception, and its defects are
number load, which is stage-3 territory. `citation_before_hook` is a floor only: it rejects
an opening sentence that is the citation, not a weak hook.

## 5. What did not cause the problem

Worth recording so the repair does not chase it:

- Titles. The 2026-09-21 retitling worked. Every headline in the batch is a reasonable
  listener-facing hook, and they should be preserved except where a title overpromises
  (Slow Wave) or its episode is reselected.
- Factual accuracy. No fabricated numbers, no causal overreach in the claims, no
  misattributed authors. The scientific gate did its job.
- Reading grade. Several of the worst episodes have short sentences and plain syntax and
  are still incomprehensible, which is the whole argument against a readability gate.
