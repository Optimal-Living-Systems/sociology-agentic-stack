# OLS Agentic Sociology Research Stack

[![CI](https://img.shields.io/badge/CI-placeholder-lightgrey)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-internal-green)](docs/RUNBOOK.md)

The **Optimal Living Systems (OLS) Open Science Research Lab** is building an
agentic, taxonomy-first research workflow for sociology and related policy domains.

This repository provides the foundational scaffolding for:
- Agent orchestration and state machines (Sherpa)
- Model routing for API + local models (LiteLLM)
- Observability and prompt lifecycle (Langfuse)
- Vector retrieval (LanceDB)
- Review-only quality audits for research artifacts
- Reproducible workflows via Kestra and documented runbooks

## Quick Start

```bash
cd /home/joel/work/sociology-agentic-stack
cp .env.example .env
make setup
make validate-schemas
make smoke
```

## First Session

```bash
make session QUERY="What drives youth civic disengagement in post-industrial cities?" \
  SEEDS="civic_disengagement,social_capital,urban_inequality"
make review
```

## Project Layout

- `integrations/` wrappers and adapters for Sherpa, Langfuse, LiteLLM, retrieval, review
- `schemas/` ontology, artifact schemas, and prompt templates (runtime-loaded)
- `state_machines/` declarative workflow definitions
- `kestra/` orchestration flows for session and corpus ingest
- `scripts/` executable CLIs and setup/smoke tools
- `docs/` architecture, runbook, ADRs, acceptance tests, security, integration map
- `artifacts/` generated outputs (gitkept, runtime-written)

## Documentation Index

- [User Manual](docs/USER_MANUAL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Runbook](docs/RUNBOOK.md)
- [Acceptance Tests](docs/ACCEPTANCE_TESTS.md)
- [Decisions (ADRs)](docs/DECISIONS.md)
- [Security Baseline](docs/SECURITY.md)
- [Integration Map](docs/INTEGRATION_MAP.md)
- [Host Validation](docs/HOST_VALIDATION.md)

## Current Phase

This repo currently implements **Phase 0** scaffolding with runnable CLIs,
state machine drafts, schema pack v1, and end-to-end smoke infrastructure.
