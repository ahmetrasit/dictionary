#!/usr/bin/env python3
"""Enrich a reviewed furuq writer response for the quran-data source corpus.

This transfer artifact is not a schema-v4 master entry. It uses the sealed
branch packages and the exact furuq packet named by their packet digest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_review import validate_review
from v2.scripts.accept_root_writer import (
    response_body,
    validate_identity,
    validate_repair_preservation,
    validate_semantic_contract,
)
from v2.scripts.assemble_entry import (
    ROOT_ENTRY_ARTIFACT_FORMAT,
    authored_root_writer_response,
    branch_claim_ref_map,
    canonical_sha256,
    dictionary_source_ids,
    json_content,
    sha256_file,
    structural_identity_refs,
    validate_fragment,
)
from v2.scripts.create_entry import (
    atomic_write,
    binding_path,
    verify_task_bindings,
    validate_root_writer_source_packages,
)
from v2.scripts.render_occurrences import (
    build_attachment_crosswalk,
    structured_occurrence_data,
    validate_packet,
)
from v2.scripts.validate_entry import ContractError, DICTIONARY_CODES, load_json


def _require_binding(binding: dict, expected_path: Path | None = None) -> Path:
    path = binding_path(binding["path"])
    if expected_path is not None and path != expected_path.resolve():
        raise ContractError(f"Unexpected bound path: {path}")
    if sha256_file(path) != binding["sha256"]:
        raise ContractError(f"Bound input digest mismatch: {path}")
    return path


def _reviewed_response(work_dir: Path, writer_task: dict) -> dict:
    envelope = writer_task["root_envelope_id"]
    response_path = work_dir / "output" / f"{envelope}_entry.json"
    response = response_body(response_path)
    validate_fragment(response, "root_writer", response_path)
    validate_identity(response, writer_task)
    validate_semantic_contract(response, writer_task)
    structural = structural_identity_refs(response)
    if structural:
        raise ContractError(f"Unresolved structural branch identity: {structural}")

    task_path = work_dir / "tasks/root_reviewer.json"
    review_task = load_json(task_path)
    if (
        review_task.get("role") != "root_reviewer"
        or review_task.get("root_envelope_id") != envelope
        or review_task.get("language") != writer_task["language"]
        or review_task.get("branch_roster") != writer_task["branch_roster"]
        or review_task.get("evidence") != writer_task["evidence"]
        or review_task.get("writer_task_sha256") != canonical_sha256(writer_task)
    ):
        raise ContractError("Reviewer task is not bound to the writer task")
    for field in ("prompt", "response_schema", "evidence"):
        _require_binding(review_task[field])
    if binding_path(review_task["writer_response"]["path"]) != response_path.resolve():
        raise ContractError("Reviewer task is bound to a different writer output")

    review_input = work_dir / "review/input"
    staged = load_json(review_input / "task.json")
    verify_task_bindings(staged, base_dir=review_input)
    if staged.get("canonical_task_sha256") != canonical_sha256(review_task):
        raise ContractError("Stale staged reviewer task")
    for field in ("role", "root_envelope_id", "language", "branch_roster", "writer_task_sha256"):
        if staged.get(field) != review_task.get(field):
            raise ContractError(f"Staged reviewer {field} differs from canonical task")
    for field in ("prompt", "response_schema", "evidence"):
        if staged[field]["sha256"] != review_task[field]["sha256"]:
            raise ContractError(f"Staged reviewer {field} differs from canonical task")
    snapshot_path = (review_input / staged["writer_response"]["path"]).resolve()
    if snapshot_path != (review_input / "writer_response.json").resolve():
        raise ContractError("Reviewer snapshot must use review/input/writer_response.json")
    snapshot = authored_root_writer_response(load_json(snapshot_path))
    validate_fragment(snapshot, "root_writer", snapshot_path)
    validate_identity(snapshot, writer_task)
    validate_semantic_contract(snapshot, writer_task)

    review_path = work_dir / "review/output/root_review.json"
    if (review_input / staged.get("output", {}).get("path", "")).resolve() != review_path.resolve():
        raise ContractError("Staged reviewer output path is invalid")
    review = load_json(review_path)
    if not isinstance(review, dict):
        raise ContractError("Reviewer output must be a JSON object")
    review.pop("inputs_sha256", None)
    validate_fragment(review, "root_reviewer", review_path)
    validate_review(review, review_task)
    verdict = review["verdict"]
    if verdict == "pass":
        if response != snapshot:
            raise ContractError("Pass review requires unchanged writer response")
        if sha256_file(response_path) != review_task["writer_response"]["sha256"]:
            raise ContractError("Pass review writer-response binding changed")
    elif verdict == "repair":
        editable_indexes = {
            writer_task["branch_roster"].index(issue["target_ref"])
            for issue in review["issues"]
            if issue["target_ref"] != "root_profile"
        }
        editable_fields: dict[int, set[str]] = {}
        for issue in review["issues"]:
            if issue["target_ref"] == "root_profile":
                if snapshot["root_profile"] == response["root_profile"]:
                    raise ContractError("Recorded root-profile repair was not applied")
                continue
            index = writer_task["branch_roster"].index(issue["target_ref"])
            editable_fields.setdefault(index, set()).add(issue["field"])
            if snapshot["branches"][index][issue["field"]] == response["branches"][index][issue["field"]]:
                raise ContractError(
                    f"Recorded repair was not applied: {issue['target_ref']} {issue['field']}"
                )
        validate_repair_preservation(
            snapshot,
            response,
            editable_branch_indexes=editable_indexes,
            editable_branch_fields=editable_fields,
            root_editable=any(issue["target_ref"] == "root_profile" for issue in review["issues"]),
        )
    else:
        raise ContractError(f"Unpublishable semantic review verdict: {verdict}")
    return response


def _source_material(writer_task: dict) -> tuple[dict, list[dict]]:
    envelope = writer_task["root_envelope_id"]
    coordinator = writer_task.get("coordinator", {})
    index_path = _require_binding(coordinator["evidence_index"])
    expected_index = PROJECT / "v2/output/branch_evidence" / envelope / "index.json"
    if index_path != expected_index.resolve():
        raise ContractError(f"Unexpected branch evidence index: {index_path}")
    index = load_json(index_path)
    if index.get("root_envelope_id") != envelope:
        raise ContractError("Branch evidence index has the wrong root envelope")
    packet_path = PROJECT / "data/output/furuq/root_packets" / f"{envelope}.json"
    if not packet_path.is_file() or sha256_file(packet_path) != index["packet_sha256"]:
        raise ContractError(f"Missing or digest-mismatched furuq packet: {packet_path}")
    packet = load_json(packet_path)
    validate_packet(packet)
    if packet["root_envelope_id"] != envelope:
        raise ContractError("Furuq packet has the wrong root envelope")
    packet_branches = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    packet_sources = {
        row["source_ref"]: row["source_id"]
        for row in packet["dictionary_sources"]
        if row.get("source_ref") and row.get("source_ref") != "-"
    }

    packages = []
    for row in index["branches"]:
        path = (index_path.parent / row["path"]).resolve()
        if not path.is_relative_to(index_path.parent) or sha256_file(path) != row["sha256"]:
            raise ContractError(f"Branch package path or digest mismatch: {path}")
        package = load_json(path)
        focus = package["branch"]
        key = (row["root_id"], row["branch_id"])
        original = packet_branches.get(key)
        if original is None or (focus["root_id"], focus["branch_id"]) != key:
            raise ContractError(f"Branch identity mismatch: {key}")
        if package.get("packet_sha256") != index["packet_sha256"]:
            raise ContractError(f"Branch package packet digest mismatch: {key}")
        for field in (
            "branch_image_ar", "what_is_ar", "what_is_not_ar",
            "source_phrase_ar", "source_refs",
        ):
            if focus.get(field) != original.get(field):
                raise ContractError(f"Branch package differs from packet: {key} {field}")
        for source in package["dictionary_basis"]["sources"]:
            for ref in source["source_refs"]:
                if packet_sources.get(ref) != source["source_id"]:
                    raise ContractError(f"Dictionary source mismatch: {key} {ref}")
        packages.append(package)
    if [f"{row['root_id']}/{row['branch_id']}" for row in index["branches"]] != writer_task["branch_roster"]:
        raise ContractError("Branch package roster differs from writer task")
    validate_root_writer_source_packages(packages, packet)
    return packet, packages


def enrich(work_dir: Path, output_path: Path) -> dict:
    work_dir = work_dir.resolve()
    writer_task = load_json(work_dir / "tasks/root_writer.json")
    verify_task_bindings(writer_task)
    if writer_task.get("role") != "root_writer" or writer_task.get("language") != "tr":
        raise ContractError("Expected a Turkish root-writer task")
    if work_dir != (PROJECT / "v2/work/entry_creation/furuq" / writer_task["root_envelope_id"] / "tr").resolve():
        raise ContractError("Furuq transfer requires the canonical furuq work directory")
    response = _reviewed_response(work_dir, writer_task)
    packet, packages = _source_material(writer_task)
    by_ref = {
        f"{package['branch']['root_id']}/{package['branch']['branch_id']}": package
        for package in packages
    }

    branches = []
    for authored in response["branches"]:
        package = by_ref[authored["branch_ref"]]
        focus = package["branch"]
        basis = package["dictionary_basis"]
        claim_refs_by_id = branch_claim_ref_map(package)
        source_notes: dict[str, list[str]] = {}
        for detail in authored["source_synthesis"]["source_details"]:
            refs = sorted({
                ref for claim_id in detail["claim_ids"]
                for ref in claim_refs_by_id[claim_id]
            })
            for source_id in dictionary_source_ids(basis, refs):
                source_notes.setdefault(DICTIONARY_CODES[source_id], []).append(
                    detail["summary"].strip()
                )
        branches.append({
            **authored,
            "branch_image_ar": focus["branch_image_ar"],
            "what_is_ar": focus["what_is_ar"],
            "what_is_not_ar": focus["what_is_not_ar"],
            "source_phrase_ar": focus["source_phrase_ar"],
            "sources": [DICTIONARY_CODES[row["source_id"]] for row in basis["sources"]],
            "source_note": {code: " ".join(parts) for code, parts in source_notes.items()},
        })
    occurrences = structured_occurrence_data(packet, build_attachment_crosswalk(packet))
    enriched = {
        "inputs_sha256": canonical_sha256(writer_task),
        "artifact_format": ROOT_ENTRY_ARTIFACT_FORMAT,
        "generated_by": "v2/scripts/enrich_furuq_writer.py",
        "root_envelope_id": writer_task["root_envelope_id"],
        "language": "tr",
        "branches": branches,
        "root_profile": response["root_profile"],
        "occurrence_evidence": {
            key: occurrences[key]
            for key in ("summary", "forms", "ayahs", "occurrences")
        },
    }
    content = json_content(enriched)
    if output_path.resolve() == (work_dir / "output" / f"{writer_task['root_envelope_id']}_entry.json").resolve():
        raise ContractError("Transfer output must not replace the live writer response")
    if output_path.is_file():
        if output_path.read_text(encoding="utf-8") == content:
            return enriched
        raise ContractError(f"Refusing to replace a different transfer artifact: {output_path}")
    atomic_write(output_path, content)
    return enriched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root_envelope_id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    envelope = args.root_envelope_id
    if not envelope.startswith("root_"):
        raise SystemExit("Expected root envelope ID")
    work_dir = PROJECT / "v2/work/entry_creation/furuq" / envelope / "tr"
    output = args.output or work_dir / "export" / f"{envelope}_entry.json"
    try:
        result = enrich(work_dir, output.resolve())
    except (OSError, ContractError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Enriched {output.resolve()} ({len(result['branches'])} branches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
