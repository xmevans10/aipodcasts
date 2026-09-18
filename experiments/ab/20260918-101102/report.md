# Article generation A/B — 20260918-101102

Model(s): deepseek-flash, deepseek-v4-pro. Host: fern. Evidence: 30944 chars.

| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash-baseline | 1 | 427 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | True | 7380 | 1118 | 0.000889 |
| flash-baseline | 2 | 476 | 7.0 | 0 | 7 | 0 | 0 | 0 | True | True | 7380 | 1398 | 0.000973 |
| flash-antislop | 1 | – | – | – | – | – | – | – | – | – | – | – | – |
| flash-antislop | 2 | – | – | – | – | – | – | – | – | – | – | – | – |
| flash-antislop-think | 1 | – | – | – | – | – | – | – | – | – | – | – | – |
| flash-antislop-think | 2 | – | – | – | – | – | – | – | – | – | – | – | – |
| pro-baseline | 1 | – | – | – | – | – | – | – | – | – | – | – | – |
| pro-baseline | 2 | – | – | – | – | – | – | – | – | – | – | – | – |
| pro-antislop | 1 | – | – | – | – | – | – | – | – | – | – | – | – |
| pro-antislop | 2 | – | – | – | – | – | – | – | – | – | – | – | – |

## Scripts

### flash-baseline run 1  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that flatness depends on growth rates matching across the leaf's width, not just top to bottom.

Picture a young Arabidopsis leaf at six days old. Under the microscope, it's a small green paddle, and you'd swear it was pressed flat between two panes of glass. Then there's its mutant cousin, jaw-D. Same age, same size, but the base has begun to curl, like a crisp left too long in the sun. Watching that curl appear, day by day, is the subject of "Growth-rate coordination across the width of a leaf preserves its flatness." Kate Harline and colleagues, writing in the journal, imaged the same living leaves every day from three to eight days after sowing, tracking every epidermal cell as it grew and divided.

Here's the puzzle. Plant cells are glued to their neighbours. They can't shuffle past each other to smooth out a wrinkle, the way you might tug a rumpled tablecloth straight. So shape has to come from coordination. The older idea was that a leaf stays flat because its top and bottom surfaces grow at matching rates. But when the team compared wild type with jaw-D, they found the top still outpaced the bottom in both, which is normal for an unfurling leaf. That wasn't the difference.

The difference was across the width. In wild-type leaves, at any given height along the leaf, the middle rib and the blade beside it grow at nearly the same rate. It's a bit like a rowing crew, where it doesn't matter that the boat is moving fast or slow, only that both oars pull together. In jaw-D, the midrib grows more slowly than the blade, and that mismatch builds up. Think of the comparison as a seam sewn with two different tensions: something has to buckle. Their models agreed, producing flat sheets when growth was even across the width, and curling ones when it wasn't. Curiously, a second defect in jaw-D, a flattened growth gradient from base to tip, turned out to make no difference to curvature at all.

The team also watched a wave of cell maturation travel from tip to base, delayed in jaw-D, and saw that the most proximal cells of a wild-type leaf contribute around thirty per cent of the final blade, against roughly fifteen per cent in jaw-D.

Now the caveats. This is Arabidopsis, first leaves, three plants per genotype, imaged under a cover slip that flattens the very tip the researchers wanted to watch. The model is a model.

So back to that curling leaf. Flatness isn't passive. It's an agreement, renewed daily across the width of the blade. I'm Clara Rowan. There's always more going on.


### flash-baseline run 2  ·  penalty 7.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that staying flat isn't about the top and bottom doing the same thing — it's about neighbours across the blade growing at matching rates.

Picture a young Arabidopsis leaf under a confocal microscope, roughly three days after sowing. It's a scrap of green smaller than a pinhead, and it will get about four hundred times bigger in area before it's done. Every day for six days, researchers imaged the very same living leaves — three wild-type, three of a mutant called jaw-D — at cellular resolution, tagging the cell membranes so each cell's outline glowed. What they were chasing is the puzzle behind the paper's title: Growth-rate coordination across the width of a leaf preserves its flatness.

Kate Harline and colleagues, publishing in this study, tracked individual cell lineages across nearly the whole bottom surface of those leaves, then modelled what the growth patterns would do mechanically. The wild-type leaves flattened out. The jaw-D leaves didn't. They rippled.

Here's the interesting part. Leaf flatness is usually framed as a two-sided problem: keep the top and bottom surfaces growing at compatible rates and the blade stays smooth. But when the team compared the two sides in wild type and jaw-D, both grew with the top faster than the bottom, and there was no obvious difference between them. That wasn't the culprit.

Instead, the trouble ran across the leaf. In wild type, at any given height along the leaf, the midrib and the blade grow at nearly the same rate — think of a row of people walking abreast, a comparison worth holding onto, because if everyone in the row keeps pace, the line stays straight. In jaw-D, the cells along the midrib grew more slowly than those in the blade beside them. Same row, mismatched strides. Modelling showed that growth that's uneven in the direction perpendicular to the main direction of growth creates conflicts and bends the leaf, while the basipetal gradient — growth slowing from base to tip — turned out to have no effect on curvature at all.

One more wrinkle: jaw-D leaves also show a flattened version of that base-to-tip growth gradient, with growth spread more evenly along the length rather than concentrated near the base. That's a real difference from wild type, but the models suggest it isn't what bends the leaf.

The caveats matter here. This is one mutant in one species, imaged under a cover slip and on agar — constraints that likely flattened the leaf tip, while unconstrained jaw-D leaves rolled back on themselves and couldn't be imaged at all. The enhanced curvature also prevented cell segmentation in some proximal regions of jaw-D, so those cells are probably undercounted. And the deepest conclusions about how growth maps onto curvature come from finite element simulations, not from direct measurement of the forces involved.

Still, the image to keep is that row of walkers. Flatness, it seems, is a neighbourhood achievement — not one surface pulling its weight, but everyone across the width keeping step. I'm Clara Rowan. There's always more going on.


### flash-antislop run 1 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### flash-antislop run 2 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### flash-antislop-think run 1 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### flash-antislop-think run 2 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### pro-baseline run 1 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### pro-baseline run 2 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### pro-antislop run 1 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>

### pro-antislop run 2 — ERROR

<urlopen error [Errno 8] nodename nor servname provided, or not known>
