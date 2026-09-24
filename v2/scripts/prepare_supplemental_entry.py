#!/usr/bin/env python3
"""Prepare sealed supplemental evidence and staged writer/reviewer bundles."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_writer import validate_identity, validate_semantic_contract
from v2.scripts.assemble_entry import FRAGMENT_SCHEMAS, canonical_sha256, root_entry_filename, sha256_file
from v2.scripts.create_entry import (
    SUPPLEMENTAL_GENERATOR, atomic_write, binding, common_task, json_content,
    write_task,
)
from v2.scripts.stage_root_reviewer import stage as stage_reviewer
from v2.scripts.stage_root_writer import stage as stage_writer
from v2.scripts.supplemental_entry import (
    REGISTRY_PATH, SOURCE_NAMES_PATH, entry_kind, evidence_from_intake,
    load_reviewed_intake, quran_data_dir, work_dir,
)
from v2.scripts.validate_agent_output import validate as validate_staged_output
from v2.scripts.validate_entry import ContractError, load_json


PROMPTS = {
    "writer": PROJECT / "v2/prompts/supplemental-writer.md",
    "reviewer": PROJECT / "v2/prompts/supplemental-reviewer.md",
}


def write_sealed(path: Path, value: dict) -> None:
    content = json_content(value)
    if path.is_file():
        if path.read_text(encoding="utf-8") != content:
            raise ContractError(f"Refusing to replace different sealed evidence: {path}")
        return
    atomic_write(path, content)


def make_task(role: str, ident: str, language: str, evidence_path: Path,
              intake_path: Path, qac_path: Path, meta: dict) -> dict:
    kind = entry_kind(ident)
    headword = kind == "grammatical_headword"
    task = common_task(role, ident, language,
                       prompt_path=PROMPTS["reviewer" if role.endswith("reviewer") else "writer"])
    task["generated_by"] = SUPPLEMENTAL_GENERATOR
    task["entryKind"] = kind
    task["headwordId" if headword else "root_envelope_id"] = ident
    if headword:
        task.pop("root_envelope_id", None)
    task["response_schema"] = binding(FRAGMENT_SCHEMAS[role])
    task["evidence"] = binding(evidence_path)
    task["supplementalIntake"] = meta
    task["coordinator"] = {
        "registry": binding(REGISTRY_PATH),
        "intake": binding(intake_path),
        "sourceNames": binding(SOURCE_NAMES_PATH),
        "qacMorphology": {
            "path": os.path.relpath(qac_path, PROJECT),
            "sha256": sha256_file(qac_path),
        },
    }
    return task


def prepare_writer(ident: str, language: str, quran_data: Path) -> Path:
    intake, meta, _, _ = load_reviewed_intake(ident, quran_data)
    work = work_dir(ident, language)
    evidence_path = work / "evidence/evidence.json"
    evidence = evidence_from_intake(intake)
    write_sealed(evidence_path, evidence)
    headword = intake["kind"] == "grammatical_headword"
    role = "headword_writer" if headword else "root_writer"
    task = make_task(role, ident, language, evidence_path,
                     REGISTRY_PATH.parent / "entries" / f"{ident}.json",
                     quran_data / "data/morphology/qac.sqlite.gz", meta)
    roster = [f"{ident}/{sense['senseId']}" for sense in intake["senses"]]
    task["sense_roster" if headword else "branch_roster"] = roster
    task_path = work / "tasks" / f"{role}.json"
    write_task(task_path, task)
    stage_writer(task_path)
    return task_path


def prepare_review(ident: str, language: str, quran_data: Path) -> Path:
    work = work_dir(ident, language)
    headword = entry_kind(ident) == "grammatical_headword"
    writer_role = "headword_writer" if headword else "root_writer"
    reviewer_role = "headword_reviewer" if headword else "root_reviewer"
    writer_task_path = work / "tasks" / f"{writer_role}.json"
    if not writer_task_path.is_file():
        raise ContractError("Prepare the supplemental writer bundle first")
    writer_task = load_json(writer_task_path)
    intake, meta, _, _ = load_reviewed_intake(ident, quran_data)
    sealed_meta = writer_task.get("supplementalIntake")
    selected_fields = ("registryPath", "intakePath", "intakeSha256")
    if (not isinstance(sealed_meta, dict)
            or any(sealed_meta.get(field) != meta[field] for field in selected_fields)):
        raise ContractError("Supplemental writer task is stale against reviewed intake")
    writer_path = work / "output" / root_entry_filename(ident)
    staged_path = work / "input/task.json"
    role, validated_path, response = validate_staged_output(staged_path)
    if role != writer_role or validated_path != writer_path.resolve():
        raise ContractError("Review requires the exact validated writer output")
    validate_identity(response, writer_task)
    validate_semantic_contract(response, writer_task)
    collection = "senses" if headword else "branches"
    if any(row["identity_judgment"]["status"] == "structural_review_required" for row in response[collection]):
        raise ContractError("Structural identity review is required before semantic review")
    snapshot = work / "review/input/writer_response.json"
    if snapshot.is_file() and snapshot.read_text(encoding="utf-8") != json_content(response):
        raise ContractError("Immutable pre-fix writer snapshot differs; refusing to replace it")
    reviewer_task = make_task(reviewer_role, ident, language, work / "evidence/evidence.json",
                              REGISTRY_PATH.parent / "entries" / f"{ident}.json",
                              quran_data / "data/morphology/qac.sqlite.gz", meta)
    roster_key = "sense_roster" if headword else "branch_roster"
    reviewer_task[roster_key] = writer_task[roster_key]
    reviewer_task["writer_response"] = binding(writer_path)
    reviewer_task["writer_task_sha256"] = canonical_sha256(writer_task)
    task_path = work / "tasks" / f"{reviewer_role}.json"
    write_task(task_path, reviewer_task)
    stage_reviewer(task_path)
    return task_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--language", default="tr")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--quran-data", type=Path)
    args = parser.parse_args(argv)
    try:
        qdata = quran_data_dir(args.quran_data)
        path = (prepare_review if args.review else prepare_writer)(args.id, args.language, qdata)
    except (OSError, ContractError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Prepared {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
