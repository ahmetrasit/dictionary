#!/usr/bin/env python3
"""Export one reviewed supplemental writer response without changing its source."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_review import validate_review
from v2.scripts.accept_root_writer import (
    response_body as root_response_body,
    validate_identity,
    validate_repair_preservation,
    validate_semantic_contract,
)
from v2.scripts.assemble_entry import (
    FRAGMENT_SCHEMAS,
    ROOT_ENTRY_ARTIFACT_FORMAT,
    canonical_sha256,
    root_entry_filename,
    sha256_file,
    validate_fragment,
)
from v2.scripts.create_entry import (
    SUPPLEMENTAL_GENERATOR,
    TASK_FORMAT,
    atomic_write,
    binding_path,
    json_content,
    verify_task_bindings,
)
from v2.scripts.supplemental_entry import (
    REGISTRY_PATH,
    SOURCE_NAMES_PATH,
    entry_kind,
    evidence_from_intake,
    load_reviewed_intake,
    occurrence_evidence,
    qac_connection,
    quran_data_dir,
    source_phrase,
    work_dir,
)
from v2.scripts.validate_entry import ContractError, load_json


GENERATED_BY = "v2/scripts/export_reviewed_supplement.py"
HEADWORD_ENTRY_ARTIFACT_FORMAT = "dictionary-v2-headword-entry-draft-v1"
UNRESOLVED_PLACEHOLDER = re.compile(r"\{\{[^{}]*\}\}")
QAC_GZIP = "data/morphology/qac.sqlite.gz"


def _bound_path(binding: dict, expected: Path, *, require_digest: bool = True) -> Path:
    if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
        raise ContractError(f"Missing bound input: {expected}")
    path = binding_path(binding["path"])
    if path != expected.resolve():
        raise ContractError(f"Unexpected bound path: {path}; expected {expected.resolve()}")
    if require_digest and (not path.is_file() or sha256_file(path) != binding.get("sha256")):
        raise ContractError(f"Bound input digest mismatch: {path}")
    return path


def _task_identity(task: dict, ident: str, kind: str, role: str,
                   intake: dict, meta: dict, work: Path, quran_data: Path) -> Path:
    headword = kind == "grammatical_headword"
    identity_key = "headwordId" if headword else "root_envelope_id"
    forbidden_key = "root_envelope_id" if headword else "headwordId"
    roster_key = "sense_roster" if headword else "branch_roster"
    roster = [f"{ident}/{sense['senseId']}" for sense in intake["senses"]]
    sealed_meta = task.get("supplementalIntake")
    selected_meta = {key: meta[key] for key in ("registryPath", "intakePath", "intakeSha256")}
    if (task.get("format") != TASK_FORMAT
            or task.get("generated_by") != SUPPLEMENTAL_GENERATOR
            or task.get("role") != role
            or task.get("entryKind") != kind
            or task.get(identity_key) != ident or forbidden_key in task
            or task.get("language") != "tr"
            or task.get(roster_key) != roster
            or not isinstance(sealed_meta, dict)
            or {key: sealed_meta.get(key) for key in selected_meta} != selected_meta):
        raise ContractError(f"Supplemental {role} task identity or intake binding drift: {ident}")
    prompt_name = "supplemental-reviewer.md" if role.endswith("reviewer") else "supplemental-writer.md"
    _bound_path(task.get("prompt"), PROJECT / "v2/prompts" / prompt_name)
    _bound_path(task.get("response_schema"), FRAGMENT_SCHEMAS[role])
    evidence_path = _bound_path(task.get("evidence"), work / "evidence/evidence.json")
    coordinator = task.get("coordinator")
    if not isinstance(coordinator, dict):
        raise ContractError("Supplemental task lacks coordinator bindings")
    registry_binding = coordinator.get("registry")
    _bound_path(registry_binding, REGISTRY_PATH, require_digest=False)
    if registry_binding.get("sha256") != sealed_meta.get("registrySha256"):
        raise ContractError("Supplemental registry provenance differs from the sealed task")
    for key, path in {
        "intake": PROJECT / meta["intakePath"],
        "sourceNames": SOURCE_NAMES_PATH,
        "qacMorphology": quran_data / QAC_GZIP,
    }.items():
        _bound_path(coordinator.get(key), path)
    return evidence_path


def _staged_task(path: Path, canonical: dict, role: str, output_path: Path,
                 *, snapshot_path: Path | None = None) -> dict:
    staged = load_json(path)
    if (not isinstance(staged, dict) or staged.get("role") != role
            or staged.get("canonical_task_sha256") != canonical_sha256(canonical)):
        raise ContractError(f"Stale staged {role} bundle: {path}")
    for key in ("format", "generated_by", "entryKind", "language", "supplementalIntake"):
        if staged.get(key) != canonical.get(key):
            raise ContractError(f"Staged {role} {key} differs from canonical task")
    for key in ("headwordId", "root_envelope_id", "sense_roster", "branch_roster", "writer_task_sha256"):
        if staged.get(key) != canonical.get(key):
            raise ContractError(f"Staged {role} {key} differs from canonical task")
    for key, name in (("prompt", "prompt.md"), ("response_schema", "response.schema.json"),
                      ("evidence", "evidence.json")):
        bound = staged.get(key)
        copied = path.parent / name
        if (not isinstance(bound, dict) or bound.get("path") != name
                or bound.get("sha256") != canonical[key]["sha256"]
                or not copied.is_file() or sha256_file(copied) != bound["sha256"]):
            raise ContractError(f"Staged {role} {key} is not the sealed copy")
    declared_output = staged.get("output", {}).get("path")
    if (not isinstance(declared_output, str)
            or (path.parent / declared_output).resolve() != output_path.resolve()):
        raise ContractError(f"Staged {role} output path differs from canonical workflow")
    if snapshot_path is not None:
        bound = staged.get("writer_response")
        if (not isinstance(bound, dict) or bound.get("path") != "writer_response.json"
                or snapshot_path.resolve() != (path.parent / "writer_response.json").resolve()
                or not snapshot_path.is_file() or sha256_file(snapshot_path) != bound["sha256"]):
            raise ContractError("Reviewer snapshot is not the bound immutable writer response")
    return staged


def _writer_response(path: Path, headword: bool) -> dict:
    value = load_json(path) if headword else root_response_body(path)
    if not isinstance(value, dict):
        raise ContractError("Writer response must be a JSON object")
    return value


def _validate_writer(response: dict, path: Path, task: dict, *, headword: bool,
                     require_resolved: bool = True) -> None:
    role = "headword_writer" if headword else "root_writer"
    validate_fragment(response, role, path)
    validate_identity(response, task)
    validate_semantic_contract(response, task)
    collection = "senses" if headword else "branches"
    structural = [row["sense_ref" if headword else "branch_ref"]
                  for row in response[collection]
                  if row["identity_judgment"]["status"] == "structural_review_required"]
    if structural:
        raise ContractError(f"Unresolved structural identity: {structural}")
    if require_resolved and UNRESOLVED_PLACEHOLDER.search(json.dumps(response, ensure_ascii=False)):
        raise ContractError("Unresolved lexical-unit placeholder in reviewed writer response")


def _reviewed_response(work: Path, writer_task: dict, intake: dict, meta: dict,
                       quran_data: Path, *, headword: bool) -> dict:
    ident = writer_task["headwordId" if headword else "root_envelope_id"]
    writer_role = "headword_writer" if headword else "root_writer"
    reviewer_role = "headword_reviewer" if headword else "root_reviewer"
    collection = "senses" if headword else "branches"
    profile_key = "headword_profile" if headword else "root_profile"
    roster_key = "sense_roster" if headword else "branch_roster"
    output_path = work / "output" / root_entry_filename(ident)
    raw_writer = load_json(output_path)
    if (not isinstance(raw_writer, dict)
            or raw_writer.get("inputs_sha256", canonical_sha256(writer_task))
               != canonical_sha256(writer_task)):
        raise ContractError("Live writer response is not bound to the sealed writer task")
    response = _writer_response(output_path, headword)
    _validate_writer(response, output_path, writer_task, headword=headword)
    _staged_task(work / "input/task.json", writer_task, writer_role, output_path)

    review_task = load_json(work / "tasks" / f"{reviewer_role}.json")
    if not isinstance(review_task, dict):
        raise ContractError("Reviewer task must be a JSON object")
    if (review_task.get("writer_task_sha256") != canonical_sha256(writer_task)
            or review_task.get(roster_key) != writer_task[roster_key]
            or review_task.get("evidence") != writer_task["evidence"]):
        raise ContractError("Reviewer task is not bound to the writer task")
    _task_identity(review_task, ident, writer_task["entryKind"], reviewer_role,
                   intake, meta, work, quran_data)
    if binding_path(review_task.get("writer_response", {}).get("path", "")) != output_path.resolve():
        raise ContractError("Reviewer task points to another writer output")
    snapshot_path = work / "review/input/writer_response.json"
    review_path = work / "review/output" / ("headword_review.json" if headword else "root_review.json")
    _staged_task(work / "review/input/task.json", review_task, reviewer_role,
                 review_path, snapshot_path=snapshot_path)
    original_hash = review_task["writer_response"]["sha256"]
    live_hash = sha256_file(output_path)
    if sha256_file(snapshot_path) != original_hash and live_hash != original_hash:
        raise ContractError("Repaired writer lacks a snapshot bound to the original writer bytes")
    snapshot = _writer_response(snapshot_path, headword)
    _validate_writer(snapshot, snapshot_path, writer_task, headword=headword,
                     require_resolved=False)

    review_stored = load_json(review_path)
    if not isinstance(review_stored, dict):
        raise ContractError("Reviewer verdict must be a JSON object")
    if ("inputs_sha256" in review_stored
            and review_stored["inputs_sha256"] != canonical_sha256(review_task)):
        raise ContractError("Reviewer verdict has a stale task digest")
    review = dict(review_stored)
    review.pop("inputs_sha256", None)
    validate_fragment(review, reviewer_role, review_path)
    validate_review(review, review_task)
    verdict = review["verdict"]
    if verdict == "pass":
        if response != snapshot or live_hash != original_hash:
            raise ContractError("Pass review requires unchanged bound writer response")
    elif verdict == "repair":
        editable_fields: dict[int, set[str]] = {}
        profile_editable = False
        for issue in review["issues"]:
            if issue["target_ref"] == profile_key:
                profile_editable = True
                if snapshot[profile_key] == response[profile_key]:
                    raise ContractError("Recorded profile repair was not applied")
                continue
            index = writer_task[roster_key].index(issue["target_ref"])
            field = issue["field"]
            editable_fields.setdefault(index, set()).add(field)
            if snapshot[collection][index][field] == response[collection][index][field]:
                raise ContractError(f"Recorded repair was not applied: {issue['target_ref']} {field}")
        validate_repair_preservation(
            snapshot, response,
            editable_branch_indexes=set(editable_fields),
            editable_branch_fields=editable_fields,
            root_editable=profile_editable,
            collection=collection,
            profile_key=profile_key,
        )
    else:
        raise ContractError(f"Unpublishable semantic review verdict: {verdict}")
    return response


def _citation_notes(authored: dict, sense: dict, sources: dict[str, dict]) -> list[dict]:
    claims = {claim["claimId"]: claim for claim in sense["claims"]}
    notes: dict[str, list[str]] = {}
    for detail in authored["source_synthesis"]["source_details"]:
        cited_keys = list(dict.fromkeys(
            key
            for claim_id in detail["claim_ids"]
            for key in claims[claim_id]["sourceKeys"]
        ))
        source_ids = {sources[key]["sourceId"] for key in cited_keys}
        if len(source_ids) != 1:
            raise ContractError("A source detail must resolve to one cited work")
        note = detail["summary"].strip()
        if not note:
            raise ContractError("A translated source detail cannot be empty")
        for key in cited_keys:
            if key not in sense["sourceKeys"]:
                raise ContractError("A source detail cites outside its sense authority")
            notes.setdefault(key, []).append(note)
    return [{"sourceKey": key, "noteTr": " ".join(notes[key])}
            for key in sense["sourceKeys"] if key in notes]


def _root_export(ident: str, writer_task: dict, response: dict,
                 intake: dict, meta: dict, names: dict, occurrences: dict) -> dict:
    sources = {row["sourceKey"]: row for row in intake["sources"]}
    branches = []
    for authored, sense in zip(response["branches"], intake["senses"]):
        if authored["branch_ref"] != f"{ident}/{sense['senseId']}":
            raise ContractError("Writer and intake branch rosters differ")
        citations = [sources[key] for key in sense["sourceKeys"]]
        badges = list(dict.fromkeys(
            names[item["sourceId"]]["badgeCode"]
            for item in citations if item["sourceType"] == "lexicon"
        ))
        citation_notes = _citation_notes(authored, sense, sources)
        source_note_parts: dict[str, list[str]] = {}
        for note in citation_notes:
            source = sources[note["sourceKey"]]
            if source["sourceType"] == "lexicon":
                code = names[source["sourceId"]]["badgeCode"]
                source_note_parts.setdefault(code, []).append(note["noteTr"])
        source_note = {code: " ".join(dict.fromkeys(parts))
                       for code, parts in source_note_parts.items()}
        branches.append({
            **authored,
            "branch_image_ar": sense["imageAr"],
            "what_is_ar": sense["whatIsAr"],
            "what_is_not_ar": sense["whatIsNotAr"],
            "source_phrase_ar": source_phrase(sense["sourceKeys"], sources),
            "sources": badges,
            "source_note": source_note,
            "citations": citations,
            "citationNotes": citation_notes,
        })
    return {
        "inputs_sha256": canonical_sha256(writer_task),
        "artifact_format": ROOT_ENTRY_ARTIFACT_FORMAT,
        "generated_by": GENERATED_BY,
        "entryKind": "lexical_root",
        "root_envelope_id": ident,
        "language": "tr",
        "supplementalIntake": meta,
        "branches": branches,
        "root_profile": response["root_profile"],
        "occurrence_evidence": occurrences,
    }


def _gloss_assessment(gloss: dict, kind: str, index: int) -> dict:
    """Project a reviewed writer error profile beside its displayed gloss."""
    profile = gloss["error_profile"]
    return {
        "kind": kind,
        "index": index,
        "text": gloss["text"],
        "applicability": gloss.get("applicability"),
        "fit": profile["fit"],
        "preserves": profile["preserves"],
        "loses": profile["loses"],
        "adds": profile["adds"],
        "collision": profile["collision"],
    }


def _headword_usage_note(authored: dict) -> str:
    """Keep reviewed identity, boundary, lexicalization and source prose together."""
    parts = (
        authored["identity_judgment"]["rationale"],
        authored["identity_judgment"]["boundary_note"],
        authored["lexicalization_scope"]["note"],
        authored["source_synthesis"]["common_summary"],
    )
    return " ".join(part.strip() for part in parts)


def _headword_export(ident: str, writer_task: dict, response: dict,
                     intake: dict, meta: dict, occurrences: dict) -> dict:
    sources = {row["sourceKey"]: row for row in intake["sources"]}
    if not isinstance(response["headword_profile"].get("summary"), str) or not response["headword_profile"]["summary"].strip():
        raise ContractError("Reviewed headword profile lacks a summary")
    senses = []
    for authored, sense in zip(response["senses"], intake["senses"]):
        if authored["sense_ref"] != f"{ident}/{sense['senseId']}":
            raise ContractError("Writer and intake sense rosters differ")
        concept = authored["concept_gloss"]
        contextual = authored["contextual_glosses"]
        excluded = authored["excluded_glosses"]
        assessments = [
            _gloss_assessment(gloss, kind, index)
            for kind, glosses in (("concept", [concept]),
                                  ("contextual", contextual),
                                  ("excluded", excluded))
            for index, gloss in enumerate(glosses)
        ]
        senses.append({
            **authored,
            "senseId": sense["senseId"],
            "definition": authored["concept_map"]["definition"],
            "conceptGloss": concept["text"],
            "contextualGlosses": [gloss["text"] for gloss in contextual],
            "excludedGlosses": [gloss["text"] for gloss in excluded],
            "glossAssessments": assessments,
            "usageNote": _headword_usage_note(authored),
            "imageArabic": sense["imageAr"],
            "whatIsArabic": sense["whatIsAr"],
            "whatIsNotArabic": sense["whatIsNotAr"],
            "sourcePhraseArabic": source_phrase(sense["sourceKeys"], sources),
            "citationKeys": sense["sourceKeys"],
            "citationNotes": _citation_notes(authored, sense, sources),
            "lexicalizationKind": authored["lexicalization_scope"]["branch_kind"],
        })
    citation_keys = list(dict.fromkeys(key for sense in intake["senses"]
                                    for key in sense["sourceKeys"]))
    return {
        "inputs_sha256": canonical_sha256(writer_task),
        "artifact_format": HEADWORD_ENTRY_ARTIFACT_FORMAT,
        "generated_by": GENERATED_BY,
        "entryKind": "grammatical_headword",
        "headwordId": ident,
        "headwordArabic": intake["headwordArabic"],
        "binding": intake["binding"],
        "language": "tr",
        "supplementalIntake": meta,
        "headwordProfile": response["headword_profile"],
        "senses": senses,
        "citations": [sources[key] for key in citation_keys],
        "occurrenceEvidence": occurrences,
    }


def export(ident: str, language: str = "tr", *, quran_data: Path | None = None,
           output: Path | None = None) -> dict:
    quran_data = quran_data_dir(quran_data)
    intake, meta, names, qac_rows = load_reviewed_intake(ident, quran_data)
    kind = entry_kind(ident)
    if intake["kind"] != kind:
        raise ContractError("Supplemental intake kind differs from its ID namespace")
    work = work_dir(ident, language).resolve()
    headword = kind == "grammatical_headword"
    role = "headword_writer" if headword else "root_writer"
    writer_task = load_json(work / "tasks" / f"{role}.json")
    if not isinstance(writer_task, dict):
        raise ContractError("Writer task must be a JSON object")
    _task_identity(writer_task, ident, kind, role, intake, meta, work, quran_data)
    verify_task_bindings(writer_task)
    evidence = load_json(work / "evidence/evidence.json")
    if evidence != evidence_from_intake(intake):
        raise ContractError("Sealed supplemental evidence differs from reviewed intake")
    response = _reviewed_response(work, writer_task, intake, meta, quran_data,
                                  headword=headword)
    with qac_connection(quran_data) as connection:
        occurrences = occurrence_evidence(qac_rows, connection)
    sealed_meta = writer_task["supplementalIntake"]
    result = (_headword_export(ident, writer_task, response, intake, sealed_meta, occurrences)
              if headword else _root_export(ident, writer_task, response, intake, sealed_meta,
                                            names, occurrences))
    output_path = (output or work / "export" / root_entry_filename(ident)).resolve()
    if output_path == (work / "output" / root_entry_filename(ident)).resolve():
        raise ContractError("Export must not replace the live writer response")
    content = json_content(result)
    if output_path.is_file():
        if output_path.read_text(encoding="utf-8") == content:
            return result
        raise ContractError(f"Refusing to replace a different reviewed export: {output_path}")
    atomic_write(output_path, content)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--language", default="tr")
    parser.add_argument("--quran-data", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = export(args.id, args.language, quran_data=args.quran_data, output=args.output)
    except (OSError, ContractError, KeyError, TypeError, ValueError, StopIteration,
            json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    collection = "senses" if result["entryKind"] == "grammatical_headword" else "branches"
    print(f"Exported reviewed {args.id} ({len(result[collection])} {collection})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
