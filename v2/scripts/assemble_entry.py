#!/usr/bin/env python3
"""Assemble one v2 entry from immutable evidence and hash-bound agent fragments."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.validate_entry import (
    ContractError,
    DICTIONARY_CODES,
    load_json,
    split_refs,
    structural_errors,
    validate_entry,
)
from v2.scripts.render_occurrences import structured_occurrence_data


FRAGMENT_SCHEMAS = {
    "root_writer": PROJECT / "v2/schema/fragments/root-writer.schema.json",
    "root_reviewer": PROJECT / "v2/schema/fragments/root-reviewer.schema.json",
    "branch_writer": PROJECT / "v2/schema/fragments/branch-writer.schema.json",
    "root_profile_writer": PROJECT / "v2/schema/fragments/root-profile.schema.json",
}
TASK_FORMAT = 4
TASK_GENERATOR = "v2/scripts/create_entry.py"
ROOT_ENTRY_ARTIFACT_FORMAT = "dictionary-v2-root-entry-draft-v1"
ROOT_ENTRY_ARTIFACT_GENERATOR = "v2/scripts/accept_root_writer.py"
ROOT_ENTRY_BRANCH_FIELDS = {
    "branch_image_ar",
    "what_is_ar",
    "source_phrase_ar",
    "sources",
    "source_note",
}


def branch_ref(root_id: str, branch_id: str) -> str:
    return f"{root_id}/{branch_id}"


def root_entry_filename(envelope: str) -> str:
    return f"{envelope}_entry.json"


def authored_root_writer_response(value: dict) -> dict:
    """Return the agent-owned portion of an accepted enriched root entry."""
    result = dict(value)
    result.pop("inputs_sha256", None)
    if (
        result.get("artifact_format") != ROOT_ENTRY_ARTIFACT_FORMAT
        or result.get("generated_by") != ROOT_ENTRY_ARTIFACT_GENERATOR
    ):
        return result
    for field in (
        "artifact_format",
        "generated_by",
        "root_envelope_id",
        "language",
        "occurrence_evidence",
    ):
        result.pop(field, None)
    branches = []
    for branch in result.get("branches", []):
        authored = dict(branch)
        for field in ROOT_ENTRY_BRANCH_FIELDS:
            authored.pop(field, None)
        branches.append(authored)
    result["branches"] = branches
    return result


def dictionary_source_ids(basis: dict, source_refs: list[str]) -> list[str]:
    """Resolve source IDs from the branch's exact dictionary reference roster."""
    source_by_ref = {
        source_ref: source["source_id"]
        for source in basis["sources"]
        for source_ref in source["source_refs"]
    }
    unknown = sorted(set(source_refs) - set(source_by_ref))
    if unknown:
        raise ContractError(
            "Source references are absent from the branch dictionary roster: "
            f"{unknown}"
        )
    return sorted({source_by_ref[source_ref] for source_ref in source_refs})


def load_rendering_policy(
    path: Path,
    envelope: str,
    packages: list[dict],
) -> dict[tuple[str, str], str]:
    if not path.is_file():
        raise ContractError(
            "needs_name_policy: missing reviewed coordinator policy " + str(path)
        )
    value = load_json(path)
    if (
        value.get("format") != "dictionary-v2-protected-name-policy-v1"
        or value.get("root_envelope_id") != envelope
        or value.get("status") != "reviewed"
    ):
        raise ContractError(f"needs_name_policy: invalid or unreviewed policy {path}")
    policy: dict[tuple[str, str], str] = {}
    for item in value.get("items", []):
        key = (item.get("root_id"), item.get("lexical_unit_id"))
        kind = item.get("rendering_kind")
        if (
            not all(isinstance(part, str) for part in key)
            or kind not in {"ordinary", "proper_name"}
            or key in policy
        ):
            raise ContractError(f"needs_name_policy: invalid or duplicate item {item!r}")
        policy[key] = kind
    expected = {
        (package["branch"]["root_id"], unit["lexical_unit_id"])
        for package in packages
        for unit in package.get("lexical_units", [])
    }
    if set(policy) != expected:
        missing = sorted(expected - set(policy))
        extra = sorted(set(policy) - expected)
        raise ContractError(
            f"needs_name_policy: roster mismatch in {path}; "
            f"missing={missing}, extra={extra}"
        )
    return policy


def agent_root_evidence(
    packages: list[dict],
    rendering_policy: dict[tuple[str, str], str],
) -> dict:
    """Project deduplicated semantic evidence and compact source claims."""
    neighbor_registry: list[dict] = []
    neighbor_by_ref: dict[str, dict] = {}
    branches = []
    for package in packages:
        focus = package["branch"]
        refs = []
        for candidate in package["furuq_candidates"]:
            ref = branch_ref(candidate["root_id"], candidate["branch_id"])
            card = {
                "neighbor_ref": ref,
                "branch_image_ar": candidate["branch_image_ar"],
                "what_is_ar": candidate["what_is_ar"],
            }
            existing = neighbor_by_ref.get(ref)
            if existing is not None and existing != card:
                raise ContractError(f"Conflicting minimal neighbor cards for {ref}")
            if existing is None:
                neighbor_by_ref[ref] = card
                neighbor_registry.append(card)
            refs.append(ref)
        source_claims = []
        basis = package["dictionary_basis"]
        for unit in package.get("lexical_units", []):
            source_refs = split_refs(unit.get("source_refs", ""))
            policy_key = (focus["root_id"], unit["lexical_unit_id"])
            if policy_key not in rendering_policy:
                raise ContractError(
                    "Missing coordinator rendering policy for "
                    f"{policy_key[0]}/{policy_key[1]}"
                )
            source_claims.append(
                {
                    "claim_id": unit["lexical_unit_id"],
                    "lexical_unit_id": unit["lexical_unit_id"],
                    "unit_kind": unit["unit_kind"],
                    "expression_ar": unit["expression_ar"],
                    "sense_ar": unit["sense_ar"],
                    "source_phrase_ar": unit["source_phrase_ar"],
                    "source_ids": dictionary_source_ids(basis, source_refs),
                    "rendering_policy": rendering_policy[policy_key],
                }
            )
        if not source_claims:
            raise ContractError(
                "Root-writer evidence requires at least one lexical source claim for "
                f"{focus['root_id']}/{focus['branch_id']}"
            )
        branches.append(
            {
                "branch_ref": branch_ref(focus["root_id"], focus["branch_id"]),
                "branch_image_ar": focus["branch_image_ar"],
                "what_is_ar": focus["what_is_ar"],
                "source_claims": source_claims,
                "neighbor_refs": refs,
            }
        )
    return {
        "format": "dictionary-v2-agent-root-evidence-v4",
        "branches": branches,
        "neighbor_registry": neighbor_registry,
    }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_content(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def resolve_project_path(value: str) -> Path:
    path = (PROJECT / value).resolve()
    try:
        path.relative_to(PROJECT)
    except ValueError as error:
        raise ContractError(f"Path escapes project root: {value}") from error
    return path


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT))
    except ValueError:
        return str(path.resolve())


def task_bindings(value: Any) -> list[dict]:
    result: list[dict] = []
    if isinstance(value, dict):
        if {"path", "sha256"}.issubset(value) and isinstance(value["path"], str):
            result.append(value)
        for child in value.values():
            result.extend(task_bindings(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(task_bindings(child))
    return result


def verify_task_bindings(task: dict) -> None:
    if task.get("format") != TASK_FORMAT or task.get("generated_by") != TASK_GENERATOR:
        raise ContractError(
            "Stale or unrecognized agent task; prepare it again with "
            "v2/scripts/create_entry.py"
        )
    for item in task_bindings(task):
        path = Path(item["path"])
        if not path.is_absolute():
            path = resolve_project_path(item["path"])
        else:
            path = path.resolve()
        if not path.is_file():
            raise ContractError(f"Task input is missing: {path}")
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise ContractError(
                f"Task input digest mismatch for {path}: expected "
                f"{item['sha256']}, got {actual}"
            )


def validate_fragment(value: dict, role: str, path: Path) -> None:
    schema = load_json(FRAGMENT_SCHEMAS[role])
    errors = structural_errors(value, schema, schema)
    if errors:
        raise ContractError(
            f"Invalid {role} response in {path}:\n- " + "\n- ".join(errors)
        )


def load_task_fragment(
    task_path: Path,
    fragment_path: Path,
    role: str,
) -> tuple[dict, dict]:
    if not task_path.is_file():
        raise ContractError(f"Missing {role} task: {task_path}")
    if not fragment_path.is_file():
        raise ContractError(f"Missing {role} fragment: {fragment_path}")
    task = load_json(task_path)
    verify_task_bindings(task)
    if task.get("role") != role:
        raise ContractError(
            f"{task_path}: expected role {role!r}, got {task.get('role')!r}"
        )
    stored = load_json(fragment_path)
    if not isinstance(stored, dict) or "inputs_sha256" not in stored:
        raise ContractError(f"{fragment_path}: missing coordinator inputs_sha256")
    expected_hash = canonical_sha256(task)
    if stored["inputs_sha256"] != expected_hash:
        raise ContractError(
            f"{fragment_path}: stale task hash; expected {expected_hash}, "
            f"got {stored['inputs_sha256']}"
        )
    if role == "root_writer":
        validate_enriched_root_writer_response(stored, task, fragment_path)
    response = (
        authored_root_writer_response(stored)
        if role == "root_writer"
        else dict(stored)
    )
    response.pop("inputs_sha256", None)
    validate_fragment(response, role, fragment_path)
    return task, response


def load_evidence(index_path: Path) -> tuple[dict, list[tuple[dict, dict, Path]]]:
    if not index_path.is_file():
        raise ContractError(f"Missing branch evidence index: {index_path}")
    index = load_json(index_path)
    if index.get("generated_by") != "v2/scripts/build_branch_evidence.py":
        raise ContractError(f"Unrecognized branch evidence index: {index_path}")
    index_relative = project_relative(index_path)
    expected_index = (
        f"v2/output/branch_evidence/{index.get('root_envelope_id', '')}/index.json"
    )
    if index_relative != expected_index:
        raise ContractError(
            f"Branch evidence index must use canonical path {expected_index}: "
            f"{index_path}"
        )
    packet_path = resolve_project_path(index["packet_path"])
    furuq_path = resolve_project_path(index["furuq_path"])
    qnet_path = resolve_project_path(index["qnet_path"])
    qnet_theme_path = resolve_project_path(index["qnet_theme_path"])
    qnet_fix_manifest_path = resolve_project_path(index["qnet_fix_manifest_path"])
    for label, path, expected in (
        ("packet", packet_path, index["packet_sha256"]),
        ("Furuq database", furuq_path, index["furuq_sha256"]),
        ("QNet incidence database", qnet_path, index["qnet_sha256"]),
        ("QNet theme database", qnet_theme_path, index["qnet_theme_sha256"]),
        (
            "QNet post-fix manifest",
            qnet_fix_manifest_path,
            index["qnet_fix_manifest_sha256"],
        ),
    ):
        if not path.is_file():
            raise ContractError(f"Missing {label}: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise ContractError(
                f"{label} digest mismatch: expected {expected}, got {actual}"
            )

    packages: list[tuple[dict, dict, Path]] = []
    seen: set[tuple[str, str]] = set()
    for row in index["branches"]:
        key = (row["root_id"], row["branch_id"])
        if key in seen:
            raise ContractError(f"Duplicate branch in evidence index: {key}")
        seen.add(key)
        package_path = (index_path.parent / row["path"]).resolve()
        try:
            package_path.relative_to(index_path.parent.resolve())
        except ValueError as error:
            raise ContractError(f"Evidence package escapes index directory: {row['path']}") from error
        if not package_path.is_file():
            raise ContractError(f"Missing branch evidence package: {package_path}")
        actual = sha256_file(package_path)
        if actual != row["sha256"]:
            raise ContractError(
                f"Branch evidence digest mismatch for {key}: expected "
                f"{row['sha256']}, got {actual}"
            )
        package = load_json(package_path)
        branch = package.get("branch", {})
        if (branch.get("root_id"), branch.get("branch_id")) != key:
            raise ContractError(f"Branch identity mismatch in {package_path}")
        if branch.get("status") != "accepted" or branch.get("contaminated") != "no":
            raise ContractError(
                "needs_evidence: focus branch is not accepted and uncontaminated: "
                f"{key[0]}/{key[1]}"
            )
        if package.get("packet_sha256") != index["packet_sha256"]:
            raise ContractError(f"Packet digest mismatch in {package_path}")
        if package.get("qnet_sha256") != index["qnet_sha256"]:
            raise ContractError(f"QNet digest mismatch in {package_path}")
        if package.get("qnet_theme_sha256") != index["qnet_theme_sha256"]:
            raise ContractError(f"QNet theme digest mismatch in {package_path}")
        if package.get("qnet_fix_manifest_sha256") != index[
            "qnet_fix_manifest_sha256"
        ]:
            raise ContractError(f"QNet post-fix digest mismatch in {package_path}")
        if package.get("furuq_sha256") != index["furuq_sha256"]:
            raise ContractError(f"Furuq digest mismatch in {package_path}")
        packages.append((row, package, package_path))
    return index, packages


def mechanical_occurrence_evidence(index: dict, language: str) -> dict:
    """Load and bind the deterministic occurrence and attachment layer."""
    envelope = index["root_envelope_id"]
    occurrence_path = f"v2/output/occurrences/{envelope}.{language}.md"
    occurrence_file = resolve_project_path(occurrence_path)
    if not occurrence_file.is_file():
        raise ContractError(f"Missing occurrence artifact: {occurrence_file}")
    alignment_path = f"v2/output/alignments/{envelope}.json"
    alignment_file = resolve_project_path(alignment_path)
    if not alignment_file.is_file():
        raise ContractError(f"Missing attachment alignment: {alignment_file}")
    packet = load_json(resolve_project_path(index["packet_path"]))
    alignment = load_json(alignment_file)
    return {
        "artifact_path": occurrence_path,
        "artifact_sha256": sha256_file(occurrence_file),
        "generator": "v2/scripts/render_occurrences.py",
        "alignment_path": alignment_path,
        "alignment_sha256": sha256_file(alignment_file),
        "alignment_generator": "v2/scripts/render_occurrences.py",
        "observations": [],
        **structured_occurrence_data(packet, alignment),
    }


def enrich_root_writer_response(response: dict, task: dict) -> dict:
    """Mechanically add Arabic, source, occurrence, and attachment evidence."""
    coordinator = task.get("coordinator", {})
    index_binding = coordinator.get("evidence_index", {})
    index_value = index_binding.get("path")
    if not isinstance(index_value, str):
        raise ContractError("Root-writer task lacks coordinator evidence index")
    index_path = resolve_project_path(index_value)
    index, package_rows = load_evidence(index_path)
    envelope = task["root_envelope_id"]
    language = task["language"]
    if index["root_envelope_id"] != envelope:
        raise ContractError("Root-writer evidence index identity mismatch")
    if index_binding != {
        "path": project_relative(index_path),
        "sha256": sha256_file(index_path),
    }:
        raise ContractError("Root-writer evidence-index binding mismatch")

    packages = {
        branch_ref(row["root_id"], row["branch_id"]): package
        for row, package, _path in package_rows
    }
    enriched_branches = []
    for authored in response["branches"]:
        ref = authored["branch_ref"]
        package = packages.get(ref)
        if package is None:
            raise ContractError(f"Root-writer branch lacks evidence package: {ref}")
        focus = package["branch"]
        basis = package["dictionary_basis"]
        units = {
            unit["lexical_unit_id"]: unit
            for unit in package.get("lexical_units", [])
        }

        def claim_refs(claim_ids: list[str]) -> list[str]:
            return sorted(
                {
                    source_ref
                    for claim_id in claim_ids
                    for source_ref in split_refs(units[claim_id].get("source_refs", ""))
                }
            )

        synthesis = authored["source_synthesis"]
        source_note_parts: dict[str, list[str]] = {}
        for detail in synthesis["source_details"]:
            refs = claim_refs(detail["claim_ids"])
            for source_id in dictionary_source_ids(basis, refs):
                code = DICTIONARY_CODES.get(source_id)
                if code is None:
                    raise ContractError(
                        f"No stable dictionary code is defined for {source_id!r}"
                    )
                source_note_parts.setdefault(code, []).append(detail["summary"].strip())
        sources = []
        for source in basis["sources"]:
            code = DICTIONARY_CODES.get(source["source_id"])
            if code is None:
                raise ContractError(
                    f"No stable dictionary code is defined for {source['source_id']!r}"
                )
            sources.append(code)
        enriched_branches.append(
            {
                **authored,
                "branch_image_ar": focus["branch_image_ar"],
                "what_is_ar": focus["what_is_ar"],
                "source_phrase_ar": focus["source_phrase_ar"],
                "sources": sources,
                "source_note": {
                    code: " ".join(parts) for code, parts in source_note_parts.items()
                },
            }
        )
    return {
        "artifact_format": ROOT_ENTRY_ARTIFACT_FORMAT,
        "generated_by": ROOT_ENTRY_ARTIFACT_GENERATOR,
        "root_envelope_id": envelope,
        "language": language,
        "branches": enriched_branches,
        "root_profile": response["root_profile"],
        "occurrence_evidence": {
            key: value
            for key, value in mechanical_occurrence_evidence(index, language).items()
            if key in {"summary", "forms", "ayahs", "occurrences"}
        },
    }


def validate_enriched_root_writer_response(value: dict, task: dict, path: Path) -> None:
    """Reject stale or edited coordinator-owned fields in an accepted entry."""
    if value.get("artifact_format") != ROOT_ENTRY_ARTIFACT_FORMAT:
        return
    expected = {
        "inputs_sha256": canonical_sha256(task),
        **enrich_root_writer_response(authored_root_writer_response(value), task),
    }
    if value != expected:
        raise ContractError(
            f"{path}: coordinator-owned Arabic, source, occurrence, or attachment "
            "fields are stale or modified"
        )


def assert_task_identity(
    task: dict,
    *,
    role: str,
    envelope: str,
    language: str,
    root_id: str | None = None,
    branch_id: str | None = None,
) -> None:
    expected = {
        "format": TASK_FORMAT,
        "generated_by": TASK_GENERATOR,
        "role": role,
        "root_envelope_id": envelope,
        "language": language,
    }
    if root_id is not None:
        expected["root_id"] = root_id
    if branch_id is not None:
        expected["branch_id"] = branch_id
    for key, value in expected.items():
        if task.get(key) != value:
            raise ContractError(
                f"Task identity {key}: expected {value!r}, got {task.get(key)!r}"
            )


def branch_from_fragment(package: dict, fragment: dict, path: str) -> dict:
    branch = package["branch"]
    key = (branch["root_id"], branch["branch_id"])
    actual_key = (fragment["root_id"], fragment["branch_id"])
    if actual_key != key:
        raise ContractError(
            f"Branch fragment identity mismatch: expected {key}, got {actual_key}"
        )

    basis = package["dictionary_basis"]
    candidate_by_key = {
        (row["root_id"], row["branch_id"]): row
        for row in package["furuq_candidates"]
    }
    for neighbor in fragment["arabic_neighbor_distinctions"]:
        neighbor_key = (
            neighbor["neighbor_root_id"],
            neighbor["neighbor_branch_id"],
        )
        if neighbor_key not in candidate_by_key:
            raise ContractError(
                f"{path}.arabic_neighbor_distinctions: neighbor "
                f"{neighbor_key[0]}/{neighbor_key[1]} is absent "
                "from the branch evidence package"
            )
    coverage = fragment["neighbor_coverage"]
    selected_neighbor_count = len(fragment["arabic_neighbor_distinctions"])
    if selected_neighbor_count == 0 and coverage["assessment"] != "none_useful":
        raise ContractError(
            f"{path}.neighbor_coverage: zero selected neighbors must be assessed "
            "as none_useful"
        )
    if selected_neighbor_count > 0 and coverage["assessment"] == "none_useful":
        raise ContractError(
            f"{path}.neighbor_coverage: none_useful requires zero selected neighbors"
        )
    if selected_neighbor_count == 1 and coverage["assessment"] == "complete":
        raise ContractError(
            f"{path}.neighbor_coverage: one selected neighbor must be assessed as "
            "single_sufficient or legacy_minimum_unverified"
        )
    if selected_neighbor_count > 1 and coverage["assessment"] == "single_sufficient":
        raise ContractError(
            f"{path}.neighbor_coverage: single_sufficient requires exactly one neighbor"
        )
    sources = [
        {
            "source_id": source["source_id"],
            "dictionary_name": source["dictionary_name"],
            "source_refs": source["source_refs"],
        }
        for source in basis["sources"]
    ]
    units = {
        unit["lexical_unit_id"]: unit for unit in package.get("lexical_units", [])
    }
    lexical_glosses = {
        row["lexical_unit_id"]: row for row in fragment["lexical_glosses"]
    }

    def claim_refs(claim_ids: list[str]) -> list[str]:
        refs = {
            source_ref
            for claim_id in claim_ids
            for source_ref in split_refs(units[claim_id].get("source_refs", ""))
        }
        return sorted(refs)

    synthesis = fragment["source_synthesis"]
    source_details = [
        {
            "kind": detail["kind"],
            "summary": detail["summary"],
            "source_refs": claim_refs(detail["claim_ids"]),
            "source_ids": dictionary_source_ids(
                basis, claim_refs(detail["claim_ids"])
            ),
        }
        for detail in synthesis["source_details"]
    ]
    disputed_details = [
        detail for detail in source_details if detail["kind"] == "disagreement"
    ]
    disagreement = None
    if disputed_details:
        disagreement = {
            "summary": " ".join(detail["summary"] for detail in disputed_details),
            "source_refs": sorted(
                {
                    source_ref
                    for detail in disputed_details
                    for source_ref in detail["source_refs"]
                }
            ),
        }
    usage_notes = [
        {
            "kind": "constraint",
            "statement": detail["summary"],
            "evidence_refs": detail["source_refs"],
        }
        for detail in source_details
        if detail["kind"] == "restriction"
    ]
    evidence_qualifiers = [
        {
            "type": "disputed",
            "statement": detail["summary"],
            "source_refs": detail["source_refs"],
        }
        for detail in disputed_details
    ]
    return {
        "root_id": branch["root_id"],
        "branch_id": branch["branch_id"],
        "branch_image_ar": branch["branch_image_ar"],
        "what_is_ar": branch["what_is_ar"],
        "what_is_not_ar": branch["what_is_not_ar"],
        "source_phrase_ar": branch["source_phrase_ar"],
        "image_transliteration": fragment["image_transliteration"],
        "summary": fragment["summary"],
        "concept_map": fragment["concept_map"],
        "lexical_realizations": [
            {
                "lexical_unit_id": unit["lexical_unit_id"],
                "expression_ar": unit["expression_ar"],
                "unit_kind": unit["unit_kind"],
                "sense_ar": unit["sense_ar"],
                "target_gloss": lexical_glosses[unit["lexical_unit_id"]][
                    "target_gloss"
                ],
                "target_rendering_kind": lexical_glosses[unit["lexical_unit_id"]][
                    "rendering_kind"
                ],
                "evidence_refs": split_refs(unit.get("source_refs", "")),
                "quran_form": (
                    {
                        "stem_ar": unit["resolved_quran_stem_ar"],
                        "tag": unit["resolved_quran_tag"],
                    }
                    if unit.get("resolved_quran_stem_ar")
                    and unit.get("resolved_quran_tag")
                    else None
                ),
            }
            for unit in package.get("lexical_units", [])
        ],
        "usage_notes": usage_notes,
        "evidence_qualifiers": evidence_qualifiers,
        "source_discussion": {
            "discussion": synthesis["common_summary"],
            "evidence_refs": claim_refs(synthesis["common_claim_ids"]),
            "details": source_details,
            "examples": [],
            "disagreement": disagreement,
        },
        "dictionary_basis": {
            "dictionary_count": basis["dictionary_count"],
            "passage_count": basis["passage_count"],
            "sources": sources,
        },
        "glosses": fragment["glosses"],
        "arabic_neighbor_distinctions": [
            {
                **neighbor,
                "expression_ar": candidate_by_key[
                    (neighbor["neighbor_root_id"], neighbor["neighbor_branch_id"])
                ]["branch_image_ar"],
                "basis": "furuq_branch_comparison",
                "evidence_refs": split_refs(
                    candidate_by_key[
                        (neighbor["neighbor_root_id"], neighbor["neighbor_branch_id"])
                    ]["source_refs"]
                ),
            }
            for neighbor in fragment["arabic_neighbor_distinctions"]
        ],
        "neighbor_coverage": {
            "candidate_count": len(package["furuq_candidates"]),
            "assessment": coverage["assessment"],
            "note": coverage["note"],
        },
    }


def _excluded_reason(error_profile: dict) -> str:
    parts = [
        error_profile[field].strip()
        for field in ("loses", "adds", "collision")
        if isinstance(error_profile.get(field), str) and error_profile[field].strip()
    ]
    return " ".join(parts) or error_profile["preserves"]


NAME_TOKEN_RE = re.compile(r"\{\{(lu_[0-9]+)\}\}")


def _approved_name_review(
    path: Path,
    *,
    envelope: str,
    language: str,
) -> tuple[dict[str, str], dict[str, dict]]:
    if not path.is_file():
        return {}, {}
    review = load_json(path)
    if review.get("format") != "dictionary-v2-name-review-v1":
        raise ContractError(f"Unrecognized name review file: {path}")
    if review.get("root_envelope_id") != envelope or review.get("language") != language:
        raise ContractError(f"Name review identity mismatch: {path}")
    approved: dict[str, str] = {}
    existing: dict[str, dict] = {}
    for item in review.get("items", []):
        key = item.get("key")
        if not isinstance(key, str) or key in existing:
            raise ContractError(f"Invalid or duplicate name review key: {key!r}")
        existing[key] = item
        if item.get("status") != "approved":
            continue
        value = item.get("value")
        if not isinstance(value, str) or len(value.strip()) < 2:
            raise ContractError(f"Approved name form lacks a value for {key}")
        if any("\u0600" <= character <= "\u06ff" for character in value):
            raise ContractError(f"Approved name form contains Arabic script for {key}")
        approved[key] = value.strip()
    return approved, existing


def _write_name_review_queue(
    path: Path,
    *,
    envelope: str,
    language: str,
    required: dict[str, str],
    existing: dict[str, dict],
) -> None:
    items = []
    for key, arabic in sorted(required.items()):
        previous = existing.get(key, {})
        items.append(
            {
                "key": key,
                "arabic": arabic,
                "status": previous.get("status", "pending"),
                "value": previous.get("value", ""),
            }
        )
    value = {
        "format": "dictionary-v2-name-review-v1",
        "root_envelope_id": envelope,
        "language": language,
        "instructions": (
            "Root writer completion queue: approve the target-language surface "
            "form for each protected proper name. These values replace writer "
            "placeholders mechanically."
        ),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(json_content(value))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _approved_transliteration_review(
    path: Path,
    *,
    envelope: str,
    language: str,
) -> tuple[dict[str, str], dict[str, dict]]:
    if not path.is_file():
        return {}, {}
    review = load_json(path)
    if review.get("format") != "dictionary-v2-transliteration-review-v1":
        raise ContractError(f"Unrecognized transliteration review file: {path}")
    if review.get("root_envelope_id") != envelope or review.get("language") != language:
        raise ContractError(f"Transliteration review identity mismatch: {path}")
    approved: dict[str, str] = {}
    existing: dict[str, dict] = {}
    for item in review.get("items", []):
        key = item.get("key")
        if not isinstance(key, str) or key in existing:
            raise ContractError(f"Invalid or duplicate transliteration review key: {key!r}")
        existing[key] = item
        if item.get("status") != "approved":
            continue
        value = item.get("value")
        if not isinstance(value, str) or len(value.strip()) < 2:
            raise ContractError(f"Approved transliteration lacks a value for {key}")
        if any("\u0600" <= character <= "\u06ff" for character in value):
            raise ContractError(f"Approved transliteration contains Arabic script for {key}")
        approved[key] = value.strip()
    return approved, existing


def _write_transliteration_review_queue(
    path: Path,
    *,
    envelope: str,
    language: str,
    missing: list[str],
    transliterations: dict,
    existing: dict[str, dict],
) -> None:
    anchors = {
        item["key"]: item["arabic"] for item in transliterations.get("gaps", [])
    }
    suggestions = transliterations.get("suggestions", {})
    items = []
    for key in missing:
        previous = existing.get(key, {})
        items.append(
            {
                "key": key,
                "arabic": anchors.get(key, previous.get("arabic", "")),
                "suggested_value": suggestions.get(
                    key, previous.get("suggested_value", "")
                ),
                "status": previous.get("status", "pending"),
                "value": previous.get("value", ""),
            }
        )
    value = {
        "format": "dictionary-v2-transliteration-review-v1",
        "root_envelope_id": envelope,
        "language": language,
        "instructions": (
            "Root writer completion queue: review only these used Arabic anchors. "
            "Set status to approved and supply value; rerunning finalization "
            "reuses the accepted root-writer response."
        ),
        "items": items,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(json_content(value))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def expand_root_writer_response(
    response: dict,
    packages: list[dict],
    transliterations: dict,
    language: str,
    envelope: str,
    transliteration_review_path: Path,
    name_review_path: Path,
) -> tuple[list[dict], dict]:
    """Restore coordinator-owned fields around a reduced root-writer response."""
    expected_refs = [
        branch_ref(package["branch"]["root_id"], package["branch"]["branch_id"])
        for package in packages
    ]
    authored = response["branches"]
    authored_refs = [row["branch_ref"] for row in authored]
    if authored_refs != expected_refs:
        raise ContractError(
            "root_writer: branch roster must match task order exactly: "
            f"expected {expected_refs}, got {authored_refs}"
        )

    values = dict(transliterations.get("values", {}))
    approved, existing_review = _approved_transliteration_review(
        transliteration_review_path,
        envelope=envelope,
        language=language,
    )
    gap_anchors = {
        item["key"]: item["arabic"] for item in transliterations.get("gaps", [])
    }
    for key in approved:
        if key not in gap_anchors or existing_review[key].get("arabic") != gap_anchors[key]:
            raise ContractError(
                f"Stale transliteration review anchor for {key}: "
                f"{transliteration_review_path}"
            )
    values.update(approved)

    approved_names, existing_name_review = _approved_name_review(
        name_review_path,
        envelope=envelope,
        language=language,
    )

    required_transliterations = {"root_profile"}
    selected_by_branch: list[list[tuple[str, dict]]] = []
    for package, row in zip(packages, authored):
        focus_ref = row["branch_ref"]
        required_transliterations.add(f"branch:{focus_ref}")
        candidates = {
            branch_ref(candidate["root_id"], candidate["branch_id"]): candidate
            for candidate in package["furuq_candidates"]
        }
        selected = []
        for distinction in row["neighbor_distinctions"]:
            ref = distinction["neighbor_ref"]
            if ref not in candidates:
                raise ContractError(
                    f"root_writer: {focus_ref} selected absent neighbor {ref}"
                )
            required_transliterations.add(f"neighbor:{ref}")
            selected.append((ref, candidates[ref]))
        selected_by_branch.append(selected)

    required_names: dict[str, str] = {}
    name_tokens: dict[str, str] = {}
    for package, row in zip(packages, authored):
        units = {
            unit["lexical_unit_id"]: unit for unit in package.get("lexical_units", [])
        }
        for lexical in row["lexical_glosses"]:
            if lexical["rendering_kind"] != "proper_name":
                continue
            lexical_id = lexical["lexical_unit_id"]
            key = f"name:{row['branch_ref']}:{lexical_id}"
            required_names[key] = units[lexical_id]["expression_ar"]
            reviewed = existing_name_review.get(key)
            if key in approved_names and (
                reviewed is None or reviewed.get("arabic") != required_names[key]
            ):
                raise ContractError(f"Stale name review anchor for {key}: {name_review_path}")
            if key in approved_names:
                existing_value = name_tokens.get(lexical_id)
                if existing_value is not None and existing_value != approved_names[key]:
                    raise ContractError(
                        f"Conflicting reviewed name forms for placeholder {lexical_id}"
                    )
                name_tokens[lexical_id] = approved_names[key]

    missing = sorted(required_transliterations - set(values))
    missing_names = sorted(set(required_names) - set(approved_names))
    pending = []
    if missing:
        _write_transliteration_review_queue(
            transliteration_review_path,
            envelope=envelope,
            language=language,
            missing=missing,
            transliterations=transliterations,
            existing=existing_review,
        )
        pending.append(
            "needs_transliteration_review: writer must complete used anchors in "
            f"{transliteration_review_path}: {missing}"
        )
    if missing_names:
        _write_name_review_queue(
            name_review_path,
            envelope=envelope,
            language=language,
            required=required_names,
            existing=existing_name_review,
        )
        pending.append(
            "needs_name_review: writer must complete protected forms in "
            f"{name_review_path}: {missing_names}"
        )
    if pending:
        raise ContractError("; ".join(pending))

    def transliteration(key: str) -> str:
        value = values.get(key)
        if not isinstance(value, str) or len(value.strip()) < 2:
            raise ContractError(f"Missing reviewed transliteration for {key}")
        return value.strip()

    def substitute_names(value: str) -> str:
        def replacement(match: re.Match[str]) -> str:
            lexical_id = match.group(1)
            if lexical_id not in name_tokens:
                raise ContractError(
                    f"Unresolved or undeclared protected-name token {match.group(0)}"
                )
            return name_tokens[lexical_id]

        return NAME_TOKEN_RE.sub(replacement, value)

    fragments = []
    for package, row, selected in zip(packages, authored, selected_by_branch):
        focus = package["branch"]
        focus_ref = row["branch_ref"]
        concept = row["concept_gloss"]
        selected_glosses = [
            {
                "rank": 1,
                "text": substitute_names(concept["text"]),
                "loanword_status": "none",
                "usage_role": "explanatory",
                "selection_role": "primary_concept_gloss",
                "applicability": substitute_names(concept["applicability"]),
                "facet_ids": concept["facet_ids"],
                "error_profile": {
                    key: substitute_names(value) if isinstance(value, str) else value
                    for key, value in concept["error_profile"].items()
                },
            }
        ]
        for rank, gloss in enumerate(row["contextual_glosses"], start=2):
            selected_glosses.append(
                {
                    "rank": rank,
                    "text": substitute_names(gloss["text"]),
                    "loanword_status": "none",
                    "usage_role": gloss["usage_role"],
                    "selection_role": "contextual_gloss",
                    "applicability": substitute_names(gloss["applicability"]),
                    "facet_ids": gloss["facet_ids"],
                    "error_profile": {
                        key: substitute_names(value) if isinstance(value, str) else value
                        for key, value in gloss["error_profile"].items()
                    },
                }
            )
        excluded_glosses = []
        for gloss in row["excluded_glosses"]:
            error_profile = {
                key: substitute_names(value) if isinstance(value, str) else value
                for key, value in gloss["error_profile"].items()
            }
            excluded_glosses.append(
                {
                    "text": substitute_names(gloss["text"]),
                    "category": gloss["category"],
                    "exclusion_reason": _excluded_reason(error_profile),
                    "error_profile": error_profile,
                }
            )

        distinctions = []
        for authored_distinction, (neighbor_ref, _candidate) in zip(
            row["neighbor_distinctions"], selected
        ):
            neighbor_root_id, neighbor_branch_id = neighbor_ref.split("/", 1)
            distinctions.append(
                {
                    "neighbor_root_id": neighbor_root_id,
                    "neighbor_branch_id": neighbor_branch_id,
                    "relation_type": authored_distinction["relation_type"],
                    "boundary_match": authored_distinction["boundary_match"],
                    "focus_only": (
                        substitute_names(authored_distinction["focus_only"])
                        if authored_distinction["focus_only"] is not None
                        else None
                    ),
                    "neighbor_only": (
                        substitute_names(authored_distinction["neighbor_only"])
                        if authored_distinction["neighbor_only"] is not None
                        else None
                    ),
                    "expression_transliteration": transliteration(
                        f"neighbor:{neighbor_ref}"
                    ),
                    "gloss": substitute_names(authored_distinction["gloss"]),
                    "shared_zone": substitute_names(authored_distinction["shared_zone"]),
                    "distinction": substitute_names(authored_distinction["distinction"]),
                }
            )

        concept_map = {
            "definition": substitute_names(row["concept_map"]["definition"]),
            "facets": [
                {
                    **facet,
                    "statement": substitute_names(facet["statement"]),
                }
                for facet in row["concept_map"]["facets"]
            ],
        }
        source_synthesis = {
            **row["source_synthesis"],
            "common_summary": substitute_names(
                row["source_synthesis"]["common_summary"]
            ),
            "source_details": [
                {
                    **detail,
                    "summary": substitute_names(detail["summary"]),
                }
                for detail in row["source_synthesis"]["source_details"]
            ],
        }
        lexical_glosses = []
        for lexical in row["lexical_glosses"]:
            lexical_glosses.append(
                {
                    "lexical_unit_id": lexical["lexical_unit_id"],
                    "rendering_kind": lexical["rendering_kind"],
                    "target_gloss": (
                        name_tokens[lexical["lexical_unit_id"]]
                        if lexical["rendering_kind"] == "proper_name"
                        else substitute_names(lexical["target_gloss"])
                    ),
                }
            )
        semantic_definition = concept_map["definition"]
        fragment = {
            "root_id": focus["root_id"],
            "branch_id": focus["branch_id"],
            "language": language,
            "image_transliteration": transliteration(f"branch:{focus_ref}"),
            "summary": semantic_definition,
            "concept_map": concept_map,
            "source_summary": source_synthesis["common_summary"],
            "source_synthesis": source_synthesis,
            "usage_notes": [],
            "evidence_qualifiers": [],
            "lexical_glosses": lexical_glosses,
            "glosses": {
                "semantic_definition": semantic_definition,
                "concept": selected_glosses[0],
                "contextual": selected_glosses[1:],
                "selected": selected_glosses,
                "excluded": excluded_glosses,
            },
            "arabic_neighbor_distinctions": distinctions,
            "neighbor_coverage": {
                "assessment": (
                    "none_useful"
                    if not distinctions
                    else "single_sufficient"
                    if len(distinctions) == 1
                    else "complete"
                ),
                "note": row["neighbor_coverage_note"],
            },
        }
        validate_fragment(fragment, "branch_writer", Path(focus_ref))
        fragments.append(fragment)

    root_profile = {
        "root_envelope_id": envelope,
        "language": language,
        "root_profile": {
            "transliteration": transliteration("root_profile"),
            "summary": response["root_profile"]["summary"],
            "polysemy": response["root_profile"]["polysemy"],
            "organization": response["root_profile"]["organization"],
            "branch_count": len(packages),
            "collocation_weight": "unknown",
            "collocation_note": (
                "Kur'an eşdizim verileri mekanik oluşum katmanında tutulur."
                if language == "tr"
                else "Quran collocation data is retained in the mechanical occurrence layer."
            ),
        },
    }
    validate_fragment(root_profile, "root_profile_writer", Path(envelope))
    return fragments, root_profile


def _root_writer_material(
    evidence_index: Path,
    work_dir: Path,
    language: str,
) -> tuple[dict, list[tuple[dict, dict, Path]], dict, list[dict], dict]:
    index, packages = load_evidence(evidence_index.resolve())
    envelope = index["root_envelope_id"]
    task_path = work_dir / "tasks/root_writer.json"
    response_path = work_dir / "fragments" / root_entry_filename(envelope)
    task, response = load_task_fragment(task_path, response_path, "root_writer")
    assert_task_identity(
        task,
        role="root_writer",
        envelope=envelope,
        language=language,
    )
    package_values = [package for _row, package, _path in packages]
    transliteration_path = work_dir / "inputs/transliterations.json"
    root_evidence_path = work_dir / "inputs/root_evidence.json"
    if not transliteration_path.is_file():
        raise ContractError(f"Missing coordinator transliterations: {transliteration_path}")
    transliterations = load_json(transliteration_path)
    if transliterations.get("format") != "dictionary-v2-transliteration-inputs-v1":
        raise ContractError(f"Unrecognized coordinator transliterations: {transliteration_path}")
    if (
        transliterations.get("root_envelope_id") != envelope
        or transliterations.get("language") != language
    ):
        raise ContractError(f"Coordinator transliteration identity mismatch: {transliteration_path}")
    coordinator = task.get("coordinator", {})
    name_policy_binding = coordinator.get("name_policy", {})
    name_policy_value = name_policy_binding.get("path")
    if not isinstance(name_policy_value, str):
        raise ContractError(f"Missing coordinator name-policy binding: {task_path}")
    name_policy_path = resolve_project_path(name_policy_value)
    rendering_policy = load_rendering_policy(
        name_policy_path, envelope, package_values
    )
    expected_evidence = agent_root_evidence(package_values, rendering_policy)
    if not root_evidence_path.is_file() or load_json(root_evidence_path) != expected_evidence:
        raise ContractError(f"Stale minimal root evidence: {root_evidence_path}")
    if task.get("evidence") != {
        "path": project_relative(root_evidence_path),
        "sha256": sha256_file(root_evidence_path),
    }:
        raise ContractError(f"Root-writer evidence binding mismatch: {task_path}")
    if coordinator.get("evidence_index") != {
        "path": project_relative(evidence_index.resolve()),
        "sha256": sha256_file(evidence_index.resolve()),
    }:
        raise ContractError(f"Coordinator evidence-index binding mismatch: {task_path}")
    if task.get("branch_roster") != [
        branch_ref(row["root_id"], row["branch_id"]) for row, _package, _path in packages
    ]:
        raise ContractError(f"Root-writer task branch roster mismatch: {task_path}")
    fragments, root_profile = expand_root_writer_response(
        response,
        package_values,
        transliterations,
        language,
        envelope,
        work_dir / "inputs/transliteration_review.json",
        work_dir / "inputs/name_review.json",
    )
    return index, packages, task, fragments, root_profile


def _write_split_values(
    packages: list[tuple[dict, dict, Path]],
    task: dict,
    fragments: list[dict],
    root_profile: dict,
    work_dir: Path,
    *,
    check: bool,
) -> None:
    task_hash = canonical_sha256(task)
    outputs = []
    for (row, _package, _path), fragment in zip(packages, fragments):
        stem = f"{row['root_id']}--{row['branch_id']}"
        outputs.append(
            (
                work_dir / "fragments/branches" / f"{stem}.json",
                {"root_inputs_sha256": task_hash, **fragment},
            )
        )
    outputs.append(
        (
            work_dir / "fragments/root_profile.json",
            {"root_inputs_sha256": task_hash, **root_profile},
        )
    )
    for path, value in outputs:
        content = json_content(value)
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise ContractError(f"Stale root-writer split fragment: {path}")
        else:
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


def write_root_writer_splits(
    evidence_index: Path,
    work_dir: Path,
    language: str,
    *,
    check: bool = False,
) -> None:
    _index, packages, task, fragments, root_profile = _root_writer_material(
        evidence_index, work_dir, language
    )
    _write_split_values(
        packages,
        task,
        fragments,
        root_profile,
        work_dir,
        check=check,
    )


def build_entry(
    evidence_index: Path,
    work_dir: Path,
    language: str,
    *,
    check_splits: bool = False,
) -> tuple[dict, dict]:
    index, packages, task, fragments, root = _root_writer_material(
        evidence_index, work_dir, language
    )
    _write_split_values(
        packages,
        task,
        fragments,
        root,
        work_dir,
        check=check_splits,
    )
    envelope = index["root_envelope_id"]
    branches = []
    for (_row, package, _package_path), fragment in zip(packages, fragments):
        branches.append(
            branch_from_fragment(
                package,
                fragment,
                f"$.branches[{len(branches)}]",
            )
        )

    entry = {
        "schema_version": 4,
        "generated_by": "v2/scripts/assemble_entry.py",
        "entry_id": f"{envelope}/{language}",
        "language": language,
        "status": "draft",
        "root_envelope_id": envelope,
        "root_ids": index["root_ids"],
        "provenance": {
            "packet_path": index["packet_path"],
            "packet_sha256": index["packet_sha256"],
            "evidence_index_path": project_relative(evidence_index.resolve()),
            "evidence_index_sha256": sha256_file(evidence_index.resolve()),
            "furuq_path": index["furuq_path"],
            "furuq_sha256": index["furuq_sha256"],
            "root_task_sha256": canonical_sha256(task),
        },
        "root_profile": root["root_profile"],
        "branches": branches,
        "occurrence_evidence": mechanical_occurrence_evidence(index, language),
    }
    return entry, index


def write_validated_entry(
    entry: dict,
    index: dict,
    output_path: Path,
    *,
    check: bool,
    force: bool,
) -> None:
    content = json_content(entry)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", dir=output_path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        validate_entry(temporary)
        if check:
            if not output_path.is_file():
                raise ContractError(f"Missing assembled entry: {output_path}")
            if output_path.read_text(encoding="utf-8") != content:
                raise ContractError(f"Stale assembled entry: {output_path}")
            return
        if output_path.exists() and not force:
            raise ContractError(
                f"Refusing to replace existing entry without --force: {output_path}"
            )
        os.replace(temporary, output_path)
    finally:
        if temporary.exists():
            temporary.unlink()


def assemble(
    evidence_index: Path,
    work_dir: Path,
    language: str,
    output_path: Path,
    *,
    check: bool = False,
    force: bool = False,
) -> dict:
    entry, index = build_entry(
        evidence_index,
        work_dir,
        language,
        check_splits=check,
    )
    write_validated_entry(
        entry,
        index,
        output_path,
        check=check,
        force=force,
    )
    return entry


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root_envelope_id")
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--evidence-index", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
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
    output = args.output or PROJECT / "v2/entries" / args.language / f"{envelope}.json"
    try:
        entry = assemble(
            evidence_index.resolve(),
            work_dir.resolve(),
            args.language,
            output.resolve(),
            check=args.check,
            force=args.force,
        )
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {output} ({len(entry['branches'])} branches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
