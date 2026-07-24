#!/usr/bin/env python3
"""Prepare a hash-bound semantic-review task for one accepted root response."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    canonical_sha256,
    load_task_fragment,
    structural_identity_refs,
)
from v2.scripts.accept_root_writer import validate_identity, validate_semantic_contract
from v2.scripts.create_entry import binding, common_task, write_task
from v2.scripts.validate_entry import ContractError, load_json


def prepare(writer_task_path: Path, writer_response_path: Path, output_path: Path) -> dict:
    writer_task, response = load_task_fragment(
        writer_task_path, writer_response_path, "root_writer"
    )
    validate_identity(response, writer_task)
    validate_semantic_contract(response, writer_task)
    structural_refs = structural_identity_refs(response)
    if structural_refs:
        raise ContractError(
            "structural_identity_review_required: park for branch-graph curation "
            f"before semantic review: {structural_refs}"
        )
    task = common_task(
        "root_reviewer",
        writer_task["root_envelope_id"],
        writer_task["language"],
    )
    task.update(
        {
            "branch_roster": writer_task["branch_roster"],
            "evidence": writer_task["evidence"],
            "writer_response": binding(writer_response_path),
            "writer_task_sha256": canonical_sha256(writer_task),
        }
    )
    if response.get("branches") is None:
        raise ContractError("Root reviewer requires a complete writer response")
    write_task(output_path, task)
    return task


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("writer_task", type=Path)
    parser.add_argument("writer_response", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    writer_task = args.writer_task.resolve()
    writer_response = args.writer_response.resolve()
    output = args.output or writer_task.parent / "root_reviewer.json"
    try:
        task = prepare(writer_task, writer_response, output.resolve())
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Prepared {output.resolve()} ({len(task['branch_roster'])} branches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
