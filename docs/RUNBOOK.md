# Runbook

## 1) Prerequisites

- Ubuntu 24.04+ host
- Python 3.12+
- Docker + Docker Compose
- Git
- Optional: Ollama for local model path

## 2) Clone and Enter Repo

```bash
git clone https://github.com/Optimal-Living-Systems/sociology-agentic-stack.git
cd sociology-agentic-stack
```

## 3) Configure Environment

```bash
cp .env.example .env
# Edit .env with real API keys and Langfuse keys
```

## 4) Install Dependencies

```bash
make setup
```

## 5) Validate Schema Pack

```bash
make validate-schemas
```

## 6) Run End-to-End Smoke

```bash
make smoke
```

## 7) Run a Research Session

```bash
make session QUERY="How does housing precarity influence civic participation?" \
  SEEDS="housing_precarity,civic_disengagement,social_capital"
```

## 8) Run Review Audits

```bash
make review
```

## 9) Optional: Trigger Kestra Ingest Flow

```bash
make ingest
```

## 10) Kestra Setup (Included in Compose Stack)

```bash
make up
make kestra-init-auth
make kestra-install-deps
make kestra-health
make kestra-import
make kestra-run QUERY="How do neighborhood institutions affect youth civic participation?" \
  SEEDS="civic_disengagement,social_capital"
```

- Kestra UI/API: `http://localhost:8080`
- Default dev auth: `admin@kestra.io` / `Kestra123`

## 11) Langfuse + LiteLLM Integration

- [TODO][Phase B1] Start Langfuse stack and generate project keys.
- [TODO][Phase B1] Start LiteLLM proxy with production router config.
- [TODO][Phase B2] Route Sherpa calls through LiteLLM endpoint.

## 12) Troubleshooting

- If `pip install` fails due network: verify DNS and rerun setup.
- If Docker daemon is down: `sudo systemctl start docker`.
- If GPU NVML fails: reboot and validate NVIDIA driver/userspace alignment.
- If schema validation fails: run `python scripts/validate_schema_pack.py --log-level DEBUG`.

## 13) Reproducibility Notes

- Keep `.env` local and never commit secrets.
- Always run with versioned schema pack (`schemas/pack_manifest.yaml`).
- Archive every completed session for traceability.
