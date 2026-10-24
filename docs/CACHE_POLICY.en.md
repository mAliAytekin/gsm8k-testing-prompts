# Model residency and prompt cache policy

[English](CACHE_POLICY.en.md) · [Türkçe](CACHE_POLICY.md)

The current setting is `keep_alive: "30m"`. The project client does not unload
models before or after generation. The runner works in model blocks, processing
a model's questions consecutively. Initial model loads and model changes still
incur costs. Ollama may evict models under memory pressure; a residency setting
does not absolutely prevent reloading. Actual warm/cold state is recorded through
`/api/ps`.

Prompt/KV caching is permitted. When present, `prompt_eval_cached_count` is
stored unchanged; a positive value is not an error. An absent counter is not
assumed to be zero and is reported as a missing measurement in the audit. This
is not returning a completed answer from a file: each question triggers a new
generation request. Previous conversation history is not appended. Qwen
think=false and all other generation settings are preserved. An unsuccessful
model response is not regenerated because it used cache.

The request's keep_alive setting overrides the server-wide default. The earlier
macOS session setting OLLAMA_KEEP_ALIVE=0 therefore does not affect these project
requests; changing global server settings or restarting Ollama is unnecessary.

New runs use separate identities and databases: repeat10-warm.sqlite and
base-warm.sqlite. Earlier cache-disabled measurements are not relabeled as warm
measurements. No zero effect of caching on accuracy is assumed; accuracy, tokens,
and timing are measured in actual runs. Cache reuse and residency are part of
the timing comparison. Client wall time includes loading; load_seconds must not
be added again.

Real technical check: artifacts/warm-model-validation.json. Across two
repetitions of a small diagnostic request, the second request found the model
resident and used cache. These two requests are not research accuracy results
or a speed estimate for the full experiment.
