#!/usr/bin/env python3
"""Export validated v2 master entries or bounded projections as JSONL."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.validate_entry import ContractError, validate_entry
from v2.scripts.project_entry import PROJECTIONS, project_entry


EXPORT_NAMES = {
    "master": "dictionary",
    "translation_agent": "translation-agent",
    "user_dictionary": "user-dictionary",
    "scholar_view": "scholar-view",
}


def render_jsonl(entries_dir: Path, projection: str = "master") -> tuple[str, int]:
    if projection not in EXPORT_NAMES:
        raise ContractError(f"Unknown JSONL projection: {projection}")
    paths = sorted(entries_dir.glob("root_*.json"))
    entries: list[dict] = []
    seen: set[str] = set()
    language: str | None = None
    for path in paths:
        entry, _packet = validate_entry(path.resolve())
        if entry["entry_id"] in seen:
            raise ContractError(f"Duplicate entry_id in JSONL export: {entry['entry_id']}")
        seen.add(entry["entry_id"])
        if language is None:
            language = entry["language"]
        elif entry["language"] != language:
            raise ContractError(
                f"Mixed languages in JSONL export: {language} and {entry['language']}"
            )
        entries.append(entry if projection == "master" else project_entry(entry, projection))
    content = "".join(
        json.dumps(
            entry,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
        for entry in entries
    )
    return content, len(entries)


def write_output(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file():
            raise ContractError(f"Missing JSONL export: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise ContractError(f"Stale JSONL export: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--entries-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--projection",
        choices=("master", *PROJECTIONS),
        default="master",
        help="Bounded consumer projection; master preserves the existing full-entry export",
    )
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries_dir = (
        args.entries_dir.resolve()
        if args.entries_dir
        else PROJECT / "v2/entries" / args.language
    )
    output = (
        args.output.resolve()
        if args.output
        else PROJECT
        / "v2/output/projections"
        / f"{EXPORT_NAMES[args.projection]}.{args.language}.jsonl"
        if args.projection != "master"
        else PROJECT / "v2/output" / f"dictionary.{args.language}.jsonl"
    )
    try:
        content, count = render_jsonl(entries_dir, args.projection)
        write_output(output, content, check=args.check)
    except (OSError, ContractError, sqlite3.Error) as error:
        raise SystemExit(str(error)) from error
    verb = "Checked" if args.check else "Exported"
    print(f"{verb} {count} {args.projection} records in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
