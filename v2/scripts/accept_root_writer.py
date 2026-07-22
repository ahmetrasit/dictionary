#!/usr/bin/env python3
"""Validate and store a root-writer response returned to the orchestrator."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    authored_root_writer_response,
    canonical_sha256,
    enrich_root_writer_response,
    root_entry_filename,
    validate_fragment,
)
from v2.scripts.create_entry import (
    atomic_write,
    binding_path,
    json_content,
    verify_task_bindings,
)
from v2.scripts.validate_entry import ContractError, load_json


def validate_identity(response: dict, task: dict) -> None:
    branches = response.get("branches")
    if not isinstance(branches, list):
        raise ContractError("root_writer: branches must be an array")
    actual = [row.get("branch_ref") for row in branches if isinstance(row, dict)]
    expected = task.get("branch_roster")
    if actual != expected:
        raise ContractError(
            f"root_writer: branch roster/order mismatch: expected {expected}, got {actual}"
        )


PLACEHOLDER_RE = re.compile(r"\{\{(lu_[0-9]+)\}\}")


def _validate_error_profile(profile: dict, path: str) -> None:
    fit = profile["fit"]
    if fit == "none" and (profile["loses"] is not None or profile["adds"] is not None):
        raise ContractError(f"{path}: fit none requires null loses and adds")
    if fit == "narrowing" and profile["loses"] is None:
        raise ContractError(f"{path}: narrowing requires a concrete loss")
    if fit == "broadening" and profile["adds"] is None:
        raise ContractError(f"{path}: broadening requires a concrete addition")


def _claim_coverage(source: dict) -> list[str]:
    result = list(source["common_claim_ids"])
    for detail in source["source_details"]:
        result.extend(detail["claim_ids"])
    result.extend(source["supporting_claim_ids"])
    result.extend(row["claim_id"] for row in source["duplicate_claims"])
    return result


def validate_semantic_contract(response: dict, task: dict) -> None:
    evidence = load_json(binding_path(task["evidence"]["path"]))
    evidence_by_ref = {row["branch_ref"]: row for row in evidence["branches"]}
    neighbor_refs = {row["neighbor_ref"] for row in evidence["neighbor_registry"]}
    for branch_index, branch in enumerate(response["branches"]):
        path = f"$.branches[{branch_index}]"
        branch_ref = branch["branch_ref"]
        supplied = evidence_by_ref[branch_ref]
        expected_claims = [row["claim_id"] for row in supplied["source_claims"]]
        expected_set = set(expected_claims)

        covered = _claim_coverage(branch["source_synthesis"])
        if len(covered) != len(set(covered)):
            raise ContractError(f"{path}.source_synthesis: a claim is dispositioned twice")
        if set(covered) != expected_set:
            raise ContractError(
                f"{path}.source_synthesis: claim coverage mismatch; "
                f"expected {expected_claims}, got {covered}"
            )
        for duplicate in branch["source_synthesis"]["duplicate_claims"]:
            if duplicate["merged_into"] not in expected_set:
                raise ContractError(
                    f"{path}.source_synthesis.duplicate_claims: invalid merge target"
                )
            if duplicate["claim_id"] == duplicate["merged_into"]:
                raise ContractError(
                    f"{path}.source_synthesis.duplicate_claims: claim cannot merge into itself"
                )

        facets = branch["concept_map"]["facets"]
        expected_facets = [f"F{index:03d}" for index in range(1, len(facets) + 1)]
        actual_facets = [row["facet_id"] for row in facets]
        if actual_facets != expected_facets:
            raise ContractError(
                f"{path}.concept_map.facets: expected sequential IDs {expected_facets}"
            )
        if not any(row["role"] == "core" for row in facets):
            raise ContractError(f"{path}.concept_map.facets: requires a core facet")
        for facet in facets:
            unknown = set(facet["claim_ids"]) - expected_set
            if unknown:
                raise ContractError(
                    f"{path}.concept_map.facets: unknown claim IDs {sorted(unknown)}"
                )
        facet_ids = set(actual_facets)
        glosses = [branch["concept_gloss"], *branch["contextual_glosses"]]
        for gloss_index, gloss in enumerate(glosses):
            unknown = set(gloss["facet_ids"]) - facet_ids
            if unknown:
                raise ContractError(
                    f"{path}.glosses[{gloss_index}]: unknown facet IDs {sorted(unknown)}"
                )
            _validate_error_profile(gloss["error_profile"], f"{path}.glosses[{gloss_index}]")
        for gloss_index, gloss in enumerate(branch["excluded_glosses"]):
            _validate_error_profile(
                gloss["error_profile"], f"{path}.excluded_glosses[{gloss_index}]"
            )
        selected_texts = [gloss["text"].casefold() for gloss in glosses]
        if len(selected_texts) != len(set(selected_texts)):
            raise ContractError(f"{path}: duplicate concept/contextual gloss")
        excluded_texts = {gloss["text"].casefold() for gloss in branch["excluded_glosses"]}
        if set(selected_texts) & excluded_texts:
            raise ContractError(f"{path}: a gloss cannot be both selected and excluded")

        lexical = branch["lexical_glosses"]
        actual_lexical = [row["lexical_unit_id"] for row in lexical]
        if actual_lexical != expected_claims:
            raise ContractError(
                f"{path}.lexical_glosses: expected exact lexical roster {expected_claims}"
            )
        rendering_policy = {
            row["lexical_unit_id"]: row["rendering_policy"]
            for row in supplied["source_claims"]
        }
        protected = {
            lexical_id
            for lexical_id, kind in rendering_policy.items()
            if kind == "proper_name"
        }
        for row in lexical:
            expected_kind = rendering_policy[row["lexical_unit_id"]]
            if row["rendering_kind"] != expected_kind:
                raise ContractError(
                    f"{path}.lexical_glosses: {row['lexical_unit_id']} must use "
                    f"coordinator rendering policy {expected_kind!r}, got "
                    f"{row['rendering_kind']!r}"
                )
            if row["rendering_kind"] == "proper_name":
                if row["target_gloss"] is not None:
                    raise ContractError(
                        f"{path}.lexical_glosses: proper name target_gloss must be null"
                    )
            elif row["target_gloss"] is None:
                raise ContractError(
                    f"{path}.lexical_glosses: ordinary target_gloss cannot be null"
                )
        authored_text = json.dumps(branch, ensure_ascii=False)
        placeholders = set(PLACEHOLDER_RE.findall(authored_text))
        if placeholders - protected:
            raise ContractError(
                f"{path}: placeholders are allowed only for declared proper names: "
                f"{sorted(placeholders - protected)}"
            )

        allowed_neighbors = set(supplied["neighbor_refs"])
        for relation_index, relation in enumerate(branch["neighbor_distinctions"]):
            relation_path = f"{path}.neighbor_distinctions[{relation_index}]"
            if relation["neighbor_ref"] not in allowed_neighbors:
                raise ContractError(f"{relation_path}: neighbor is outside supplied roster")
            if relation["neighbor_ref"] not in neighbor_refs:
                raise ContractError(f"{relation_path}: missing neighbor evidence card")
            relation_type = relation["relation_type"]
            match = relation["boundary_match"]
            asymmetry = relation["focus_only"] is not None or relation["neighbor_only"] is not None
            if match == "exact" and (relation_type != "synonym" or asymmetry):
                raise ContractError(
                    f"{relation_path}: exact boundary requires synonym and no asymmetry"
                )
            if relation_type == "synonym" and (match != "exact" or asymmetry):
                raise ContractError(
                    f"{relation_path}: synonym requires exact boundary and no asymmetry"
                )
            if relation_type == "near_synonym" and (match != "partial" or not asymmetry):
                raise ContractError(
                    f"{relation_path}: near_synonym requires partial boundary and asymmetry"
                )
            if relation_type in {"antonym", "polarity_pair"} and match != "opposed":
                raise ContractError(f"{relation_path}: opposed relation requires opposed boundary")
            if relation_type == "same_field" and match != "field_only":
                raise ContractError(f"{relation_path}: same_field requires field_only boundary")
            if relation_type == "thematic" and match != "thematic_only":
                raise ContractError(f"{relation_path}: thematic requires thematic_only boundary")


def validate_repair_preservation(
    previous: dict,
    candidate: dict,
    *,
    editable_branch_indexes: set[int],
    root_editable: bool,
) -> None:
    previous_branches = previous.get("branches", [])
    candidate_branches = candidate.get("branches", [])
    if len(previous_branches) != len(candidate_branches):
        raise ContractError("repair changed the branch roster")
    for index, (before, after) in enumerate(zip(previous_branches, candidate_branches)):
        if index not in editable_branch_indexes and before != after:
            raise ContractError(f"repair changed protected branch index {index}")
    if not root_editable and previous.get("root_profile") != candidate.get("root_profile"):
        raise ContractError("repair changed the protected root profile")


def response_body(path: Path) -> dict:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ContractError("root_writer: response must be a JSON object")
    return authored_root_writer_response(value)


def accept(
    task_path: Path,
    response_path: Path,
    output_path: Path,
    *,
    previous_path: Path | None = None,
    editable_branch_indexes: set[int] | None = None,
    root_editable: bool = False,
) -> dict:
    task = load_json(task_path)
    verify_task_bindings(task)
    response = response_body(response_path)
    validate_fragment(response, "root_writer", response_path)
    validate_identity(response, task)
    validate_semantic_contract(response, task)
    if previous_path is not None:
        previous = response_body(previous_path)
        editable = editable_branch_indexes or set()
        all_branches = set(range(len(task.get("branch_roster", []))))
        if editable - all_branches:
            raise ContractError("repair scope contains an invalid branch index")
        if editable != all_branches or not root_editable:
            validate_identity(previous, task)
            validate_repair_preservation(
                previous,
                response,
                editable_branch_indexes=editable,
                root_editable=root_editable,
            )
    enriched = enrich_root_writer_response(response, task)
    stored = {"inputs_sha256": canonical_sha256(task), **enriched}
    atomic_write(output_path, json_content(stored))
    expected_agent_output = (
        task_path.parent.parent
        / "output"
        / root_entry_filename(task["root_envelope_id"])
    ).resolve()
    if response_path.resolve() == expected_agent_output:
        atomic_write(expected_agent_output, json_content(stored))
    return stored


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument(
        "response",
        nargs="?",
        type=Path,
        help="default: the task's sibling output/{root_envelope_id}_entry.json",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--repair-scope", type=Path)
    parser.add_argument("--editable-branch-index", action="append", type=int, default=[])
    parser.add_argument("--root-editable", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.repair_scope and not args.previous:
        raise SystemExit("--repair-scope requires --previous")
    if args.repair_scope and (args.editable_branch_index or args.root_editable):
        raise SystemExit("use either --repair-scope or explicit scope options")
    if not args.previous and (args.editable_branch_index or args.root_editable):
        raise SystemExit("repair scope options require --previous")
    task = args.task.resolve()
    task_value = load_json(task)
    filename = root_entry_filename(task_value["root_envelope_id"])
    response = args.response or task.parent.parent / "output" / filename
    output = args.output
    if output is None:
        output = task.parent.parent / "fragments" / filename
    error_output = task.parent.parent / "output/validation_error.txt"
    editable_branch_indexes = set(args.editable_branch_index)
    root_editable = args.root_editable
    if args.repair_scope:
        scope = load_json(args.repair_scope.resolve())
        if not isinstance(scope, dict) or scope.get("repairable_by") != "root_writer":
            raise SystemExit("repair scope is not owned by the root writer")
        editable_branch_indexes = set(scope.get("editable_branch_indexes", []))
        root_editable = scope.get("root_editable") is True
    try:
        stored = accept(
            task,
            response.resolve(),
            output.resolve(),
            previous_path=args.previous.resolve() if args.previous else None,
            editable_branch_indexes=editable_branch_indexes,
            root_editable=root_editable,
        )
    except (OSError, ContractError, KeyError, TypeError, json.JSONDecodeError) as error:
        atomic_write(error_output, str(error).rstrip() + "\n")
        raise SystemExit(str(error)) from error
    if error_output.exists():
        error_output.unlink()
    print(f"Accepted {output.resolve()} ({len(stored['branches'])} branches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
