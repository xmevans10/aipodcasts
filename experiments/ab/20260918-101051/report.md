# Article generation A/B — 20260918-101051

Model(s): deepseek-flash. Host: fern. Evidence: 30944 chars.

| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash-baseline | 1 | 496 | 9.5 | 0 | 9 | 0 | 0 | 0 | True | True | 7380 | 1351 | 0.000959 |

## Scripts

### flash-baseline run 1  ·  penalty 9.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that flatness depends on growth being matched across the leaf's width, not just on the top and bottom growing in step.

Picture a young Arabidopsis leaf three days after sowing. It's barely more than a green smudge under the microscope, but it's already busy. Every cell is quietly swelling and dividing, and none of them can wander off — plant cells are glued to their neighbours for life. So whatever shape the leaf ends up, it has to be built by negotiation, not migration. That negotiation is the subject of a paper titled Growth-rate coordination across the width of a leaf preserves its flatness, by Kate Harline and colleagues. Their work appears in the pages of a study on the jagged and wavy mutant, jaw-D, and it asks a deceptively simple question: how does a leaf stay flat?

The team took wild-type Arabidopsis and the jaw-D mutant — a plant whose leaves ripple instead of lying smooth — and imaged the same living leaves every day from three to eight days after sowing. Three leaves per genotype, tracked cell by cell, using confocal microscopy and software that turns the curved surface into a workable map. The jaw-D mutation is known to overexpress a microRNA that represses TCP transcription factors, delaying the leaf's maturation. That delay, it turns out, has consequences for geometry.

Think of a choir, if you will, where every singer must swell at the same rate to keep the sound even. That's a comparison, not a claim about plants. In wild-type leaves, growth along the length of the leaf is carefully matched across its width. The midrib and the blade grow at nearly the same pace, so no internal tug-of-war develops, and the blade stays flat. In jaw-D, the midrib grows more slowly than the blade, and the growth gradient that normally sweeps from base to tip is flattened out. The result is a growth conflict — a mechanical mismatch — and the leaf curves. Curvature becomes strong around six days after sowing. Modelling with finite element simulations supported the idea: uniform growth across the width kept the model leaf flat, while uneven growth produced curvature, and uneven growth on both axes could even generate a twisted or saddle-like form.

What's striking is that the usual suspect — differential growth between the top and bottom of the leaf — doesn't explain it. Both wild type and jaw-D grow faster on the upper side, consistent with unfurling, and the difference between them isn't significant there.

But there are limits. The jaw-D leaves were grown between a cover slip and agar, which likely flattened the leaf tip artificially, and unconstrained jaw-D leaves rolled back on themselves, making them impossible to image. Cell segmentation failed in some proximal regions of jaw-D, so those cells are probably undercounted. And the study used a single mutant in one species — Arabidopsis — so whether the same coordination holds in other leaf forms remains an open question.

Still, back to that three-day-old smudge. Flatness isn't the absence of growth. It's growth that has learned to agree with itself across the whole blade. I'm Clara Rowan. There's always more going on.

