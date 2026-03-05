# LiteLLM Proxy

This folder contains the LiteLLM proxy configuration for a single, OpenAI-compatible
routing endpoint. The proxy is the only model gateway used by Sherpa and review tools.

## Config File

- `config.yaml` defines model aliases and provider connections.
- All secrets are pulled from environment variables.

## Expected Environment Variables

- `LITELLM_MASTER_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `MISTRAL_API_KEY`
- `OLLAMA_BASE_URL`

## Start (CLI)

```bash
# Install proxy extras once in the venv
pip install "litellm[proxy]"

# Start proxy using this config
litellm --config integrations/litellm/config.yaml --detailed_debug
```

## Test

```bash
python - <<'PY'
from openai import OpenAI
client = OpenAI(api_key="test", base_url="http://localhost:4000/v1")
resp = client.chat.completions.create(
  model="synthesis",
  messages=[{"role": "user", "content": "Say hello"}]
)
print(resp.choices[0].message.content)
PY
```
