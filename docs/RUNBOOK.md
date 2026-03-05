# Runbook

## 0) Golden Path (End-to-End Quick Start)

Minimum steps for a fresh engineer to bring the stack up and run a real session:

```bash
# 1. Clone and enter
git clone https://github.com/Optimal-Living-Systems/sociology-agentic-stack.git
cd sociology-agentic-stack

# 2. Configure environment (use defaults for local dev)
cp .env.example .env

# 3. Install Python deps
make setup

# 4. Start infra stack
make up

# 5. Wait for Kestra to be ready
make kestra-wait

# 6. Initialize Kestra auth (one-time, safe to rerun)
make kestra-init-auth

# 7. Pull local model (one-time; ~2 GB download)
./scripts/docker_compose.sh exec -T ollama ollama pull llama3.2:latest

# 8. Import Kestra flows
make kestra-import

# 9. Run a CLI session (real model call)
make session QUERY="How does housing precarity influence civic participation?" \
  SEEDS="housing_precarity,civic_disengagement"

# 10. Run a Kestra session (real model call)
make kestra-run QUERY="How does housing precarity influence civic participation?" \
  SEEDS="housing_precarity,civic_disengagement"
```

Artifacts appear under `artifacts/`. Kestra execution status at `http://localhost:8080`.

---

## 1) Prerequisites

- Ubuntu 24.04+ host
- Python 3.12+
- Docker + Docker Compose
- Git

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
make up
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
make kestra-build
make kestra-health
make kestra-import
make kestra-run QUERY="How do neighborhood institutions affect youth civic participation?" \
  SEEDS="civic_disengagement,social_capital"
```

- Kestra UI/API: `http://localhost:8080`
- Default dev auth: `admin@kestra.io` / `Kestra123`

## 11) Langfuse + LiteLLM Integration

- LiteLLM endpoint: `http://localhost:4000/v1`
- Ollama endpoint (in-stack): `http://localhost:11434`
- Default local model aliases `synthesis` and `analysis` are routed to Ollama (`llama3.2:latest`).
- First-time model bootstrap:

```bash
./scripts/docker_compose.sh exec -T ollama ollama pull llama3.2:latest
```

## 12) Troubleshooting

**Docker permission denied** (`Got permission denied while trying to connect to the Docker daemon`):
```bash
# Check if you're in docker group
id | grep docker
# If not, add yourself and refresh session
sudo usermod -aG docker $USER
newgrp docker   # or log out/in
# The scripts/docker_compose.sh wrapper handles this automatically for make targets
```

**Model not found** (`litellm.BadRequestError: model not found` or empty response):
```bash
# Confirm model is pulled in Ollama container
./scripts/docker_compose.sh exec -T ollama ollama list
# Pull if missing
./scripts/docker_compose.sh exec -T ollama ollama pull llama3.2:latest
```

**Kestra not ready** (`✗ Kestra not reachable` or curl fails after `make up`):
```bash
# Wait for Kestra to finish starting (up to ~3 min on cold start)
make kestra-wait
# Check container logs if it fails
make kestra-logs
```

**Kestra basic auth not initialized** (`401 Unauthorized` on API calls):
```bash
make kestra-init-auth
```

**Pip install network failure**:
```bash
# Verify DNS and retry
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.lock
```

**Docker daemon is down**:
```bash
sudo systemctl start docker
```

**GPU NVML fails**: Reboot and verify NVIDIA driver/userspace alignment (`nvidia-smi`).

**Schema validation fails**:
```bash
python scripts/validate_schema_pack.py --log-level DEBUG
```

## 13) Reproducibility Notes

- Keep `.env` local and never commit secrets.
- Always run with versioned schema pack (`schemas/pack_manifest.yaml`).
- Archive every completed session for traceability.
