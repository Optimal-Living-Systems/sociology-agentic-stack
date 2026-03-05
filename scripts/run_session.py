#!/usr/bin/env python3
"""Run one sociology research session.

This CLI is intentionally deterministic in Phase 0. It validates runtime inputs,
loads schema pack metadata, and emits representative artifacts so downstream
review, archive, and orchestration flows can be exercised safely.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml

from _common import configure_logging, ensure_dir, load_environment, require_file

# Ensure repo root is on sys.path when executing scripts directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from integrations.langfuse.tracing import LangfuseTracer, build_metadata  # noqa: E402

LOGGER = logging.getLogger("run_session")


def parse_args() -> argparse.Namespace:
    """Build and parse command-line arguments for the session runner."""
    parser = argparse.ArgumentParser(
        description="Run the OLS sociology research session workflow."
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Research question to answer in this session.",
    )
    parser.add_argument(
        "--taxonomy-seeds",
        default="",
        help="Comma-separated ontology node IDs (e.g. civic_disengagement,social_capital).",
    )
    parser.add_argument(
        "--model-config",
        default="default",
        help="Model routing profile alias (from future router config).",
    )
    parser.add_argument(
        "--corpus-id",
        default="sociology",
        help="Corpus identifier used for retrieval context.",
    )
    parser.add_argument(
        "--schema-pack-version",
        default="1.0.0",
        help="Expected schema pack version; validated against manifest.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Output directory for generated artifacts.",
    )
    parser.add_argument(
        "--schema-root",
        default="schemas",
        help="Schema pack root directory.",
    )
    parser.add_argument(
        "--state-machine",
        default="state_machines/sociology_session.json",
        help="Path to workflow state machine JSON definition.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional externally-specified run identifier.",
    )
    parser.add_argument(
        "--agent-name",
        default="sherpa",
        help="Logical agent name for observability metadata.",
    )
    parser.add_argument(
        "--policy-name",
        default="sociology_session",
        help="Policy/workflow name used for observability metadata.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print planned actions without writing artifacts.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> int:
    """Entrypoint with explicit success/failure return codes."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        schema_root = (repo_root / args.schema_root).resolve()
        artifacts_dir = (repo_root / args.artifacts_dir).resolve()
        state_machine_path = (repo_root / args.state_machine).resolve()

        require_file(schema_root / "pack_manifest.yaml", "schema pack manifest")
        require_file(schema_root / "ontology.yaml", "ontology definition")
        require_file(state_machine_path, "sociology state machine")

        manifest = yaml.safe_load((schema_root / "pack_manifest.yaml").read_text())
        actual_version = manifest["schema_pack"]["version"]
        if args.schema_pack_version != actual_version:
            raise ValueError(
                f"Schema pack version mismatch: expected {args.schema_pack_version}, "
                f"found {actual_version}"
            )

        seed_nodes = [s.strip() for s in args.taxonomy_seeds.split(",") if s.strip()]
        run_id = args.run_id or f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        LOGGER.info("Session configuration loaded successfully.")
        LOGGER.info("run_id=%s query=%s", run_id, args.query)
        LOGGER.info("taxonomy_seeds=%s", seed_nodes if seed_nodes else "<none>")
        LOGGER.info("model_config=%s corpus_id=%s", args.model_config, args.corpus_id)

        tracer = LangfuseTracer()
        trace_meta = build_metadata(
            run_id=run_id,
            agent_name=args.agent_name,
            policy_name=args.policy_name,
            state_name="INTAKE",
            corpus_id=args.corpus_id,
        )

        summary = None
        claims = None
        glossary = None
        critique = None
        summary_metadata = None

        if args.dry_run:
            LOGGER.info("Dry-run enabled. No artifacts will be written.")

        with tracer.start_trace(
            name=args.policy_name,
            session_id=run_id,
            metadata=trace_meta,
        ):
            for state in [
                "INTAKE",
                "RETRIEVE_LOCAL",
                "RETRIEVE_WEB",
                "SYNTHESIZE",
                "CRITIQUE",
                "FINALIZE",
            ]:
                state_meta = build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name=state,
                    corpus_id=args.corpus_id,
                )
                with tracer.start_span(name=state, metadata=state_meta):
                    if state == "INTAKE":
                        LOGGER.info("INTAKE complete.")
                    elif state == "RETRIEVE_LOCAL":
                        LOGGER.info("RETRIEVE_LOCAL complete (placeholder).")
                    elif state == "RETRIEVE_WEB":
                        LOGGER.info("RETRIEVE_WEB complete (placeholder).")
                    elif state == "SYNTHESIZE":
                        summary = f"""# Sociology Research Summary

## Query
{args.query}

## Core Findings
- Civic disengagement is associated with lower institutional trust [S001].
- Urban inequality shapes participation through neighborhood effects [S002].

## Key Mechanisms
- Social capital mediates civic participation in local networks [S003].
- Housing precarity weakens sustained public engagement [S004].

## Equity and Justice Implications
- Structural racism and environmental injustice can compound disengagement risk [S005].

## Open Questions
- Which interventions most effectively rebuild trust in local institutions?
- How do intrinsic motivation and collective identity interact in youth organizing?
"""
                        claims = [
                            {
                                "id": "CLM-001",
                                "claim_text": "Lower institutional trust is associated with increased civic disengagement among urban youth.",
                                "confidence": 0.78,
                                "evidence_refs": ["S001", "S002"],
                                "taxonomy_nodes": ["civic_disengagement", "institutional_trust", "urban_inequality"],
                                "counterarguments": [
                                    "Some communities maintain participation via informal civic networks."
                                ],
                            },
                            {
                                "id": "CLM-002",
                                "claim_text": "Housing precarity reduces continuity in collective participation.",
                                "confidence": 0.74,
                                "evidence_refs": ["S004"],
                                "taxonomy_nodes": ["housing_precarity", "social_movements", "social_capital"],
                                "counterarguments": [
                                    "Short-term mobilization can still occur despite housing instability."
                                ],
                            },
                        ]
                        glossary = [
                            {
                                "term": "Institutional Trust",
                                "definition": "Perceived legitimacy and reliability of public institutions.",
                                "domain": "political_sociology",
                                "related_terms": ["Political Participation", "Civic Disengagement"],
                                "source_refs": ["S001", "S003"],
                            },
                            {
                                "term": "Environmental Justice",
                                "definition": "Fair distribution of environmental harms, benefits, and decision-making power.",
                                "domain": "environmental_sociology",
                                "related_terms": ["Urban Inequality", "Climate Vulnerability"],
                                "source_refs": ["S005"],
                            },
                        ]
                        critique = """# Critique Report (Session-Level)

- No high-severity schema issues detected in generated placeholder artifacts.
- Citation coverage appears sufficient for all generated claims.
- Full audit should be performed with `scripts/run_review.py`.
"""
                        summary_metadata = {
                            "run_id": run_id,
                            "query": args.query,
                            "taxonomy_seeds": seed_nodes,
                            "sources_cited": 5,
                            "schema_pack_version": args.schema_pack_version,
                            "model_used": args.model_config,
                            "timestamp": timestamp,
                        }
                    elif state == "CRITIQUE":
                        LOGGER.info("CRITIQUE complete (placeholder).")
                    elif state == "FINALIZE":
                        if args.dry_run:
                            LOGGER.info("Dry-run: skipping artifact writes.")
                            continue
                        if summary is None or claims is None or glossary is None or critique is None:
                            raise RuntimeError("SYNTHESIZE did not produce artifacts.")
                        ensure_dir(artifacts_dir)
                        (artifacts_dir / "summary.md").write_text(summary)
                        with (artifacts_dir / "claims.jsonl").open("w", encoding="utf-8") as fp:
                            for rec in claims:
                                fp.write(json.dumps(rec, ensure_ascii=True) + "\n")
                        with (artifacts_dir / "glossary.jsonl").open("w", encoding="utf-8") as fp:
                            for rec in glossary:
                                fp.write(json.dumps(rec, ensure_ascii=True) + "\n")
                        (artifacts_dir / "critique.md").write_text(critique)
                        (artifacts_dir / "summary.metadata.json").write_text(
                            json.dumps(summary_metadata, indent=2)
                        )
                        LOGGER.info("Artifacts written to %s", artifacts_dir)
                        LOGGER.info(
                            "Generated files: summary.md, claims.jsonl, glossary.jsonl, critique.md"
                        )

        tracer.flush()
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Session run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
