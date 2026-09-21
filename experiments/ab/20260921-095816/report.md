# Article generation A/B — 20260921-095816

Model(s): deepseek-flash, gpt-5.6-luna. Host: fern. Evidence: 30944 chars.

| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash-antislop | 1 | 411 | 0.5 | 0 | 0 | 0 | 0 | 0 | True | True | 8082 | 1050 | 0.001842 |
| flash-antislop | 2 | 422 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | False | 8082 | 1185 | 0.001923 |
| flash-clues | 1 | 403 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | False | 8198 | 1101 | 0.00189 |
| flash-clues | 2 | 554 | 0.5 | 0 | 0 | 0 | 0 | 0 | True | True | 8198 | 1521 | 0.002142 |
| luna-antislop | 1 | 509 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | True | 8119 | 1221 | 0.003089 |
| luna-antislop | 2 | 465 | 0.0 | 0 | 0 | 0 | 0 | 0 | False | True | 8119 | 1195 | 0.003058 |
| luna-clues | 1 | 502 | 0.5 | 0 | 0 | 0 | 0 | 0 | True | True | 8235 | 1183 | 0.003067 |
| luna-clues | 2 | 480 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | True | 8235 | 1262 | 0.003161 |

## Scripts

### flash-antislop run 1  ·  penalty 0.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that keeping a blade flat takes teamwork across its width, not just top-to-bottom balance.

Watch a young Arabidopsis leaf for a few days and you'd swear it has a plan. It starts as a tiny green paddle and, over about six days, it expands roughly four hundredfold in area while staying remarkably flat. No curling, no rippling. Just a neat, level blade. That flatness is the puzzle Kate Harline and colleagues took on in a study titled Growth-rate coordination across the width of a leaf preserves its flatness. They imaged the same living leaves, day after day, from three to eight days after sowing, tracking every epidermal cell.

The team compared ordinary wild-type plants with a mutant called jagged and wavy, or jaw-D. These mutant leaves don't stay flat. They curve into ripples. The researchers used confocal microscopy and software to turn those stacks of images into curved two-dimensional surfaces, then followed each cell lineage over time. Think of it a bit like a crowd doing the wave at a match: if everyone along a row lifts their arms together, the row stays even, but if one section keeps standing while the next sits down, the whole line buckles. That's the comparison, not a perfect one, but it captures the idea of growth conflict.

So what did they find? In wild-type leaves, growth slows progressively from base to tip, a basipetal gradient, and crucially the growth rate along any given horizontal slice is fairly even across the leaf's width. In jaw-D, two things go wrong. The base-to-tip gradient flattens out, and the midrib grows more slowly than the surrounding blade. That mismatch across the width creates mechanical conflict, and the leaf curves. Cell divisions largely stop by five to six days, so growth, not division, drives the difference.

The modelling backed this up. When the team simulated uniform growth across the width, leaves stayed flat even with a strong base-to-tip gradient. Make the growth uneven across the width, and the model curls. Remove the base-to-tip gradient entirely and the flat model stays flat, the curved one stays curved. Curvature, it seems, comes down to coordination across the width.

There are limits. The imaging captured just the first two leaves, and proximal regions of jaw-D were hard to segment because of the curvature. Later leaves might behave differently. The models are simulations, not direct measurements of forces inside a real leaf.

Still, that flat little paddle is doing something quietly impressive. It's not just growing. It's growing together. I'm Clara Rowan. There's always more going on.


### flash-antislop run 2  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that keeping a blade flat isn't about top and bottom growing in step, but about growth being even across the leaf's width.

A leaf, held up to the light, looks like the simplest thing in the world. Flat, green, a bit of a sun-catcher. Then you find one that has buckled into ripples, and the flatness stops looking simple. Something had to be organised to get that surface, and a new study in Arabidopsis thaliana has gone looking for what.

The work is called Growth-rate coordination across the width of a leaf preserves its flatness. Kate Harline and colleagues tracked the same living leaves, cell by cell, as they grew. There's no journal named in what I've got, so I'll leave it there. They imaged wild-type plants and a mutant called jagged and wavy, or jaw-D, every day from three to eight days after sowing, three leaves per genotype. The mutant overexpresses a microRNA that represses TCP transcription factors, which delays the leaf's maturation. The team used confocal microscopy on the leaf's bottom surface and software to turn those stacks into curved two-dimensional meshes, then followed every cell lineage over time.

Here's the useful comparison. Think of a row of people carrying a long table. If everyone walks at the same pace, the table stays level. If the person in the middle dawdles while the ones on either side stride ahead, the table twists and buckles. That's roughly what the team found happening across the leaf's width.

In wild-type leaves, growth along the length is uneven from base to tip, a basipetal gradient, but at any given height across the leaf's width, growth is even. No conflict, so the blade stays flat. In jaw-D, that evenness breaks down. The midrib, the strip over the central vascular bundle, grows more slowly than the blade beside it. By six days after sowing, the jaw-D leaf has curved, and the curvature runs across the whole lamina, not just at the margins.

Modelling backed this up. Simulations with uniform growth across the width stayed flat. Make that growth uneven and the model leaf curved. Remove the base-to-tip gradient entirely and the outcome barely changed, which suggests that gradient isn't what drives the curvature. Uneven growth in both directions at once produced a twisted form; twice as much unevenness across the width gave a curled, saddle-like shape.

One thing worth flagging: leaf flatness is often framed as a problem of synchronising growth on the top and bottom surfaces. In these leaves, the top grew faster than the bottom in both genotypes, consistent with unfurling, so that difference doesn't explain the waviness.

I'm Clara Rowan. There's always more going on.

> podcast error: The spoken script must include its limitations paragraph

### flash-clues run 1  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that flatness depends on growth staying even across the leaf's width, not just top-to-bottom.

A leaf tip bends down toward the agar, and by the next morning the whole blade has folded into a ripple that won't sit flat. That's a jaw-D mutant of Arabidopsis thaliana, and it's the subject of a study titled Growth-rate coordination across the width of a leaf preserves its flatness, by Kate Harline and colleagues, published in the journal PLOS Biology. The researchers wanted to know why some leaves stay flat while others curve, so they watched the same living leaves grow, day by day, from three to eight days after sowing. They imaged nearly the whole bottom surface of each leaf at cellular resolution, then tracked every epidermal cell lineage over time. Both wild-type and jaw-D leaves ended up about the same size at maturity, and their area, length, width, cell number and cell density were not statistically different during the imaging window. So the difference isn't how much they grow. It's how that growth is arranged. Think of it like a neighbourhood where everyone is painting their houses at once. If everyone on a street works at the same pace, no problem. But if one house races ahead while the one next to it dawdles, the fence between them starts to lean. That's the comparison: in jaw-D, the midrib grows more slowly than the blade beside it, and that mismatch across the leaf's width creates a growth conflict that buckles the leaf into ripples. In wild type, the midrib and blade grow at nearly the same rate, so no conflict arises and the leaf stays flat. Computer models backed this up. When the researchers simulated uniform growth across the width, the leaf stayed flat. When they made it uneven, it curved. Interestingly, removing the normal tip-to-base growth gradient had no effect on curvature at all. The key is coordination across the width, at every point along the leaf's length. There are caveats. The jaw-D leaves were grown between a cover slip and the agar, which likely flattened the tip artificially, and some proximal regions couldn't be segmented, so those cells may be undercounted. The study looked at one mutant in one species, so whether the same rule holds for other leaf shapes is an open question. But the pattern is clear: a flat leaf isn't just a leaf that grows the right amount. It's a leaf whose cells agree on the pace. I'm Clara Rowan. There's always more going on.

> podcast error: The spoken script must include its limitations paragraph

### flash-clues run 2  ·  penalty 0.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that keeping a blade flat needs growth rates to match across the leaf, not just top to bottom.

A young Arabidopsis leaf under the microscope looks, at first, like nothing much is happening. It sits there, a small green paddle, while the clock on the imaging rig ticks over. Then, across the width of that paddle, a quiet argument begins. Cells near the midrib grow at one pace, cells out towards the blade grow at another. As far as anyone can tell, that mismatch is what bends a leaf out of shape.

That is the puzzle in a new study titled Growth-rate coordination across the width of a leaf preserves its flatness. Kate Harline and colleagues, writing in the journal, followed the same living leaves day after day to see how flatness is built and lost. Their question is simple enough: when cells cannot move past their neighbours, how does an organ end up flat at all?

To find out, they imaged wild-type Arabidopsis leaves and a mutant called jagged and wavy, or jaw-D, every day from three to eight days after sowing. They tagged cell membranes with a fluorescent marker, then tracked each cell lineage over time. The jaw-D mutant overexpresses a microRNA that represses TCP transcription factors, which delays the leaf's maturation. The team captured both the birth of curvature and the ordinary growth that keeps a normal leaf flat, watching the same tissue through roughly a 400-fold increase in area.

Here is the comparison that helps. Think of two neighbours laying a patio together, one working quickly and one slowly, with the slabs locked edge to edge so neither can slide. If they keep different paces across the width of the row, the surface buckles. That is roughly the situation in the jaw-D leaf. The midrib grows more slowly than the blade beside it, and the leaf curves. In wild-type leaves, the midrib and blade grow at nearly matching rates, so the blade stays flat.

The modelling backed this up. When the researchers simulated proximal-distal growth that was uniform across the leaf's width, the leaf stayed flat. When they made that growth uneven across the width, the model curved, and with stronger unevenness it produced saddle shapes like a potato chip. Removing the basipetal growth gradient made no difference to curvature, which suggests the top-to-bottom story is not the main cause here.

jagged and wavy leaves also showed a flatter growth gradient from tip to base, and delayed pavement cell differentiation. Their stomatal patterning, by contrast, progressed fairly normally. The authors conclude that cell growth is coordinated across the width of the wild-type leaf to maintain flatness, and that disrupting this coordination in jaw-D lets growth conflicts bend the blade.

That said, the study has limits. The imaging captured only the first leaves, in one species, and the enhanced curvature of jaw-D sometimes prevented cell segmentation, so proximal jaw-D cells may be undercounted. The jaw-D leaves were also grown between a cover slip and the agar, which likely flattened the tip. Overgrowth along the margins, seen in some other work, was not evident in these first leaves, though it might occur in later ones.

So the flat leaf on the windowsill is not passive. It is the product of cells keeping pace across the blade, day after day, without ever moving past each other. Miss that coordination, and the leaf curls.

I'm Clara Rowan. There's always more going on.


### luna-antislop run 1  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** How does a leaf stay flat while its cells grow in different places at different speeds? Live imaging and modelling in Arabidopsis point to coordination across the blade.

A young leaf is doing something rather demanding. Its cells are multiplying and expanding, but they can’t shuffle past their neighbours. Somehow, the whole sheet stays flat rather than buckling into a green crisp.

That puzzle sits at the heart of “Growth-rate coordination across the width of a leaf preserves its flatness”. The paper, by Kate Harline and colleagues, examines Arabidopsis thaliana, the small mustard plant often used in laboratory research.

The researchers compared ordinary plants with a mutant called jaw-D. Its leaves become wavy and form ripples. The team repeatedly imaged the same developing leaves from three to eight days after sowing, tracking cell boundaries across nearly the whole lower surface. They paired those observations with computer models of a growing leaf.

The ordinary leaves had a growth pattern that changed from base to tip. Crucially, at each position along the length, growth was fairly even across the width. The middle vein and the surrounding blade kept pace with one another.

In jaw-D, the middle vein grew more slowly than the blade around it. That difference created what the researchers call growth conflicts. The leaf began curving at about six days after sowing, and the curvature involved the whole blade, rather than just its edges.

Comparison: think of a tablecloth being pulled at different speeds across its width. The cloth may wrinkle or lift, even if the overall amount of fabric stays much the same. In these leaves, uneven growth seems to create a similar mechanical problem.

The mutant’s length was still similar to the ordinary leaf’s length. That’s important. A leaf can reach roughly the same final size while taking a different route to get there. The jaw-D mutation also delayed the normal wave of cell maturation moving from the tip towards the base. But the modelling suggested that the altered base-to-tip pattern alone didn’t explain the curl. The key was its lack of coordination across the width.

The study also tested the familiar idea that flatness mainly depends on matching growth between the top and bottom surfaces. Both types of leaf had faster growth on the upper side at this stage, so that difference didn’t account for the mutant’s abnormal shape. The authors instead point to growth coordination across the blade as the central requirement for a flat leaf.

There are limits to keep in view. The live-imaging comparison used three leaves of each genotype, and some curved jaw-D regions couldn’t be segmented. The finite-element simulations were based on manually specified growth rates and simplified material assumptions. The experiments used one Arabidopsis mutant and young first leaves, so the same mechanism may not apply in every species or leaf type.

Still, the little leaf offers a neat lesson in plant architecture. Flatness doesn’t require every cell to grow at the same speed. It requires neighbouring regions to grow in a compatible pattern. When the middle and the blade fall out of step, a flat surface can become a ripple. I'm Clara Rowan. There's always more going on.


### luna-antislop run 2  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** A mutant Arabidopsis leaf reveals how carefully matched growth across its width helps a young leaf stay flat.

A young leaf is quietly getting wider, longer and more complicated by the hour. Yet somehow, it usually keeps its shape as a flat blade rather than folding itself into a botanical crisp. The paper “Growth-rate coordination across the width of a leaf preserves its flatness” comes from Kate Harline and colleagues. It asks how a leaf manages that balancing act.

The researchers studied Arabidopsis thaliana, comparing ordinary plants with the jagged and wavy, or jaw-D, mutant. In this mutant, a change involving miR319 delays leaf maturation, and the leaves develop ripples and curves instead of staying flat.

Harline and colleagues repeatedly imaged the same young leaves from three to eight days after sowing. They used confocal microscopy to follow cells in the lower epidermis, tracking how individual cells grew, divided and contributed to the final shape. They also built computer models to test which growth patterns would bend a leaf.

The overall size of wild-type and jaw-D leaves was broadly similar. Their shapes were not. The mutant’s curvature became strong around day six, and it affected the whole leaf rather than just the edges. In jaw-D, the central midrib grew more slowly than the surrounding blade. In ordinary leaves, growth across the width was more even.

Comparison: picture a sheet being stretched from end to end. If every strip across its width lengthens by the same amount, it can remain flat. If one strip lags while its neighbours pull ahead, the sheet has to buckle somewhere. The models produced the same kind of result. Uneven growth across the leaf, perpendicular to its main direction of growth, created curvature.

There was another difference. Normal leaves showed a gradient in growth from the base towards the tip. The mutant’s gradient was flatter, so cells in different parts of the leaf contributed more equally to the final tissue. That change alone did not explain the bending. The key mechanical conflict came from the mismatch between the midrib and the blade across the leaf’s width.

This study examined early leaves of Arabidopsis, including only three live-imaged leaves per genotype, and its finite-element models used manually specified growth rates based on qualitative imaging. The real jaw-D leaves were also grown under cover-slip and agar constraints during imaging, and trichomes left gaps that limited conclusions about growth on the upper surface. The findings therefore show how this mutant’s measured growth patterns can generate curvature, rather than proving that the same mechanism controls flatness in every plant species.

So the flat leaf isn’t simply growing in one direction. Its cells are keeping pace across the width as the whole blade expands. A quiet bit of coordination, repeated across thousands of cells, keeps the leaf from becoming a crisp. I'm Clara Rowan. There's always more going on.

> draft error: Evidence quote not found in original source

### luna-clues run 1  ·  penalty 0.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** A mutant Arabidopsis leaf curls when growth along its midrib falls out of step with growth across the blade.

A young leaf is meant to be a remarkably tidy bit of construction. Cells multiply, stretch and mature, yet they can’t slide past their neighbours. So how does the whole thing stay flat rather than turning into botanical origami?

This is Growth-rate coordination across the width of a leaf preserves its flatness. The study, by Kate Harline and colleagues, examines developing Arabidopsis thaliana leaves, using live imaging and computer modelling. There’s no journal named in the supplied material.

The researchers compare ordinary plants with a mutant called jaw-D. Its leaves develop ripples and curves. The mutation causes overexpression of miR319, which delays leaf maturation by repressing TCP transcription factors. Harline and colleagues repeatedly image the same leaves from three to eight days after sowing, tracking individual epidermal cells. They also build models to test which growth patterns produce a curve.

The key difference appears across the leaf’s width. In a normal leaf, the midrib and the blade grow at broadly similar rates at the same position along the leaf. In jaw-D, the midrib grows more slowly while much of the blade grows faster. That mismatch creates mechanical conflict, and the leaf bends. As a comparison, it’s a bit like a sheet whose centre and edges are being pulled at different speeds. The sheet has to go somewhere, and flat isn’t the only option.

The mutant also loses the normal gradient of growth from the base towards the tip. Yet the models suggest that this change alone doesn’t explain the curvature. What matters for flatness is whether growth is coordinated across the width at each point along the leaf. When the simulated growth is even across that width, the model remains flat. When it’s uneven, curvature appears. Stronger mismatches across the width can produce a saddle-like shape, rather like a potato chip. Plants, apparently, have their own ideas about crispness.

The work also separates this effect from the usual top-versus-bottom explanation. Both normal and jaw-D leaves grow faster on the upper side than the lower side at this stage, consistent with unfurling. The researchers say the abnormal curvature is instead linked to poor coordination from the base towards the tip across the leaf’s width.

There are important limits. The live-imaging sample was small, with three leaves of each genotype, and some curved jaw-D regions could not be segmented, so proximal cells were probably undercounted. The experiments used early first leaves of one Arabidopsis mutant, and the computer models set growth rates manually from qualitative imaging assessments. Real leaves also grew under cover-slip and agar constraints during imaging, which affected their shape. The findings therefore show a mechanism supported by this mutant and these models, not a universal rule for every leaf.

Still, the opening puzzle has a pleasing answer. Flatness doesn’t require every part of a leaf to grow at the same speed. It requires neighbouring regions to keep their growth in step across the width. I'm Clara Rowan. There's always more going on.


### luna-clues run 2  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging and modelling of Arabidopsis leaves reveal how uneven growth across the midrib and blade makes a young leaf ripple.

A tiny Arabidopsis leaf begins to curl near its base, while its neighbour stays neatly flat. Same sort of plant, similar size, very different geometry. Plants, it turns out, have a folding problem.

Growth-rate coordination across the width of a leaf preserves its flatness is a study by Kate Harline and colleagues. The paper examines young leaves of Arabidopsis thaliana, comparing ordinary wild-type plants with a mutant called jaw-D, whose leaves develop ripples instead of remaining flat.

The researchers repeatedly imaged the same living leaves from three to eight days after sowing. Confocal microscopy let them follow cell boundaries and lineages across nearly the whole lower surface. They then measured growth along the length of the leaf, from tip to base, and across its width, from midrib to edge. Finally, they built mechanical models to test which patterns could produce curvature.

The jaw-D leaves weren’t simply bigger. At maturity, the two groups had similar median leaf size, although jaw-D leaves had a shorter stalk and more variation between paired leaves. Their shape began to diverge early. By day six, jaw-D leaves showed strong curvature, while wild-type leaves flattened towards zero curvature.

The key difference was across the width. In wild-type leaves, the midrib and the surrounding blade grew at broadly similar rates at the same height. In jaw-D, the midrib grew more slowly than the blade. That mismatch created mechanical conflict, so the whole leaf curved rather than just its edges. As far as anyone can tell, the plant isn’t trying to make a tiny potato chip. The tissue is simply growing unevenly, and the sheet has to accommodate the disagreement.

The team also found that jaw-D had a flatter version of the normal base-to-tip growth gradient, along with delayed pavement-cell differentiation. Yet models showed that this lengthwise gradient alone didn’t explain the curvature. When growth was equal across the width, the model stayed flat even when different parts grew by different amounts. When growth varied across the width, curvature appeared. In one simulation, stronger mismatch from midrib to blade produced a curled, saddle-like form.

There’s an important limit here. The live imaging covered only the first leaves of plants grown under laboratory conditions, and some curved jaw-D regions couldn’t be segmented, so proximal cell counts were probably low. The mechanical simulations used manually specified growth patterns and a simplified material model. Trichomes also obscured parts of the upper surface, preventing a strong conclusion about growth there. The findings show how this mutant behaves, but they don’t establish that every leaf, or every plant species, uses precisely the same coordination system.

So, that little curl begins with a quiet disagreement across the leaf’s width. Flatness isn’t just a matter of growing evenly overall. It depends on neighbouring tissues keeping pace in the right places. I'm Clara Rowan. There's always more going on.

