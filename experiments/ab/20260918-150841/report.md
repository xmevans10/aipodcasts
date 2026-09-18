# Article generation A/B — 20260918-150841

Model(s): gpt-5.6-luna. Host: fern. Evidence: 30944 chars.

| variant | run | words | style penalty | vocab | em dash | hedge | not-X-but-Y | staged | valid draft | valid podcast | in tok | out tok | ~$ off-peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luna-baseline | 1 | 462 | 21.5 | 0 | 1 | 0 | 0 | 0 | True | True | 7454 | 1182 | 0.002909 |
| luna-baseline | 2 | 481 | 1.5 | 0 | 1 | 0 | 0 | 0 | True | True | 7454 | 1221 | 0.002956 |
| luna-antislop | 1 | 436 | 0.0 | 0 | 0 | 0 | 0 | 0 | False | True | 8118 | 1062 | 0.002898 |
| luna-antislop | 2 | 464 | 0.5 | 0 | 0 | 0 | 0 | 0 | False | True | 8118 | 1165 | 0.003022 |

## Scripts

### luna-baseline run 1  ·  penalty 21.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** A tiny Arabidopsis mutant reveals that keeping a leaf flat depends on coordinating growth across its width, not simply on synchronising its top and bottom surfaces.

Watch a young leaf at the microscope and it looks less like a quiet green plate than a busy construction site. Cells are growing, dividing and changing shape, yet none can simply slide past its neighbours. So how does the whole thing avoid buckling?

This is **Growth-rate coordination across the width of a leaf preserves its flatness**. The study, titled “Growth-rate coordination across the width of a leaf preserves its flatness”, comes from Kate Harline and colleagues. They worked with the small flowering plant *Arabidopsis thaliana*, comparing ordinary plants with a mutant called jaw-D, whose young leaves become jagged and wavy rather than staying flat.

The researchers repeatedly imaged living first leaves from three to eight days after sowing. Using confocal microscopy, they tracked cell boundaries and lineages across nearly the entire lower surface. They also built computer models to test which growth patterns would make a leaf bend.

At first, the mutant seems puzzling. Its leaves ended up roughly the same size as ordinary leaves. But their growth was arranged differently. In normal leaves, growth changes from the base towards the tip, while growth at each level is relatively even across the leaf’s width. In jaw-D, that lengthwise gradient was flattened. More importantly, the central midrib grew more slowly than the surrounding blade.

That mismatch matters. **As a comparison**, imagine a neighbourhood where the roads on either side of the high street suddenly lengthen at different speeds. The street map may still cover the same area, but something has to give. In the leaf, the result is a mechanical conflict: parts of the tissue are trying to extend at different rates, and the sheet curves. The researchers found that curvature became especially clear around day six.

The models supported that interpretation. When growth along the length of the simulated leaf was matched across its width, the leaf stayed flat. When it varied across the width, the model curved—even when the overall length could remain similar. The familiar top-versus-bottom explanation for leaf shape wasn’t enough here: the study points to coordination across the blade as a crucial part of flatness.

There are boundaries to this conclusion. The work examined early first leaves of one *Arabidopsis* mutant under controlled laboratory conditions, and some curved regions were difficult to segment. The finite-element models used manually specified growth patterns and simplified mechanical assumptions. The authors also note that gaps caused by trichomes prevent a strong conclusion about coordination on the upper surface, and leaves from other species may use different lengthwise growth patterns.

So, that apparently simple green plane is being kept level by a choreography spread across its width. Not a leaf standing still, but a leaf negotiating its shape while it grows. I'm Clara Rowan. There's always more going on.


### luna-baseline run 2  ·  penalty 1.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** How a tiny Arabidopsis mutant reveals that keeping a leaf flat depends on growth coordination across its width.

A young leaf is meant to be a rather good piece of engineering: expanding, dividing, and still managing to stay flat. But in one small laboratory plant, the leaf develops ripples instead. Why?

This is “Growth-rate coordination across the width of a leaf preserves its flatness”. The study, titled “Growth-rate coordination across the width of a leaf preserves its flatness”, comes from Kate Harline and colleagues. It examines Arabidopsis thaliana, the small mustard plant that has become a regular in plant biology’s neighbourhood.

The researchers compared ordinary wild-type plants with a mutant called jaw-D. In this mutant, a microRNA is overproduced, delaying part of the leaf’s maturation. The team repeatedly imaged the same developing leaves from three to eight days after sowing, tracking cell boundaries, growth, division and differentiation with confocal microscopy. There were three leaves of each genotype in this live-imaging experiment.

At first glance, the two kinds of leaf were surprisingly alike. Their area, length, cell number and density weren’t statistically different during the imaging window. At maturity, they also had similar median size. Yet by six days, jaw-D leaves had begun to curve, eventually forming two ripples, while wild-type leaves flattened out.

The important difference wasn’t simply that one region grew more quickly. In a normal leaf, growth along its length changes from base to tip, but at each level it’s coordinated across the width. The midrib and the surrounding blade grow at broadly similar rates. In jaw-D, the midrib grows more slowly than the blade. That mismatch creates what the researchers describe as mechanical conflicts.

Comparison: it’s a bit like extending a tablecloth when the middle and edges are being pulled at different speeds. The cloth doesn’t politely remain a plane; it buckles. The leaf’s version is more elegant, but the geometry is unforgiving.

Finite-element models supported this explanation. When growth was even across the width, the simulated leaf stayed flat. When it varied across the width, the model curved. The models also suggested that the familiar base-to-tip growth gradient alone couldn’t explain the waviness. It was the lack of coordination perpendicular to that main direction that mattered most.

The study has important limits. It examined early first leaves of one Arabidopsis mutant and wild-type background, with only three leaves per genotype in the live-imaging experiment. The mechanical simulations used manually specified growth rates based on qualitative assessment of imaging data, and the real leaves were grown under imaging constraints that could flatten parts of the mutant leaves. The packet also provides selected passages rather than the complete paper, so additional limitations may be described elsewhere.

So, a flat leaf isn’t merely growing evenly. It’s growing unevenly, but in a coordinated way—rather like a carefully managed neighbourhood where everyone can renovate without pushing the next house sideways. I'm Clara Rowan. There's always more going on.


### luna-antislop run 1  ·  penalty 0.0

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging and modelling in Arabidopsis thaliana suggest that a leaf stays flat when growth is coordinated across its width.

A young leaf is quietly building itself, cell by cell. Along the middle, the midrib grows. Out towards the edges, the blade expands. The whole thing sounds like a recipe for a crumple, yet most leaves manage a remarkably good impression of flatness.

“Growth-rate coordination across the width of a leaf preserves its flatness” is the study by Kate Harline and colleagues. It examines the plant Arabidopsis thaliana, using a mutant called jagged and wavy, or jaw-D, whose leaves develop ripples instead of staying flat. The paper has no journal listed in the supplied material.

The researchers repeatedly imaged living first leaves from three to eight days after sowing. They tracked individual epidermal cells, measuring their growth, division and changing position. They compared ordinary, wild-type plants with jaw-D plants, whose overproduction of a small regulatory RNA delays aspects of leaf maturation.

The leaves were similar in overall size. Their shapes were not. In wild type, growth along the length of the leaf formed a gradient, with growth slowing towards the tip. Crucially, at each level along that length, growth across the width was relatively even. The midrib and the surrounding blade kept pace.

In jaw-D, the midrib grew more slowly than the blade. That difference set up what the researchers call a growth conflict. A comparison might be a sheet of pastry being stretched more in the middle than at the edges: the material has to bend somewhere. In the simulations, uneven growth across the width produced curvature, while more evenly coordinated growth allowed the model leaf to remain flat.

The team also found that the jaw-D leaf’s length could stay similar to wild type despite having a different pattern of growth along its length. That matters because overall size alone can hide how a shape was made. The models suggested that the lengthwise growth gradient itself didn’t explain the curvature. The key was whether growth was coordinated across the width.

There are limits to this picture. The live imaging covered only three leaves of each genotype, the work used one Arabidopsis mutant and early leaves, and the mechanical simulations were based on manually specified growth rates and an idealised material model. Imaging constraints affected some jaw-D leaves, and gaps caused by trichomes prevented a strong conclusion about growth on one leaf surface.

So the flat leaf isn’t simply growing at one uniform pace. It’s keeping different parts in step, like a very disciplined neighbourhood where every extension agrees on the building schedule. Back at the bench, a ripple begins when that agreement slips. I'm Clara Rowan. There's always more going on.

> draft error: Evidence quote not found in original source

### luna-antislop run 2  ·  penalty 0.5

**Title:** Growth-rate coordination across the width of a leaf preserves its flatness

**Dek:** Live imaging and modelling of Arabidopsis leaves suggest that flatness depends on growth staying coordinated across the leaf’s width, not simply on growth from tip to base.

A young leaf is quietly building itself, cell by cell. Its cells can’t shuffle past their neighbours, yet the finished leaf still has to spread into a remarkably flat blade. What keeps it from buckling into a botanical crisp?

The paper is titled “Growth-rate coordination across the width of a leaf preserves its flatness”. Kate Harline and colleagues studied the question in Arabidopsis thaliana, using a mutant called jagged and wavy, or jaw-D. In this mutant, the leaves develop ripples and curves instead of staying flat.

The researchers repeatedly imaged the same developing leaves from three to eight days after sowing. They used confocal microscopy to follow cell boundaries and track individual cell lineages. They compared normal plants with jaw-D plants, then used computer models to test which patterns of growth could produce the observed shapes.

The overall leaf size was surprisingly similar between the two groups. The difference was in how growth was distributed. In normal leaves, the midrib and the surrounding blade grew at broadly similar rates across the width. In jaw-D leaves, the midrib grew more slowly than the blade. That mismatch created what the researchers call growth conflicts, bending the whole leaf rather than just its edges.

Comparison: it’s a little like stretching a sheet of dough while one strip through the middle lags behind. The sheet has to accommodate the disagreement somehow, and a flat surface becomes a difficult arrangement.

The team also found that jaw-D leaves had a flattened pattern of growth from base towards tip, along with delayed cell maturation. But their models suggested that this tip-to-base pattern alone didn’t explain the curvature. Curvature appeared when growth was uneven across the leaf in the direction perpendicular to its main growth. When the simulated midrib and blade grew differently, the model curved in a way that resembled the mutant leaves.

This was a study of early leaves in one Arabidopsis mutant, not a survey of leaf shapes across plants. The live-imaging set was small, with three leaves of each genotype, and the jaw-D curvature sometimes prevented cells near the base from being segmented. The finite-element models used manually specified growth rates based on qualitative assessment of imaging data, and the real leaves were grown under mechanical constraints from the cover slip and agar. Trichomes also obscured parts of the upper leaf surface, so the researchers could not make a strong conclusion about growth coordination there. These limits mean the work supports a mechanism for this mutant and developmental window, rather than proving the same process explains flatness in every species or leaf.

So, that little leaf stays flat through agreement across its width. Its cells don’t need to move house. They need to grow in step. I'm Clara Rowan. There's always more going on.

> draft error: Evidence quote not found in original source
