# =============================================================================
# OLS Agentic Sociology Research Stack — Makefile
# =============================================================================
# Usage:
#   make setup              Install dependencies and validate environment
#   make smoke              Run smoke test (validates all components)
#   make session QUERY="your research question" SEEDS="topic1,topic2"
#   make review             Run review agent on latest artifacts
#   make validate-schemas   Check schema pack for errors
#   make sync-prompts       Push templates to Langfuse
#   make dry-run QUERY="your question"   Estimate costs without calling APIs
#   make ingest             Trigger Kestra corpus ingestion flow
#   make clean              Remove generated artifacts
#   make help               Show this help
# =============================================================================

SHELL := /bin/bash
VENV := .venv/bin/activate
PYTHON := source $(VENV) && python

.DEFAULT_GOAL := help

# --- Setup ---
.PHONY: setup
setup: ## Install all dependencies and validate environment
	@echo "=== Setting up OLS Sociology Research Stack ==="
	@test -d .venv || python3 -m venv .venv
	@source $(VENV) && pip install --upgrade pip
	@source $(VENV) && pip install -r requirements.lock
	@source $(VENV) && python -c "import sherpa_ai; print('  ✓ sherpa-ai installed')"
	@source $(VENV) && python -c "import langfuse; print('  ✓ langfuse SDK installed')"
	@source $(VENV) && python -c "import instructor; print('  ✓ instructor installed')"
	@source $(VENV) && python -c "import lancedb; print('  ✓ lancedb installed')"
	@echo "=== Setup complete ==="

# --- Smoke Test ---
.PHONY: smoke
smoke: ## Run end-to-end smoke test
	@echo "=== Running smoke test ==="
	$(PYTHON) scripts/smoke_test.py
	@echo "=== Smoke test complete ==="

# --- Research Session ---
QUERY ?= Sociological drivers of civic disengagement in urban youth
SEEDS ?= civic_participation,urban_inequality
MODEL_CONFIG ?= default
CORPUS ?= sociology
SCHEMA_VERSION ?= 1.0.0

.PHONY: session
session: ## Run a research session. Usage: make session QUERY="your question" SEEDS="topic1,topic2"
	@echo "=== Starting research session ==="
	@echo "  Query: $(QUERY)"
	@echo "  Seeds: $(SEEDS)"
	$(PYTHON) scripts/run_session.py \
		--query "$(QUERY)" \
		--taxonomy-seeds "$(SEEDS)" \
		--model-config "$(MODEL_CONFIG)" \
		--corpus-id "$(CORPUS)" \
		--schema-pack-version "$(SCHEMA_VERSION)"
	@echo "=== Session complete. Artifacts in artifacts/ ==="

# --- Dry Run (cost estimation) ---
.PHONY: dry-run
dry-run: ## Estimate costs without calling APIs. Usage: make dry-run QUERY="your question"
	@echo "=== Dry run (no API calls) ==="
	$(PYTHON) scripts/run_session.py \
		--query "$(QUERY)" \
		--taxonomy-seeds "$(SEEDS)" \
		--dry-run
	@echo "=== Dry run complete ==="

# --- Review ---
.PHONY: review
review: ## Run review agent on latest artifacts
	@echo "=== Running review agent ==="
	$(PYTHON) scripts/run_review.py \
		--artifacts-dir artifacts/ \
		--report-dir docs/review_reports/
	@echo "=== Review complete. Reports in docs/review_reports/ ==="

# --- Schema Validation ---
.PHONY: validate-schemas
validate-schemas: ## Validate schema pack for errors
	@echo "=== Validating schema pack ==="
	$(PYTHON) scripts/validate_schema_pack.py
	@echo "=== Schema validation complete ==="

# --- Prompt Sync ---
.PHONY: sync-prompts
sync-prompts: ## Push prompt templates to Langfuse
	@echo "=== Syncing prompts to Langfuse ==="
	$(PYTHON) scripts/sync_prompts_to_langfuse.py
	@echo "=== Prompt sync complete ==="

# --- Corpus Ingestion (via Kestra) ---
.PHONY: ingest
ingest: ## Trigger Kestra corpus ingestion flow
	@echo "=== Triggering Kestra corpus ingest ==="
	@curl -s -X POST http://localhost:8080/api/v1/executions/ols.research/corpus-ingest \
		-H "Content-Type: application/json" \
		|| echo "  ⚠ Kestra not reachable. Is it running? Check: docker ps"
	@echo "=== Ingest triggered ==="

# --- Cleanup ---
.PHONY: clean
clean: ## Remove generated artifacts (keeps reports)
	@echo "=== Cleaning artifacts ==="
	rm -f artifacts/*.md artifacts/*.jsonl
	@echo "=== Clean complete ==="

# --- Help ---
.PHONY: help
help: ## Show this help message
	@echo "OLS Agentic Sociology Research Stack"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36mmake %-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
