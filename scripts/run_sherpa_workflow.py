#!/usr/bin/env python3
"""Run a Sherpa-backed workflow from a JSON state machine definition.

This is a scaffold runner: it loads the state machine JSON, iterates through
states in order, and emits Langfuse traces/spans. If --use-sherpa is enabled,
it initializes Sherpa components to verify SDK wiring without executing full
agentic reasoning yet.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

import yaml

from _common import configure_logging, load_environment, require_file

# Ensure repo root is on sys.path when executing scripts directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from integrations.langfuse.tracing import LangfuseTracer, build_metadata  # noqa: E402

LOGGER = logging.getLogger("run_sherpa_workflow")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for workflow runner."""
    parser = argparse.ArgumentParser(
        description="Run a Sherpa workflow from a JSON state machine definition."
    )
    parser.add_argument(
        "--state-machine",
        default="state_machines/sociology_session.json",
        help="Path to a state machine JSON file.",
    )
    parser.add_argument(
        "--query",
        default="",
        help="Optional user query for context/logging.",
    )
    parser.add_argument(
        "--taxonomy-seeds",
        default="",
        help="Comma-separated taxonomy seeds for context/logging.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run identifier. Defaults to timestamp-based ID.",
    )
    parser.add_argument(
        "--agent-name",
        default="sherpa",
        help="Logical agent name for observability metadata.",
    )
    parser.add_argument(
        "--policy-name",
        default="sherpa_workflow",
        help="Policy/workflow name used for observability metadata.",
    )
    parser.add_argument(
        "--corpus-id",
        default="sociology",
        help="Corpus identifier for observability metadata.",
    )
    parser.add_argument(
        "--schema-root",
        default="schemas",
        help="Schema pack root directory (contains pack_manifest.yaml).",
    )
    parser.add_argument(
        "--router-config",
        default="integrations/config/router.yaml",
        help="Router config used for LiteLLM base_url and model aliases.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory where synthesized artifacts are written.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute the workflow without calling models or writing artifacts.",
    )
    parser.add_argument(
        "--use-sherpa",
        action="store_true",
        help="Initialize Sherpa components (no external calls unless extended).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name used for SherpaChatOpenAI when --use-sherpa is set.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def load_state_machine(path: Path) -> dict:
    """Load and minimally validate a state machine definition."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "states" not in raw or "initial_state" not in raw:
        raise ValueError("State machine JSON missing required keys: states/initial_state")
    return raw


def load_schema_pack(schema_root: Path) -> dict:
    """Load schema pack manifest and return manifest dict."""
    manifest_path = schema_root / "pack_manifest.yaml"
    require_file(manifest_path, "schema pack manifest")
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def load_templates(schema_root: Path, manifest: dict) -> Dict[str, dict]:
    """Load all templates from the schema pack into a name->template map."""
    templates: Dict[str, dict] = {}
    for rel_path in manifest["schema_pack"]["templates"]:
        path = schema_root / rel_path
        require_file(path, f"template file ({rel_path})")
        tpl = yaml.safe_load(path.read_text(encoding="utf-8"))
        templates[tpl["name"]] = tpl
    return templates


def render_template(text: str, variables: Dict[str, str]) -> str:
    """Render a simple {{var}} template without external dependencies."""
    output = text
    for key, value in variables.items():
        output = output.replace(f"{{{{{key}}}}}", value)
    return output


def normalize_jsonl(output: str) -> str:
    """Normalize model output to JSONL if possible."""
    cleaned = output.strip()
    if not cleaned:
        return cleaned
    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            data = json.loads(cleaned)
            return "\n".join(json.dumps(item, ensure_ascii=True) for item in data)
        except Exception:
            return cleaned
    return cleaned


def load_router_config(path: Path) -> dict:
    """Load router configuration for LiteLLM settings."""
    require_file(path, "router config")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def resolve_state_sequence(state_machine: dict) -> List[str]:
    """Resolve an ordered state list from transitions.

    This follows the first available transition from each state, skipping retry
    paths if possible. It is a pragmatic linearization for MVP scaffolding.
    """
    states = {state["id"]: state for state in state_machine.get("states", [])}
    transitions = state_machine.get("transitions", [])
    end_states = set(state_machine.get("end_states", []))
    current = state_machine.get("initial_state")

    if current not in states:
        raise ValueError(f"Initial state '{current}' is not defined in states list.")

    sequence: List[str] = []
    visited = set()
    max_steps = max(len(states) * 2, 1)

    while current and len(sequence) < max_steps:
        sequence.append(current)
        if current in end_states:
            break
        visited.add(current)
        outgoing = [t for t in transitions if t.get("from") == current]
        if not outgoing:
            break
        # Prefer end-state transitions, then non-retry transitions.
        next_state = None
        for t in outgoing:
            if t.get("to") in end_states:
                next_state = t.get("to")
                break
        if next_state is None:
            for t in outgoing:
                cond = str(t.get("condition", ""))
                if "retry" not in cond:
                    next_state = t.get("to")
                    break
        if next_state is None:
            next_state = outgoing[0].get("to")
        if next_state in visited and next_state not in end_states:
            break
        current = next_state

    if not sequence:
        raise ValueError("Failed to resolve any state sequence from state machine JSON.")
    return sequence


def initialize_sherpa_components(model_name: str) -> Dict[str, object]:
    """Initialize Sherpa components to validate SDK wiring.

    This does not execute external calls. It ensures the Sherpa classes are
    importable and configured, preparing for later expansion.
    """
    from sherpa_ai.models import SherpaChatOpenAI
    from sherpa_ai.policies import ReactPolicy

    llm = SherpaChatOpenAI(model=model_name)
    policy = ReactPolicy(
        role_description="OLS sociology workflow agent",
        output_instruction="Produce structured outputs aligned with schema packs.",
    )
    return {"llm": llm, "policy": policy}


def main() -> int:
    """Run workflow and emit traces/spans."""
    args = parse_args()
    configure_logging(args.log_level)

    try:
        repo_root = load_environment()
        sm_path = (repo_root / args.state_machine).resolve()
        schema_root = (repo_root / args.schema_root).resolve()
        router_path = (repo_root / args.router_config).resolve()
        artifacts_dir = (repo_root / args.artifacts_dir).resolve()
        require_file(sm_path, "state machine")
        require_file(schema_root / "pack_manifest.yaml", "schema pack manifest")

        state_machine = load_state_machine(sm_path)
        state_sequence = resolve_state_sequence(state_machine)

        run_id = args.run_id or f"sherpa-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        seed_nodes = [s.strip() for s in args.taxonomy_seeds.split(",") if s.strip()]

        manifest = load_schema_pack(schema_root)
        templates = load_templates(schema_root, manifest)
        router_config = load_router_config(router_path)

        base_url = router_config["router"]["base_url"]
        api_key_env = router_config["router"]["api_key_env"]
        api_key = os.getenv(api_key_env)
        defaults = router_config["router"]["defaults"]

        summary_out = None
        claims_out = None
        glossary_out = None
        critique_out = None

        LOGGER.info("Loaded state machine: %s", state_machine.get("name", sm_path.name))
        LOGGER.info("State sequence: %s", " -> ".join(state_sequence))
        if args.query:
            LOGGER.info("Query: %s", args.query)
        if seed_nodes:
            LOGGER.info("Taxonomy seeds: %s", seed_nodes)

        llm = None
        if args.use_sherpa and not args.dry_run:
            if not api_key:
                raise EnvironmentError(
                    f"Missing required env var for LiteLLM key: {api_key_env}"
                )
            from sherpa_ai.models import SherpaChatOpenAI

            llm = SherpaChatOpenAI(
                model=defaults.get("synthesis_model", args.model),
                base_url=base_url,
                api_key=api_key,
            )
            LOGGER.info("Sherpa LLM initialized with base_url=%s", base_url)
        elif args.use_sherpa:
            LOGGER.info("Dry-run enabled: skipping Sherpa LLM initialization.")

        tracer = LangfuseTracer()
        trace_meta = build_metadata(
            run_id=run_id,
            agent_name=args.agent_name,
            policy_name=args.policy_name,
            state_name=state_sequence[0],
            corpus_id=args.corpus_id,
        )

        with tracer.start_trace(
            name=args.policy_name,
            session_id=run_id,
            metadata=trace_meta,
        ):
            for state in state_sequence:
                state_meta = build_metadata(
                    run_id=run_id,
                    agent_name=args.agent_name,
                    policy_name=args.policy_name,
                    state_name=state,
                    corpus_id=args.corpus_id,
                )
                with tracer.start_span(name=state, metadata=state_meta):
                    if state == "SYNTHESIZE":
                        if args.dry_run:
                            LOGGER.info("SYNTHESIZE dry-run: skipping model calls.")
                            summary_out = "# Summary (dry-run)"
                            claims_out = ""
                            glossary_out = ""
                            critique_out = "# Critique (dry-run)"
                            continue

                        if not llm:
                            raise RuntimeError("Sherpa LLM not initialized. Use --use-sherpa.")

                        variables = {
                            "query": args.query or "<no query>",
                            "taxonomy_seeds": ", ".join(seed_nodes) if seed_nodes else "<none>",
                            "ontology_context": "Loaded from schema pack",
                            "sources_block": "(sources will be injected in later phase)",
                            "summary_markdown": "(summary will be injected)",
                            "source_index": "(source index will be injected)",
                            "claims_jsonl": "(claims will be injected)",
                            "ontology_nodes": ", ".join(seed_nodes) if seed_nodes else "<none>",
                            "schema_bundle": "(schemas loaded in runtime)",
                        }

                        def call_template(name: str, model_alias: str) -> str:
                            tpl = templates[name]
                            system_prompt = tpl["system_prompt"]
                            user_prompt = render_template(tpl["user_prompt_template"], variables)
                            response = llm.invoke(
                                [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt},
                                ],
                                model=model_alias,
                            )
                            return response.content if hasattr(response, "content") else str(response)

                        summary_out = call_template(
                            "synthesize_summary",
                            defaults.get("synthesis_model", args.model),
                        )
                        variables["summary_markdown"] = summary_out
                        claims_out = call_template(
                            "synthesize_claims",
                            defaults.get("extraction_model", args.model),
                        )
                        variables["claims_jsonl"] = claims_out
                        glossary_out = call_template(
                            "synthesize_glossary",
                            defaults.get("extraction_model", args.model),
                        )
                        critique_out = "# Critique\n\nPlaceholder critique."

                        claims_out = normalize_jsonl(claims_out)
                        glossary_out = normalize_jsonl(glossary_out)

                        LOGGER.info("SYNTHESIZE complete via Sherpa LLM.")
                    elif state == "FINALIZE":
                        if args.dry_run:
                            LOGGER.info("FINALIZE dry-run: skipping artifact writes.")
                            continue
                        if summary_out is None or claims_out is None or glossary_out is None:
                            raise RuntimeError("SYNTHESIZE did not produce artifacts.")
                        artifacts_dir.mkdir(parents=True, exist_ok=True)
                        (artifacts_dir / "summary.md").write_text(summary_out)
                        (artifacts_dir / "claims.jsonl").write_text(claims_out)
                        (artifacts_dir / "glossary.jsonl").write_text(glossary_out)
                        (artifacts_dir / "critique.md").write_text(critique_out or "")
                        LOGGER.info("Artifacts written to %s", artifacts_dir)
                    else:
                        LOGGER.info("State %s executed (placeholder)", state)

        tracer.flush()
        LOGGER.info("Workflow run complete.")
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Sherpa workflow run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
