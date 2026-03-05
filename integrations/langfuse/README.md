# Langfuse Tracing Adapter

This folder contains a minimal adapter that emits Langfuse traces and spans for
OLS workflows. The adapter enforces one trace per run and one span per state,
with required metadata keys.

## Files
- `tracing.py` — Langfuse wrapper with `start_trace`, `start_span`, and metadata helpers.

## Required Environment Variables
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST` (defaults to `http://localhost:3000`)

## Minimal Example

```python
from integrations.langfuse.tracing import LangfuseTracer, build_metadata

tracer = LangfuseTracer()
meta = build_metadata(
    run_id="run-123",
    agent_name="sherpa",
    policy_name="sociology_session",
    state_name="INTAKE",
    corpus_id="sociology",
)

with tracer.start_trace(
    name="sociology_session",
    session_id="session-123",
    metadata=meta,
):
    with tracer.start_span(name="INTAKE", metadata=meta):
        pass

tracer.flush()
```
