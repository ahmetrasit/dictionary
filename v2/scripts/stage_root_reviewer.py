#!/usr/bin/env python3
"""Stage one semantic-review package in a regular review/input folder."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    authored_root_writer_response,
    canonical_sha256,
    json_content,
    sha256_file,
)
from v2.scripts.create_entry import (
    atomic_write,
    binding_path,
    path_ref,
    verify_task_bindings,
)
from v2.scripts.validate_entry import ContractError, load_json


PACKAGE_FILES = {
    "instructions.md",
    "task.json",
    "prompt.md",
    "response.schema.json",
    "evidence.json",
    "writer_response.json",
}


def stage(task_path: Path) -> dict:
    task = load_json(task_path)
    verify_task_bindings(task)
    input_dir = task_path.parent.parent / "review/input"
    input_dir.mkdir(parents=True, exist_ok=True)
    unexpected = {path.name for path in input_dir.iterdir()} - PACKAGE_FILES
    if unexpected:
        raise ContractError(
            f"Reviewer input folder contains unexpected files: {sorted(unexpected)}"
        )
    staged = copy.deepcopy(task)
    task_hash = canonical_sha256(task)
    previous_task_hash = None
    staged_task_path = input_dir / "task.json"
    if staged_task_path.is_file():
        previous = load_json(staged_task_path)
        if isinstance(previous, dict):
            previous_task_hash = previous.get("canonical_task_sha256")
    staged["canonical_task_sha256"] = task_hash
    staged["output"] = {"path": "../output/root_review.json"}
    staged["validation"] = {
        "command": [
            "python3",
            "v2/scripts/validate_agent_output.py",
            path_ref(input_dir / "task.json"),
        ]
    }
    output_dir = input_dir.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    if previous_task_hash != task_hash:
        for name in (
            "root_review.json",
            "semantic_review_error.txt",
            "repair_scope.json",
            "editorial_review.txt",
        ):
            path = output_dir / name
            if path.exists():
                path.unlink()
    destinations = {
        "prompt": input_dir / "prompt.md",
        "response_schema": input_dir / "response.schema.json",
        "evidence": input_dir / "evidence.json",
    }
    for key, destination in destinations.items():
        source = binding_path(staged[key]["path"])
        shutil.copyfile(source, destination)
        if sha256_file(destination) != staged[key]["sha256"]:
            raise ContractError(f"Copied reviewer input changed: {source}")
        staged[key]["path"] = destination.name
    writer_source = binding_path(staged["writer_response"]["path"])
    writer_value = load_json(writer_source)
    if not isinstance(writer_value, dict):
        raise ContractError(f"Writer response must be a JSON object: {writer_source}")
    writer_destination = input_dir / "writer_response.json"
    atomic_write(
        writer_destination,
        json_content(authored_root_writer_response(writer_value)),
    )
    staged["writer_response"] = {
        "path": writer_destination.name,
        "sha256": sha256_file(writer_destination),
    }
    atomic_write(
        input_dir / "task.json",
        json.dumps(staged, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write(
        input_dir / "instructions.md",
        "Read only the files named by task.json in this review/input folder. "
        "Do not inspect any other file or directory. Compare writer_response.json "
        "only with evidence.json under prompt.md. Write exactly one schema-valid "
        "JSON object directly to task output.path. Do not use `/tmp`, "
        "`/private/tmp`, another operating-system temporary directory, or a "
        "runtime scratch path, even as an intermediate copy. Modify nothing "
        "else. Then run the exact argv in task.json.validation.command from the "
        "repository root. If validation fails, keep the output file, correct it "
        "from the exact error, and rerun the same command. Return only after it "
        "passes.\n",
    )
    return staged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    args = parser.parse_args(argv)
    task = args.task.resolve()
    try:
        staged = stage(task)
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(
        f"Staged {task.parent.parent / 'review/input'} "
        f"({len(staged['branch_roster'])} branches)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
