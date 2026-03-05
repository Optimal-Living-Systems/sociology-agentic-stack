#!/usr/bin/env python3
"""Archive session artifacts with metadata for reproducibility."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import configure_logging, ensure_dir, load_environment

LOGGER = logging.getLogger("archive_session")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for archive workflow."""
    parser = argparse.ArgumentParser(
        description="Archive artifacts into a timestamped directory and tarball."
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory containing generated artifacts to archive.",
    )
    parser.add_argument(
        "--archive-dir",
        default="data/archives",
        help="Destination directory for archived sessions.",
    )
    parser.add_argument(
        "--session-id",
        default="",
        help="Optional session ID for archive naming. Defaults to UTC timestamp.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> int:
    """Archive all eligible files and return 0/1 exit code."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        artifacts_dir = (repo_root / args.artifacts_dir).resolve()
        archive_root = (repo_root / args.archive_dir).resolve()

        if not artifacts_dir.exists():
            raise FileNotFoundError(f"Artifacts directory does not exist: {artifacts_dir}")

        ensure_dir(archive_root)
        session_id = args.session_id or datetime.now(timezone.utc).strftime("session-%Y%m%dT%H%M%SZ")
        session_archive_dir = archive_root / session_id
        ensure_dir(session_archive_dir)

        copied_files = []
        for path in sorted(artifacts_dir.glob("*")):
            if path.is_file() and path.name != ".gitkeep":
                target = session_archive_dir / path.name
                shutil.copy2(path, target)
                copied_files.append(path.name)

        manifest = {
            "session_id": session_id,
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(copied_files),
            "artifacts": copied_files,
            "source_dir": str(artifacts_dir),
        }
        (session_archive_dir / "archive_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        # Create compressed tar.gz for easy transfer/backups.
        tarball_base = archive_root / session_id
        shutil.make_archive(str(tarball_base), "gztar", root_dir=session_archive_dir)

        LOGGER.info("Archive created: %s", session_archive_dir)
        LOGGER.info("Tarball created: %s.tar.gz", tarball_base)
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Archive failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
