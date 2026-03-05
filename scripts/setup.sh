#!/usr/bin/env bash
# =============================================================================
# OLS Agentic Sociology Research Stack — Setup Script
# =============================================================================
# This script bootstraps the local Python environment and verifies key imports.
# It is safe to re-run; existing virtualenvs are reused.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "=== OLS Stack Setup ==="

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing locked dependencies..."
pip install -r requirements.lock

echo "Validating critical imports..."
python -c "import sherpa_ai; print('  ✓ sherpa_ai')"
python -c "import langfuse; print('  ✓ langfuse')"
python -c "import instructor; print('  ✓ instructor')"
python -c "import lancedb; print('  ✓ lancedb')"
python -c "import pydantic; print('  ✓ pydantic')"
python -c "import jsonschema; print('  ✓ jsonschema')"
python -c "import yaml; print('  ✓ yaml')"
python -c "import dotenv; print('  ✓ dotenv')"
python -c "import httpx; print('  ✓ httpx')"
python -c "import tenacity; print('  ✓ tenacity')"

echo "=== Setup complete ==="
