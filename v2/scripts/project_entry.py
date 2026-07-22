#!/usr/bin/env python3
"""Derive bounded consumer projections from one validated master entry."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.validate_entry import ContractError, DICTIONARY_CODES, validate_entry


PROJECTION_VERSION = 3
PROJECTIONS = ("translation_agent", "user_dictionary", "scholar_view")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def master_binding(entry: dict) -> dict:
    return {
        "entry_id": entry["entry_id"],
        "schema_version": entry["schema_version"],
        "sha256": hashlib.sha256(canonical_json_bytes(entry)).hexdigest(),
    }


def projection_identity(entry: dict, projection: str) -> dict:
    return {
        "projection": projection,
        "projection_version": PROJECTION_VERSION,
        "master": master_binding(entry),
        "entry_id": entry["entry_id"],
        "language": entry["language"],
        "status": entry["status"],
        "root_envelope_id": entry["root_envelope_id"],
        "root_ids": copy.deepcopy(entry["root_ids"]),
    }


def branch_source_attribution(branch: dict) -> tuple[list[str], dict[str, str]]:
    source_by_ref = {
        source_ref: DICTIONARY_CODES[source["source_id"]]
        for source in branch["dictionary_basis"]["sources"]
        for source_ref in source["source_refs"]
    }
    sources = [
        DICTIONARY_CODES[source["source_id"]]
        for source in branch["dictionary_basis"]["sources"]
    ]
    note_parts: dict[str, list[str]] = {}
    for detail in branch["source_discussion"].get("details", []):
        for code in sorted({source_by_ref[ref] for ref in detail["source_refs"]}):
            note_parts.setdefault(code, []).append(detail["summary"].strip())
    return sources, {
        code: " ".join(parts) for code, parts in note_parts.items()
    }


def translation_agent_projection(entry: dict) -> dict:
    """Expose branch boundaries, gloss candidates, and translation-risk notes."""

    result = projection_identity(entry, "translation_agent")
    profile = entry["root_profile"]
    result["root_profile"] = {
        "transliteration": profile["transliteration"],
        "summary": profile["summary"],
        "polysemy": profile["polysemy"],
        "organization": profile["organization"],
        "branch_count": profile["branch_count"],
    }
    result["branches"] = []
    for branch in entry["branches"]:
        sources, source_note = branch_source_attribution(branch)
        result["branches"].append({
            "root_id": branch["root_id"],
            "branch_id": branch["branch_id"],
            "branch_image_ar": branch["branch_image_ar"],
            "what_is_ar": branch["what_is_ar"],
            "what_is_not_ar": branch["what_is_not_ar"],
            "source_phrase_ar": branch["source_phrase_ar"],
            "sources": sources,
            "source_note": source_note,
            "image_transliteration": branch["image_transliteration"],
            "summary": branch["summary"],
            **(
                {"concept_map": copy.deepcopy(branch["concept_map"])}
                if "concept_map" in branch
                else {}
            ),
            "lexical_glosses": [
                {
                    "lexical_unit_id": unit["lexical_unit_id"],
                    "target_gloss": unit.get("target_gloss"),
                }
                for unit in branch["lexical_realizations"]
                if "target_gloss" in unit
            ],
            "gloss_candidates": copy.deepcopy(branch["glosses"]),
        })
    result["occurrence_evidence"] = {
        key: copy.deepcopy(value)
        for key, value in entry["occurrence_evidence"].items()
        if key in {"summary", "forms", "ayahs", "occurrences"}
    }
    return result


def user_dictionary_projection(entry: dict) -> dict:
    """Expose only reader-facing definitions, selected glosses, and key contrasts."""

    result = projection_identity(entry, "user_dictionary")
    profile = entry["root_profile"]
    result["root_profile"] = {
        "transliteration": profile["transliteration"],
        "summary": profile["summary"],
        "branch_count": profile["branch_count"],
    }
    branches = []
    for branch in entry["branches"]:
        sources, source_note = branch_source_attribution(branch)
        # Neighbor distinctions are author-ordered. When present, the first row is
        # the normative key distinction for compact reader projections.
        distinctions = branch["arabic_neighbor_distinctions"]
        key_distinction = None
        if distinctions:
            neighbor = distinctions[0]
            key_distinction = {
                "neighbor_root_id": neighbor["neighbor_root_id"],
                "neighbor_branch_id": neighbor["neighbor_branch_id"],
                **(
                    {"relation_type": neighbor["relation_type"]}
                    if "relation_type" in neighbor
                    else {}
                ),
                "expression_ar": neighbor["expression_ar"],
                "expression_transliteration": neighbor[
                    "expression_transliteration"
                ],
                "gloss": neighbor["gloss"],
                "distinction": neighbor["distinction"],
            }
        branches.append(
            {
                "root_id": branch["root_id"],
                "branch_id": branch["branch_id"],
                "branch_image_ar": branch["branch_image_ar"],
                "what_is_ar": branch["what_is_ar"],
                "source_phrase_ar": branch["source_phrase_ar"],
                "sources": sources,
                "source_note": source_note,
                "image_transliteration": branch["image_transliteration"],
                "definition": branch.get("concept_map", {}).get(
                    "definition", branch["glosses"]["semantic_definition"]
                ),
                "concept_gloss": {
                    "text": branch["glosses"].get(
                        "concept", branch["glosses"]["selected"][0]
                    )["text"]
                },
                "contextual_glosses": [
                    {"text": gloss["text"]}
                    for gloss in branch["glosses"].get(
                        "contextual", branch["glosses"]["selected"][1:]
                    )
                ],
                "key_distinction": key_distinction,
            }
        )
    result["branches"] = branches
    occurrence = entry["occurrence_evidence"]
    result["occurrence_evidence"] = {
        "summary": copy.deepcopy(occurrence["summary"]),
    }
    return result


def scholar_view_projection(entry: dict) -> dict:
    """Expose the complete validated entry only to the scholar consumer."""

    return {
        "projection": "scholar_view",
        "projection_version": PROJECTION_VERSION,
        "master": master_binding(entry),
        "entry": copy.deepcopy(entry),
    }


def project_entry(entry: dict, projection: str) -> dict:
    projectors = {
        "translation_agent": translation_agent_projection,
        "user_dictionary": user_dictionary_projection,
        "scholar_view": scholar_view_projection,
    }
    try:
        projector = projectors[projection]
    except KeyError as error:
        raise ContractError(f"Unknown entry projection: {projection}") from error
    return projector(entry)


def render_projection(entry: dict, projection: str) -> str:
    return json.dumps(
        project_entry(entry, projection),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def write_output(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file():
            raise ContractError(f"Missing entry projection: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise ContractError(f"Stale entry projection: {path}")
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path)
    parser.add_argument("--projection", choices=PROJECTIONS, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        entry, _packet = validate_entry(args.entry.resolve())
        content = render_projection(entry, args.projection)
        if args.output is None:
            if args.check:
                raise ContractError("--check requires --output")
            sys.stdout.write(content)
        else:
            write_output(args.output.resolve(), content, check=args.check)
            action = "Checked" if args.check else "Wrote"
            print(f"{action} {args.projection} projection at {args.output}")
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
