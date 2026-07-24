#!/usr/bin/env python3
"""Validate and store one evidence-grounded semantic review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    ROOT_EVIDENCE_FORMAT,
    canonical_sha256,
    validate_fragment,
)
from v2.scripts.create_entry import atomic_write, binding_path, json_content, verify_task_bindings
from v2.scripts.validate_entry import ContractError, load_json


def validate_review(response: dict, task: dict) -> None:
    verdict = response["verdict"]
    issues = response["issues"]
    if verdict == "pass" and issues:
        raise ContractError("root_reviewer: pass requires no issues")
    if verdict != "pass" and not issues:
        raise ContractError(f"root_reviewer: {verdict} requires at least one issue")
    if verdict == "repair" and any(issue["confidence"] == "low" for issue in issues):
        raise ContractError(
            "root_reviewer: low-confidence judgments require editorial_review"
        )
    roster = task["branch_roster"]
    evidence = load_json(binding_path(task["evidence"]["path"]))
    if evidence.get("format") != ROOT_EVIDENCE_FORMAT:
        raise ContractError(
            f"root_reviewer: expected evidence format {ROOT_EVIDENCE_FORMAT!r}"
        )
    branch_claims_by_ref = {
        branch["branch_ref"]: {
            claim["claim_id"] for claim in branch["branch_claims"]
        }
        for branch in evidence["branches"]
    }
    lexical_ids_by_ref = {
        branch["branch_ref"]: {
            unit["lexical_unit_id"] for unit in branch["lexical_units"]
        }
        for branch in evidence["branches"]
    }
    for index, issue in enumerate(issues):
        target = issue["target_ref"]
        if target == "root_profile":
            if issue["field"] != "root_profile" or issue["claim_ids"]:
                raise ContractError(
                    f"root_reviewer.issues[{index}]: root profile issue has invalid scope"
                )
            continue
        if target not in roster:
            raise ContractError(
                f"root_reviewer.issues[{index}]: target is outside branch roster"
            )
        allowed_ids = (
            lexical_ids_by_ref[target]
            if issue["field"] == "lexical_glosses"
            else branch_claims_by_ref[target]
        )
        unknown = set(issue["claim_ids"]) - allowed_ids
        if unknown:
            raise ContractError(
                f"root_reviewer.issues[{index}]: evidence IDs are outside the "
                f"{issue['field']} roster: {sorted(unknown)}"
            )


def response_body(path: Path) -> dict:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ContractError("root_reviewer: response must be a JSON object")
    value = dict(value)
    value.pop("inputs_sha256", None)
    return value


def accept(task_path: Path, response_path: Path, output_path: Path) -> dict:
    task = load_json(task_path)
    verify_task_bindings(task)
    response = response_body(response_path)
    validate_fragment(response, "root_reviewer", response_path)
    validate_review(response, task)
    stored = {"inputs_sha256": canonical_sha256(task), **response}
    atomic_write(output_path, json_content(stored))
    return stored


def repair_scope(review: dict, task: dict) -> dict:
    indexes = {
        task["branch_roster"].index(issue["target_ref"])
        for issue in review["issues"]
        if issue["target_ref"] != "root_profile"
    }
    return {
        "repairable_by": "root_writer",
        "editable_branch_indexes": sorted(indexes),
        "root_editable": any(
            issue["target_ref"] == "root_profile" for issue in review["issues"]
        ),
    }


def review_error(review: dict) -> str:
    lines = [review["summary"]]
    for issue in review["issues"]:
        lines.append(
            f"{issue['target_ref']} {issue['field']} ({issue['severity']}, "
            f"{issue['confidence']}): {issue['evidence_conflict']} "
            f"Smallest correction: {issue['smallest_correction']}"
        )
    return "\n".join(lines) + "\n"


def check_review(task_path: Path, fragment_path: Path) -> dict:
    task = load_json(task_path)
    verify_task_bindings(task)
    stored = load_json(fragment_path)
    if stored.get("inputs_sha256") != canonical_sha256(task):
        raise ContractError("Stale root semantic review task hash")
    response = dict(stored)
    response.pop("inputs_sha256", None)
    validate_fragment(response, "root_reviewer", fragment_path)
    validate_review(response, task)
    return response


def check_pass(task_path: Path, fragment_path: Path) -> dict:
    response = check_review(task_path, fragment_path)
    if response["verdict"] != "pass":
        raise ContractError(
            f"semantic_review_{response['verdict']}: root review has not passed"
        )
    return response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("response", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    task_path = args.task.resolve()
    work_dir = task_path.parent.parent
    response_path = args.response or work_dir / "review/output/root_review.json"
    output_path = args.output or work_dir / "fragments/root_review.json"
    try:
        review = accept(task_path, response_path.resolve(), output_path.resolve())
        task = load_json(task_path)
        review_output = work_dir / "review/output"
        review_output.mkdir(parents=True, exist_ok=True)
        if review["verdict"] == "repair":
            atomic_write(
                review_output / "semantic_review_error.txt", review_error(review)
            )
            atomic_write(
                review_output / "repair_scope.json",
                json_content(repair_scope(review, task)),
            )
        elif review["verdict"] == "editorial_review":
            atomic_write(
                review_output / "editorial_review.txt", review_error(review)
            )
        for name in (
            "semantic_review_error.txt",
            "repair_scope.json",
            "editorial_review.txt",
        ):
            path = review_output / name
            if review["verdict"] == "pass" and path.exists():
                path.unlink()
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Accepted {output_path.resolve()} ({review['verdict']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
