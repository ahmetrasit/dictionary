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
from v2.scripts.branch_lexicalization import branch_lexicalization_profile
from v2.scripts.create_entry import publish_pair
from v2.scripts.render_entry import render
from v2.scripts.render_occurrences import structured_occurrence_data
from v2.scripts.validate_entry import (
    load_json,
    project_path,
    sha256_file,
    ContractError,
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


def migrate_entry(path: Path, *, force: bool) -> None:
    entry = load_json(path)
    entry.pop("review_gate", None)
    legacy_entry = entry.get("schema_version") < 4
    evidence_index_path = project_path(entry["provenance"]["evidence_index_path"])
    index, packages = load_evidence(evidence_index_path)
    entry["provenance"].update(
        {
            "packet_path": index["packet_path"],
            "packet_sha256": index["packet_sha256"],
            "evidence_index_sha256": sha256_file(evidence_index_path),
            "furuq_path": index["furuq_path"],
            "furuq_sha256": index["furuq_sha256"],
        }
    )
    packet = load_json(project_path(entry["provenance"]["packet_path"]))
    packages_by_branch = {
        (row["root_id"], row["branch_id"]): package
        for row, package, _package_path in packages
    }
    packet_branches = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    for branch in entry["branches"]:
        branch_key = (branch["root_id"], branch["branch_id"])
        if legacy_entry:
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
        branch["lexicalization_profile"] = branch_lexicalization_profile(
            branch["lexical_realizations"]
        )

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
        "Kur'an eşdizim verileri mekanik oluşum katmanında tutulur."
        if entry["language"] == "tr"
        else "Quran occurrence data is retained in the mechanical evidence layer."
    )

    markdown_path = path.with_suffix(".md")
    with tempfile.TemporaryDirectory(prefix=f".{path.stem}.migrate.", dir=path.parent) as directory:
        stage_dir = Path(directory)
        entry_stage = stage_dir / path.name
        markdown_stage = stage_dir / markdown_path.name
        entry_stage.write_text(json_content(entry), encoding="utf-8")
        validate_entry(entry_stage)
        render(entry_stage, markdown_stage)
        render(entry_stage, markdown_stage, check=True)
        publish_pair(
            entry_stage,
            markdown_stage,
            path,
            markdown_path,
            force_entry=force,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all Turkish entries plus the schema fixture",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of reviewed, published, invalid, or unmarked outputs",
    )
    args = parser.parse_args()
    paths = [path.resolve() for path in args.paths]
    if not paths and not args.all:
        raise SystemExit("Pass explicit paths or --all")
    if args.all:
        if paths:
            raise SystemExit("Use either explicit paths or --all, not both")
        paths = sorted((PROJECT / "v2/entries/tr").glob("root_*.json"))
        paths.append(PROJECT / "v2/examples/root_000858.tr.entry.json")
    for path in paths:
        try:
            migrate_entry(path, force=args.force)
        except ContractError as error:
            raise SystemExit(str(error)) from error
        print(f"Migrated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
