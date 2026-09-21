# Blind AI judge — leaf draft A/B

Judges: pro, flash (DeepSeek, thinking disabled, temp 0). `composite` is the mean of hook, clarity, spoken rhythm, human voice, host fit and overall across both judges. `bundled-baseline` scripts cover different papers, so their `fidelity` is null and only craft dimensions are comparable. Note: `backend/data/baseline-2026-09-17/manifest.json` records the bundled scripts as assistant-authored, not a live Luna API run, so treat `bundled-baseline` as a human/assistant quality reference, not API output.

| rank | condition | n | composite | fidelity | det. style penalty |
|---|---|---|---|---|---|
| 1 | flash-clues | 2 | 8.25 | 8.0 | 0.25 |
| 2 | flash-baseline | 5 | 8.18 | 7.4 | 4.8 |
| 3 | pro-antislop | 2 | 8.12 | 8.5 | 0.0 |
| 4 | flash-antislop-think | 2 | 8.04 | 8.5 | 0.5 |
| 5 | flash-antislop | 4 | 8.02 | 8.12 | 0.75 |
| 6 | luna-clues | 2 | 8.0 | 8.5 | 0.25 |
| 7 | luna-antislop | 4 | 7.88 | 8.62 | 0.12 |
| 8 | pro-baseline | 2 | 7.88 | 8.0 | 0.25 |
| 9 | luna-baseline | 3 | 7.86 | 8.5 | 12.17 |

## Verdict

Raw craft leader: **flash-clues** (8.25/10). Conditions within 0.15 (treated as a tie): flash-clues, flash-baseline, pro-antislop.

Practical winner on equal craft with the fewest AI tells: **pro-antislop** — composite 8.12, style penalty 0.0, fidelity 8.5.

Margin between raw leader and runner-up is only 0.07, so trust the tie-break on AI tells rather than the ordering.

## Per-sample detail

| candidate | condition | composite | overall | fidelity | style penalty | judge tells |
|---|---|---|---|---|---|---|
| flash-antislop--0214d8d16ee7 | flash-antislop | 7.75 | 7.5 | 8.5 | 0.5 | It's not just growing. It's growing together.; So what did they find?; There are limits.; There's always more going on. |
| flash-antislop--2660172c5aa9 | flash-antislop | 8.5 | 8.5 | 9.0 | 2.5 | That quiet trick is the subject of a paper called...; There's always more going on. |
| flash-antislop--e490fd6b5779 | flash-antislop | 7.75 | 7.5 | 7.5 | 0.0 | Back to that small green paddle under the microscope.; That is the comparison.; its headline is this: |
| flash-antislop--e623c3d9aef0 | flash-antislop | 8.08 | 8.0 | 7.5 | 0.0 | Here's the useful comparison; I'm Clara Rowan. There's always more going on.; One thing worth flagging; There's no journal named in what I've got, so I'll leave |
| flash-antislop-think--2a3447a5e51c | flash-antislop-think | 7.92 | 7.5 | 8.0 | 1.0 | Back to that pinhead leaf.; Here's the question:; Now the limits.; That's a comparison. |
| flash-antislop-think--64000f565a26 | flash-antislop-think | 8.17 | 8.5 | 9.0 | 0.0 | 'So back to that green speck.' — slightly formulaic callback; 'Then came the growth maps.' — mild staged-reveal transition; The bus-stop analogy is a touch tidy |
| flash-baseline--440042c08791 | flash-baseline | 7.83 | 7.5 | 7.0 | 9.5 | But there are limits; It's growth that has learned to agree with itself across the whole blade.; That's a comparison, not a claim about plants; That's a compari |
| flash-baseline--460feabf0a7c | flash-baseline | 8.0 | 8.0 | 7.5 | 7.0 | Here's the interesting part; One more wrinkle; There's always more going on; the image to keep is |
| flash-baseline--984ec3b7b31b | flash-baseline | 8.67 | 8.5 | 8.0 | 0.0 | formulaic sign-off: 'There's always more going on.'; staged reveal: 'Here's the puzzle.' |
| flash-baseline--e264042e1af7 | flash-baseline | 8.33 | 8.0 | 7.5 | 0.5 | It is worth noting that; So back to that pinhead leaf; The closing 'There's always more going on' is a bit of a stock sign-off.; The phrase 'That small drama is |
| flash-baseline--ea4f81bb9b2b | flash-baseline | 8.08 | 8.0 | 7.0 | 7.0 | formulaic sign-off: 'There's always more going on'; neighbourhood/house-by-house analogy feels slightly over-explained; staged reveal framing: 'That quiet trick |
| flash-clues--4df72e7f09e2 | flash-clues | 8.5 | 8.5 | 8.0 | 0.5 | Here is the comparison that helps; So the flat leaf on the windowsill is not passive; That said, the study has limits |
| flash-clues--ea2521ec758d | flash-clues | 8.0 | 8.0 | 8.0 | 0.0 | But the pattern is clear: a flat leaf isn't just a leaf that grows the right amount. It's a leaf whose cells agree on the pace.; So the difference isn't how muc |
| luna-antislop--0e774356b86d | luna-antislop | 8.17 | 8.0 | 9.0 | 0.5 | Comparison: it’s a little like...; So, that little leaf...; The closing line 'There's always more going on' feels like a generic sign-off.; The phrase 'botanica |
| luna-antislop--1c97c47ac984 | luna-antislop | 7.83 | 8.0 | 9.0 | 0.0 | Comparison: picture a sheet being stretched; formulaic closing 'There's always more going on'; staged signposting with 'There was another difference' |
| luna-antislop--56b8be38c403 | luna-antislop | 7.83 | 7.5 | 8.5 | 0.0 | The paper has no journal listed in the supplied material.; There's always more going on. |
| luna-antislop--afa0cd8ca187 | luna-antislop | 7.67 | 7.5 | 8.0 | 0.0 | Comparison: think of a tablecloth; That puzzle sits at the heart of; There's always more going on |
| luna-baseline--58d10196a5f6 | luna-baseline | 8.17 | 8.0 | 9.0 | 13.5 | So, back to that tiny construction site; There's always more going on; nature's geometry, with fewer snacks |
| luna-baseline--d830c12e8d8a | luna-baseline | 7.5 | 7.5 | 7.5 | 1.5 | Comparison: it’s a bit like; The opening line 'A young leaf is meant to be a rather good piece of engineering' is slightly generic.; The phrase 'Comparison: it' |
| luna-baseline--fe1f1cb3f710 | luna-baseline | 7.92 | 8.0 | 9.0 | 21.5 | **As a comparison**; Not a leaf standing still, but a leaf negotiating its shape while it grows; The opening 'Watch a young leaf at the microscope...' is engagi |
| luna-clues--4e46fa22474b | luna-clues | 7.83 | 7.5 | 8.0 | 0.5 | I'm Clara Rowan. There's always more going on.; There’s no journal named in the supplied material.; This is Growth-rate coordination across the width of a leaf  |
| luna-clues--ea32f93f1ee3 | luna-clues | 8.17 | 8.0 | 9.0 | 0.0 | As far as anyone can tell; There's always more going on |
| pro-antislop--49fc7caaea52 | pro-antislop | 8.0 | 8.0 | 8.0 | 0.0 | It’s a bit like a sheet of pastry that rises unevenly in one spot while the rest stays flat, the tension has to go somewhere; It’s the kind of small oddity you  |
| pro-antislop--4f1501b6eb50 | pro-antislop | 8.25 | 8.0 | 9.0 | 0.0 | It's a bit like a neighbourhood where everyone adds an extension at their own pace; So the next time you see a flat leaf, consider the quiet agreement among its |
| pro-baseline--519002b2971a | pro-baseline | 8.0 | 8.0 | 7.5 | 0.5 | But the takeaway is rather lovely; So what's going on beneath that green surface?; There's always more going on; Think of it like a group of people rolling out  |
| pro-baseline--c9add3a46b1a | pro-baseline | 7.75 | 7.5 | 8.5 | 0.0 | less ordinary than it looks; the leaf remembers it in every curve; the picture is clear |
