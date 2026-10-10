PYTHON ?= python
DAYS ?= 365

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make setup"
	@echo "  make generate DAYS=10"
	@echo "  make run DAYS=5"
	@echo "  make benchmark DAYS=30"
	@echo "  make chaos"
	@echo "  make backfill"
	@echo "  make test"
	@echo "  make clean"

.PHONY: setup
setup:
	$(PYTHON) -m pip install -r requirements.txt

.PHONY: generate
generate:
	$(PYTHON) generate_data.py --days $(DAYS)

.PHONY: run
run:
	$(PYTHON) orchestrator.py run --days $(DAYS)

.PHONY: benchmark
benchmark:
	$(PYTHON) orchestrator.py benchmark --days $(DAYS)

.PHONY: chaos
chaos:
	$(PYTHON) orchestrator.py chaos

.PHONY: backfill
backfill:
	$(PYTHON) backfill.py

.PHONY: test
test:
	$(PYTHON) -m pytest -q

.PHONY: clean
clean:
	$(PYTHON) orchestrator.py clean