#!/usr/bin/env python3
"""Promote finalized Quran-corpus entry JSON to the root-level final surface."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.create_entry import atomic_write, json_content
from v2.scripts.validate_entry import ContractError, load_json, validate_entry


MANIFEST_FORMAT = "dictionary-final-entry-manifest-v1"
ROOT_ENVELOPE_RE = re.compile(r"^root_[0-9]{6}(--root_[0-9]{6})*$")
ROOT_ID_RE = re.compile(r"root_([0-9]{6})")
QURANIC_ORIGIN_RE = re.compile(rb'"origin_corpus"\s*:\s*"quranic"')


def envelope_sort_key(envelope: str) -> tuple[int, ...]:
    values = tuple(int(value) for value in ROOT_ID_RE.findall(envelope))
    if not values:
        raise ContractError(f"Invalid root envelope ID: {envelope!r}")
    return values


def relative_path(path: Path, project: Path = PROJECT) -> str:
    try:
        return path.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(project: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def git_head(project: Path) -> str | None:
    return git_value(project, ["rev-parse", "--verify", "HEAD"])


def git_has_changes(project: Path, path: Path) -> bool | None:
    rel = relative_path(path, project)
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--", rel],
            cwd=project,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def packet_is_quranic(packet: dict[str, Any]) -> bool:
    return any(branch.get("origin_corpus") == "quranic" for branch in packet["branches"])


def quranic_packet_envelopes(packet_dir: Path) -> set[str]:
    envelopes: set[str] = set()
    for path in sorted(packet_dir.glob("root_*.json")):
        envelope = path.stem
        if not ROOT_ENVELOPE_RE.fullmatch(envelope):
            continue
        if QURANIC_ORIGIN_RE.search(path.read_bytes()):
            envelopes.add(envelope)
    return envelopes


def final_entry_rows(
    source_dir: Path,
    packet_dir: Path,
    language: str,
) -> tuple[list[dict[str, Any]], set[str]]:
    quranic_envelopes = quranic_packet_envelopes(packet_dir)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_path in sorted(source_dir.glob("root_*.json")):
        entry, packet = validate_entry(source_path.resolve())
        envelope = entry["root_envelope_id"]
        if source_path.stem != envelope:
            raise ContractError(
                f"Entry filename must match root_envelope_id: {source_path}"
            )
        if envelope in seen:
            raise ContractError(f"Duplicate root envelope in source entries: {envelope}")
        if entry["language"] != language:
            raise ContractError(
                f"Language mismatch in {source_path}: expected {language!r}, "
                f"got {entry['language']!r}"
            )
        if envelope not in quranic_envelopes or not packet_is_quranic(packet):
            raise ContractError(
                f"Refusing non-Quranic or non-packet entry in final surface: {source_path}"
            )
        seen.add(envelope)
        rows.append(
            {
                "root_envelope_id": envelope,
                "entry_id": entry["entry_id"],
                "language": entry["language"],
                "status": entry["status"],
                "source_path": relative_path(source_path),
                "path": f"entries/{language}/{source_path.name}",
                "sha256": sha256_file(source_path),
            }
        )
    rows.sort(key=lambda row: envelope_sort_key(row["root_envelope_id"]))
    return rows, quranic_envelopes


def existing_manifest_values(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.is_file():
        return {}
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def manifest_content(
    *,
    language: str,
    source_dir: Path,
    destination_dir: Path,
    packet_dir: Path,
    entries: list[dict[str, Any]],
    quranic_envelopes: set[str],
    generated_date: str,
    source_commit: str | None,
    source_tree_has_uncommitted_changes: bool | None,
) -> str:
    promoted = {entry["root_envelope_id"] for entry in entries}
    missing = sorted(quranic_envelopes - promoted, key=envelope_sort_key)
    manifest = {
        "format": MANIFEST_FORMAT,
        "scope": "quranic",
        "language": language,
        "generated_by": "v2/scripts/promote_final_entries.py",
        "generated_date": generated_date,
        "source_commit": source_commit,
        "source_tree_has_uncommitted_changes": source_tree_has_uncommitted_changes,
        "source_dir": relative_path(source_dir),
        "destination_dir": relative_path(destination_dir),
        "packet_dir": relative_path(packet_dir),
        "quranic_packet_envelope_count": len(quranic_envelopes),
        "final_entry_count": len(entries),
        "missing_quranic_packet_envelope_count": len(missing),
        "missing_quranic_packet_envelopes": missing,
        "entries": entries,
    }
    return json_content(manifest)


def write_if_changed(path: Path, content: str) -> None:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    atomic_write(path, content)


def promote(
    *,
    language: str,
    source_dir: Path,
    destination_dir: Path,
    packet_dir: Path,
    check: bool = False,
    prune: bool = True,
    require_complete: bool = False,
    generated_date: str | None = None,
    source_commit: str | None = None,
    source_tree_has_uncommitted_changes: bool | None = None,
    project: Path = PROJECT,
) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    destination_dir = destination_dir.resolve()
    packet_dir = packet_dir.resolve()
    rows, quranic_envelopes = final_entry_rows(source_dir, packet_dir, language)
    selected = {row["root_envelope_id"] for row in rows}
    missing = sorted(quranic_envelopes - selected, key=envelope_sort_key)
    if require_complete and missing:
        raise ContractError(
            "Final entry surface is incomplete for Quranic scope: "
            f"{len(missing)} missing envelope(s)"
        )

    manifest_path = destination_dir / "manifest.json"
    existing = existing_manifest_values(manifest_path)
    resolved_generated_date = generated_date
    if resolved_generated_date is None and check:
        resolved_generated_date = existing.get("generated_date")
    if resolved_generated_date is None:
        resolved_generated_date = dt.date.today().isoformat()
    resolved_source_commit = source_commit
    if resolved_source_commit is None and check:
        resolved_source_commit = existing.get("source_commit")
    if resolved_source_commit is None:
        resolved_source_commit = git_head(project)
    resolved_dirty = source_tree_has_uncommitted_changes
    if resolved_dirty is None and check and "source_tree_has_uncommitted_changes" in existing:
        resolved_dirty = existing["source_tree_has_uncommitted_changes"]
    if resolved_dirty is None:
        resolved_dirty = git_has_changes(project, source_dir)

    content_by_target: dict[Path, str] = {}
    for row in rows:
        source_path = project / row["source_path"]
        content_by_target[destination_dir / f"{row['root_envelope_id']}.json"] = (
            source_path.read_text(encoding="utf-8")
        )
    expected_manifest = manifest_content(
        language=language,
        source_dir=source_dir,
        destination_dir=destination_dir,
        packet_dir=packet_dir,
        entries=rows,
        quranic_envelopes=quranic_envelopes,
        generated_date=resolved_generated_date,
        source_commit=resolved_source_commit,
        source_tree_has_uncommitted_changes=resolved_dirty,
    )

    stale_targets = [
        path
        for path in sorted(destination_dir.glob("root_*.json"))
        if path.stem not in selected
    ]
    if check:
        errors: list[str] = []
        for target, expected in content_by_target.items():
            if not target.is_file():
                errors.append(f"Missing final entry: {relative_path(target, project)}")
            elif target.read_text(encoding="utf-8") != expected:
                errors.append(f"Stale final entry: {relative_path(target, project)}")
        if prune:
            errors.extend(
                f"Stale final entry: {relative_path(path, project)}"
                for path in stale_targets
            )
        if not manifest_path.is_file():
            errors.append(f"Missing final manifest: {relative_path(manifest_path, project)}")
        elif manifest_path.read_text(encoding="utf-8") != expected_manifest:
            errors.append(f"Stale final manifest: {relative_path(manifest_path, project)}")
        if errors:
            raise ContractError("\n".join(errors))
    else:
        destination_dir.mkdir(parents=True, exist_ok=True)
        for target, expected in content_by_target.items():
            write_if_changed(target, expected)
        if prune:
            for path in stale_targets:
                path.unlink()
        write_if_changed(manifest_path, expected_manifest)

    return {
        "language": language,
        "entry_count": len(rows),
        "quranic_packet_envelope_count": len(quranic_envelopes),
        "missing_quranic_packet_envelope_count": len(missing),
        "destination_dir": relative_path(destination_dir, project),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--destination-dir", type=Path)
    parser.add_argument(
        "--packet-dir",
        type=Path,
        default=PROJECT / "data/output/root_packets",
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-prune", action="store_true")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail unless every Quranic packet envelope has a final entry JSON.",
    )
    parser.add_argument("--generated-date")
    parser.add_argument("--source-commit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_dir = args.source_dir or PROJECT / "v2/entries" / args.language
    destination_dir = args.destination_dir or PROJECT / "entries" / args.language
    try:
        result = promote(
            language=args.language,
            source_dir=source_dir,
            destination_dir=destination_dir,
            packet_dir=args.packet_dir,
            check=args.check,
            prune=not args.no_prune,
            require_complete=args.require_complete,
            generated_date=args.generated_date,
            source_commit=args.source_commit,
        )
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    verb = "Checked" if args.check else "Promoted"
    print(
        f"{verb} {result['entry_count']} final {result['language']} entries "
        f"to {result['destination_dir']} "
        f"({result['missing_quranic_packet_envelope_count']} missing of "
        f"{result['quranic_packet_envelope_count']} Quranic packet envelopes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
