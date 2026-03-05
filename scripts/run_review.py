#!/usr/bin/env python3
"""Run review-only audits on generated research artifacts.

This script enforces read-only analysis of artifacts and writes findings reports
under docs/review_reports. It does not modify source artifacts.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

from _common import configure_logging, ensure_dir, load_environment, require_file

# Ensure repo root is on sys.path when executing scripts directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from integrations.langfuse.tracing import LangfuseTracer, build_metadata  # noqa: E402

LOGGER = logging.getLogger("run_review")


def parse_args() -> argparse.Namespace:
    """Build CLI arguments for review runner."""
    parser = argparse.ArgumentParser(
        description="Run citation/schema/duplication audits in review-only mode."
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory containing summary.md, claims.jsonl, glossary.jsonl.",
    )
    parser.add_argument(
        "--report-dir",
        default="docs/review_reports",
        help="Directory where markdown and JSON findings reports are written.",
    )
    parser.add_argument(
        "--schema-root",
        default="schemas",
        help="Root directory containing artifact schemas.",
    )
    parser.add_argument(
        "--mode",
        default="review-only",
        choices=["review-only"],
        help="Execution mode. Only review-only is allowed by policy.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional session run identifier for observability.",
    )
    parser.add_argument(
        "--agent-name",
        default="roborev",
        help="Logical agent name for observability metadata.",
    )
    parser.add_argument(
        "--policy-name",
        default="review_session",
        help="Policy/workflow name used for observability metadata.",
    )
    parser.add_argument(
        "--corpus-id",
        default="sociology",
        help="Corpus identifier for observability metadata.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def _read_jsonl(path: Path) -> list[dict]:
    """Read JSON Lines file into a list of dict objects."""
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as fp:
        for idx, line in enumerate(fp, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "id": f"line-{idx}",
                        "_parse_error": str(exc),
                        "_raw": line,
                    }
                )
    return records


def main() -> int:
    """Run audit checks and write reports with exit code semantics."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        artifacts_dir = (repo_root / args.artifacts_dir).resolve()
        report_dir = (repo_root / args.report_dir).resolve()
        schema_root = (repo_root / args.schema_root).resolve()

        require_file(artifacts_dir / "summary.md", "summary artifact")
        require_file(artifacts_dir / "claims.jsonl", "claims artifact")
        require_file(artifacts_dir / "glossary.jsonl", "glossary artifact")
        require_file(
            schema_root / "artifact_schemas/claim.jsonschema",
            "claim schema",
        )
        require_file(
            schema_root / "artifact_schemas/glossary_entry.jsonschema",
            "glossary schema",
        )

        ensure_dir(report_dir)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = args.run_id or f"review-{timestamp}"

        tracer = LangfuseTracer()
        trace_meta = build_metadata(
            run_id=run_id,
            agent_name=args.agent_name,
            policy_name=args.policy_name,
            state_name="LOAD_ARTIFACTS",
            corpus_id=args.corpus_id,
        )

        findings: list[dict] = []

        report_md = None
        report_jsonl = None

        with tracer.start_trace(
            name=args.policy_name,
            session_id=run_id,
            metadata=trace_meta,
        ):
            # LOAD_ARTIFACTS
            with tracer.start_span(
                name="LOAD_ARTIFACTS",
                metadata=build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name="LOAD_ARTIFACTS",
                    corpus_id=args.corpus_id,
                ),
            ):
                summary_text = (artifacts_dir / "summary.md").read_text(encoding="utf-8")
                claims = _read_jsonl(artifacts_dir / "claims.jsonl")
                glossary = _read_jsonl(artifacts_dir / "glossary.jsonl")
                claim_schema = json.loads(
                    (schema_root / "artifact_schemas/claim.jsonschema").read_text(encoding="utf-8")
                )
                glossary_schema = json.loads(
                    (schema_root / "artifact_schemas/glossary_entry.jsonschema").read_text(encoding="utf-8")
                )

            # CITATION_AUDIT
            with tracer.start_span(
                name="CITATION_AUDIT",
                metadata=build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name="CITATION_AUDIT",
                    corpus_id=args.corpus_id,
                ),
            ):
                if "[S" not in summary_text:
                    findings.append(
                        {
                            "id": "FIND-CIT-001",
                            "finding_type": "missing_citation",
                            "severity": "high",
                            "description": "Summary has no inline source citation markers.",
                            "affected_artifact": "artifacts/summary.md",
                        }
                    )

                for claim in claims:
                    claim_id = claim.get("id", "unknown")
                    refs = claim.get("evidence_refs", [])
                    if not isinstance(refs, list) or not refs:
                        findings.append(
                            {
                                "id": f"FIND-CIT-{claim_id}",
                                "finding_type": "unsupported_claim",
                                "severity": "high",
                                "description": "Claim lacks evidence_refs.",
                                "affected_artifact": "artifacts/claims.jsonl",
                                "affected_record_id": claim_id,
                            }
                        )

        # Schema audit using jsonschema when available.
        try:
            import jsonschema

            for claim in claims:
                if "_parse_error" in claim:
                    findings.append(
                        {
                            "id": f"FIND-SCH-ERR-{claim.get('id', 'unknown')}",
                            "finding_type": "schema_violation",
                            "severity": "high",
                            "description": f"JSON parse error in claims.jsonl: {claim['_parse_error']}",
                            "affected_artifact": "artifacts/claims.jsonl",
                            "affected_record_id": claim.get("id", "unknown"),
                        }
                    )
                    continue
                try:
                    jsonschema.validate(instance=claim, schema=claim_schema)
                except Exception as exc:  # pylint: disable=broad-except
                    findings.append(
                        {
                            "id": f"FIND-SCH-CLM-{claim.get('id', 'unknown')}",
                            "finding_type": "schema_violation",
                            "severity": "medium",
                            "description": f"Claim schema violation: {exc}",
                            "affected_artifact": "artifacts/claims.jsonl",
                            "affected_record_id": claim.get("id", "unknown"),
                        }
                    )

            for entry in glossary:
                term = entry.get("term", "unknown")
                if "_parse_error" in entry:
                    findings.append(
                        {
                            "id": f"FIND-SCH-GLS-{term}",
                            "finding_type": "schema_violation",
                            "severity": "high",
                            "description": f"JSON parse error in glossary.jsonl: {entry['_parse_error']}",
                            "affected_artifact": "artifacts/glossary.jsonl",
                            "affected_record_id": term,
                        }
                    )
                    continue
                try:
                    jsonschema.validate(instance=entry, schema=glossary_schema)
                except Exception as exc:  # pylint: disable=broad-except
                    findings.append(
                        {
                            "id": f"FIND-SCH-TERM-{term}",
                            "finding_type": "schema_violation",
                            "severity": "medium",
                            "description": f"Glossary schema violation: {exc}",
                            "affected_artifact": "artifacts/glossary.jsonl",
                            "affected_record_id": term,
                        }
                    )

        except ImportError:
            LOGGER.warning("jsonschema is not installed; schema validation checks skipped.")

            # SCHEMA_AUDIT
            with tracer.start_span(
                name="SCHEMA_AUDIT",
                metadata=build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name="SCHEMA_AUDIT",
                    corpus_id=args.corpus_id,
                ),
            ):
                # Schema audit logic is above (jsonschema validation).
                pass

            # DUPLICATION_AUDIT
            with tracer.start_span(
                name="DUPLICATION_AUDIT",
                metadata=build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name="DUPLICATION_AUDIT",
                    corpus_id=args.corpus_id,
                ),
            ):
                claim_texts = [
                    c.get("claim_text", "").strip().lower()
                    for c in claims
                    if isinstance(c, dict)
                ]
                duplicate_claims = [text for text, cnt in Counter(claim_texts).items() if text and cnt > 1]
                for text in duplicate_claims:
                    findings.append(
                        {
                            "id": f"FIND-DUP-CLM-{abs(hash(text)) % 10000}",
                            "finding_type": "duplicate_entry",
                            "severity": "medium",
                            "description": f"Duplicate claim_text detected: {text[:120]}",
                            "affected_artifact": "artifacts/claims.jsonl",
                        }
                    )

                term_counter = Counter([
                    g.get("term", "").strip().lower() for g in glossary if isinstance(g, dict)
                ])
                for term, cnt in term_counter.items():
                    if term and cnt > 1:
                        findings.append(
                            {
                                "id": f"FIND-DUP-TERM-{abs(hash(term)) % 10000}",
                                "finding_type": "duplicate_entry",
                                "severity": "medium",
                                "description": f"Duplicate glossary term detected: {term}",
                                "affected_artifact": "artifacts/glossary.jsonl",
                                "affected_record_id": term,
                            }
                        )

                definitions_by_term: dict[str, set[str]] = {}
                for entry in glossary:
                    term = entry.get("term", "").strip().lower()
                    definition = entry.get("definition", "").strip()
                    if not term:
                        continue
                    definitions_by_term.setdefault(term, set()).add(definition)
                for term, defs in definitions_by_term.items():
                    if len([d for d in defs if d]) > 1:
                        findings.append(
                            {
                                "id": f"FIND-INC-{abs(hash(term)) % 10000}",
                                "finding_type": "inconsistent_definition",
                                "severity": "low",
                                "description": f"Term '{term}' has inconsistent definitions.",
                                "affected_artifact": "artifacts/glossary.jsonl",
                                "affected_record_id": term,
                            }
                        )

            # WRITE_REPORT
            with tracer.start_span(
                name="WRITE_REPORT",
                metadata=build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name="WRITE_REPORT",
                    corpus_id=args.corpus_id,
                ),
            ):
                report_md = report_dir / f"review_report_{timestamp}.md"
                report_jsonl = report_dir / f"review_findings_{timestamp}.jsonl"

                summary_lines = [
                    "# Review Report",
                    "",
                    f"- Mode: {args.mode}",
                    f"- Timestamp (UTC): {timestamp}",
                    f"- Findings: {len(findings)}",
                    "",
                    "## Findings",
                ]
                if not findings:
                    summary_lines.append("- No issues detected.")
                else:
                    for item in findings:
                        summary_lines.append(
                            f"- [{item['severity'].upper()}] {item['finding_type']} | {item['affected_artifact']} | {item['description']}"
                        )

                report_md.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
                with report_jsonl.open("w", encoding="utf-8") as fp:
                    for item in findings:
                        fp.write(json.dumps(item, ensure_ascii=True) + "\n")

        tracer.flush()
        LOGGER.info("Review complete in review-only mode.")
        if report_md:
            LOGGER.info("Markdown report: %s", report_md)
        if report_jsonl:
            LOGGER.info("JSONL findings: %s", report_jsonl)
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Review run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
