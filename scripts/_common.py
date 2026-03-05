#!/usr/bin/env python3
"""Shared utilities for OLS sociology stack scripts.

This module centralizes environment loading, structured logging, and simple
filesystem helpers so each CLI entry point remains concise and consistent.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv


def configure_logging(level: str = "INFO") -> None:
    """Configure timestamped logging for all CLI scripts."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def load_environment(repo_root: Path | None = None) -> Path:
    """Load .env file if available and return normalized repo root path."""
    root = repo_root or Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Also load from process environment if .env is absent.
        load_dotenv(override=False)
    return root


def ensure_dir(path: Path) -> None:
    """Create directory path if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def require_file(path: Path, label: str) -> None:
    """Raise FileNotFoundError with a clear label if file is missing."""
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")


def env_flag(name: str, default: bool = False) -> bool:
    """Parse boolean-like environment variables safely."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
