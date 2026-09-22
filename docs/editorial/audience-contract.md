# The Zwicky audience contract

Canonical editorial standard for spoken Zwicky episodes, solo and co-hosted.
Version: `audience-contract-v1` (2026-09-22).

This document is the standard that generation prompts, deterministic validators and the
audience reviewer all refer to. When a prompt, a validator and this document disagree,
this document describes the intent and the disagreement is a bug to be fixed here first.

Companion documents:

- [Latest-batch review and enforcement map](latest-batch-review.md) — what the 2026-09-21
  batch got wrong, and which module owns each rule.
- `backend/tests/fixtures/editorial_cases.json` — the regression fixtures these rules are
  tested against.

## 1. Who is listening

An intelligent, curious adult with no specialist training. No assumed course in biology,
statistics, astronomy or machine learning. They are listening **once**, while doing
something else. They cannot reread a sentence, pause to look a word up, or inspect a chart.

After one listen they should be able to answer, in their own words:

1. What question did the researchers ask?
2. What did they actually do?
3. What did they find, and why is that interesting?
4. What does this evidence *not* establish?

An episode that fails any of these four has failed, no matter how accurate it is.

A low reading-grade score, short sentences, a friendly opening and a passed factual
verifier are **not** evidence of comprehensibility. Neither is an audience-review pass:
that is a calibrated proxy, not a measurement of real listeners.

## 2. One question, one result, one boundary

Each episode carries:

- **one central question** the paper actually asked;
- **one main result** worth explaining;
- **one meaningful boundary** on that result.

Secondary results, secondary statistics and secondary caveats are cut. A second finding
earns a place only when the main finding is unintelligible without it.

## 3. Explain the phenomenon before naming it

Describe what is happening in ordinary words first. Introduce a specialist term only when
the listener genuinely needs it afterwards — then explain it immediately, and prefer the
everyday phrase for the rest of the episode.

"A protein complex that clamps DNA into loops" comes before "cohesin", not after it.

A term that never gets used again after its definition should not have been introduced.

## 4. Approximate targets, not universal gates

These are editorial targets for a typical episode, not hard numeric gates. Justified
exceptions are allowed and should be visible in the script itself.

| Dimension | Usual target | When to exceed it |
|---|---|---|
| New essential technical terms | at most 2 | a third term is unavoidable and each is explained on first use |
| Important result numbers | 1–2 | a second number is the comparison that makes the first meaningful |
| Method/population numbers | as few as possible | a sample size, population or design fact that prevents a misleading claim is **essential** and must be kept |
| Spoken length | roughly 3–5 minutes (≈350–500 words) | never pad thin evidence to reach it |
| Sentences | natural and varied | no chopping ordinary sentences into fragments for drama |

Never simplify by deleting a number that keeps a claim honest. "22 donated human eyes" is
essential. "a radius of curvature correlated with all measured shear changes" is not.

## 5. A connected explanation, not a template

What / how / result / limit should read as one argument, each part motivating the next.

Avoid a mandatory repetitive shape that makes all sixteen shows sound identical. Hosts
have distinct voices; the contract constrains clarity, not personality.

## 6. Hook, title and dek

- The hook is concrete and **supported by the actual episode**. It must not promise a
  result the paper did not produce.
- The hook comes **first**. No episode opens on a long paper citation.
- The listener-facing title follows the existing shared title rules in
  `podcast.TITLE_GUIDE`: 4–9 words typical, 12 words and 72 characters hard ceiling,
  distinct from the paper title.
- A title must not imply a treatment, a causal effect, or a real-world experiment that
  was never run. An intriguing title that the evidence cannot support is a defect, not a
  stylistic choice.
- The dek is concrete: what was studied, in what population, with what result.

## 7. Analogies

At most **one** analogy per episode, and only when it reduces the listener's burden.

- No required analogy. An episode with no analogy is fine.
- Never speak a production label. `"Comparison:"`, `"Limitations:"`, `"Analogy:"` and
  similar prefixes are formatting instructions, never spoken words. Mark a comparison with
  ordinary English: "it's a bit like…", "think of it as…".
- An analogy must be scientifically bounded and obviously nonliteral.
- If a second analogy is needed to explain the first, both are wrong.

## 8. Limitations

One plain-language limitations passage, spoken once, and exactly matched by the `caveat`
field.

- Preserve every material uncertainty: study population, design, association vs causation,
  simulation vs observation, laboratory vs clinic.
- Do not read an abstract's methods section aloud.
- Do not repeat the same caveat in two paragraphs to satisfy two validators.
- Do not append a legal-sounding disclaimer.

"Verbatim limitations" means the spoken text contains the `caveat` string exactly. It does
**not** mean reading packet instructions aloud, and it does not mean copying source prose.

## 9. Source gaps are packet limits, not study weaknesses

Our evidence packet is partial by construction. When a fact is absent from the packet, say
so as a limit of **this episode's evidence**, if it must be said at all. Never assert it as
a weakness of the paper.

Forbidden:

- "The samples don't reach that far" when the packet merely omits sample counts.
- "The authors did not validate X" when the packet merely does not include the validation.
- Inventing a sample count, a missing dimension, or an absent control.

Preferred, and used sparingly: "This episode is built from the paper's abstract, so the
full methods aren't in front of us."

The packet's own `scope` string is an **internal control**. It is never spoken, never
copied into `caveat`, and never paraphrased as a spoken caveat.

## 10. Co-hosted shows

Dialogue must be progressive, not a monologue split across names.

- One presenter asks the question a listener would actually ask.
- The next **answers it in easier words**, and does not introduce three new concepts.
- Every exchange must move the explanation forward. Alternating expert-sounding speeches
  is a failure even when each speech is accurate.
- Stable speaker names and host IDs, participation and run limits, source attribution and
  each presenter's own exact sign-off are preserved unchanged.

## 11. Beat fit

The connection between a paper and its show must be grounded in the paper, not
manufactured by an opening metaphor.

- A laboratory NMR method is not an astronomy story because atoms were made in stars.
- Eye biomechanics is not a sports-performance story because both involve tissue under
  load.
- If fit cannot be justified from the paper itself, select a better candidate for that
  show or withhold the episode. Do not write around it.

## 12. Precedence

When requirements conflict, resolve in this order:

1. **Factual fidelity and attribution** — evidence-backed claims, correct population and
   design, faithful uncertainty, first-author credit, exact source metadata.
2. **Audience comprehension** — this document.
3. **Host personality** — persona, delivery, hook style, sign-off.
4. **Stylistic flourish** — analogies, rhythm, wit.

A lower level never overrides a higher one. Personality never changes a finding. Style
never removes a caveat.

## 13. Spoken citation policy

**Current policy (retained, user-confirmed 2026-09-22): exact paper title spoken once.**

- The accessible hook comes **first**.
- The exact `source_title` then appears **once**, within the opening, together with the
  first named author and "and colleagues" where there are multiple authors, plus the
  journal where available.
- The exact episode headline also appears once in the opening, and is a different string
  from the paper title.
- The full exact citation always remains in source metadata and the app's source card.

Known cost of this policy: a long technical paper title in the first 30 seconds is a real
obstacle for a general listener. The contract mitigates it by requiring the hook first and
the title once, never twice.

**Approved alternative, not currently active:** exact title in the source card only; the
spoken opening names the first author, the journal and a natural description of the topic.

Adopting the alternative requires an explicit user decision, and then a coherent change to
both schemas' consumers, both prompt sets, both validators, repair messages, the regression
fixtures and this document, in one change. A recommendation in a review is not an approval.
Validators are never silently removed.

## 14. What this contract does not do

It does not ban technical vocabulary, scientific names, units or numbers. A blacklist
cannot decide whether science is understandable, and a gate tuned to reject difficult
subjects would be worse than the problem it replaces. Deterministic checks cover
unambiguous defects only (see the enforcement map); comprehension is judged by structured
audience review against this document.
