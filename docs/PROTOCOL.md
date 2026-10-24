# GSM8K controlled representation experiment — current protocol

Research question: How does the benefit of external computation in small language models vary with representation, model size, and supplied solution/API demonstrations?

This is a controlled comparison and error analysis, not a new-method or priority claim. PAL, program execution, symbolic solving and chain-of-thought are existing approaches. Model training contamination cannot be ruled out.

## Research hypotheses

H1: Relative representation performance varies by model size.
H2: Arithmetic expressions may offer a better accuracy–cost tradeoff than Python in small models.
H3: Deterministic state updates may outperform unrestricted PAL on process questions.
H4: SymPy benefits depend on question type; API and representation errors limit net gains.
H5: One SymPy demonstration may reduce API/syntax errors and increase accuracy.
H6: The second demonstration's marginal benefit depends on model size and need not be positive.

Current condition selection follows earlier exploratory runs; it is not a fresh preregistration. The hypotheses are retained as research questions, with no new confirmatory results.

## Design

Five exact target models, all publisher GGUF Q8_0, with revision and file SHA256 pinned in configs/models.json. Locally created Ollama aliases are clearly identified. No LFM2.5, Qwen3.5, base model or different quantization substitution. Comparisons across families confound size, architecture and training; within-family size trends remain descriptive with only 2–3 sizes.

15 base conditions per model: K2 natural language CoT zero-shot; K3 expression zero-shot; K4 free Python/PAL zero-shot; K5 deterministic state updating zero-shot; K6 SymPy zero-shot; K7 same SymPy instruction plus one example; K8 same instruction plus two examples. K2–K5 each also have one-shot and two-shot controls. K4 may use any representation and available library; library use is recorded in code and can be reviewed. K5 strategy compliance is reviewed separately, never used to exclude incorrect or noncompliant outputs from the primary denominator.

The ten-question runner adds K9 with ONE fixed Gemma teacher example, bringing its total to 16. The base CLI has 15 conditions and does not include K9. See REPEAT10_PROTOCOL.md and K9_PROTOCOL.md.

Main pair A uses train indices 0 and 2, in that order. Pair B: 3 and 4; pair C: 7 and 8. Same question pair and order across all demonstration conditions, with arm-specific correct solutions. Zero-shot conditions are shared baselines: robustness runs execute only the 10 few-shot conditions for B/C, not duplicate baselines. Demonstration selection is fixed before pilot output inspection. Demonstrations are algorithmically and manually checked against official train answers. Adding examples simultaneously changes API familiarity, representation guidance, content and prompt length: these controls cannot fully causally isolate API teaching from general few-shot benefit.

Official Hugging Face openai/gsm8k main revision 740312add88f781978c0658806c59bc2815b9866; verified byte-equivalent canonical JSONL from the original repository. Exactly 200 of 7473 train items sampled with Python Random seed 20261021; demonstration items must be disjoint. Full 1319-item test held out. Smoke uses two pilot questions and is not pooled with pilot observations. No prompt/parser/config tuning on test outcomes. All question text remains original English. Gold is available to evaluation only; prompt builder accepts Question objects without answers. SHA256 manifests detect drift.

## Generation and execution

One sample per question/model/condition. temperature 0, seed 20261021, top_k 1, top_p 1, min_p 0, repeat_penalty 1, num_ctx 4096, num_predict 512. All options explicit in config; any model/template defaults are captured by /api/show. Qwen think=false. No self-consistency, repair, reranking, escalation, or retry after model failure. Ambiguous interrupted requests are infrastructure failures and are not silently regenerated. Read-only health checks can retry. Initial limits may be changed using pilot only; freeze command binds final config, code, prompts, demos and model digests before main evaluation. A revised condition must be revalidated under a new run identity.

The client preserves model residency with keep_alive="30m" and permits prompt/KV cache reuse; condition order is shuffled reproducibly within each question. Cold/warm refers to /api/ps immediately before generation, not a controlled cache experiment. Actual prompt/eval token counts, prompt/decode/load durations, client wall time and code/container wall times are separate. Cold loads, cache reuse, memory eviction and thermal effects limit timing generalization. Exact bitwise determinism is not promised on Metal or across backend versions. Quantization is controlled at Q8_0, but publisher conversion details and architectures may differ.

Arithmetic evaluator uses an AST allowlist and exact Fraction arithmetic. Allowed + - * / // % ** and unary +/-, parentheses and decimal literals; no names/calls/attributes. Max 1024 chars, 128 AST nodes, depth 32; abs(value)<=10^30, numerator and denominator <=256 bits; integer exponents -12..12. No eval/exec.

Python runs only in Docker Desktop's Linux VM, each job in a separate unprivileged container, no network, mounts, Docker socket or host secrets; root filesystem read-only; 16 MiB noexec temporary filesystem; all capabilities dropped and no-new-privileges; default seccomp remains enabled. 768 MiB container memory, 512 MiB child virtual memory, one CPU, 32 container PIDs, child CPU 3s/4s, 5s child wall limit, 15s whole container wall limit, 64 KiB file/output limits. Python 3.12.8, SymPy 1.13.3, mpmath 1.3.0, immutable image ID stored in each run. No host fallback. Container/VM security depends on maintained Docker and host OS; AST inspection alone is not a sandbox. Generation-only and deferred isolated execution are separate CLI operations.

## Outcomes

Primary outcome: exact normalized final scalar equality over every planned question. No broad numerical tolerance and no last-number heuristic. Currency prefix, valid thousands grouping, equivalent integer/decimal/fraction accepted. K2 exactly one last-line FINAL field; K3 whole expression; code exactly one stdout line FINAL: scalar. Optional single whole-response Python fence permitted. No unmarked prose stripping or code repair. Truncations count incorrect; transport/execution infrastructure and missing records are separate unavailable outcomes, not model errors. A conservative byte-based prompt bound rejects potential context overflow before submission; returned token counts and stop reason are also checked. Ollama does not expose a fully reliable original pre-truncation token count, so silent input truncation cannot be proven absent by API alone.

Report planned denominator, recorded/generated/evaluable counts, infrastructure/missing counts, completion status; unconditional correct/planned is explicitly a lower bound until complete. Also report correct/evaluable, parseability, executable fraction, accuracy among executable outputs (selected subset), errors, token totals and generation/load/execution timing. Format, syntax, runtime/API, resource, wrong answer, correct, truncation and infrastructure statuses remain distinct. Semantic modeling vs arithmetic errors require blinded human review unless established by direct evidence.

## Inference

The question is the sampling unit. Paired question bootstrap with 10000 resamples, seed 20261021; 95% percentile CIs for paired accuracy differences. Two-sided exact McNemar on discordant question outcomes. Never treat conditions, example pairs or reruns as independent questions.

Base CLI planned comparisons per model: K3−K4 (H2), K5−K4 (overall descriptive; process subgroup H3 only after annotations), K7−K6 (H5), K8−K7 (H6). One family of 20 tests, Holm adjusted across all five models and four contrasts. Incomplete pairs are not assigned primary inferential results. Within-family difference-in-differences for K3−K4 and K8−K7: largest minus smallest LFM2, and largest minus smallest Qwen3; joint question bootstrap CIs, separate Holm family of 4 two-sided paired permutation tests. These are interaction tests; separate significance at two sizes does not establish interaction. No universal capability threshold claims. Other condition pairs, costs and subgroup results are exploratory and identified as such. Robustness pairs reported separately or averaged within question with cluster bootstrap, never stacked as independent observations.

Question annotations are independent of model output; see ANNOTATION.md. No subgroup claims until labels are validated. Cost conclusions require both accuracy and measured tokens/time, without post-hoc composite weights. Pilot is for feasibility, failure analysis and freezing; it is not confirmatory evidence for these hypotheses. Main evaluation is explicit user action only.
