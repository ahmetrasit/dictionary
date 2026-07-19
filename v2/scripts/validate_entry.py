#!/usr/bin/env python3
"""Validate one v2 target-language encyclopedia entry against its evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = PROJECT / "v2/schema/encyclopedia-entry.schema.json"
DEFAULT_FURUQ = PROJECT / "data/working/furuq_v4.sqlite"
OCCURRENCE_MARKER = "<!-- generated-by: v2/scripts/render_occurrences.py schema=1 -->"

DICTIONARY_NAMES = {
    "ayn": "Kitāb al-ʿAyn",
    "jamhara": "Jamharat al-Lugha",
    "maqayis": "Maqāyīs al-Lugha",
    "mufradat": "al-Mufradāt fī Gharīb al-Qurʾān",
    "sihah": "al-Ṣiḥāḥ",
    "tahdhib": "Tahdhīb al-Lugha",
}


class ContractError(ValueError):
    """Raised when an entry violates the structural or evidence contract."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object)
    except json.JSONDecodeError as error:
        raise ContractError(f"Invalid JSON in {path}: {error}") from error


def value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return type(value).__name__


def resolve_ref(root_schema: dict, reference: str) -> dict:
    if not reference.startswith("#/"):
        raise ContractError(f"Unsupported schema reference: {reference}")
    value: Any = root_schema
    for part in reference[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[part]
    if not isinstance(value, dict):
        raise ContractError(f"Schema reference is not an object: {reference}")
    return value


def structural_errors(
    value: Any,
    schema: dict,
    root_schema: dict,
    path: str = "$",
) -> list[str]:
    if "$ref" in schema:
        return structural_errors(value, resolve_ref(root_schema, schema["$ref"]), root_schema, path)

    errors: list[str] = []
    expected = schema.get("type")
    expected_types = [expected] if isinstance(expected, str) else expected
    if expected_types and value_type(value) not in expected_types:
        return [
            f"{path}: expected {' or '.join(expected_types)}, got {value_type(value)}"
        ]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not in {schema['enum']!r}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}: missing required property {required!r}")
        if schema.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                errors.append(f"{path}: unknown property {key!r}")
        for key, child in value.items():
            if key in properties:
                errors.extend(
                    structural_errors(child, properties[key], root_schema, f"{path}.{key}")
                )

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: requires at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: allows at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path}: items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(
                    structural_errors(item, item_schema, root_schema, f"{path}[{index}]")
                )

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: must have at least {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: must have at most {schema['maxLength']} characters")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match {schema['pattern']!r}")

    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: must be at least {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: must be at most {schema['maximum']}")
    return errors


def split_refs(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def project_path(relative: str) -> Path:
    path = (PROJECT / relative).resolve()
    try:
        path.relative_to(PROJECT)
    except ValueError as error:
        raise ContractError(f"Path escapes project root: {relative}") from error
    return path


def packet_source_map(packet: dict) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for source in packet["dictionary_sources"]:
        source_ref = source.get("source_ref", "")
        if not source_ref or source_ref == "-":
            continue
        key = (source.get("root_id", ""), source_ref)
        source_id = source.get("source_id", "")
        if key in result and result[key] != source_id:
            raise ContractError(
                f"Packet source reference resolves to multiple dictionaries: {key}"
            )
        result[key] = source_id
    return result


def packet_source_text_map(packet: dict) -> dict[tuple[str, str], str]:
    return {
        (source.get("root_id", ""), source.get("source_ref", "")): source.get(
            "entry_text_clean", ""
        )
        for source in packet["dictionary_sources"]
        if source.get("source_ref") and source.get("source_ref") != "-"
    }


def validate_dictionary_basis(
    authored: dict,
    packet_branch: dict,
    sources: dict[tuple[str, str], str],
    source_texts: dict[tuple[str, str], str],
    path: str,
) -> list[str]:
    errors: list[str] = []
    root_id = authored["root_id"]
    required_refs = split_refs(packet_branch.get("source_refs", ""))
    basis = authored["dictionary_basis"]
    seen_refs: list[str] = []
    seen_ids: list[str] = []
    for index, source in enumerate(basis["sources"]):
        source_path = f"{path}.dictionary_basis.sources[{index}]"
        source_id = source["source_id"]
        seen_ids.append(source_id)
        expected_name = DICTIONARY_NAMES.get(source_id)
        if expected_name and source["dictionary_name"] != expected_name:
            errors.append(
                f"{source_path}.dictionary_name: expected {expected_name!r}"
            )
        for source_ref in source["source_refs"]:
            seen_refs.append(source_ref)
            actual_id = sources.get((root_id, source_ref))
            if actual_id is None:
                errors.append(
                    f"{source_path}.source_refs: packet has no matching source {source_ref!r}"
                )
            elif actual_id != source_id:
                errors.append(
                    f"{source_path}.source_refs: {source_ref!r} belongs to {actual_id!r}, "
                    f"not {source_id!r}"
                )

    if len(seen_refs) != len(set(seen_refs)):
        errors.append(f"{path}.dictionary_basis: source references must not repeat")
    if set(seen_refs) != set(required_refs):
        missing = sorted(set(required_refs) - set(seen_refs))
        extra = sorted(set(seen_refs) - set(required_refs))
        errors.append(
            f"{path}.dictionary_basis: source roster mismatch; missing={missing}; extra={extra}"
        )
    unique_ids = set(seen_ids)
    if len(seen_ids) != len(unique_ids):
        errors.append(f"{path}.dictionary_basis: each dictionary must have one source row")
    if basis["dictionary_count"] != len(unique_ids):
        errors.append(
            f"{path}.dictionary_basis.dictionary_count: expected {len(unique_ids)}"
        )
    if basis["passage_count"] != len(set(seen_refs)):
        errors.append(
            f"{path}.dictionary_basis.passage_count: expected {len(set(seen_refs))}"
        )

    discussion = authored["source_discussion"]
    discussion_refs = list(discussion["evidence_refs"])
    for index, example in enumerate(discussion["examples"]):
        discussion_refs.extend(example["source_refs"])
        cited_texts = [
            source_texts.get((root_id, source_ref), "")
            for source_ref in example["source_refs"]
        ]
        cited_texts.append(packet_branch.get("source_phrase_ar", ""))
        if not any(example["arabic"] in text for text in cited_texts):
            errors.append(
                f"{path}.source_discussion.examples[{index}].arabic: not an exact "
                "substring of the cited dictionary passage or frozen source phrase"
            )
    if discussion["disagreement"]:
        discussion_refs.extend(discussion["disagreement"]["source_refs"])
    unknown = sorted(set(discussion_refs) - set(required_refs))
    if unknown:
        errors.append(f"{path}.source_discussion: non-branch source refs {unknown}")
    disagreement_roles = {
        ref
        for source in basis["sources"]
        if "disagreement" in source["roles"]
        for ref in source["source_refs"]
    }
    if discussion["disagreement"] is None and disagreement_roles:
        errors.append(
            f"{path}: dictionary basis marks disagreement but disagreement is null"
        )
    if discussion["disagreement"] is not None:
        stated_refs = set(discussion["disagreement"]["source_refs"])
        if not stated_refs.intersection(disagreement_roles):
            errors.append(
                f"{path}.source_discussion.disagreement: no cited source is marked "
                "with the disagreement role"
            )
    return errors


def validate_glosses(branch: dict, path: str) -> list[str]:
    errors: list[str] = []
    selected = branch["glosses"]["selected"]
    ranks = [row["rank"] for row in selected]
    expected = list(range(1, len(selected) + 1))
    if ranks != expected:
        errors.append(f"{path}.glosses.selected: ranks must be {expected}, got {ranks}")
    for index, gloss in enumerate(selected):
        if gloss["loanword_status"] == "common" and gloss["rank"] != 2:
            errors.append(
                f"{path}.glosses.selected[{index}]: a common loanword may only be rank 2"
            )
    selected_text = {row["text"].strip().casefold() for row in selected}
    excluded = branch["glosses"]["excluded"]
    excluded_text = [row["text"].strip().casefold() for row in excluded]
    if len(excluded_text) != len(set(excluded_text)):
        errors.append(f"{path}.glosses.excluded: gloss text must be unique")
    overlap = sorted(selected_text & set(excluded_text))
    if overlap:
        errors.append(f"{path}.glosses: selected and excluded glosses overlap: {overlap}")
    return errors


def furuq_branch(
    db: sqlite3.Connection, root_id: str, branch_id: str
) -> sqlite3.Row | None:
    return db.execute(
        "SELECT root_id, branch_id, source_refs, status, contaminated "
        "FROM branch_images "
        "WHERE root_id=? AND branch_id=?",
        (root_id, branch_id),
    ).fetchone()


def validate_neighbors(
    branch: dict,
    db: sqlite3.Connection,
    path: str,
) -> list[str]:
    errors: list[str] = []
    focus = (branch["root_id"], branch["branch_id"])
    seen: set[tuple[str, str]] = set()
    for index, neighbor in enumerate(branch["arabic_neighbor_distinctions"]):
        neighbor_path = f"{path}.arabic_neighbor_distinctions[{index}]"
        key = (neighbor["neighbor_root_id"], neighbor["neighbor_branch_id"])
        if key == focus:
            errors.append(f"{neighbor_path}: focus branch cannot be its own neighbor")
        if key in seen:
            errors.append(f"{neighbor_path}: duplicate neighbor {key[0]}/{key[1]}")
        seen.add(key)
        row = furuq_branch(db, *key)
        if row is None:
            errors.append(f"{neighbor_path}: unknown Furuq branch {key[0]}/{key[1]}")
            continue
        if row["status"] != "accepted" or row["contaminated"] != "no":
            errors.append(
                f"{neighbor_path}: Furuq branch {key[0]}/{key[1]} is not an "
                "accepted, uncontaminated comparison target"
            )
            continue
        source_refs = set(split_refs(row["source_refs"]))
        if not source_refs.intersection(neighbor["evidence_refs"]):
            errors.append(
                f"{neighbor_path}.evidence_refs: no reference belongs to the neighbor's "
                "Furuq source roster"
            )
    return errors


def occurrence_evidence_refs(packet: dict) -> set[str]:
    result = {
        row["qac_ref"] for row in packet["qac"]["occurrences"]
    } | {
        row["qac_word_ref"] for row in packet["qac"]["occurrences"]
    } | {
        ayah["ref"] for ayah in packet["qac"]["ayah_contexts"]
    }
    result.update(
        f"q:{row['surah']}:{row['ayah']}:{row['word_index']}"
        for row in packet["qac"]["occurrences"]
    )
    result.update(
        row.get("unit_id", "") for row in packet["attachments"]["attachments"]
    )
    form_keys: dict[tuple[str, str, str, str], str] = {}
    for row in packet["qac"]["occurrences"]:
        key = tuple(
            str(row.get(field, ""))
            for field in ("lemma_ar", "surface_ar", "pos", "morph_features")
        )
        form_keys.setdefault(key, f"F{len(form_keys) + 1:03d}")
    result.update(form_keys.values())
    result.discard("")
    return result


def validate_occurrence(entry: dict, packet: dict) -> list[str]:
    errors: list[str] = []
    occurrence = entry["occurrence_evidence"]
    expected = (
        f"v2/output/occurrences/{entry['root_envelope_id']}.{entry['language']}.md"
    )
    if occurrence["artifact_path"] != expected:
        errors.append(
            f"$.occurrence_evidence.artifact_path: expected {expected!r}"
        )
    artifact = project_path(occurrence["artifact_path"])
    if not artifact.is_file():
        errors.append(f"$.occurrence_evidence.artifact_path: missing file {artifact}")
    else:
        first = artifact.read_text(encoding="utf-8").splitlines()[:1]
        if first != [OCCURRENCE_MARKER]:
            errors.append(
                "$.occurrence_evidence.artifact_path: file lacks occurrence generator marker"
            )
    allowed = occurrence_evidence_refs(packet)
    for index, observation in enumerate(occurrence["observations"]):
        unknown = sorted(set(observation["evidence_refs"]) - allowed)
        if unknown:
            errors.append(
                f"$.occurrence_evidence.observations[{index}].evidence_refs: "
                f"unknown references {unknown}"
            )
    return errors


def validate_semantics(
    entry: dict,
    packet: dict,
    furuq_path: Path,
) -> list[str]:
    errors: list[str] = []
    language = entry["language"]
    envelope = packet["root_envelope_id"]
    if entry["root_envelope_id"] != envelope:
        errors.append(f"$.root_envelope_id: expected {envelope!r}")
    if entry["entry_id"] != f"{envelope}/{language}":
        errors.append(f"$.entry_id: expected {envelope}/{language!s}")
    packet_root_ids = [row["root_id"] for row in packet["v4_roots"]]
    if entry["root_ids"] != packet_root_ids:
        errors.append(f"$.root_ids: expected packet order {packet_root_ids}")

    packet_branches = [
        (row["root_id"], row["branch_id"]) for row in packet["branches"]
    ]
    authored_branches = [
        (row["root_id"], row["branch_id"]) for row in entry["branches"]
    ]
    if authored_branches != packet_branches:
        errors.append(f"$.branches: expected exact packet roster {packet_branches}")
    count = len(packet_branches)
    profile = entry["root_profile"]
    if profile["branch_count"] != count:
        errors.append(f"$.root_profile.branch_count: expected {count}")
    if count == 1:
        if profile["polysemy"] != "monosemic" or profile["organization"] != "monosemic":
            errors.append("$.root_profile: a one-branch entry must be monosemic")
    elif profile["polysemy"] != "polysemic" or profile["organization"] == "monosemic":
        errors.append("$.root_profile: a multi-branch entry must be polysemic")

    source_map = packet_source_map(packet)
    source_texts = packet_source_text_map(packet)
    packet_by_branch = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    if not furuq_path.is_file():
        raise ContractError(f"Missing Furuq database: {furuq_path}")
    db = sqlite3.connect(f"file:{furuq_path.resolve()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        for index, branch in enumerate(entry["branches"]):
            path = f"$.branches[{index}]"
            packet_branch = packet_by_branch.get((branch["root_id"], branch["branch_id"]))
            if packet_branch is None:
                continue
            errors.extend(
                validate_dictionary_basis(
                    branch, packet_branch, source_map, source_texts, path
                )
            )
            errors.extend(validate_glosses(branch, path))
            errors.extend(validate_neighbors(branch, db, path))
    finally:
        db.close()
    errors.extend(validate_occurrence(entry, packet))
    return errors


def validate_entry(
    entry_path: Path,
    schema_path: Path = DEFAULT_SCHEMA,
    packet_path: Path | None = None,
    furuq_path: Path = DEFAULT_FURUQ,
) -> tuple[dict, dict]:
    entry = load_json(entry_path)
    schema = load_json(schema_path)
    errors = structural_errors(entry, schema, schema)
    if errors:
        raise ContractError("Structural validation failed:\n- " + "\n- ".join(errors))

    declared_packet = project_path(entry["provenance"]["packet_path"])
    packet_path = packet_path.resolve() if packet_path else declared_packet
    if packet_path != declared_packet:
        raise ContractError(
            f"Explicit packet {packet_path} does not match declared packet {declared_packet}"
        )
    if not packet_path.is_file():
        raise ContractError(f"Missing root packet: {packet_path}")
    digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    if entry["provenance"]["packet_sha256"] != digest:
        raise ContractError(
            "Packet digest mismatch: "
            f"expected {entry['provenance']['packet_sha256']}, got {digest}"
        )
    packet = load_json(packet_path)
    errors = validate_semantics(entry, packet, furuq_path)
    if errors:
        raise ContractError("Evidence validation failed:\n- " + "\n- ".join(errors))
    return entry, packet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--furuq", type=Path, default=DEFAULT_FURUQ)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        entry, _packet = validate_entry(
            args.entry.resolve(),
            args.schema.resolve(),
            args.packet,
            args.furuq.resolve(),
        )
    except (OSError, ContractError, sqlite3.Error) as error:
        raise SystemExit(str(error)) from error
    print(
        f"Valid v2 entry: {entry['entry_id']} "
        f"({len(entry['branches'])} branches, {entry['language']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
