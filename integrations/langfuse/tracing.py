#!/usr/bin/env python3
"""Langfuse tracing adapter for the OLS sociology stack.

This module wraps the Langfuse Python SDK (v3) in a minimal interface so
workflows can emit one trace per run and one span per state with required
metadata keys.
"""

from __future__ import annotations

import contextlib
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Optional

from langfuse import Langfuse, propagate_attributes

LOGGER = logging.getLogger("ols.langfuse")


@dataclass
class TraceMetadata:
    """Trace-level metadata required by the OLS workflow spec."""

    run_id: str
    agent_name: str
    policy_name: str
    state_name: str
    corpus_id: str
    git_commit_sha: str

    def as_dict(self) -> Dict[str, str]:
        """Return metadata as a plain dict for Langfuse."""
        return {
            "run_id": self.run_id,
            "agent_name": self.agent_name,
            "policy_name": self.policy_name,
            "state_name": self.state_name,
            "corpus_id": self.corpus_id,
            "git_commit_sha": self.git_commit_sha,
        }


class _NullSpan:
    """No-op span used when tracing is disabled or misconfigured."""

    def __enter__(self) -> "_NullSpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def start_as_current_generation(self, *_, **__) -> "_NullSpan":
        return self

    def update(self, *_, **__) -> None:
        return None

    def update_trace(self, *_, **__) -> None:
        return None


class LangfuseTracer:
    """Thin wrapper around the Langfuse SDK for consistent OLS tracing."""

    def __init__(self, *, enabled: Optional[bool] = None) -> None:
        self._enabled = enabled if enabled is not None else self._env_enabled()
        self._client: Optional[Langfuse] = None
        if self._enabled:
            self._client = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                base_url=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
            )

    @staticmethod
    def _env_enabled() -> bool:
        """Enable tracing only when required env vars are present."""
        return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

    @staticmethod
    def resolve_git_sha() -> str:
        """Return short git SHA or "unknown" if not available."""
        try:
            return (
                subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
                .strip()
            )
        except Exception:  # pragma: no cover - used in CLI contexts
            return "unknown"

    @contextlib.contextmanager
    def start_trace(
        self,
        *,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Any]:
        """Create a root span and propagate trace-level attributes.

        Uses Langfuse's OpenTelemetry-based context to ensure child spans inherit
        the required attributes.
        """

        if not self._client:
            yield _NullSpan()
            return

        with self._client.start_as_current_span(name=name) as span:
            with propagate_attributes(
                user_id=user_id,
                session_id=session_id,
                tags=list(tags) if tags else None,
                metadata=metadata or {},
            ):
                yield span

    @contextlib.contextmanager
    def start_span(self, *, name: str, metadata: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
        """Start a child span under the current trace context."""
        if not self._client:
            yield _NullSpan()
            return

        with self._client.start_as_current_span(name=name, metadata=metadata) as span:
            yield span

    def flush(self) -> None:
        """Flush buffered traces to Langfuse."""
        if self._client:
            try:
                self._client.flush()
            except Exception as exc:  # pragma: no cover - best effort
                LOGGER.warning("Langfuse flush failed: %s", exc)


def build_metadata(
    *,
    run_id: str,
    agent_name: str,
    policy_name: str,
    state_name: str,
    corpus_id: str,
) -> Dict[str, str]:
    """Build required metadata dict for the OLS trace spec."""
    return TraceMetadata(
        run_id=run_id,
        agent_name=agent_name,
        policy_name=policy_name,
        state_name=state_name,
        corpus_id=corpus_id,
        git_commit_sha=LangfuseTracer.resolve_git_sha(),
    ).as_dict()
