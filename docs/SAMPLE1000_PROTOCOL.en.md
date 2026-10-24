# Fixed 1,000-question exploratory experiment

[English](SAMPLE1000_PROTOCOL.en.md) · [Türkçe](SAMPLE1000_PROTOCOL.md)

“1,000 records” is interpreted as 1,000 distinct GSM8K questions. Five models and
16 conditions produce 80,000 student generations. K9 uses one example; there is
no judging, re-solving, or automatic repair. Other parameters match the
10-question run.

The pool combines the official main train+test splits (8,792 questions),
excluding active pair A demonstrations train0/train2, leaving 8,790 questions.
A sample of 1,000 is selected with seed20261021 without inspecting model outputs
or gold answers. IDs/hashes are fixed in data/sample1000-manifest.json. K9 uses
train0. All models and conditions use the same manifest. Overlap with the
previous pilot is flagged separately. Train/test source counts are recorded;
no independent held-out test claim is made. Earlier results for overlapping
questions are not reused.

Warm policy: keep_alive30m, model blocks, caching permitted; actual counters and
times are recorded. Q8_0, temperature0, Qwen think=false, context4096, output512.
A run is rejected if the data/model locks or sandbox do not match. Every example
must pass the conservative context preflight; questions are not discarded to
make the conditions fit.

A separate configuration, configs/sample1000.json, and database,
results/sample1000-warm.sqlite, are used. After interruption, resume with the
same sources/configuration preserves records; ambiguous inflight requests are
marked as infrastructure errors and are not regenerated. Completion is reported
explicitly. The initial estimate from the 10-question run was about 11 hours,
not a guarantee.

Commands:
```
.venv/bin/python scripts/sample_run.py prepare
.venv/bin/python scripts/sample_run.py run
.venv/bin/python scripts/sample_run.py status
.venv/bin/python scripts/sample_run.py resume RUN_ID
.venv/bin/python scripts/sample_run.py analyze RUN_ID
```
On completion, an annotated report, figure, and ZIP are generated automatically.
Repeated conditions for the same question are not independent observations. The
existing paired K9−K2_1shot comparison uses question-level bootstrap intervals,
McNemar tests, and a five-test Holm family, and remains exploratory.
