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

# Ensure repo root is on sys.path when executing scripts directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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
        "--labels",
        default="production",
        help="Comma-separated Langfuse labels to apply (default: production).",
    )
    parser.add_argument(
        "--tags",
        default="ols,sociology",
        help="Comma-separated Langfuse tags for prompt grouping.",
    )
    parser.add_argument(
        "--commit-message",
        default="Sync from repo schema pack",
        help="Commit message recorded in Langfuse prompt history.",
    )
    parser.add_argument(
        "--prompt-type",
        choices=["chat", "text"],
        default="chat",
        help="Prompt type to create in Langfuse (chat recommended).",
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

        try:
            from langfuse import Langfuse
        except Exception as exc:  # pragma: no cover - runtime import guard
            raise RuntimeError("Langfuse SDK is not installed in this environment.") from exc

        labels = [label.strip() for label in args.labels.split(",") if label.strip()]
        if not labels:
            labels = ["production"]
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else None

        client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            base_url=os.getenv("LANGFUSE_HOST"),
        )

        for tpl in templates:
            prompt_name = tpl["name"]
            prompt_config = {
                "model": tpl.get("model_hint", ""),
                "template_version": tpl.get("version", ""),
                "schema_pack": manifest["schema_pack"]["name"],
            }
            if args.prompt_type == "chat":
                prompt_payload = [
                    {"role": "system", "content": tpl["system_prompt"]},
                    {"role": "user", "content": tpl["user_prompt_template"]},
                ]
            else:
                prompt_payload = f"{tpl['system_prompt']}\n\n{tpl['user_prompt_template']}"

            client.create_prompt(
                name=prompt_name,
                prompt=prompt_payload,
                labels=labels,
                tags=tags,
                type=args.prompt_type,
                config=prompt_config,
                commit_message=args.commit_message,
            )
            LOGGER.info(
                "Synced prompt '%s' version '%s' to %s",
                prompt_name,
                tpl.get("version", "unknown"),
                os.getenv("LANGFUSE_HOST"),
            )

        LOGGER.info("Prompt sync apply-mode completed.")
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Prompt sync failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
