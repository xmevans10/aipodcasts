# Stage 2 — Repair generation instructions and deterministic validation

Read `00-shared-context.md` and the completed stage-1 contract. Implement the changes in
production paths for both solo and dialogue. Preserve their shared scientific guarantees.

## Goal

Make understandable speech the default and block objectively invalid speech before it
can be narrated. Keep source evidence, internal control instructions, and listener-facing
copy distinct. Do not solve this with one extra paragraph appended to an already
contradictory prompt.

## Required work

1. Trace instruction assembly in `draft_story`, schemas, host guides and all validators.
   Reconcile contradictions: mandatory exact titles versus accessible openings; “no
   headings” versus “Comparison:” labels; limitations versus packet `scope`; host persona
   demands versus evidence and beat fit. Establish an explicit precedence order: factual
   fidelity and attribution, audience comprehension, host personality, stylistic flourish.

2. Consolidate shared title/audience/speech rules so solo and dialogue do not diverge.
   Reuse `TITLE_GUIDE` and the stage-1 contract. Keep the useful current title examples,
   preserve the short-title checks, and prohibit claims in headlines that the script's
   evidence cannot support. An intriguing title must not imply a treatment, causal effect,
   or real-world experiment that was never tested.

3. Give the writer a compact process: select the one supported finding worth explaining;
   identify the prerequisite idea; explain the method in ordinary actions; state the result
   and its boundary; then edit out unnecessary names, numbers and asides. Do not demand
   verbose hidden reasoning, produce a public outline, or add an extra paid call merely
   to demonstrate a multistage architecture.

4. Explicitly mark `scope`, provenance notes, omission metadata, review instructions and
   formatting requirements as internal controls, never spoken content or a caveat to copy.
   Preserve the evidence-selection controls. Do not delete warnings from evidence packets
   just because a writer previously repeated them. The caveat should be a real, plain-language
   limitation supported by the evidence, repeated exactly in speech once.

5. Make co-host explanations progressive. One presenter may ask the question a listener
   would ask; the next must answer it in easier words, not introduce three new concepts.
   Preserve stable speaker names/IDs, participation/run constraints, source attribution,
   and each presenter's exact sign-off in that presenter's own turn.

6. Add shared deterministic checks for clear defects, with actionable repair errors:
   - Known internal instruction leakage, including scope boilerplate and “Do not claim a
     complete review”; cover meaningful normalization/case/whitespace variations.
   - Spoken production labels, markdown and stage directions where unambiguously invalid.
   - Title/paper-title confusion after retitling and malformed generated punctuation where
     it can be tested reliably. Avoid a universal string ban that rejects harmless usage.
   - Existing schema, source/claim, headline, author, caveat and sign-off requirements.
   Do NOT use a blanket ban on technical vocabulary, scientific names, units or numbers.
   Broader comprehension belongs to stage 3.

7. If the user explicitly approved moving paper titles to source cards, change both schemas'
   consumers, prompts, validators, repair messages, regression fixtures and docs coherently.
   Preserve exact source metadata and first-author credit. Otherwise keep current checks
   and place the long title only once after a clear hook. Do not duplicate it to satisfy
   two independent validators.

8. Feed specific validation errors back through the existing bounded repair loop. Every
   provider attempt must be accounted for; honor the current cap and selected model.
   Never fix failures by stripping problematic speech after verification or silently
   truncating scientific content. Edits invalidate approvals and require fresh review.

## Verification

Add tests of actual validation and repair behavior, not snapshots that merely assert a
prompt contains “plain English.” Cover solo/duo/four-host leakage, legitimate limitations,
unknown speakers, another presenter's sign-off, retained quote checks, episode-vs-paper
attribution, and repair exhaustion that leaves a draft unapproved. Test source data cannot
become executable instructions.

Use mocked provider responses for deterministic repair-loop tests. A bounded live pilot
can later validate writing quality with configured providers; offline passing tests alone
must not be described as proof that listeners will understand the output.

Done when both generation paths use the reconciled shared contract, clear defects fail
with useful messages, existing scientific checks remain intact, attempts remain bounded,
and relevant tests plus the required backend suite pass. Update prompt/version metadata
where the repository tracks generation versions. Do not regenerate/publish all episodes yet.
