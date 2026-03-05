from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_sherpa_workflow as workflow  # noqa: E402


def load_schemas() -> dict:
    schema_root = REPO_ROOT / "schemas"
    manifest = workflow.load_schema_pack(schema_root)
    return workflow.load_artifact_schemas(schema_root, manifest)


def test_claims_validation_passes_for_valid_jsonl() -> None:
    schemas = load_schemas()
    claims_jsonl = (
        '{"id":"claim-1","claim_text":"Housing instability lowers civic trust.",'
        '"confidence":0.81,"evidence_refs":["S1"],"taxonomy_nodes":["urban_inequality"]}'
    )
    records = workflow.validate_jsonl_output(claims_jsonl, schemas["claim"], "claims")
    assert len(records) == 1
    assert records[0]["id"] == "claim-1"


def test_claims_validation_fails_when_required_key_missing() -> None:
    schemas = load_schemas()
    invalid_jsonl = (
        '{"id":"claim-1","claim_text":"Missing confidence field.",'
        '"evidence_refs":["S1"],"taxonomy_nodes":["urban_inequality"]}'
    )
    with pytest.raises(ValueError, match="failed schema validation"):
        workflow.validate_jsonl_output(invalid_jsonl, schemas["claim"], "claims")


def test_summary_metadata_validation_passes_for_generated_record() -> None:
    schemas = load_schemas()
    metadata = workflow.build_summary_metadata_record(
        run_id="run-123",
        query="How does housing precarity shape civic participation?",
        taxonomy_seeds=["housing_precarity", "civic_disengagement"],
        schema_pack_version="1.0.0",
        model_used="synthesis",
        sources_cited=3,
    )
    workflow.validate_records_against_schema(
        [metadata], schemas["summary_metadata"], "summary_metadata"
    )


def test_summary_metadata_validation_fails_without_timestamp() -> None:
    schemas = load_schemas()
    metadata = workflow.build_summary_metadata_record(
        run_id="run-456",
        query="What predicts youth civic disengagement?",
        taxonomy_seeds=["civic_disengagement"],
        schema_pack_version="1.0.0",
        model_used="synthesis",
        sources_cited=1,
    )
    metadata.pop("timestamp")
    with pytest.raises(ValueError, match="failed schema validation"):
        workflow.validate_records_against_schema(
            [metadata], schemas["summary_metadata"], "summary_metadata"
        )
