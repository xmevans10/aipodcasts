# Efficient science ingestion

**Historical first-selector result, superseded after quality audit:** **100,493 source characters → 17,862 serialized evidence-packet characters (82.2% smaller)**. The packet contains 14 intact paragraphs; 47 extracted prose paragraphs are omitted. Figure/table captions are excluded from selection. The complete extracted source remains stored for editorial review.

This is a character measurement, not an exact tokenizer count or a dollar-saving guarantee. Schema/instructions and output also consume tokens. The backend now records provider-reported input/output token counts on actual OpenAI responses; there have been no live generation calls yet.

## What the selector does

Extract section-labelled paragraphs from primary article XML. Keep the full source separately. Deduplicate identical paragraphs. Reserve room for available abstract, explicit limitation, results, methods and discussion passages; prioritize sample-size paragraphs. Fill spare room across sections instead of simply taking the start of the paper. Preserve whole paragraphs and their source IDs. Target 18,000 serialized source-input characters; expand adaptively up to twice the target when required evidence needs room (absolute cap 60,000). If required selected evidence cannot fit, stop instead of slicing it silently.

No extra LLM call or embeddings service is required. Selection is a heuristic, not a guarantee of sufficient evidence. Implicit limitations, essential figure information or detailed methods may be omitted. The prompt explicitly labels the packet partial. All model-provided evidence quotations must match text actually supplied to that model, not merely some unseen part of the full paper. A human editor must still consult the complete source and can increase the budget for a complex paper.

## Existing cost controls

- Discovery retrieves feed metadata before full-text ingestion.
- Existing DOI/host records and generated drafts are reused rather than regenerated.
- The client cannot initiate generation. One published script/audio file serves many listeners.
- Script lengths, output tokens and daily provider-call attempts are bounded.
- Provider failures are not retried automatically.

The daily cap counts requests, not dollars. A provider timeout may still incur charges. Configure provider-side budgets separately.

## Usage

```
python3 backend/pipeline.py packet e94c833d4832dae56f3c
python3 backend/pipeline.py usage
```

Optional local override in `backend/.env`: `LILT_MAX_SOURCE_CHARS=24000` (allowed range 2,000–60,000). Review the resulting packet before generating. The current leaf sample uses the 18,000-character default.

The CLI now reads allowlisted provider settings from `backend/.env` without executing shell expressions. Existing nonempty process environment values take precedence. The file is git-ignored and was created with owner-only permissions. Deployment/origin/data paths still use actual process environment variables.

Next experiments after credentials: compare full-paper and packet-based drafts on at least 10 varied papers, with blinded editorial scoring for factual accuracy, critical omissions and listening quality. Do not reduce the budget further solely because the first sample looks good. For difficult stories, retrieve additional specific sections; avoid an unconditional second whole-paper summary pass. Consider provider batch/caching features only after measuring real usage and checking current service terms.

Verified model reference for the first configured trial: https://developers.openai.com/api/docs/models/gpt-5.6-luna . Model selection remains configurable. This choice is for a quality/cost experiment, not a claim that the model is sufficient without editorial evaluation.

## Podcast writer

Default: `gpt-5.6-luna`, `reasoning.effort=low`, 3,500 maximum output tokens, one generation request. The same request produces the headline, deck, spoken script, limitation excerpt and evidence map. No separate polishing request, automatic retries or silent promotion to a more expensive model. Low reasoning is a trial choice; assess scientific and editorial quality before production.

The prompt in `backend/podcast.py` requires a curiosity hook, spoken headline, exact paper title, named-author credit, accessible explanation, limitations and a closing callback. Full author metadata is now part of the capped input packet. Actual narration uses the script once, followed by source-credit guidance and AI-voice disclosure, without repeating the headline or caveat. These deterministic gates cannot guarantee an engaging or fully accurate episode; editorial review remains necessary.

The revised reference script is `editorial/leaf-sample.md`. It was written in this assistant session, not generated via the live Luna API. The older 17,862-character measurement predates the added citation metadata; current packets remain capped at 18,000 characters.

## Full-versus-slim audit and token measurements

The original packet failed 9 of 18 curated evidence-availability checks. It is superseded. The revised packet retains all 18 checks on this same paper, with a 30,944-character packet. See [the audit](editorial/evidence-audit.md) for losses, fixes and evaluation limits. No paired live model pass has run.

Local counts using tiktoken o200k_base (fallback, NOT verified Luna billing):

| Source-input form | Tokens |
|---|---:|
| Full article JSON | 23,145 |
| Original slim JSON, rejected by audit | 3,975 |
| Revised JSON, readable | 6,883 |
| Revised JSON, pretty-printed | 7,043 |
| Revised JSON, compact — production choice | 6,722 |
| Revised labelled text, same evidence/metadata | 6,553 |

Compact JSON saves 161 tokens versus default JSON on this packet. Labelled text saves only another 169 tokens (2.5% of compact JSON). JSON provides stable parsing/validation and source identifiers, not compression. Keep structured output; changing the input format should be evaluated for model quality, not just token count. These counts exclude instructions, output schema and API framing. Exact model-specific input accounting requires the authenticated Responses input-token endpoint or recorded live response usage: https://developers.openai.com/api/reference/typescript/resources/responses/subresources/input_tokens .

Production now serializes input JSON compactly. Other priorities: avoid duplicate generations, preserve fixed prompt prefixes for potential provider caching, generate one approved script per story, constrain evidence-quote length, and retrieve additional sections only when necessary. Provider caching/batch discounts concern cost, not necessarily fewer context tokens; check current terms before adopting. Gzip/Base64 are transport/storage encodings, not useful ways to reduce text seen by a language model.
