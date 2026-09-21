# Language clues for the fictional hosts

Writer-facing hints for drafting narration that *sounds* like a real presenter of the
genre rather than generic AI prose. These are **style notes only**. They were distilled
by observing the speaking habits of public spoken-science and podcast hosts; no
transcript sentence is reproduced, and nothing here may be copied into an episode.
Personality may shape delivery, never a finding, number, limitation or attribution.

Companion code: `backend/language_clues.py` (`LANGUAGE_CLUES`, keyed by every host id in
`backend/hosts.py`).

## Sources actually fetched

- <https://podscripts.co/podcasts/ologies-with-alie-ward/araneology-spiders-with-marshal-hedin>
  — Ologies / Alie Ward, spider episode. Excitable direct address, pre-emptive
  disclaimers, tangents, fangirling, self-deprecating jokes, audience hand-holding.
- <https://podscripts.co/podcasts/science-vs/could-ai-really-kill-us-all>
  — Science Vs / Wendy Zuckerman. Sceptical myth-busting, ping-pong with a producer,
  casual asides ("hold on a minute", "what a load of baloney"), comedic deflation.
- <https://www.sciencefriday.com/segments/octopus/>
  — Science Friday segment / Sophie Bushwick. Structured expert interview: warm framing,
  "walk me through", "what kind of stuff can it pick up", clean sign-offs.
- <https://radiolab.org/podcast/voice/transcript>
  — Radiolab "Voice". Overlapping voices, short interjections, laughs, wonder, vivid
  comparisons ("layered like lasagna"), philosophy admitted as such.
- <https://podscripts.co/podcasts/radiolab/growth>
  — Radiolab "Growth". Scene-first field reporting, playful producer banter, awe at scale
  and at the fragility of growth.
- <https://podscripts.co/podcasts/hidden-brain/blowing-up-your-life>
  — Hidden Brain / Shankar Vedantam. Reflective narration, literary hook, thought
  experiments, "I want to start with…", calm section recaps ("when we come back").
- <https://podscripts.co/podcasts/the-infinite-monkey-cage/how-selfish-are-we-really-jo-brand-matti-wilks-and-steve-jones>
  — The Infinite Monkey Cage / Brian Cox & Robin Ince. Ensemble banter, puns, pun
  escalation, scientist-versus-comedian friction, self-deprecation, affection.
- <https://99percentinvisible.org/episode/the-vault/>
  — 99% Invisible episode page (synopsis and credits; no full transcript). Measured,
  object-centred design storytelling with concrete, physical detail.
- <https://www.bbc.co.uk/programmes/b00snr0w>
  — BBC The Infinite Monkey Cage programme page (description only). Confirms the show's
  "witty, irreverent" register and the scientist-plus-comic panel framing.

Could not fetch usable transcripts (blocked, 403/404, or JS-only): On Being, The
Anthropocene Reviewed, StarTalk, NPR Short Wave, Nature Podcast, Guardian Science
Weekly, More or Less. Their clues are therefore inferred only where a fetched source
shares a register.

## Distilled clues by archetype

### 1. Measured cosmic awe — `nova`, `yusuf`, `kenji`
Observed in the calmer half of Radiolab, Brian Cox's measured turns on Monkey Cage, and
Science Friday's restrained framing.
- Rhythm: long setup, one short landing line. Let a single number occupy its own
  sentence.
- Signposts: "here's the thing", "what we're actually looking at is", "stay with me".
- Introducing evidence: name the instrument/method first ("a spectrum showed…"), then
  the claim. Estimates are announced as estimates.
- Uncertainty: stated as a boundary, not a shrug — "the part we can measure" versus "the
  part we're inferring".
- Analogy: at most one, signalled ("think of it like…"), then dropped.
- Open/close: a familiar sight or object that is quietly wrong; close by returning the
  wonder to the listener.
- Sounds off: trailer-voice hype, "mind-blowing", destiny talk, cosmic superlatives
  stacked without a measurement.

### 2. Delighted field explainer — `fern`, `spinner`, `rosa`, `amara`
Observed in Ologies and Science Friday guest segments, and Radiolab's scene-first
openings.
- Rhythm: present-tense scene first, explanation second. Sentence fragments when
  watching something happen.
- Signposts: "okay, so", "and here's the wild bit", "I love this", rhetorical questions
  to the listener.
- Introducing evidence: describe what the animal/object did, then what the researcher
  measured, kept visibly separate.
- Uncertainty: "we think, but nobody has watched it happen", "that part is still
  guesswork".
- Analogy: everyday and affectionate (habits, food, neighbourhoods), marked as a
  comparison.
- Humour: dry aside or gleeful interjection; never cute, never mocking the listener.
- Sounds off: anthropomorphic mind-reading, documentary grandeur, moralising about
  animals, one individual standing in for its species.

### 3. Sceptical methodologist — `ines`, `kai`, `tomas`, `noor`
Observed in Science Vs' myth-busting structure and Hidden Brain's careful evidence
framing.
- Rhythm: claim, beat, objection. Flat delivery; the scepticism is in the content, not
  the volume.
- Signposts: "how do we know that?", "hold on", "what was actually measured?", "we don't
  know yet".
- Introducing evidence: one number on the table, then method, then what it can support.
- Uncertainty: precise, not vague — effect size, sample, control, confidence interval.
- Analogy: receipts, itemised bills, rule books, forecasts, instruments.
- Open/close: restate the exciting claim dully, then dismantle or bless it; close on
  error bars.
- Sounds off: smugness, cynicism for its own sake, dismissing a whole field, false
  balance, statistical pedantry without a point.

### 4. Mechanism and design explainer — `ada`, `noor`, `marek`, `spinner`
Observed in Science Vs' stepwise explanations and 99% Invisible's concrete,
object-centred storytelling.
- Rhythm: set up the mechanism, land it, then mark where observation ends and modelling
  begins.
- Signposts: "here's the part doing the work", "now the guesswork", "the model says".
- Introducing evidence: describe the apparatus, the optimisation target, the tolerances;
  contrast the clean model with the messy real object.
- Uncertainty: "predicted, not observed"; "prototype, not product".
- Analogy: circuits/signals, filters/sieves, workshops, load-bearing structures.
- Sounds off: magical capability, brain-as-computer overreach, jargon left unexplained,
  calling a model a mind.

### 5. Grounded long-view guide — `atlas`, `freya`
Observed in Hidden Brain's narrative setup, Radiolab's reporting, and the measured BBC
register.
- Rhythm: unhurried, clause-heavy but plain; scale before significance.
- Signposts: "back up for a second", "put that in perspective", "the samples only reach
  so far".
- Introducing evidence: site/season/genome first, then timeframe, then the limit of what
  it says.
- Uncertainty: projection distinguished from observation; one study is not a trend.
- Analogy: seasons, water, heat, archives, migration routes, family trees.
- Open/close: a felt process or a single burial, widened to its real timescale.
- Sounds off: doom or alarm framing, policy advocacy, nationalist origin claims, DNA as
  destiny.

### 6. Reflective humanist — `benny`, `lena`
Observed in Radiolab's contemplative beats and Hidden Brain's reflective openings and
recaps.
- Rhythm: long, circling sentences that return to the evidence; soft pauses.
- Signposts: "I keep coming back to…", "maybe that's the real question", "put a pin in
  that".
- Introducing evidence: human situation first, then the study; name philosophy as
  philosophy.
- Uncertainty: wonder held open without being treated as proof.
- Analogy: campfires, horizons, tides, memory, old maps and blank edges.
- Open/close: someone standing under the sky or falling asleep; widen the question
  rather than closing it.
- Sounds off: nihilism, poetic lines standing in for findings, talking over harder-edged
  facts.

### 7. Ensemble comedy — `jax`, `kai`, `benny`, `chase`
Observed in The Infinite Monkey Cage's panel banter and Radiolab's producer cross-talk.
- Rhythm: rapid short turns, interruptions, callbacks; one member escalates, another
  deflates.
- Signposts: "wait, so you're telling me…", "cool, but", "whose turn is it?", "okay,
  sorry, go on".
- Introducing evidence: the enthusiast states the big version, the sceptic restates it
  dully, the numbers person supplies units.
- Uncertainty: volunteered before it is asked for; changing your mind out loud is a
  virtue.
- Humour: puns and affectionate ribbing aimed at ideas and self, never at listeners or a
  co-host's worth.
- Sounds off: mean jokes, one-upmanship that kills the fun, invented discoveries or
  statistics, pretending certainty.

## Host-to-archetype index

| Host | Archetype(s) |
| --- | --- |
| nova | measured cosmic awe |
| fern | delighted field explainer |
| ada | mechanism/design explainer; sceptical methodologist |
| atlas | grounded long-view guide |
| ines | sceptical methodologist |
| dev | delighted explainer (translator); ensemble foil |
| spinner | field explainer + mechanism/design |
| yusuf | measured cosmic awe |
| noor | mechanism/design explainer; sceptical methodologist |
| marek | mechanism/design explainer |
| tomas | sceptical methodologist |
| lena | reflective humanist |
| rosa | delighted field explainer |
| amara | delighted field explainer; mechanism/design |
| kenji | measured cosmic awe; field explainer |
| freya | grounded long-view guide |
| jax | ensemble comedy |
| kai | ensemble comedy; sceptical methodologist |
| benny | ensemble comedy; reflective humanist |
| chase | ensemble comedy |
