# =============================================================================
# OLS Agentic Sociology Research Stack — Makefile
# =============================================================================
# Usage:
#   make setup              Install dependencies and validate environment
#   make smoke              Run smoke test (validates all components)
#   make session QUERY="your research question" SEEDS="topic1,topic2"
#   make sherpa-run QUERY="your research question" SEEDS="topic1,topic2"
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
COMPOSE_FILE ?= compose.yaml
COMPOSE := ./scripts/docker_compose.sh
KESTRA_URL ?= http://localhost:8080
KESTRA_API_PREFIX ?= /api/v1/main
KESTRA_USERNAME ?= admin@kestra.io
KESTRA_PASSWORD ?= Kestra123
KESTRA_AUTH ?= $(KESTRA_USERNAME):$(KESTRA_PASSWORD)

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

# --- Infra Bring-up ---
.PHONY: up
up: ## Start local infra stack (Langfuse + LiteLLM)
	@echo "=== Starting infra stack via $(COMPOSE_FILE) ==="
	@$(COMPOSE) up -d --remove-orphans
	@echo "=== Infra stack is up ==="

.PHONY: down
down: ## Stop local infra stack
	@echo "=== Stopping infra stack ==="
	@$(COMPOSE) down
	@echo "=== Infra stack is down ==="

SERVICE ?=
.PHONY: logs
logs: ## Tail infra logs. Usage: make logs SERVICE=litellm
	@$(COMPOSE) logs -f --tail=100 $(SERVICE)

.PHONY: kestra-health
kestra-health: ## Check Kestra API reachability and auth
	@echo "=== Checking Kestra health at $(KESTRA_URL) ==="
	@curl -fsS "$(KESTRA_URL)/api/v1/configs" >/dev/null \
		&& echo "  ✓ Kestra configs endpoint reachable" \
		|| (echo "  ✗ Kestra configs endpoint unreachable"; exit 1)
	@curl -fsS -u "$(KESTRA_AUTH)" "$(KESTRA_URL)$(KESTRA_API_PREFIX)/flows/search" >/dev/null \
		&& echo "  ✓ Kestra reachable" \
		|| (echo "  ✗ Kestra not reachable"; exit 1)

.PHONY: kestra-init-auth
kestra-init-auth: ## Initialize Kestra basic auth account (one-time in fresh DB)
	@echo "=== Initializing Kestra basic auth (if needed) ==="
	@if curl -fsS "$(KESTRA_URL)/api/v1/configs" | grep -q '"isBasicAuthInitialized":true'; then \
		echo "  ✓ Basic auth already initialized"; \
	else \
		curl -fsS -X POST "$(KESTRA_URL)$(KESTRA_API_PREFIX)/basicAuth" \
			-H "Content-Type: application/json" \
			-d '{"uid":"ols-dev-bootstrap","username":"$(KESTRA_USERNAME)","password":"$(KESTRA_PASSWORD)"}' >/dev/null && \
		echo "  ✓ Basic auth initialized for $(KESTRA_USERNAME)"; \
	fi

.PHONY: kestra-import
kestra-import: ## Import Kestra flows from kestra/flows/*.yaml
	@echo "=== Importing Kestra flows ==="
	@curl -fsS -u "$(KESTRA_AUTH)" -X POST "$(KESTRA_URL)$(KESTRA_API_PREFIX)/flows/import" \
		-H "Content-Type: multipart/form-data" \
		-F "fileUpload=@kestra/flows/research_session.yaml" >/dev/null
	@curl -fsS -u "$(KESTRA_AUTH)" -X POST "$(KESTRA_URL)$(KESTRA_API_PREFIX)/flows/import" \
		-H "Content-Type: multipart/form-data" \
		-F "fileUpload=@kestra/flows/corpus_ingest.yaml" >/dev/null
	@echo "  ✓ Imported research_session + corpus_ingest"

.PHONY: kestra-run
kestra-run: ## Trigger Kestra research session flow using QUERY/SEEDS vars
	@echo "=== Triggering Kestra research session flow ==="
	@curl -fsS -u "$(KESTRA_AUTH)" -X POST "$(KESTRA_URL)$(KESTRA_API_PREFIX)/executions/ols.research/sociology-research-session" \
		-H "Content-Type: multipart/form-data" \
		-F "query=$(QUERY)" \
		-F "taxonomy_seeds=$(SEEDS)" \
		-F "model_config=$(MODEL_CONFIG)" \
		-F "corpus_id=$(CORPUS)" \
		-F "schema_pack_version=$(SCHEMA_VERSION)"
	@echo ""
	@echo "=== Kestra execution triggered ==="

.PHONY: kestra-logs
kestra-logs: ## Tail Kestra container logs
	@$(COMPOSE) logs -f --tail=200 kestra

.PHONY: kestra-install-deps
kestra-install-deps: ## Install Python deps inside Kestra container for flow scripts
	@echo "=== Installing Python dependencies inside Kestra container ==="
	@$(COMPOSE) exec -T kestra sh -lc "pip3 install -r /home/joel/work/sociology-agentic-stack/requirements.lock"
	@echo "  ✓ Kestra Python dependencies installed"

# --- Research Session ---
QUERY ?= Sociological drivers of civic disengagement in urban youth
SEEDS ?= civic_participation,urban_inequality
MODEL_CONFIG ?= default
CORPUS ?= sociology
SCHEMA_VERSION ?= 1.0.0
SOURCE_DIR ?= data/corpus

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

# --- Sherpa Workflow Runner ---
.PHONY: sherpa-run
sherpa-run: ## Run Sherpa workflow runner. Usage: make sherpa-run QUERY="your question" SEEDS="topic1,topic2"
	@echo "=== Starting Sherpa workflow run ==="
	@echo "  Query: $(QUERY)"
	@echo "  Seeds: $(SEEDS)"
	$(PYTHON) scripts/run_sherpa_workflow.py \
		--query "$(QUERY)" \
		--taxonomy-seeds "$(SEEDS)" \
		--use-sherpa
	@echo "=== Sherpa workflow complete ==="

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

.PHONY: sync-prompts-apply
sync-prompts-apply: ## Push prompt templates to Langfuse (apply mode)
	@echo "=== Syncing prompts to Langfuse (apply) ==="
	$(PYTHON) scripts/sync_prompts_to_langfuse.py --apply
	@echo "=== Prompt sync apply complete ==="

# --- Corpus Ingestion (via Kestra) ---
.PHONY: ingest
ingest: ## Trigger Kestra corpus ingestion flow
	@echo "=== Triggering Kestra corpus ingest ==="
	@curl -s -u "$(KESTRA_AUTH)" -X POST "$(KESTRA_URL)$(KESTRA_API_PREFIX)/executions/ols.research/corpus-ingest" \
		-H "Content-Type: multipart/form-data" \
		-F "source_dir=$(SOURCE_DIR)" \
		-F "corpus_id=$(CORPUS)" \
		|| echo "  ⚠ Kestra not reachable. Is it running? Check: docker ps"
	@echo "=== Ingest triggered ==="

# --- Cleanup ---
.PHONY: clean
clean: ## Remove generated artifacts (keeps reports)
	@echo "=== Cleaning artifacts ==="
	rm -f artifacts/*.md artifacts/*.jsonl
	@echo "=== Clean complete ==="

# --- Tests ---
.PHONY: test
test: ## Run Python test suite
	@echo "=== Running tests ==="
	@source $(VENV) && pytest -q
	@echo "=== Tests complete ==="

# --- Help ---
.PHONY: help
help: ## Show this help message
	@echo "OLS Agentic Sociology Research Stack"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36mmake %-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
