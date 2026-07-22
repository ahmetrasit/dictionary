#!/usr/bin/env python3
"""Check whether a stored root-writer fragment matches its canonical task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_writer import validate_identity, validate_semantic_contract
from v2.scripts.assemble_entry import load_task_fragment
from v2.scripts.validate_entry import ContractError


def check(task_path: Path, fragment_path: Path) -> dict:
    task, response = load_task_fragment(task_path, fragment_path, "root_writer")
    validate_identity(response, task)
    validate_semantic_contract(response, task)
    return response


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("fragment", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        response = check(args.task.resolve(), args.fragment.resolve())
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Reusable root-writer fragment ({len(response['branches'])} branches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
