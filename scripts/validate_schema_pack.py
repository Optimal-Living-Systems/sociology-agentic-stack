#!/usr/bin/env python3
"""Validate the sociology schema pack for syntax and structural integrity."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from _common import configure_logging, load_environment, require_file

LOGGER = logging.getLogger("validate_schema_pack")

REQUIRED_TEMPLATE_KEYS = {
    "name",
    "version",
    "description",
    "model_hint",
    "system_prompt",
    "user_prompt_template",
    "expected_output_format",
    "notes",
}


def parse_args() -> argparse.Namespace:
    """Build CLI parser for schema pack validation."""
    parser = argparse.ArgumentParser(
        description="Validate manifest, ontology, JSON schemas, and templates."
    )
    parser.add_argument(
        "--schema-root",
        default="schemas",
        help="Schema root directory containing pack_manifest.yaml.",
    )
    parser.add_argument(
        "--min-ontology-nodes",
        type=int,
        default=15,
        help="Minimum required ontology node count.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> int:
    """Run all validations and return exit status."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        schema_root = (repo_root / args.schema_root).resolve()
        manifest_path = schema_root / "pack_manifest.yaml"

        require_file(manifest_path, "schema pack manifest")
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

        if "schema_pack" not in manifest:
            raise ValueError("Manifest missing 'schema_pack' root key.")

        schema_pack = manifest["schema_pack"]
        required_manifest_keys = {
            "name",
            "version",
            "domain",
            "description",
            "compatible_workflow",
            "created",
            "ontology_file",
            "artifact_schemas",
            "templates",
        }
        missing_manifest = required_manifest_keys - set(schema_pack.keys())
        if missing_manifest:
            raise ValueError(f"Manifest missing keys: {sorted(missing_manifest)}")

        ontology_path = schema_root / schema_pack["ontology_file"]
        require_file(ontology_path, "ontology file")
        ontology = yaml.safe_load(ontology_path.read_text(encoding="utf-8"))
        nodes = ontology.get("ontology", {}).get("nodes", [])
        if len(nodes) < args.min_ontology_nodes:
            raise ValueError(
                f"Ontology has {len(nodes)} nodes; expected at least {args.min_ontology_nodes}."
            )

        for schema_rel in schema_pack["artifact_schemas"]:
            schema_path = schema_root / schema_rel
            require_file(schema_path, f"artifact schema ({schema_rel})")
            json.loads(schema_path.read_text(encoding="utf-8"))

        for template_rel in schema_pack["templates"]:
            template_path = schema_root / template_rel
            require_file(template_path, f"template file ({template_rel})")
            template_data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
            missing_keys = REQUIRED_TEMPLATE_KEYS - set(template_data.keys())
            if missing_keys:
                raise ValueError(
                    f"Template {template_rel} missing keys: {sorted(missing_keys)}"
                )

        LOGGER.info(
            "Schema pack validation passed: %s v%s",
            schema_pack["name"],
            schema_pack["version"],
        )
        LOGGER.info("Ontology node count: %s", len(nodes))
        LOGGER.info("Artifact schemas: %s", len(schema_pack["artifact_schemas"]))
        LOGGER.info("Templates: %s", len(schema_pack["templates"]))
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Schema pack validation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
