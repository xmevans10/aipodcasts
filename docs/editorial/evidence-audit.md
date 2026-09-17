# Slim-versus-full evidence audit

## Result

The original slim selector lost meaningful evidence. Its revised version retains all 18 curated evidence checks on this paper, including all 14 checks marked core. This is an in-sample regression result, not proof of general semantic completeness or an independent model evaluation.

Source: [Growth-rate coordination across the width of a leaf preserves its flatness](https://doi.org/10.1371/journal.pbio.3003993). CC BY 4.0; complete author attribution is retained in backend/evals/leaf/source.json.

| Check | Original slim | Revised slim |
|---|---|---|
| Arabidopsis and jaw-D, rather than a general survey of all leaves | Retained | Retained |
| Slower mutant midrib versus blade; coordinated widthwise growth in wild type | Retained | Retained |
| Direction and spatial arrangement matter, not simply the amount of uneven growth | Missing | Retained |
| Repeated imaging: three leaves per genotype, days 3–8 | Retained | Retained |
| Primary live imaging measured lower epidermis | Retained | Retained |
| Curvature obscured proximal mutant cells, likely undercounting them | Retained | Retained |
| Mature-leaf sample is separate and larger (34/36 leaves) | Retained | Retained |
| Maturation is delayed in the mutant | Retained | Retained |
| Removing the longitudinal gradient did not change modeled curvature | Missing | Retained |
| Coverslip/agar mechanically constrained leaf shape; unconstrained leaves rolled | Missing | Retained |
| Model growth rates/directions were manually set from qualitative imaging assessment | Missing | Retained |
| Gaps from trichomes prevent a strong upper-surface coordination conclusion | Missing | Retained |
| No observed early margin overgrowth; later leaves could differ | Missing | Retained |
| Other species have other growth patterns; extension is prediction/future work | Missing | Retained |
| Top/bottom growth differences occurred in both genotypes, arguing against that explanation | Retained | Retained |
| Stomatal patterning relatively preserved despite pavement-cell differences | Retained | Retained |
| Mutant has more mature leaf-size outliers | Missing | Retained |
| Lineage tracking supports altered spatial contribution of progenitor cells | Missing | Retained |

## What changed

The selector now reserves explicit negative controls, modeling assumptions, mechanical constraints and sample-size paragraphs. It also retains a concluding paragraph from every Results subsection and the final Discussion paragraph. Background prose no longer crowds out late results and boundary conditions. Selection remains deterministic and adds no LLM call.

The target remains 18,000 characters, but necessary evidence can expand the packet up to twice the target, capped at 60,000 characters. The leaf paper uses a 31,000-character budget and contains 30,944 characters. If required material exceeds the hard limit, generation stops for curation/full-text processing rather than silently dropping it.

The original packet was 17,895 characters and passed 9/18 checks (7/14 core). The revised packet passes 18/18 (14/14 core), at a cost of more input. Compared with 100,493 characters of extracted source text, the revised packet is approximately 69% smaller.

## Important scientific distinctions recovered

- Removing the tip-to-base gradient did not change curvature in the models; its alteration alone cannot explain the mutant shape.
- Leaves were mechanically constrained between coverslip and agar during imaging; unconstrained mutant leaves rolled back.
- Simulated growth rates and directions were specified manually from qualitative assessment, not an independently fitted quantitative prediction.
- Upper-surface imaging gaps prevented a strong conclusion about coordination there.
- Early leaf margins did not show the expected overgrowth; later leaves may differ.
- Other species have different growth patterns; broader applicability remains a prediction.

## Boundaries and remaining work

This audit compared the stored extracted main-article text and its section-labelled prose with the selected passages. It does not inspect raw figure pixels, supplementary datasets, supplementary text or author code. The checklist measures availability of selected evidence, not whether a writer uses it correctly. It was curated and used to improve the selector on this same paper, so it is not a holdout evaluation. Test on additional paper types before claiming general quality.

No live full-versus-slim Luna generation was run because OPENAI_API_KEY is not configured. A reusable paired harness is implemented: `python3 backend/evals/evaluate.py --live`. It uses identical writer instructions/model settings for both inputs, records actual provider token usage, caches matching responses and never publishes. A blinded editor must score factual accuracy, critical omissions, attribution, uncertainty and listening quality; one pair alone is not sufficient evidence of equivalence.

Reproduce source audit: `python3 backend/evals/evaluate.py`. Regression suite: `python3 -m unittest discover -s backend/tests -q`. Thirty-four tests passed.
