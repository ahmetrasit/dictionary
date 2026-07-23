#!/usr/bin/env python3
"""Check whether a stored semantic review matches its current task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_review import check_pass, check_review
from v2.scripts.validate_entry import ContractError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("fragment", type=Path)
    parser.add_argument(
        "--any-verdict",
        action="store_true",
        help="Validate and report a bound review without requiring a pass",
    )
    args = parser.parse_args(argv)
    try:
        review = (
            check_review(args.task.resolve(), args.fragment.resolve())
            if args.any_verdict
            else check_pass(args.task.resolve(), args.fragment.resolve())
        )
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    if args.any_verdict:
        print(f"Valid semantic review ({review['verdict']})")
    else:
        print("Reusable semantic-review pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
