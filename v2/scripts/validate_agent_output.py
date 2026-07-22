#!/usr/bin/env python3
"""Read-only validation of a staged writer or reviewer output in its real folder."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_review import (
    response_body as review_response_body,
    validate_review,
)
from v2.scripts.accept_root_writer import (
    response_body as writer_response_body,
    validate_identity,
    validate_semantic_contract,
)
from v2.scripts.assemble_entry import (
    canonical_sha256,
    root_entry_filename,
    validate_fragment,
)
from v2.scripts.create_entry import verify_task_bindings
from v2.scripts.validate_entry import ContractError, load_json


def _work_dir(task_path: Path, role: str) -> Path:
    if role == "root_writer":
        return task_path.parent.parent
    if role == "root_reviewer":
        return task_path.parent.parent.parent
    raise ContractError(f"Unsupported staged agent role: {role!r}")


def _expected_output(task_path: Path, role: str, task: dict) -> Path:
    work_dir = _work_dir(task_path, role)
    if role == "root_writer":
        return (work_dir / "output" / root_entry_filename(
            task["root_envelope_id"]
        )).resolve()
    return (work_dir / "review/output/root_review.json").resolve()


def _canonical_task(task_path: Path, role: str) -> Path:
    return (_work_dir(task_path, role) / "tasks" / f"{role}.json").resolve()


def _absolute_evidence_task(task: dict, task_path: Path) -> dict:
    adjusted = copy.deepcopy(task)
    adjusted["evidence"]["path"] = str(
        (task_path.parent / task["evidence"]["path"]).resolve()
    )
    return adjusted


def validate(task_path: Path) -> tuple[str, Path, dict]:
    task_path = task_path.resolve()
    task = load_json(task_path)
    if not isinstance(task, dict):
        raise ContractError("Staged agent task must be a JSON object")
    role = task.get("role")
    if role not in {"root_writer", "root_reviewer"}:
        raise ContractError(f"Unsupported staged agent role: {role!r}")
    verify_task_bindings(task, base_dir=task_path.parent)

    canonical_path = _canonical_task(task_path, role)
    canonical = load_json(canonical_path)
    verify_task_bindings(canonical)
    expected_task_hash = canonical_sha256(canonical)
    if task.get("canonical_task_sha256") != expected_task_hash:
        raise ContractError(
            "Staged agent task is stale; restage it before validating output"
        )

    declared = task.get("output", {}).get("path")
    if not isinstance(declared, str):
        raise ContractError("Staged agent task has no output.path")
    response_path = (task_path.parent / declared).resolve()
    expected_output = _expected_output(task_path, role, task)
    if response_path != expected_output:
        raise ContractError(
            f"Agent output must remain at {expected_output}, got {response_path}"
        )

    adjusted = _absolute_evidence_task(task, task_path)
    if role == "root_writer":
        response = writer_response_body(response_path)
        validate_fragment(response, role, response_path)
        validate_identity(response, adjusted)
        validate_semantic_contract(response, adjusted)
    else:
        response = review_response_body(response_path)
        validate_fragment(response, role, response_path)
        validate_review(response, adjusted)
    return role, response_path, response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    args = parser.parse_args(argv)
    try:
        role, response_path, response = validate(args.task)
    except (
        OSError,
        ContractError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        raise SystemExit(str(error)) from error
    if role == "root_writer":
        detail = f"{len(response['branches'])} branches"
    else:
        detail = response["verdict"]
    print(f"Valid {role} output at {response_path} ({detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
