#!/usr/bin/env python3
"""Sync local prompt templates to Langfuse prompt management.

Phase 0 behavior is safe-by-default: dry-run unless --apply is explicitly set.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

from _common import configure_logging, load_environment, require_file

LOGGER = logging.getLogger("sync_prompts")


def parse_args() -> argparse.Namespace:
    """Define CLI flags for prompt sync behavior."""
    parser = argparse.ArgumentParser(
        description="Sync schema template prompts to Langfuse prompt management."
    )
    parser.add_argument(
        "--schema-root",
        default="schemas",
        help="Schema root directory containing pack_manifest.yaml and templates/.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute actual sync. Without this flag, script performs dry-run only.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> int:
    """Load template metadata and either dry-run or attempt sync."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        schema_root = (repo_root / args.schema_root).resolve()
        manifest_path = schema_root / "pack_manifest.yaml"
        require_file(manifest_path, "schema pack manifest")

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        template_files = manifest["schema_pack"]["templates"]

        templates = []
        for rel_path in template_files:
            path = schema_root / rel_path
            require_file(path, f"template file ({rel_path})")
            templates.append(yaml.safe_load(path.read_text(encoding="utf-8")))

        LOGGER.info("Loaded %d templates from schema pack.", len(templates))

        if not args.apply:
            LOGGER.info("Dry-run mode: no changes were sent to Langfuse.")
            for tpl in templates:
                LOGGER.info("Would sync prompt: %s v%s", tpl["name"], tpl["version"])
            return 0

        required_env = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"]
        missing_env = [key for key in required_env if not os.getenv(key)]
        if missing_env:
            raise EnvironmentError(
                f"Cannot sync prompts, missing environment variables: {missing_env}"
            )

        # Integration placeholder for Phase A1+ implementation.
        # We log explicit intent and keep this action side-effect-light until
        # Langfuse project bootstrap is fully configured.
        for tpl in templates:
            LOGGER.info(
                "Apply sync queued for prompt '%s' version '%s' to %s",
                tpl["name"],
                tpl["version"],
                os.getenv("LANGFUSE_HOST"),
            )

        LOGGER.info("Prompt sync apply-mode completed (phase-0 no-op transport).")
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Prompt sync failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
