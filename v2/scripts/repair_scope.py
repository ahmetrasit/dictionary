#!/usr/bin/env python3
"""Classify an assembly/finalization error into deterministic or writer-owned scope."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.validate_entry import ContractError, load_json
from v2.scripts.create_entry import atomic_write


DETERMINISTIC_MARKERS = (
    ".dictionary_basis",
    "$.provenance",
    ".artifact_path",
    ".artifact_sha256",
    "exact packet roster",
    "evidence index",
    "digest mismatch",
    "source roster mismatch",
    "semantic_review_editorial_review",
)


def classify(error: str, task: dict) -> dict:
    if any(marker in error for marker in DETERMINISTIC_MARKERS):
        return {
            "repairable_by": "deterministic_pipeline",
            "editable_branch_indexes": [],
            "root_editable": False,
        }
    count = len(task.get("branch_roster", []))
    indexes = sorted(
        {
            int(match)
            for match in re.findall(r"\$\.branches\[([0-9]+)\]", error)
            if int(match) < count
        }
    )
    root_editable = "$.root_profile" in error
    if not indexes and not root_editable:
        indexes = list(range(count))
        root_editable = True
    return {
        "repairable_by": "root_writer",
        "editable_branch_indexes": indexes,
        "root_editable": root_editable,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("--error-file", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        task = load_json(args.task.resolve())
        error = args.error_file.read_text(encoding="utf-8")
        result = classify(error, task)
    except (OSError, ContractError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc)) from exc
    content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        atomic_write(args.output.resolve(), content)
        print(f"Wrote {args.output.resolve()}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
