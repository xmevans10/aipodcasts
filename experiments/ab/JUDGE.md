# Blind AI judge — leaf draft A/B

Judges: pro, flash (DeepSeek, thinking disabled, temp 0). `composite` is the mean of hook, clarity, spoken rhythm, human voice, host fit and overall across both judges. `bundled-baseline` scripts cover different papers, so their `fidelity` is null and only craft dimensions are comparable. Note: `backend/data/baseline-2026-09-17/manifest.json` records the bundled scripts as assistant-authored, not a live Luna API run, so treat `bundled-baseline` as a human/assistant quality reference, not API output.

| rank | condition | n | composite | fidelity | det. style penalty |
|---|---|---|---|---|---|
| 1 | flash-baseline | 5 | 8.18 | 7.4 | 4.8 |
| 2 | pro-antislop | 2 | 8.12 | 8.5 | 0.0 |
| 3 | flash-antislop | 2 | 8.12 | 8.25 | 1.25 |
| 4 | flash-antislop-think | 2 | 8.04 | 8.5 | 0.5 |
| 5 | luna-antislop | 2 | 8.0 | 8.75 | 0.25 |
| 6 | pro-baseline | 2 | 7.88 | 8.0 | 0.25 |
| 7 | luna-baseline | 3 | 7.86 | 8.5 | 12.17 |
| 8 | bundled-baseline | 4 | 7.33 | None | 0.25 |

## Verdict

Raw craft leader: **flash-baseline** (8.18/10). Conditions within 0.15 (treated as a tie): flash-baseline, pro-antislop, flash-antislop, flash-antislop-think.

Practical winner on equal craft with the fewest AI tells: **pro-antislop** — composite 8.12, style penalty 0.0, fidelity 8.5.

Margin between raw leader and runner-up is only 0.06, so trust the tie-break on AI tells rather than the ordering.

## Per-sample detail

| candidate | condition | composite | overall | fidelity | style penalty | judge tells |
|---|---|---|---|---|---|---|
| bundled-baseline--clara | bundled-baseline | 8.08 | 8.0 | None | 0.0 | But here's where the story needs its brakes.; Sometimes the interesting question isn't whether... It's what...; Today's headline:; there's something wonderful h |
| bundled-baseline--elias | bundled-baseline | 7.58 | 7.5 | None | 1.0 | Let's keep asking how.; Resembling is the important word.; That's a metaphor.; The final line 'Your host and narration are AI-generated.' is a direct disclosure |
| bundled-baseline--mira | bundled-baseline | 8.25 | 8.0 | None | 0.0 | And the hole isn't the whole story; Here's the lovely part; So the next time the Moon looks perfectly still, remember; Stay a little curious; The closing 'Stay  |
| bundled-baseline--theo | bundled-baseline | 5.42 | 5.0 | None | 0.0 | Each method has limitations — vague hedge with no specifics; I'm Theo Mercer, and this is Sound Science (show name mismatch with host profile); Some sentences a |
| flash-antislop--2660172c5aa9 | flash-antislop | 8.5 | 8.5 | 9.0 | 2.5 | That quiet trick is the subject of a paper called...; There's always more going on. |
| flash-antislop--e490fd6b5779 | flash-antislop | 7.75 | 7.5 | 7.5 | 0.0 | Back to that small green paddle under the microscope.; That is the comparison.; its headline is this: |
| flash-antislop-think--2a3447a5e51c | flash-antislop-think | 7.92 | 7.5 | 8.0 | 1.0 | Back to that pinhead leaf.; Here's the question:; Now the limits.; That's a comparison. |
| flash-antislop-think--64000f565a26 | flash-antislop-think | 8.17 | 8.5 | 9.0 | 0.0 | 'So back to that green speck.' — slightly formulaic callback; 'Then came the growth maps.' — mild staged-reveal transition; The bus-stop analogy is a touch tidy |
| flash-baseline--440042c08791 | flash-baseline | 7.83 | 7.5 | 7.0 | 9.5 | But there are limits; It's growth that has learned to agree with itself across the whole blade.; That's a comparison, not a claim about plants; That's a compari |
| flash-baseline--460feabf0a7c | flash-baseline | 8.0 | 8.0 | 7.5 | 7.0 | Here's the interesting part; One more wrinkle; There's always more going on; the image to keep is |
| flash-baseline--984ec3b7b31b | flash-baseline | 8.67 | 8.5 | 8.0 | 0.0 | formulaic sign-off: 'There's always more going on.'; staged reveal: 'Here's the puzzle.' |
| flash-baseline--e264042e1af7 | flash-baseline | 8.33 | 8.0 | 7.5 | 0.5 | It is worth noting that; So back to that pinhead leaf; The closing 'There's always more going on' is a bit of a stock sign-off.; The phrase 'That small drama is |
| flash-baseline--ea4f81bb9b2b | flash-baseline | 8.08 | 8.0 | 7.0 | 7.0 | formulaic sign-off: 'There's always more going on'; neighbourhood/house-by-house analogy feels slightly over-explained; staged reveal framing: 'That quiet trick |
| luna-antislop--0e774356b86d | luna-antislop | 8.17 | 8.0 | 9.0 | 0.5 | Comparison: it’s a little like...; So, that little leaf...; The closing line 'There's always more going on' feels like a generic sign-off.; The phrase 'botanica |
| luna-antislop--56b8be38c403 | luna-antislop | 7.83 | 7.5 | 8.5 | 0.0 | The paper has no journal listed in the supplied material.; There's always more going on. |
| luna-baseline--58d10196a5f6 | luna-baseline | 8.17 | 8.0 | 9.0 | 13.5 | So, back to that tiny construction site; There's always more going on; nature's geometry, with fewer snacks |
| luna-baseline--d830c12e8d8a | luna-baseline | 7.5 | 7.5 | 7.5 | 1.5 | Comparison: it’s a bit like; The opening line 'A young leaf is meant to be a rather good piece of engineering' is slightly generic.; The phrase 'Comparison: it' |
| luna-baseline--fe1f1cb3f710 | luna-baseline | 7.92 | 8.0 | 9.0 | 21.5 | **As a comparison**; Not a leaf standing still, but a leaf negotiating its shape while it grows; The opening 'Watch a young leaf at the microscope...' is engagi |
| pro-antislop--49fc7caaea52 | pro-antislop | 8.0 | 8.0 | 8.0 | 0.0 | It’s a bit like a sheet of pastry that rises unevenly in one spot while the rest stays flat, the tension has to go somewhere; It’s the kind of small oddity you  |
| pro-antislop--4f1501b6eb50 | pro-antislop | 8.25 | 8.0 | 9.0 | 0.0 | It's a bit like a neighbourhood where everyone adds an extension at their own pace; So the next time you see a flat leaf, consider the quiet agreement among its |
| pro-baseline--519002b2971a | pro-baseline | 8.0 | 8.0 | 7.5 | 0.5 | But the takeaway is rather lovely; So what's going on beneath that green surface?; There's always more going on; Think of it like a group of people rolling out  |
| pro-baseline--c9add3a46b1a | pro-baseline | 7.75 | 7.5 | 8.5 | 0.0 | less ordinary than it looks; the leaf remembers it in every curve; the picture is clear |
