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
    validate_repair_preservation,
    validate_semantic_contract,
)
from v2.scripts.assemble_entry import (
    canonical_sha256,
    root_entry_filename,
    sha256_file,
    validate_fragment,
)
from v2.scripts.create_entry import (
    SUPPLEMENTAL_GENERATOR,
    binding_path,
    verify_task_bindings,
)
from v2.scripts.validate_entry import ContractError, load_json


def _work_dir(task_path: Path, role: str) -> Path:
    if role in {"root_writer", "headword_writer"}:
        return task_path.parent.parent
    if role in {"root_reviewer", "headword_reviewer"}:
        return task_path.parent.parent.parent
    raise ContractError(f"Unsupported staged agent role: {role!r}")


def _expected_output(task_path: Path, role: str, task: dict) -> Path:
    work_dir = _work_dir(task_path, role)
    if role in {"root_writer", "headword_writer"}:
        return (work_dir / "output" / root_entry_filename(
            task["headwordId"] if role == "headword_writer" else task["root_envelope_id"]
        )).resolve()
    name = "headword_review.json" if role == "headword_reviewer" else "root_review.json"
    return (work_dir / "review/output" / name).resolve()


def _canonical_task(task_path: Path, role: str) -> Path:
    return (_work_dir(task_path, role) / "tasks" / f"{role}.json").resolve()


def _absolute_evidence_task(task: dict, task_path: Path) -> dict:
    adjusted = copy.deepcopy(task)
    adjusted["evidence"]["path"] = str(
        (task_path.parent / task["evidence"]["path"]).resolve()
    )
    return adjusted


def _validate_reviewer_writer_state(task_path: Path, role: str, staged: dict,
                                    canonical: dict, review: dict) -> None:
    """Check the bound pre-fix snapshot and any recorded live repair."""
    headword = role == "headword_reviewer"
    ident = staged["headwordId" if headword else "root_envelope_id"]
    writer_role = "headword_writer" if headword else "root_writer"
    collection = "senses" if headword else "branches"
    profile_key = "headword_profile" if headword else "root_profile"
    roster = canonical["sense_roster" if headword else "branch_roster"]
    live_path = (_work_dir(task_path, role) / "output" / root_entry_filename(ident)).resolve()
    if binding_path(canonical["writer_response"]["path"]) != live_path:
        raise ContractError("Canonical reviewer task points to another writer output")
    snapshot_path = (task_path.parent / "writer_response.json").resolve()
    if (staged.get("writer_response", {}).get("path") != "writer_response.json"
            or sha256_file(snapshot_path) != staged["writer_response"].get("sha256")):
        raise ContractError("Staged reviewer snapshot differs from its immutable binding")
    original_hash = canonical["writer_response"]["sha256"]
    snapshot_hash = sha256_file(snapshot_path)
    live_hash = sha256_file(live_path)
    if snapshot_hash != original_hash and live_hash != original_hash:
        raise ContractError("Repaired writer lacks a snapshot bound to the original writer bytes")
    adjusted = _absolute_evidence_task(staged, task_path)
    read = load_json if headword else writer_response_body
    snapshot = read(snapshot_path)
    live = read(live_path)
    if canonical.get("generated_by") == SUPPLEMENTAL_GENERATOR and load_json(live_path) != live:
        raise ContractError("Supplemental live writer response contains coordinator-only fields")
    for path, response in ((snapshot_path, snapshot), (live_path, live)):
        validate_fragment(response, writer_role, path)
        validate_identity(response, adjusted)
        validate_semantic_contract(response, adjusted)
    if live_hash == original_hash:
        if live != snapshot:
            raise ContractError("Bound live writer response differs from reviewer snapshot")
        return
    if review["verdict"] != "repair":
        raise ContractError("Only a recorded repair may change the bound live writer response")
    editable_fields: dict[int, set[str]] = {}
    profile_editable = False
    for issue in review["issues"]:
        target = issue["target_ref"]
        field = issue["field"]
        if target == profile_key:
            profile_editable = True
            if snapshot[profile_key] == live[profile_key]:
                raise ContractError("Recorded profile repair was not applied")
            continue
        index = roster.index(target)
        editable_fields.setdefault(index, set()).add(field)
        if snapshot[collection][index][field] == live[collection][index][field]:
            raise ContractError(f"Recorded repair was not applied: {target} {field}")
    validate_repair_preservation(
        snapshot, live,
        editable_branch_indexes=set(editable_fields),
        editable_branch_fields=editable_fields,
        root_editable=profile_editable,
        collection=collection,
        profile_key=profile_key,
    )


def validate(task_path: Path) -> tuple[str, Path, dict]:
    task_path = task_path.resolve()
    task = load_json(task_path)
    if not isinstance(task, dict):
        raise ContractError("Staged agent task must be a JSON object")
    role = task.get("role")
    if role not in {"root_writer", "root_reviewer", "headword_writer", "headword_reviewer"}:
        raise ContractError(f"Unsupported staged agent role: {role!r}")
    verify_task_bindings(task, base_dir=task_path.parent)

    canonical_path = _canonical_task(task_path, role)
    canonical = load_json(canonical_path)
    if role in {"root_reviewer", "headword_reviewer"}:
        # The canonical task binds the live writer's original bytes. Reviewer B
        # may subsequently repair that file, so check its other inputs here and
        # compare the live response with the immutable snapshot below.
        canonical_inputs = copy.deepcopy(canonical)
        canonical_inputs.pop("writer_response", None)
        verify_task_bindings(canonical_inputs)
    else:
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
    if role in {"root_writer", "headword_writer"}:
        response = load_json(response_path) if role == "headword_writer" else writer_response_body(response_path)
        validate_fragment(response, role, response_path)
        validate_identity(response, adjusted)
        validate_semantic_contract(response, adjusted)
    else:
        response = review_response_body(response_path)
        validate_fragment(response, role, response_path)
        validate_review(response, adjusted)
        _validate_reviewer_writer_state(task_path, role, task, canonical, response)
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
    if role in {"root_writer", "headword_writer"}:
        detail = f"{len(response['senses'] if role == 'headword_writer' else response['branches'])} items"
    else:
        detail = response["verdict"]
    print(f"Valid {role} output at {response_path} ({detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
