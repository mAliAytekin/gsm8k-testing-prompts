# K9 — one teacher demonstration

[English](K9_PROTOCOL.en.md) · [Türkçe](K9_PROTOCOL.md)

K9 uses the same common instruction, CoT output contract, and parser as K2.
The only difference is the fixed example explanation in the prompt. The exact
teacher name is gemma4:26b-mlx; it neither replaces the student during generation
nor judges its answers.

The existing demonstrations/k9/teacher.json bank contains four previously
generated explanations for train questions 0/2/3/4. The current runner selects
only the first one (train0). Remaining explanations are retained for provenance
integrity and are not added to the current student prompt. Bank generation
settings are in configs/k9.json.

`python scripts/k9.py verify` validates the questions, split separation, final
numerical answers, solution-review hash, and raw teacher responses. `prepare`
preserves an existing bank; it is a generation tool if the bank is absent. The
old four-example K9 student runner was removed. The current student experiment
uses scripts/repeat10.py.

Source responses are available under artifacts/k9-teacher. Step review was
performed by an agent; it is not presented as independent human verification.
Examples do not overlap the pilot/test questions. No advantage from a stronger
teacher is assumed; K9 is compared with K2_1shot using the same example question
and count. This comparison does not eliminate explanation-content differences.
