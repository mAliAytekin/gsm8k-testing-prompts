# GSM8K with small language models

[English](README.en.md) · [Türkçe](README.md)

A Python project investigating the effects of solution representation, model size,
and solution/API demonstrations through local Ollama inference. The goal is a
controlled experiment and error analysis; no new-method or priority claim is made.

## Current scope

Five models: LFM2-350M, LFM2-700M, LFM2-1.2B, Qwen3-0.6B, and Qwen3-1.7B.
All are local Ollama aliases imported from the original publishers' Q8_0 GGUF
weights. Sources and file revisions are pinned in the [model manifest](configs/models.json);
verified Ollama digests are pinned in the [lock file](configs/model-lock.json).

| Condition | Task | Demonstrations |
|---|---|---:|
| K2 | Step-by-step natural-language reasoning (CoT) | 0 |
| K2_1shot / K2_2shot | CoT | 1 / 2 |
| K3 | Arithmetic expression for a safe calculator | 0 |
| K3_1shot / K3_2shot | Arithmetic expression | 1 / 2 |
| K4 | Unrestricted Python/PAL | 0 |
| K4_1shot / K4_2shot | Python/PAL | 1 / 2 |
| K5 | Python with deterministic state updates | 0 |
| K5_1shot / K5_2shot | State updates | 1 / 2 |
| K6 / K7 / K8 | SymPy | 0 / 1 / 2 |
| K9 | Fixed CoT explanation from the Gemma teacher | 1 |

There are **16 conditions per model**. K1, K10, and Gemma-based judging are absent.
Gemma is only the source of K9's previously generated teacher demonstration.
Pair A uses train questions 0/2; K9 uses only the explanation for train question 0.

## Experimental results — 1,000 questions

**Run completed:** 1,000 distinct questions × 16 conditions × 5 models = **80,000
records**. Of these, **79,999 are evaluable**; one Ollama request encountered an
infrastructure error and was not regenerated. Run ID: `db66d8df297c69c75c54`.

The sample was selected with seed `20261021` from the official GSM8K main
train+test pool after excluding the active demonstration questions: **858 train +
142 test**. Question IDs and hashes are in the [fixed manifest](data/sample1000-manifest.json).
The manifest flags 18 questions overlapping the earlier 200-question pilot. This
is neither an independent held-out test nor an official test benchmark score; it
is a sample evaluation using a design fixed after earlier exploratory work.

### Annotated figure

![End-to-end accuracy of 16 conditions across five Q8_0 models on 1,000 GSM8K questions](reports/db66d8df297c69c75c54/accuracy.png)

**How to read the figure:** rows are conditions, columns are models, and darker
blue means higher accuracy. Each cell covers 1,000 questions. Percentages divide
correct outputs by the 1,000 planned questions and are shown only for fully
evaluable cells. `N/A` marks a cell with missing infrastructure coverage.
`1shot` means one solved demonstration and `2shot` means two; these are not numbers
of generation attempts. CoT means step-by-step natural-language reasoning, PAL
means a Python program, and SymPy means symbolic mathematics code. The figure
retains Turkish descriptive labels; the condition IDs correspond to the English
table above.

**The metric is end-to-end success:** formatting, execution, and numerical
correctness are evaluated jointly. The figure should therefore not be interpreted
as a measure of mathematical ability alone.

### Accuracy across all conditions (%)

| Condition | LFM2-350M | LFM2-700M | LFM2-1.2B | Qwen3-0.6B | Qwen3-1.7B |
|---|---:|---:|---:|---:|---:|
| K2 | 5.9 | 14.2 | 15.0 | 10.0 | 81.4 |
| K3 | 0.0 | 0.0 | 0.2 | 2.2 | 32.7 |
| K4 | N/A¹ | 0.0 | 0.0 | 0.0 | 0.0 |
| K5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| K6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| K7 | 2.4 | 7.4 | 5.5 | 0.0 | 49.9 |
| K8 | 2.0 | 7.8 | 20.3 | 6.5 | 52.2 |
| K2_1shot | 33.1 | 18.7 | 63.9 | 31.8 | 66.0 |
| K2_2shot | 35.0 | 55.3 | 66.0 | 47.5 | 76.6 |
| K3_1shot | 0.0 | 0.2 | 11.5 | 1.3 | 20.3 |
| K3_2shot | 0.1 | 0.7 | 17.6 | 11.5 | 32.4 |
| K4_1shot | 1.5 | 12.0 | 6.4 | 0.0 | 25.0 |
| K4_2shot | 3.7 | 23.3 | 13.6 | 0.0 | 50.7 |
| K5_1shot | 0.6 | 8.6 | 7.8 | 0.3 | 21.5 |
| K5_2shot | 1.5 | 21.4 | 19.8 | 23.6 | 50.4 |
| K9 | 32.0 | 35.9 | 66.7 | 36.7 | 45.6 |

¹ LFM2-350M / K4: **0 correct, 999 evaluable outputs, and 1 infrastructure error**.
The correct/planned lower bound is 0%; the incomplete cell is not presented as a
completed accuracy score. Every other cell is evaluable for 1,000/1,000 questions.
Values use one decimal place; one correct answer equals 0.1 percentage points.

### Findings and interpretation

- **Demonstration effects depend on the model.** With two CoT examples,
  LFM2-350M improved from 5.9% to 35.0%, LFM2-700M from 14.2% to 55.3%,
  LFM2-1.2B from 15.0% to 66.0%, and Qwen3-0.6B from 10.0% to 47.5%.
  In contrast, Qwen3-1.7B's zero-shot CoT score of 81.4% exceeded its two-shot
  score of 76.6%. More examples do not improve every model. Separate
  confirmatory tests are not claimed for all these differences.
- **External-computation conditions did not outperform each model's best
  natural-language condition in this run.** Compliance with the requested
  representation/output contract is an important component. In zero-shot Python
  and SymPy conditions, outputs such as `FINAL: 540` appeared instead of programs.
  Python may parse this as a variable annotation, but it prints nothing; merely
  containing a numerical answer is not successful execution. Zeros in these
  conditions are therefore not, on their own, evidence of mathematical inability.
- **State updates did not show a general advantage over unrestricted PAL.** With
  two examples, K5 exceeded K4 for LFM2-1.2B (19.8% versus 13.6%) and Qwen3-0.6B
  (23.6% versus 0%). It was lower for LFM2-350M/700M and similar for Qwen3-1.7B
  (50.4% versus 50.7%). Human annotations needed to assess process-question
  advantages or actual strategy compliance have not been completed.
- **SymPy demonstrations particularly improved end-to-end success for
  Qwen3-1.7B:** K6 scored 0%, K7 49.9%, and K8 52.2%. These remain below the
  same model's zero-shot CoT score. The observed gains combine API teaching,
  output formatting, and general few-shot benefits.
- **The Gemma teacher example did not have a uniform effect.** K9 and standard
  one-shot CoT use the same example question and example count; explanation
  content/source changes. Improvements were observed for LFM2-700M and
  Qwen3-0.6B, and a decline for Qwen3-1.7B. Although LFM2-1.2B's highest observed
  score was K9 at 66.7%, this is insufficient statistical evidence of superiority
  over standard one-shot CoT.

### K9 − standard one-shot CoT: paired comparison

Differences below are in **percentage points**. The same 1,000 questions are
paired within each model. The 95% intervals use 10,000 question-level bootstrap
resamples. P-values use two-sided exact McNemar tests and Holm correction across
five models. These comparisons are exploratory.

| Model | K9 − K2_1shot | 95% bootstrap interval | Holm p |
|---|---:|---:|---:|
| lfm2-350m | -1.1 | [-4.3, +2.0] | 0.539 |
| lfm2-700m | +17.2 | [+13.9, +20.5] | 1.42e-22 |
| lfm2-1.2b | +2.8 | [-0.2, +5.8] | 0.167 |
| qwen3-0.6b | +4.9 | [+2.3, +7.5] | 0.001 |
| qwen3-1.7b | -20.4 | [-23.4, -17.4] | 3.57e-36 |

### Error distribution and time

These counts describe 80,000 condition/model outputs, not 80,000 independent
mathematics questions. Error labels are execution/parser outcomes, not
human-verified semantic causes.

| Outcome | Count |
|---|---:|
| Correct | 14,137 |
| Parsed, incorrect answer | 15,442 |
| Formatting/parsing error | 28,158 |
| Syntax error | 19,738 |
| Runtime/API error | 1,431 |
| Time/resource limit | 398 |
| Generation truncation | 695 |
| Infrastructure error | 1 |

On an Apple M3 Max / 36 GiB system, generation took **10.99 hours** and isolated
execution/evaluation **1.54 hours**, for a total measured time of **12.53 hours**.
Model loading took **14.2 minutes** and is included in generation time; it must
not be added again. The same speed is not guaranteed on other hardware or loads.

Input/output tokens: **22,472,679 / 7,629,427**. Prompt caching was permitted:
**6,607,335 cached tokens**, with no missing counter measurements. The model was
already resident before **79,995 requests**; five requests started cold.

### Limitations and downloadable files

Conditions are repeated measurements of the same questions and must not be
pooled as independent observations. Architecture, training, and parameter count
vary together across models. A universal capability threshold cannot be inferred
from a few model sizes. Until question-type annotations and human error reviews
are complete, no process/equation subgroup or semantic error-cause claims are
made. K9 uses one fixed teacher example; robustness across other example pairs
has not been measured. GSM8K overlap with model training data cannot be ruled out.

- [Self-contained detailed report in English](reports/db66d8df297c69c75c54/REPORT.en.md)
- [Figure — PNG](reports/db66d8df297c69c75c54/accuracy.png) · [SVG](reports/db66d8df297c69c75c54/accuracy.svg)
- [Machine-readable results](reports/db66d8df297c69c75c54/summary.json) · [Cell-level results and costs](reports/db66d8df297c69c75c54/summary.csv)
- [Run audit](reports/db66d8df297c69c75c54/audit.json)
- [Reports, figure, results, and question manifest — ZIP](reports/db66d8df297c69c75c54/GSM8K_REPORT_PACKAGE.zip)

## Installation and checks

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/python -m gsm8k_lab check
.venv/bin/python scripts/k9.py verify
.venv/bin/python -m pytest -q
# Real Docker isolation tests:
GSM8K_DOCKER_TESTS=1 .venv/bin/python -m pytest -q tests/test_sandbox.py
```

Ollama should listen on loopback; do not expose it to the external network.
Python/SymPy require Docker Desktop and the
`gsm8k-sandbox:py3.12.8-sympy1.13.3` image. If the image is absent:
`docker build -t gsm8k-sandbox:py3.12.8-sympy1.13.3 sandbox`.
Prepare models with `.venv/bin/python -m gsm8k_lab prepare-models`.
To download data again, first install `requirements-data.txt`, then run
`.venv/bin/python scripts/prepare_hf_data.py` followed by
`.venv/bin/python -m gsm8k_lab prepare-data`. Data is already prepared locally.

## Quick validation on 10 questions

These commands run the fixed 10-question validation across 16 conditions. The
results above come from the separate 1,000-question run.

```bash
# 5 models × 16 conditions × 10 fixed pilot questions = 800 generations
.venv/bin/python scripts/repeat10.py run
.venv/bin/python scripts/repeat10.py resume RUN_ID
.venv/bin/python scripts/repeat10.py analyze RUN_ID
# Update the annotated report/figure without calling a model:
.venv/bin/python scripts/explain_report.py RUN_ID
```

[repeat10.json](configs/repeat10.json) writes to `results/repeat10-warm.sqlite`.
Run IDs derive from source/config/prompt/model identities. Calling the same run
again skips or resumes records. Changed sources require a new identity.
[Repeat protocol](docs/REPEAT10_PROTOCOL.en.md).

## Combined 1,000-question sample

A sample of 1,000 questions is selected with seed 20261021 from train+test after
excluding the active demonstrations: 858 train and 142 test questions. The
manifest is `data/sample1000-manifest.json`. There are 80,000 generations with
`keep_alive=30m` and caching permitted. The 18 questions overlapping the earlier
pilot are flagged; this sample is not an independent held-out test.
Results are written to `results/sample1000-warm.sqlite`.
[Protocol](docs/SAMPLE1000_PROTOCOL.en.md).

```bash
.venv/bin/python scripts/sample_run.py run
.venv/bin/python scripts/sample_run.py status
.venv/bin/python scripts/sample_run.py resume RUN_ID
.venv/bin/python scripts/sample_run.py analyze RUN_ID
```

The run has completed; the annotated report, figure, and ZIP are linked above.
These files are generated automatically after a new run or reanalysis. The
long-run launcher uses `caffeinate` to prevent idle sleep during execution.
Progress is recorded in `artifacts/sample1000.log` and
`artifacts/repeat1000-latest.json`.

## Pilot and main-test scope

The base CLI supports **15 conditions, excluding K9**. `scripts/repeat10.py`
runs 16 conditions, including K9, on 10 questions. A unified runner extending
K9 to the 200-question pilot or full official test is not implemented; that
scope is not claimed to be ready. The separate 1,000-question sample runner is
shown above.

```bash
.venv/bin/python -m gsm8k_lab smoke --models lfm2-350m
.venv/bin/python -m gsm8k_lab pilot
.venv/bin/python -m gsm8k_lab resume RUN_ID
.venv/bin/python -m gsm8k_lab analyze RUN_ID
.venv/bin/python -m gsm8k_lab review RUN_ID
.venv/bin/python -m gsm8k_lab estimate --pilot-run RUN_ID
.venv/bin/python -m gsm8k_lab freeze RUN_ID
# Only after a new pilot/protocol is frozen and the user requests it:
.venv/bin/python -m gsm8k_lab main
```

The base pilot requires 15,000 generations; the full base test requires 98,925.
The base CLI uses `results/base-warm.sqlite`. The obsolete protocol freeze was
removed; `freeze` is required before a new main test. Separate B/C robustness
runs use `robustness --pair B` / `--pair C`; repeated questions are not counted
as independent observations.

## Data and evaluation

Official [openai/gsm8k main](https://huggingface.co/datasets/openai/gsm8k), revision
`740312add88f781978c0658806c59bc2815b9866`: 7,473 train and 1,319 test questions.
The 200-question train pilot uses seed 20261021; demonstrations are outside it.
Original English text is preserved. Gold answers enter only the evaluation layer.

Temperature=0, context=4096, output=512, Qwen think=false; all settings are logged.
[Cache policy](docs/CACHE_POLICY.en.md): `keep_alive="30m"`; models stay resident
between requests, prompt caching is permitted, and counters are recorded.
Python/SymPy run only in network-disabled, resource-limited Docker containers
without host file mounts. There is no host execution fallback. Arithmetic uses
an AST allowlist. CoT requires a final `FINAL: <number>` line; code stdout must
contain exactly one `FINAL: <number>` line; the expression condition requires
one expression as the entire output. Formatting failures count against accuracy.
The metric is end-to-end success, not mathematical ability alone.

[Experiment protocol](docs/PROTOCOL.md), [annotation guide](docs/ANNOTATION.md),
[K9 examples](docs/K9_PROTOCOL.en.md), [model sources](docs/MODELS_AND_SOURCES.md).

## Sharing result files

GitHub displays the README figure through a relative path. Include the report,
PNG/SVG, summary.json/CSV, audit.json, and ZIP in
`reports/db66d8df297c69c75c54/` in the repository. Raw outputs are stored locally
in `results/sample1000-warm.sqlite`; large SQLite files and model weights are
excluded by `.gitignore`. The sharing package contains summary results, methods,
and the question manifest, not all raw model outputs. For full raw-record
inspection, share the SQLite database separately through a data repository or
release.
