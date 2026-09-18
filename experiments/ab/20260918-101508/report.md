# Article generation A/B — 20260918-101508

Model(s): deepseek-flash, deepseek-v4-pro. Host: fern. Evidence: 30944 chars.

| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flash-baseline | 1 | 477 | 7.0 | 0 | 7 | 0 | 0 | 0 | True | True | 7380 | 1372 | 0.000965 |
| flash-baseline | 2 | 518 | 0.5 | 0 | 0 | 0 | 0 | 0 | True | True | 7380 | 1441 | 0.000986 |
| flash-antislop | 1 | 533 | 2.5 | 0 | 0 | 0 | 1 | 0 | True | True | 8049 | 1484 | 0.001049 |
| flash-antislop | 2 | 425 | 0.0 | 0 | 0 | 0 | 0 | 0 | True | False | 8049 | 1305 | 0.000995 |
| flash-antislop-think | 1 | – | – | – | – | – | – | – | – | – | – | – | – |
| flash-antislop-think | 2 | – | – | – | – | – | – | – | – | – | – | – | – |
| pro-baseline | 1 | 485 | 0.5 | 0 | 0 | 0 | 0 | 0 | True | True | 7377 | 1379 | 0.0038 |
| pro-baseline | 2 | 421 | 0.0 | 0 | 0 | 0 | 0 | 0 | False | True | 7377 | 1031 | 0.003455 |
| pro-antislop | 1 | 465 | 0.0 | 0 | 0 | 0 | 0 | 0 | False | False | 8046 | 1236 | 0.003879 |
| pro-antislop | 2 | 418 | 0.0 | 0 | 0 | 0 | 0 | 0 | False | True | 8046 | 1136 | 0.00378 |

## Scripts

### flash-baseline run 1  ·  penalty 7.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that flatness depends on growth staying even across the leaf's width, not just on matching growth between top and bottom.

Picture a young Arabidopsis leaf under the microscope, barely a millimetre across, and the first thing you notice is how stubbornly level it stays. Day after day, it widens and lengthens, and somehow it does not buckle. That quiet trick is the subject of today's episode: Growth-rate coordination across the width of a leaf preserves its flatness.

The work comes from Kate Harline and colleagues, published in the journal PLOS Biology, and it uses a mutant with a wonderfully descriptive name — jagged and wavy, or jaw-D. These plants overexpress a microRNA called miR319, which represses TCP transcription factors and delays the leaf's maturation. The result is a leaf that ripples instead of lying flat.

Harline and colleagues imaged the same living leaves every day from three to eight days after sowing, tracking individual cells with confocal microscopy and software that turns the curved surface into a workable map. They followed wild-type and jaw-D leaves through roughly a four-hundred-fold increase in area. Think of it as watching a neighbourhood grow house by house, except every house is a cell and none of them can pick up and move. That comparison matters, because in a leaf, every cell is stuck with its neighbours.

What they found was a problem of coordination. In wild type, growth slows progressively from base to tip — a basipetal gradient — and crucially, at any given height, the tissue grows at the same rate right across the leaf's width. In jaw-D, that base-to-tip gradient is flattened out, and worse, the midrib grows more slowly than the blade beside it. That mismatch creates what the authors call growth conflicts, and the leaf curves. Modelling with finite element simulations backed this up: when growth was uneven across the width, the model leaf bent; when it was even, the leaf stayed flat, even with the gradient removed entirely.

Interestingly, the old explanation — that flatness depends on the top and bottom surfaces growing at matched rates — did not hold up here. Both wild type and jaw-D grow faster on the upper surface, and that difference looks the same in both.

But this is a single study in one species, and a partial one at that. The authors themselves note that jaw-D leaves had to be grown between a cover slip and agar, which likely flattened the leaf tip; unconstrained leaves rolled back on themselves. Cell segmentation failed in some proximal regions of jaw-D, so those cells are probably undercounted. And the modelling used manually specified growth rates, not measured ones fed directly into the simulation. The broader claim — that this mechanism holds across other species with different growth patterns — is a prediction, not a result.

So back to that level little leaf. It is not flat because nothing is happening. It is flat because everything is happening in step across its width. I'm Clara Rowan. There's always more going on.


### flash-baseline run 2  ·  penalty 0.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging and modelling of Arabidopsis leaves reveal that flatness depends on growth being matched across the leaf's width, not just top to bottom.

Picture a young Arabidopsis leaf the size of a pinhead, sitting under a microscope. It is not flat yet. Over six days it will expand roughly four hundred fold in area, and if all goes well, it will end up smooth and level, like a well-laid table. If something goes wrong, it ripples like a crisp. That small drama is the subject of a study titled Growth-rate coordination across the width of a leaf preserves its flatness. Kate Harline and colleagues, with collaborators including Brendan Lane and Maura J. Zimmermann, tracked living leaves cell by cell to find out what keeps a blade flat. The work used time-lapse confocal imaging of wild-type Arabidopsis thaliana and a mutant called jagged and wavy, or jaw-D, whose leaves curve instead of lying flat.

The researchers imaged the same first leaves every day from three to eight days after sowing, capturing nearly the entire bottom epidermis at cellular resolution. They then reconstructed the curved surfaces in three dimensions and followed each cell lineage over time. Wild-type and jaw-D leaves were comparable in area, length, width, cell number and cell density, so they could be compared at matching stages. The jaw-D leaves began to curve at six days, with strong positive curvature across the base of the blade.

What did they find? Two differences in growth. First, wild type has a basipetal gradient: growth is fastest near the base and slows towards the tip, like a queue that moves quickly at the front and dawdles at the back. In jaw-D, that gradient is flattened, so growth is spread more evenly along the length. Second, and crucially, wild-type leaves grow at nearly the same rate across their width at each height, with the midrib keeping pace with the blade. In jaw-D, the midrib grows more slowly than the blade. That mismatch creates what the authors call growth conflicts, and the leaf buckles into ripples. Modelling with finite element simulations supported this: when growth along the length was uniform across the width, the model leaf stayed flat; when it was uneven across the width, the leaf curved. Removing the basipetal gradient alone changed nothing, so the width-wise coordination is the key.

It is worth noting that this is a study of one species and one mutant, using three leaves per genotype for the live imaging. The jaw-D plants were grown constrained between a cover slip and agar, which may have flattened the leaf tip. Jaw-D leaves that were not constrained tended to roll back on themselves, preventing imaging. The findings are consistent with the hypothesis that mediolateral growth conflicts cause curvature, but they do not prove it in every leaf or every species. The authors also note that growth patterns differ across plant species, and future work is needed to see whether the same principle holds elsewhere.

So back to that pinhead leaf. Flatness is not a passive default. It is an achievement of coordination, a quiet agreement across the width of the blade to grow at matching rates. When that agreement breaks down, the leaf curls. I'm Clara Rowan. There's always more going on.


### flash-antislop run 1  ·  penalty 2.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that flatness depends on matching growth rates across the leaf's width, not just top to bottom.

A young Arabidopsis leaf, a few days old, sits under the microscope. It is small, pale and almost perfectly flat, like a piece of paper laid on a table. Six days later it will be four hundred times larger in area. It stays flat the whole way. That quiet trick is the subject of a paper called Growth-rate coordination across the width of a leaf preserves its flatness. Kate Harline and colleagues tracked individual cells in living leaves to find out how that flatness is kept. The work is in Arabidopsis thaliana, the thale cress, using the jagged and wavy mutant, jaw-D, whose leaves curl instead of lying flat.

The team imaged the same first leaves every day from three to eight days after sowing, three leaves per genotype, following cell boundaries marked with a fluorescent membrane tag. Wild type and jaw-D reached the same overall size and cell count, so the two could be compared stage by stage. Then the leaves diverged. In wild type, growth is fastest near the base and slows toward the tip, a basipetal gradient, and maturation sweeps down from the tip in the same direction. In jaw-D, that gradient is flattened out: growth is spread more evenly along the leaf's length, and the wave of cell maturation arrives later and weaker.

The second difference is across the leaf's width. In wild type, the midrib and the blade beside it grow at nearly the same rate. In jaw-D, the midrib lags behind the blade from four to eight days. Picture a row of neighbours extending their gardens at different speeds while the fence between them stays fixed. That comparison is the useful one here. The slow midrib and the faster blade pull against each other, and the leaf has nowhere to go but out of the plane. The team's finite element models bear this out: when growth along the length is uniform across the width, the leaf stays flat even with a strong basipetal gradient. Make that growth uneven across the width, and curvature appears. Remove the basipetal gradient entirely and nothing changes. Curvature comes from the side-to-side mismatch.

This runs against the usual framing, which puts leaf flatness down to matching growth on the top and bottom surfaces. The team checked that too: the adaxial side does grow faster than the abaxial in both genotypes, consistent with the leaf unfurling, and the difference is no larger in jaw-D.

What are the limits? The imaging covers the first leaves of one species over six days, three leaves per genotype, with proximal jaw-D cells likely undercounted where curvature blocked segmentation, and the leaves were grown between a cover slip and agar, which flattens the tip. The modelling used growth rates set by hand from the imaging data, so the simulations test a mechanism rather than prove it. And the mediolateral coordination on the adaxial side is suggested, not settled, because trichomes hid too many cells.

Back to that flat young leaf. It is not holding its shape by accident. Every column of cells across its width is keeping pace with its neighbours, and the moment that agreement slips, the blade curls. I'm Clara Rowan. There's always more going on.


### flash-antislop run 2  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging of Arabidopsis leaves shows that flatness depends on growth staying even across the width of the blade, not just between top and bottom.

A young Arabidopsis leaf, a few days old, sits under the microscope like a small green paddle. Watch it for six days and something odd happens. In some plants it stays a paddle. In others, the base begins to curl, and by the end you have two ripples where there should be a flat blade. That quiet difference is the subject of a new study in Arabidopsis thaliana, and its headline is this: growth-rate coordination across the width of a leaf preserves its flatness. Kate Harline and colleagues used time-lapse live imaging to follow the same developing leaves from three days after sowing to eight, tracking every epidermal cell lineage across a 400-fold increase in area. The work is published in the journal PLoS Biology.

The puzzle is straightforward. Cells in a leaf cannot move past their neighbours, so any change in organ shape has to come out of growth and division alone. The mutant they studied, jaw-D, overexpresses a microRNA called miR319, which represses TCP transcription factors and delays the leaf's maturation. Its leaves grow to roughly the same size as wild type but never stay flat. The researchers imaged the bottom epidermis at cellular resolution, built 2.5D mesh surfaces with MorphoGraphX, and followed each cell over time.

What they found was a coordination problem across the width of the leaf. Think of a rowing crew, where each oar has to pull at the same rate as the others or the boat turns. That is the comparison. In wild type, growth along the length of the leaf is uneven from base to tip, but at any given height across the blade the rate is nearly even. In jaw-D, the midrib grows more slowly than the blade beside it. That mismatch creates a growth conflict, and the leaf curves.

Finite element modelling backed this up. When the model's lengthwise growth was uniform across the width, the leaf stayed flat. When it was not, the leaf curved. Removing the base-to-tip gradient altogether changed nothing, which suggests the gradient is not what causes the ripples.

One caveat matters here. The jaw-D leaves in the imaging setup were grown between a cover slip and agar, which likely flattened the tip artificially. Unconstrained jaw-D leaves rolled back on themselves and could not be imaged at all.

Back to that small green paddle under the microscope. Flatness, it turns out, is not a passive default. It is an achievement, held in place by growth rates agreeing across the width of the blade.

I'm Clara Rowan. There's always more going on.

> podcast error: The spoken script must include its limitations paragraph

### flash-antislop-think run 1 — ERROR

unparseable JSON

### flash-antislop-think run 2 — ERROR

unparseable JSON

### pro-baseline run 1  ·  penalty 0.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Why do some leaves ripple while others stay flat? Live imaging of a mutant Arabidopsis leaf shows that the secret lies in coordinating growth across the leaf's width.

It's a small, almost boring thing: a leaf unfurling on a windowsill. But watch closely on a still afternoon, and the way it holds its shape is a quiet piece of engineering. Some leaves stay perfectly flat as they expand. Others, with a tiny genetic tweak, can't help but ripple. So what's going on beneath that green surface? Today: how a leaf keeps its cool and stays flat, and what happens when the coordination breaks down.

This is "Growth-rate coordination across the width of a leaf preserves its flatness." The paper comes from Kate Harline and colleagues, and it looks at a mutant of Arabidopsis thaliana called jaw-D, whose leaves don't lie flat. The team used time-lapse live imaging to watch the same developing leaves day after day, tracking individual cells as they grew and divided. They found that in wild-type plants, growth is coordinated across the width of the leaf, so each region expands at a similar rate from the midrib to the edges. In the mutant, that coordination fails: the midrib grows more slowly than the blade, creating mechanical conflicts that buckle the leaf into its characteristic ripples.

Think of it like a group of people rolling out a bedsheet. If everyone pulls at the same speed, the sheet stays flat. But if the people in the middle lag while those at the edges rush ahead, the sheet bunches and warps. That's the comparison here: the leaf's midrib is like the slow pullers in the middle, and the blade edges are the fast ones, and the result is a leaf that can't help but curve.

The researchers also built computer models of leaf growth to test this idea. When they gave the model a uniform growth rate across the leaf's width, it stayed flat. When they made the midrib grow slower than the blade, the model leaf curved, just like the real jaw-D leaves. Interestingly, changing the growth gradient along the leaf's length, from base to tip, didn't affect flatness. It was all about the widthwise coordination.

There's a limit to what this study can tell us. The live imaging was done on only three leaves per genotype, and some regions of the mutant leaf couldn't be fully captured because of the curvature. Also, the study focuses on the first two leaves of Arabidopsis, so it's not certain the same mechanism applies to all leaves or to other species. And while the models are useful, they are simplified representations of a complex biological process.

But the takeaway is rather lovely: flatness isn't just a default. It's actively maintained by a leaf-wide conversation between cells, a kind of unspoken agreement to grow at the same rate across the width. When that agreement breaks, even a little, the leaf remembers how to ripple. So next time you see a flat leaf, you're looking at a well-coordinated team. I'm Clara Rowan. There's always more going on.


### pro-baseline run 2  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** A plant mutant with wavy leaves reveals the hidden growth choreography that keeps wild leaves flat.

A leaf unfurls on an Arabidopsis plant, and for days it stays perfectly flat. Then, just six days after sowing, everything changes in a mutant called jaw-D: it bends, ripples, and refuses to lie smooth. Kate Harline and colleagues wanted to know why. Their paper, "Growth-rate coordination across the width of a leaf preserves its flatness," explains how the ordinary flat leaf is less ordinary than it looks. Using live imaging, they tracked thousands of cells in wild-type and jaw-D leaves as they grew, and found that flatness depends on a kind of neighbourhood agreement about growth rates.

Think of it like a row of people rolling out a sheet of dough. If everyone pulls at the same speed, the dough stays flat. But if the middle of the row slows down while the edges keep pulling, the dough buckles and wrinkles. That's the comparison here. In wild-type leaves, the midrib and the blade grow at nearly the same rate across the width, so no conflict arises. In jaw-D, the midrib grows more slowly than the blade, creating mechanical conflicts that make the whole leaf curve. The team's modelling showed that curvature develops when growth is uneven across the leaf in the direction perpendicular to the main direction of growth. They also found that jaw-D has a flattened growth gradient from tip to base, but that defect alone doesn't explain the curves. The key is the mismatch from middle to edge.

The study wasn't just about a mutant. It suggests that wild-type plants actively coordinate growth across the blade to stay flat. The authors note that the wild-type leaf exhibits a basipetal growth gradient, with faster growth near the base, but that growth rate is uniform across the width at each height. That uniformity avoids conflict. In jaw-D, the lack of coordination leads to ripples. They saw no difference in growth between the top and bottom sides of the leaf, ruling out another long-standing idea.

There are limits. The live imaging captured only the first of two ripples, and the constrained growth under a coverslip may have flattened the leaf tip. Also, the study focused on the first leaves of Arabidopsis, so the findings may not apply to all leaf shapes or species. The authors call for future work on the long-distance signals that coordinate growth across the width. Still, the picture is clear: a flat leaf is a coordinated leaf, and when the coordination slips, the leaf remembers it in every curve.

I'm Clara Rowan. There's always more going on.

> draft error: Evidence quote not found in original source

### pro-antislop run 1  ·  penalty 0.0

**Title:** Why a Wavy Leaf Reveals the Secret to Staying Flat

**Dek:** A mutant Arabidopsis with rippled leaves helps show that coordination across the width of a leaf, not just top to bottom, keeps it flat.

A seedling pushes up through the soil, two tiny leaves unrolling like damp paper. At first they look identical, smooth and green. Then one of them starts to ripple, a gentle wave running across its surface. It’s the kind of small oddity you might miss on an ordinary afternoon, but it’s the starting point for a question about how leaves keep their shape.

That question is the focus of a study called 'Growth-rate coordination across the width of a leaf preserves its flatness', by Kate Harline and colleagues. They looked at a mutant Arabidopsis plant called jaw-D, whose leaves go wavy instead of flat. The paper appears in the journal PLOS Biology.

Harline and colleagues used time-lapse imaging to watch individual leaves grow from three to eight days old, tracking every cell on the underside. They found that in normal plants, growth follows a gradient: cells near the tip slow down and mature early, while cells near the base keep growing. But the mutant jaw-D flattens that gradient, so growth is more even from tip to base. That alone didn’t explain the waviness.

The real problem was across the width of the leaf. In wild-type leaves, the midrib and the blade grow at nearly the same rate at each position, like two lanes of traffic moving in perfect sync. In jaw-D, the midrib grows slower than the surrounding blade. That mismatch creates a mechanical conflict, and the leaf buckles into a ripple. It’s a bit like a sheet of pastry that rises unevenly in one spot while the rest stays flat, the tension has to go somewhere.

The team tested this with computer models. When growth was uniform across the width, the simulated leaf stayed flat, even with the normal tip-to-base gradient. When they made the midrib slower than the blade, the model curled, just like the mutant. They also checked top-versus-bottom growth, often blamed for curling, and found no real difference between wild-type and jaw-D. So the waviness comes from side-to-side coordination, not top-to-bottom.

There are limits to this study. The researchers imaged only the first two leaves of Arabidopsis, and the mutant was grown between a cover slip and agar, which may have flattened the leaf tip artificially. Cell segmentation was also incomplete in the most curved regions, so proximal cells may be undercounted. The study is based on one mutant in one species, and the findings may not apply to all leaf shapes. The modelling used simplified growth rules, not the full complexity of a living leaf.

Still, the picture is clear: flatness isn’t just about local matching between top and bottom. It’s about global coordination across the width. When that coordination breaks, the leaf ripples. I’m Clara Rowan. There’s always more going on.

> draft error: Evidence quote not found in original source
> podcast error: Podcast opening must include the exact episode headline

### pro-antislop run 2  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Why do some leaves stay flat while others ripple? Live imaging of a mutant plant shows that coordinated growth across the leaf's width prevents mechanical conflicts.

A leaf's shape is a bit like a slow, green argument. Every cell is fixed in place, so when one part grows faster than its neighbours, something has to give. In a normal Arabidopsis leaf, the whole blade stays remarkably flat. But in a mutant called jaw-D, the leaf ripples and curls like a strip of paper that got damp and dried unevenly. The question is what's different. The paper is 'Growth-rate coordination across the width of a leaf preserves its flatness,' by Kate Harline and colleagues. They grew wild-type and jaw-D plants, then used time-lapse confocal imaging to watch the same first leaves develop day by day, from three to eight days after sowing. It's a bit like a neighbourhood where everyone adds an extension at their own pace; in a flat leaf, the builders along the street all keep the same schedule. In wild type, growth is strongest near the base and slows toward the tip, but at any given height, the midrib and the blade grow at nearly the same rate. That evenness across the width means no part is being pulled or pushed out of plane. In jaw-D, that coordination breaks down. The midrib grows more slowly than the surrounding blade. The authors found this by tracking cell lineages and measuring growth rates in both directions. The difference appears around day six, when wild-type leaves flatten and jaw-D leaves start to curve. They then used computer modelling to test whether this uneven growth could cause curvature. When they made growth uniform across the width, the virtual leaf stayed flat. When they made the midrib grow slower than the blade, the leaf curved, much like jaw-D. They also removed the usual tip-to-base growth gradient and found it didn't matter for curvature. What mattered was the mismatch across the width. The study has limitations. It examined only the first leaves of one species, Arabidopsis thaliana, with a small sample of three leaves per genotype for live imaging, and the constrained growth under a coverslip may affect how curvature appears. The models used manually set growth rates based on qualitative assessment of the imaging data, and some proximal cells in jaw-D were likely undercounted due to curvature, so the full picture of growth conflicts may be incomplete. Also, the paper does not identify the molecular signals that coordinate growth across the leaf width. So the next time you see a flat leaf, consider the quiet agreement among its cells. I'm Clara Rowan. There's always more going on.

> draft error: Evidence quote not found in original source
