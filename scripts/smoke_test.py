#!/usr/bin/env python3
"""Run end-to-end smoke checks for Phase 0 scaffolding."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import configure_logging, ensure_dir, load_environment

LOGGER = logging.getLogger("smoke_test")


def parse_args() -> argparse.Namespace:
    """Parse smoke test CLI options."""
    parser = argparse.ArgumentParser(
        description="Run schema/session/review/archive smoke sequence."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def run_step(command: list[str], cwd: Path) -> tuple[int, str]:
    """Execute one subprocess step and return exit code plus combined output."""
    proc = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output


def main() -> int:
    """Run smoke pipeline and emit a markdown report."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        ensure_dir(repo_root / "artifacts")

        steps = [
            ["python", "scripts/validate_schema_pack.py"],
            [
                "python",
                "scripts/run_session.py",
                "--query",
                "Smoke test query",
                "--taxonomy-seeds",
                "civic_disengagement,social_capital",
            ],
            [
                "python",
                "scripts/run_review.py",
                "--artifacts-dir",
                "artifacts",
                "--report-dir",
                "docs/review_reports",
            ],
            [
                "python",
                "scripts/archive_session.py",
                "--artifacts-dir",
                "artifacts",
                "--archive-dir",
                "data/archives",
            ],
        ]

        report_lines = [
            "# Smoke Test Report",
            "",
            f"Timestamp (UTC): {datetime.now(timezone.utc).isoformat()}",
            "",
        ]

        for cmd in steps:
            LOGGER.info("Running step: %s", " ".join(cmd))
            code, output = run_step(cmd, repo_root)
            report_lines.append(f"## {' '.join(cmd)}")
            report_lines.append(f"Exit code: {code}")
            report_lines.append("```text")
            report_lines.append(output.strip() or "<no output>")
            report_lines.append("```")
            report_lines.append("")
            if code != 0:
                (repo_root / "artifacts/smoke_test_report.md").write_text(
                    "\n".join(report_lines), encoding="utf-8"
                )
                LOGGER.error("Smoke test failed at step: %s", " ".join(cmd))
                return 1

        (repo_root / "artifacts/smoke_test_report.md").write_text(
            "\n".join(report_lines), encoding="utf-8"
        )
        LOGGER.info("Smoke test passed. Report written to artifacts/smoke_test_report.md")
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Smoke test failed unexpectedly: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
