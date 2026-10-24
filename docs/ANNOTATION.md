# Question annotations and blinded error review

Question annotation precedes output inspection. Annotators see only the original question and its ID, not model predictions, condition/model identity, correctness or timing. `data/annotations-template.csv` includes pilot and test questions; train/test scope remains explicit in IDs.

Fields:

| Field | Values | Rule |
|---|---|---|
| process_sequence | yes / no / ambiguous | At least two events/stages whose ordered updates affect a persistent quantity; simple static addition alone is not sufficient. |
| equation_need | direct_arithmetic / unknown_relation / simultaneous / ambiguous | `unknown_relation`: a quantity is specified through a relationship naturally expressed with an unknown; `simultaneous`: multiple linked unknowns/constraints. This is representational suitability, not a proof that algebra is mathematically necessary. |
| quantity_structure | count / money / rate / ratio_percent / time_distance / mixed / other | Use mixed when multiple dimensions are essential. |
| reviewer | nonempty identifier | Human annotator. |
| validated | yes / no | Yes only after independent review/adjudication. |
| rationale | short justification | Cite the relevant statement in the question. |

Use two independent annotators, record disagreement and adjudication; preserve original forms. Annotate without model outcomes. Report label counts and agreement before subgroup analysis. Do not claim a subgroup effect until every analyzed question has adjudicated validated labels. Automated suggestions, if later added, are provisional and require human validation; this project does not infer labels from successful strategies or output code.

## Error review

`python -m gsm8k_lab review RUN_ID` samples up to 3 records in each model × condition × observed-status stratum with fixed seed. Each reviewer row contains an opaque review ID, question, reference answer, raw response and execution stdout; model/condition/status labels are withheld. Code representation can make arm inference possible, so blinding is partial, not guaranteed. Keep `review-key-private.json` with the coordinator; it records stratum size, sample size and inclusion probability. Preserve these probabilities for population-weighted summaries; a balanced error sample is not a population frequency estimate. Repeated conditions of the same question remain clustered.

Review fields (yes / no / uncertain, plus rationale):

- semantic_modeling_error: incorrect quantities, relations, units, event order or requested target; only assign with supporting evidence.
- arithmetic_error: representation and numerical setup are correct but a calculation is wrong; do not guess from a wrong final answer alone.
- api_error: unsupported function/signature/object usage, distinguish from general Python syntax failures.
- state_update_compliance: explicit meaningful state variables updated in problem order; loops neither required nor sufficient. For nonprocess questions use `not_applicable` if this concept cannot be meaningfully assessed.
- uncertain: any uncertainty that prevents a reliable causal error classification.

Multiple error mechanisms may co-occur. Keep automatic execution categories separate from manual semantic labels. K5 noncompliance never removes an observation from the primary accuracy denominator. No automated subgroup/semantic conclusions are emitted by the reporting code.
