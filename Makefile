PY := .venv/bin/python
.PHONY: check test smoke pilot analyze estimate
check:
	$(PY) -m gsm8k_lab check
test:
	GSM8K_DOCKER_TESTS=1 $(PY) -m pytest -q
smoke:
	$(PY) -m gsm8k_lab smoke --models lfm2-350m
pilot:
	$(PY) -m gsm8k_lab pilot
analyze:
	$(PY) -m gsm8k_lab analyze $(RUN_ID)
estimate:
	$(PY) -m gsm8k_lab estimate --pilot-run $(RUN_ID)
