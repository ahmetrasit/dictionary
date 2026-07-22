#!/usr/bin/env python3
"""Check whether a stored semantic-review pass matches its current task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_review import check_pass
from v2.scripts.validate_entry import ContractError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("fragment", type=Path)
    args = parser.parse_args(argv)
    try:
        check_pass(args.task.resolve(), args.fragment.resolve())
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print("Reusable semantic-review pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
