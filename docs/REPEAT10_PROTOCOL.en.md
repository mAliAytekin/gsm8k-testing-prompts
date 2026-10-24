# 10-question experiment — repeat10-warm-v5

[English](REPEAT10_PROTOCOL.en.md) · [Türkçe](REPEAT10_PROTOCOL.md)

K2–K8, one-/two-shot controls for K2–K5, and K9 with one teacher example:
16 conditions per model, five Q8_0 models, and 800 generations in total.
The first 10 IDs in the fixed 200-question pilot manifest are used. K9 uses
only the train0 explanation; other demonstration conditions use pair A.

Condition selection was updated after earlier exploratory observations. This
design is not presented as a new preregistration made before the first
evaluation. Each question receives one response, without automatic repair,
judging, or re-solving.

Configuration: configs/repeat10.json; output: results/repeat10-warm.sqlite.
Model digests and the data-manifest hash are verified against
configs/model-lock.json; no earlier run database is required. Code, prompts,
demonstrations, and configuration hashes are included in the identity.
Qwen think=false, temperature=0, context4096, output512. Models stay resident
between requests with keep_alive="30m". Prompt cache reuse is accepted; measured
and missing counters are recorded separately. Docker isolation is mandatory.

After execution, reports/RUN_ID/ contains a table, figure, audit, and time/token
summaries. The denominator is 10 per cell; missing coverage is shown explicitly.
K9−K2_1shot is compared exploratorily across five models using question-paired
bootstrap intervals, McNemar tests, and a five-test Holm family. Repeated
conditions for the same question are not independent observations. The K9
contrast changes both teacher source and explanation content.

Commands are in the README. No new run or full test was started during cleanup.
