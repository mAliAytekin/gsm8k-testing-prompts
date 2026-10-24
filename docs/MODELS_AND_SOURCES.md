# Verified sources — 2026-10-21

All chosen files are in the original model publisher's repository. The metadata snapshots in `sources/` were retrieved from the Hugging Face model API with file blobs/size/SHA256. `configs/models.json` pins each repository commit and exact filename. Published model names and parameter labels are not silently equated with exact parameter counts; Ollama `/api/show` supplies actual GGUF metadata for each run.

- [LiquidAI/LFM2-350M model card](https://huggingface.co/LiquidAI/LFM2-350M), [official GGUF](https://huggingface.co/LiquidAI/LFM2-350M-GGUF).
- [LiquidAI/LFM2-700M model card](https://huggingface.co/LiquidAI/LFM2-700M), [official GGUF](https://huggingface.co/LiquidAI/LFM2-700M-GGUF).
- [LiquidAI/LFM2-1.2B model card](https://huggingface.co/LiquidAI/LFM2-1.2B), [official GGUF](https://huggingface.co/LiquidAI/LFM2-1.2B-GGUF).
- [Qwen/Qwen3-0.6B model card](https://huggingface.co/Qwen/Qwen3-0.6B), [official GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF).
- [Qwen/Qwen3-1.7B model card](https://huggingface.co/Qwen/Qwen3-1.7B), [official GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF).
- [Liquid's model format documentation](https://docs.liquid.ai/lfm/models/complete-library): GGUF formats including Q8_0 and Ollama compatibility.
- [Ollama Qwen3 tag list](https://ollama.com/library/qwen3/tags): `qwen3:0.6b-q8_0` and `qwen3:1.7b-q8_0` verified. These registry artifacts differ in size from the publisher GGUF artifacts; this experiment uses the pinned publisher artifacts for all models, not a mixture.
- [Ollama GGUF import](https://docs.ollama.com/import): local Modelfile `FROM` import. `gsm8k-*` labels in this project are newly created local aliases, not claimed official registry tags. Ollama imports GGUF templates; template snapshots are retained.
- [Ollama chat API](https://docs.ollama.com/api/chat): `think=false`, nonstream response, token counts and duration fields. Qwen's published template has thinking controls; actual generated thinking field is checked, unexpected thinking marks the record unavailable.
- [Official GSM8K source at pinned commit](https://github.com/openai/grade-school-math/tree/3101c7d5072418e28b9008a6636bde82a006892c): `grade_school_math/data/train.jsonl` and `test.jsonl`, main (not Socratic) format.

The LFM2 cards identify the LFM1.0 license; Qwen3 cards identify Apache-2.0. Retain and consult the respective publisher licenses for redistribution. Downloaded weights are local artifacts and are excluded from git. Dataset and model training contamination cannot be ruled out by this experiment.

This work makes no novelty or priority claim. Chain-of-thought, program-aided language models, executable arithmetic and symbolic solving are prior approaches; this repository provides a controlled evaluation implementation rather than claiming to invent them.

## Requested Hugging Face dataset source

[openai/gsm8k main](https://huggingface.co/datasets/openai/gsm8k/tree/740312add88f781978c0658806c59bc2815b9866/main) is pinned to revision `740312add88f781978c0658806c59bc2815b9866`. All 7473 train and 1319 test question/answer rows, in order, are identical to the initial canonical GitHub snapshot. Converting the HF Parquet rows with standard ASCII JSON serialization also gives exactly the same raw JSONL SHA256 hashes. See `data/huggingface-equivalence.json` and `data/huggingface-source-manifest.json`. Data provenance is preserved independently of run reports. Current commands use the same pinned dataset and split manifests.
