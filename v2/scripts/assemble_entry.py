#!/usr/bin/env python3
"""Assemble one v2 entry from immutable evidence and hash-bound agent fragments."""

from __future__ import annotations

import argparse
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

from v2.scripts.validate_entry import (
    ContractError,
    load_json,
    structural_errors,
    validate_entry,
)


FRAGMENT_SCHEMAS = {
    "branch_writer": PROJECT / "v2/schema/fragments/branch-writer.schema.json",
    "occurrence_observer": (
        PROJECT / "v2/schema/fragments/occurrence-observer.schema.json"
    ),
    "root_profile_writer": PROJECT / "v2/schema/fragments/root-profile.schema.json",
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
    response = dict(stored)
    response.pop("inputs_sha256")
    validate_fragment(response, role, fragment_path)
    return task, response


def load_evidence(index_path: Path) -> tuple[dict, list[tuple[dict, dict, Path]]]:
    if not index_path.is_file():
        raise ContractError(f"Missing branch evidence index: {index_path}")
    index = load_json(index_path)
    if index.get("generated_by") != "v2/scripts/build_branch_evidence.py":
        raise ContractError(f"Unrecognized branch evidence index: {index_path}")
    packet_path = resolve_project_path(index["packet_path"])
    furuq_path = resolve_project_path(index["furuq_path"])
    qnet_path = resolve_project_path(index["qnet_path"])
    for label, path, expected in (
        ("packet", packet_path, index["packet_sha256"]),
        ("Furuq database", furuq_path, index["furuq_sha256"]),
        ("QNet incidence database", qnet_path, index["qnet_sha256"]),
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
        if package.get("packet_sha256") != index["packet_sha256"]:
            raise ContractError(f"Packet digest mismatch in {package_path}")
        if package.get("qnet_sha256") != index["qnet_sha256"]:
            raise ContractError(f"QNet digest mismatch in {package_path}")
        packages.append((row, package, package_path))
    return index, packages


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


def branch_from_fragment(package: dict, fragment: dict) -> dict:
    branch = package["branch"]
    key = (branch["root_id"], branch["branch_id"])
    actual_key = (fragment["root_id"], fragment["branch_id"])
    if actual_key != key:
        raise ContractError(
            f"Branch fragment identity mismatch: expected {key}, got {actual_key}"
        )

    basis = package["dictionary_basis"]
    expected_ids = [row["source_id"] for row in basis["sources"]]
    annotations = fragment["dictionary_annotations"]
    actual_ids = [row["source_id"] for row in annotations]
    if len(actual_ids) != len(set(actual_ids)):
        raise ContractError(f"{key}: duplicate dictionary annotation source_id")
    if set(actual_ids) != set(expected_ids):
        raise ContractError(
            f"{key}: dictionary annotation roster mismatch; expected "
            f"{expected_ids}, got {actual_ids}"
        )
    annotation_by_id = {row["source_id"]: row for row in annotations}
    sources = []
    for source in basis["sources"]:
        annotation = annotation_by_id[source["source_id"]]
        sources.append(
            {
                "source_id": source["source_id"],
                "dictionary_name": source["dictionary_name"],
                "roles": annotation["roles"],
                "source_refs": source["source_refs"],
                "contribution": annotation["contribution"],
            }
        )
    return {
        "root_id": branch["root_id"],
        "branch_id": branch["branch_id"],
        "image_transliteration": fragment["image_transliteration"],
        "summary": fragment["summary"],
        "source_discussion": fragment["source_discussion"],
        "dictionary_basis": {
            "dictionary_count": basis["dictionary_count"],
            "passage_count": basis["passage_count"],
            "sources": sources,
        },
        "glosses": fragment["glosses"],
        "arabic_neighbor_distinctions": fragment[
            "arabic_neighbor_distinctions"
        ],
    }


def build_entry(
    evidence_index: Path,
    work_dir: Path,
    language: str,
) -> tuple[dict, dict]:
    index, packages = load_evidence(evidence_index.resolve())
    envelope = index["root_envelope_id"]
    branches = []
    branch_dependencies = []
    for row, package, package_path in packages:
        stem = f"{row['root_id']}--{row['branch_id']}"
        task_path = work_dir / "tasks/branches" / f"{stem}.json"
        fragment_path = work_dir / "fragments/branches" / f"{stem}.json"
        task, fragment = load_task_fragment(task_path, fragment_path, "branch_writer")
        assert_task_identity(
            task,
            role="branch_writer",
            envelope=envelope,
            language=language,
            root_id=row["root_id"],
            branch_id=row["branch_id"],
        )
        if fragment["language"] != language:
            raise ContractError(f"Wrong-language branch fragment: {fragment_path}")
        evidence = task.get("evidence", {})
        if (
            evidence.get("path") != project_relative(package_path)
            or evidence.get("sha256") != row["sha256"]
        ):
            raise ContractError(f"Task evidence binding mismatch: {task_path}")
        branches.append(branch_from_fragment(package, fragment))
        branch_dependencies.append(
            {
                "root_id": row["root_id"],
                "branch_id": row["branch_id"],
                "path": project_relative(fragment_path),
                "sha256": sha256_file(fragment_path),
            }
        )

    occurrence_task_path = work_dir / "tasks/occurrence_observations.json"
    occurrence_fragment_path = work_dir / "fragments/occurrence_observations.json"
    occurrence_task, occurrence = load_task_fragment(
        occurrence_task_path,
        occurrence_fragment_path,
        "occurrence_observer",
    )
    assert_task_identity(
        occurrence_task,
        role="occurrence_observer",
        envelope=envelope,
        language=language,
    )
    if (
        occurrence["root_envelope_id"] != envelope
        or occurrence["language"] != language
    ):
        raise ContractError(f"Occurrence fragment identity mismatch: {occurrence_fragment_path}")
    occurrence_path = f"v2/output/occurrences/{envelope}.{language}.md"
    occurrence_binding = occurrence_task.get("occurrence_artifact", {})
    if occurrence_binding.get("path") != occurrence_path:
        raise ContractError(f"Occurrence task artifact mismatch: {occurrence_task_path}")
    occurrence_file = resolve_project_path(occurrence_path)
    if not occurrence_file.is_file():
        raise ContractError(f"Missing occurrence artifact: {occurrence_file}")
    if occurrence_binding.get("sha256") != sha256_file(occurrence_file):
        raise ContractError(f"Occurrence task artifact digest mismatch: {occurrence_task_path}")
    if occurrence_task.get("packet") != {
        "path": index["packet_path"],
        "sha256": index["packet_sha256"],
    }:
        raise ContractError(f"Occurrence task packet binding mismatch: {occurrence_task_path}")

    root_task_path = work_dir / "tasks/root_profile.json"
    root_fragment_path = work_dir / "fragments/root_profile.json"
    root_task, root = load_task_fragment(
        root_task_path,
        root_fragment_path,
        "root_profile_writer",
    )
    assert_task_identity(
        root_task,
        role="root_profile_writer",
        envelope=envelope,
        language=language,
    )
    if root["root_envelope_id"] != envelope or root["language"] != language:
        raise ContractError(f"Root-profile fragment identity mismatch: {root_fragment_path}")
    expected_dependencies = {
        "branch_fragments": branch_dependencies,
        "occurrence_fragment": {
            "path": project_relative(occurrence_fragment_path),
            "sha256": sha256_file(occurrence_fragment_path),
        },
    }
    if root_task.get("dependencies") != expected_dependencies:
        raise ContractError(f"Root-profile task dependency mismatch: {root_task_path}")
    if root_task.get("root_ids") != index["root_ids"]:
        raise ContractError(f"Root-profile task root roster mismatch: {root_task_path}")
    if root_task.get("branch_count") != len(packages):
        raise ContractError(f"Root-profile task branch count mismatch: {root_task_path}")

    entry = {
        "schema_version": 2,
        "entry_id": f"{envelope}/{language}",
        "language": language,
        "status": "draft",
        "root_envelope_id": envelope,
        "root_ids": index["root_ids"],
        "provenance": {
            "packet_path": index["packet_path"],
            "packet_sha256": index["packet_sha256"],
        },
        "root_profile": root["root_profile"],
        "branches": branches,
        "occurrence_evidence": {
            "artifact_path": occurrence_path,
            "generator": "v2/scripts/render_occurrences.py",
            "observations": occurrence["observations"],
        },
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
        validate_entry(
            temporary,
            furuq_path=resolve_project_path(index["furuq_path"]),
        )
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
    entry, index = build_entry(evidence_index, work_dir, language)
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
