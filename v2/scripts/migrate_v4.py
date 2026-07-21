#!/usr/bin/env python3
"""Migrate schema-v3 entries to deterministic schema v4."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import load_evidence
from v2.scripts.render_entry import render
from v2.scripts.render_occurrences import structured_occurrence_data
from v2.scripts.validate_entry import (
    load_json,
    project_path,
    sha256_file,
    validate_entry,
)


def json_content(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def migrate_entry(path: Path) -> None:
    entry = load_json(path)
    packet = load_json(project_path(entry["provenance"]["packet_path"]))
    _index, packages = load_evidence(
        project_path(entry["provenance"]["evidence_index_path"])
    )
    packages_by_branch = {
        (row["root_id"], row["branch_id"]): package
        for row, package, _package_path in packages
    }
    packet_branches = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    for branch in entry["branches"]:
        branch_key = (branch["root_id"], branch["branch_id"])
        frozen = packet_branches[branch_key]
        package = packages_by_branch[branch_key]
        for field in (
            "branch_image_ar",
            "what_is_ar",
            "what_is_not_ar",
            "source_phrase_ar",
        ):
            branch[field] = frozen[field]

        branch_refs = [
            source_ref
            for source in branch["dictionary_basis"]["sources"]
            for source_ref in source["source_refs"]
        ]
        for source in branch["dictionary_basis"]["sources"]:
            source.pop("roles", None)
            source.pop("contribution", None)
        branch["usage_notes"] = [
            {**note, "evidence_refs": branch_refs}
            for note in branch["usage_notes"]
            if note["kind"] in {"register", "constraint", "technical"}
        ]
        branch["evidence_qualifiers"] = [
            {**qualifier, "source_refs": branch_refs}
            for qualifier in branch["evidence_qualifiers"]
        ]
        disputed = next(
            (
                qualifier["statement"]
                for qualifier in branch["evidence_qualifiers"]
                if qualifier["type"] == "disputed"
            ),
            None,
        )
        branch["source_discussion"] = {
            "discussion": branch["source_discussion"]["discussion"],
            "evidence_refs": branch_refs,
            "examples": [],
            "disagreement": (
                {"summary": disputed, "source_refs": branch_refs}
                if disputed
                else None
            ),
        }
        candidates = {
            (row["root_id"], row["branch_id"]): row
            for row in package["furuq_candidates"]
        }
        for neighbor in branch["arabic_neighbor_distinctions"]:
            candidate = candidates[
                (neighbor["neighbor_root_id"], neighbor["neighbor_branch_id"])
            ]
            neighbor["expression_ar"] = candidate["branch_image_ar"]
            neighbor["basis"] = "furuq_branch_comparison"
            neighbor["evidence_refs"] = [
                value.strip()
                for value in candidate["source_refs"].split(";")
                if value.strip()
            ]

    occurrence = entry["occurrence_evidence"]
    artifact_path = project_path(occurrence["artifact_path"])
    alignment_path = project_path(occurrence["alignment_path"])
    alignment = load_json(alignment_path)
    occurrence["artifact_sha256"] = sha256_file(artifact_path)
    occurrence["alignment_sha256"] = sha256_file(alignment_path)
    occurrence["observations"] = []
    occurrence.update(structured_occurrence_data(packet, alignment))
    entry["schema_version"] = 4
    entry["root_profile"]["collocation_weight"] = "unknown"
    entry["root_profile"]["collocation_note"] = (
        "Quran oluşum verileri mekanik kanıt katmanında tutulur."
        if entry["language"] == "tr"
        else "Quran occurrence data is retained in the mechanical evidence layer."
    )

    atomic_write(path, json_content(entry))
    validate_entry(path)
    render(path, path.with_suffix(".md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = [path.resolve() for path in args.paths]
    if not paths:
        paths = sorted((PROJECT / "v2/entries/tr").glob("root_*.json"))
        paths.append(PROJECT / "v2/examples/root_000858.tr.entry.json")
    for path in paths:
        migrate_entry(path)
        print(f"Migrated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
