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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

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
        require_file(sm_path, "state machine")

        state_machine = load_state_machine(sm_path)
        state_sequence = resolve_state_sequence(state_machine)

        run_id = args.run_id or f"sherpa-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        seed_nodes = [s.strip() for s in args.taxonomy_seeds.split(",") if s.strip()]

        LOGGER.info("Loaded state machine: %s", state_machine.get("name", sm_path.name))
        LOGGER.info("State sequence: %s", " -> ".join(state_sequence))
        if args.query:
            LOGGER.info("Query: %s", args.query)
        if seed_nodes:
            LOGGER.info("Taxonomy seeds: %s", seed_nodes)

        if args.use_sherpa:
            components = initialize_sherpa_components(args.model)
            LOGGER.info("Sherpa components initialized: %s", ", ".join(components.keys()))

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
                    LOGGER.info("State %s executed (placeholder)", state)

        tracer.flush()
        LOGGER.info("Workflow run complete.")
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Sherpa workflow run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
