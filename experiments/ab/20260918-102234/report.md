# Article generation A/B — 20260918-102234

Model(s): deepseek-flash. Host: fern. Evidence: 30944 chars.

| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash-antislop-think | 1 | 491 | 1.0 | 0 | 0 | 0 | 0 | 0 | True | True | 8074 | 7838 | 0.002957 |
| flash-antislop-think | 2 | 512 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | True | 8074 | 11064 | 0.003925 |

## Scripts

### flash-antislop-think run 1  ·  penalty 1.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging and modelling in Arabidopsis show that a leaf stays flat only when growth is coordinated across its width.

In a growth chamber under constant light, a first leaf of Arabidopsis is barely bigger than a pinhead. Seen from below through a confocal microscope, its epidermis is a green mosaic of cell outlines, each one mapped day after day. That is where this story starts.

The paper is called Growth-rate coordination across the width of a leaf preserves its flatness. Kate Harline and colleagues live-imaged wild-type and jaw-D mutant first leaves from three to eight days after sowing. They tracked cells as the leaf grew, then built models to test what bends a blade.

Here's the question: cells in a leaf can't wander past their neighbours. So how does a leaf stay flat while its cells divide and expand? The jaw-D mutant overexpresses miR319, which represses TCP transcription factors and delays leaf maturation. The mutant leaf ends up rippled. Wild-type leaves do not.

The researchers found that jaw-D curvature begins at six days after sowing. The whole leaf curves, not just its margins. Two growth patterns stand out. Along the tip-to-base axis, the usual basipetal growth gradient is flattened in jaw-D. Across the width, from midrib to blade, jaw-D grows unevenly: the midrib is slower than the blade. Wild type is more even there.

Think of a row of people carrying a long table. That's a comparison. If everyone walks at the same pace, the table stays level. If the middle slows while the edges keep going, the table twists. In the leaf, slower midrib growth next to faster blade growth creates a growth conflict, and the blade curves.

Their models back this up. When tip-to-base growth is uniform across the leaf's width, the model stays flat. When it is uneven across the width, the model curls like jaw-D. Taking away the basipetal gradient doesn't change that.

What about top and bottom? The adaxial side grows faster than the abaxial side in both genotypes. The team saw no obvious difference in that rate between wild type and jaw-D, so it doesn't explain the waviness. Curvature traces to coordination across the width.

At maturity, the team compared thirty-four wild-type leaves with thirty-six jaw-D leaves.

Now the limits. The live imaging tracked only three leaves per genotype, and only first leaves, so later leaves could behave differently. The mutant's strong curvature made some proximal cells hard to segment, likely undercounting them. Imaging held leaves between a cover slip and agar, which may flatten the tip, and mature jaw-D leaves had to be torn at the margin to measure. The finite element models were built with growth rates set by hand from qualitative imaging. This is one study in Arabidopsis, not a rule for every leaf.

Back to that pinhead leaf. Flatness isn't just a default. It's a daily negotiation, with each region growing in step across the blade. When the midrib and blade fall out of step, the leaf pays for it in ripples.

I'm Clara Rowan. There's always more going on.


### flash-antislop-think run 2  ·  penalty 0.0

**Title:** The Leaf That Refuses to Ripple

**Dek:** Live imaging and modelling show how a leaf keeps its blade flat, and what goes wrong when growth across its width falls out of step.

At three days after sowing, a first leaf is a green speck under a microscope. By eight days, it has already set the shape it will keep as it expands four-hundredfold. This is Wild Company. Today's episode: The Leaf That Refuses to Ripple. In the paper 'Growth-rate coordination across the width of a leaf preserves its flatness', Kate Harline and colleagues watched that speck become a leaf in Arabidopsis thaliana. They wanted to know how a leaf stays flat while its cells grow and divide in a tight neighbourhood, unable to move past one another.

They imaged the same living wild-type and jaw-D mutant first leaves every day from three to eight days after sowing. Fluorescent markers outlined the epidermal cells. Confocal stacks became curved two-dimensional meshes, and the team tracked cell lineages through time. The jaw-D mutant overexpresses miR319, which represses TCP transcription factors and delays leaf maturation. In jaw-D, the wave of maturation from tip downwards ran late. By six days, jaw-D leaves had a strong positive curvature across the proximal end. Wild-type leaves tightened towards zero, flattening out.

Then came the growth maps. Wild type has a basipetal gradient, fast near the base, slowing towards the tip. jaw-D flattens that gradient, so medium growth spreads along more of the leaf. Across the width of the leaf, wild type is fairly even. jaw-D is not. Its midrib grows more slowly than the blade. A comparison: a row of neighbours walking to the same bus stop. If the middle one dawdles while either side strides ahead, the line buckles. The cells aren't choosing anything; the mechanical mismatch is the point. Modelling supported that picture. When proximal-distal growth was uniform across the leaf width, the simulated leaf stayed flat. When it varied across the width, the leaf curved. Removing the basipetal gradient alone did not change flatness or curvature. Differential growth between top and bottom sides was similar in both genotypes, so it didn't explain the jaw-D waviness.

The authors conclude that coordination across the leaf's width, not just local top-bottom matching, keeps the blade flat. The finding comes from first leaves of one species and a mutant, and the models are simulations, not a direct experimental proof of every mechanical step. Some caveats. The live imaging tracked only three leaves per genotype, and the jaw-D leaf's extra curvature undercounted proximal cells. The imaged jaw-D leaf was grown between a cover slip and agar, which likely flattened the tip, and unconstrained jaw-D leaves rolled back so they could not be imaged. The study follows first leaves of Arabidopsis; other species have different growth patterns. On the adaxial side, trichomes blocked enough cells that the authors could not draw a strong conclusion, and possible later margin overgrowth in jaw-D was not captured here.

So back to that green speck. Flatness isn't a passive default. It looks more like a neighbourhood agreeing on pace, at least across the width of the blade, so the leaf can get on with the ordinary business of being a leaf. I'm Clara Rowan. There's always more going on.

