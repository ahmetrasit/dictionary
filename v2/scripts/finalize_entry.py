#!/usr/bin/env python3
"""Deterministically assemble, render, and atomically publish one prepared entry."""

from __future__ import annotations

import argparse
import contextlib
import sys
import tempfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import assemble
from v2.scripts.accept_root_review import check_pass as check_semantic_review
from v2.scripts.create_entry import check_output_targets, publish_pair
from v2.scripts.create_entry import atomic_write
from v2.scripts.render_entry import render
from v2.scripts.validate_entry import ContractError


def finalize(
    envelope: str,
    language: str,
    *,
    evidence_index: Path,
    work_dir: Path,
    entry_path: Path,
    markdown_path: Path,
    force_entry: bool = False,
) -> None:
    check_semantic_review(
        work_dir / "tasks/root_reviewer.json",
        work_dir / "fragments/root_review.json",
    )
    check_output_targets(entry_path, markdown_path, force_entry=force_entry)
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.ExitStack() as stack:
        entry_stage = Path(
            stack.enter_context(
                tempfile.TemporaryDirectory(
                    prefix=f".{envelope}.entry.", dir=entry_path.parent
                )
            )
        ) / entry_path.name
        markdown_stage = Path(
            stack.enter_context(
                tempfile.TemporaryDirectory(
                    prefix=f".{envelope}.markdown.", dir=markdown_path.parent
                )
            )
        ) / markdown_path.name
        assemble(evidence_index, work_dir, language, entry_stage)
        render(entry_stage, markdown_stage)
        render(entry_stage, markdown_stage, check=True)
        publish_pair(
            entry_stage,
            markdown_stage,
            entry_path,
            markdown_path,
            force_entry=force_entry,
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root_envelope_id")
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--evidence-index", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--entry", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--force-entry", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    envelope = args.root_envelope_id
    evidence_index = args.evidence_index or (
        PROJECT / "v2/output/branch_evidence" / envelope / "index.json"
    )
    work_dir = args.work_dir or (
        PROJECT / "v2/work/entry_creation" / envelope / args.language
    )
    entry = args.entry or PROJECT / "v2/entries" / args.language / f"{envelope}.json"
    markdown = args.markdown or entry.with_suffix(".md")
    error_output = work_dir.resolve() / "output/finalize_error.txt"
    try:
        finalize(
            envelope,
            args.language,
            evidence_index=evidence_index.resolve(),
            work_dir=work_dir.resolve(),
            entry_path=entry.resolve(),
            markdown_path=markdown.resolve(),
            force_entry=args.force_entry,
        )
    except (OSError, ContractError, KeyError, TypeError) as error:
        atomic_write(error_output, str(error).rstrip() + "\n")
        raise SystemExit(str(error)) from error
    if error_output.exists():
        error_output.unlink()
    print(f"Published {entry.resolve()} and {markdown.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
