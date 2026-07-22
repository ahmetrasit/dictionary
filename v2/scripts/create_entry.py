#!/usr/bin/env python3
"""Prepare deterministic evidence and one root-writer task for an orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    FRAGMENT_SCHEMAS,
    agent_root_evidence,
    project_relative,
    sha256_file,
    load_rendering_policy,
)
from v2.scripts.build_branch_evidence import (
    DEFAULT_FURUQ,
    DEFAULT_QNET,
    DEFAULT_QNET_FIX_MANIFEST,
    DEFAULT_QNET_THEME,
    build_packages,
    write_packages,
)
from v2.scripts.render_occurrences import (
    build_attachment_crosswalk,
    load_packet,
    render_markdown as render_occurrences,
    validate_attachment_crosswalk,
    validate_packet,
    write_crosswalk,
    write_generated as write_occurrences,
)
from v2.scripts.output_protection import protect_pinned_entries
from v2.scripts.validate_entry import ContractError, load_json


GENERATOR = "v2/scripts/create_entry.py"
TASK_FORMAT = 4
PROTECTED_NAME_POLICY_DIR = PROJECT / "v2/policy/protected_names"
PROMPTS = {
    "root_writer": PROJECT / "v2/prompts/root-writer.md",
    "root_reviewer": PROJECT / "v2/prompts/root-reviewer.md",
}


def json_content(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def compact_json_content(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def path_ref(path: Path) -> str:
    return project_relative(path)


def binding(path: Path) -> dict:
    return {"path": path_ref(path), "sha256": sha256_file(path)}


def require_project_path(path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT)
    except ValueError as error:
        raise ContractError(f"{label} must be inside the project: {resolved}") from error
    return resolved


def load_canonical_packet(
    selector: str, packet_argument: Path | None
) -> tuple[Path, dict]:
    packet_path, packet = load_packet(PROJECT, selector, packet_argument)
    validate_packet(packet)
    envelope = packet["root_envelope_id"]
    expected_packet = (
        PROJECT / "data/output/root_packets" / f"{envelope}.json"
    ).resolve()
    if packet_path.resolve() != expected_packet:
        raise ContractError(
            f"Entry workflow requires canonical packet {expected_packet}, got "
            f"{packet_path.resolve()}"
        )
    return packet_path.resolve(), packet


def atomic_write(path: Path, content: str) -> None:
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


def binding_path(value: str, base_dir: Path = PROJECT) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base_dir / path).resolve()


def task_bindings(value: Any) -> list[dict]:
    result: list[dict] = []
    if isinstance(value, dict):
        if set(("path", "sha256")).issubset(value) and isinstance(value["path"], str):
            result.append(value)
        for child in value.values():
            result.extend(task_bindings(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(task_bindings(child))
    return result


def verify_task_bindings(task: dict, base_dir: Path = PROJECT) -> None:
    if task.get("format") != TASK_FORMAT or task.get("generated_by") != GENERATOR:
        raise ContractError(
            "Stale or unrecognized agent task; prepare it again with "
            "v2/scripts/create_entry.py"
        )
    for item in task_bindings(task):
        path = binding_path(item["path"], base_dir)
        if not path.is_file():
            raise ContractError(f"Task input is missing: {path}")
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise ContractError(
                f"Task input digest mismatch for {path}: expected "
                f"{item['sha256']}, got {actual}; prepare tasks again"
            )


def write_task(path: Path, task: dict) -> None:
    if path.exists():
        current = load_json(path)
        if current.get("generated_by") != GENERATOR:
            raise ContractError(f"Refusing to replace unmarked task: {path}")
    atomic_write(path, json_content(task))


def common_task(role: str, envelope: str, language: str) -> dict:
    return {
        "format": TASK_FORMAT,
        "generated_by": GENERATOR,
        "role": role,
        "root_envelope_id": envelope,
        "language": language,
        "prompt": binding(PROMPTS[role]),
        "response_schema": binding(FRAGMENT_SCHEMAS[role]),
    }


def prepare_inputs(
    selector: str,
    language: str,
    packet_argument: Path | None,
    furuq_path: Path,
    evidence_dir: Path | None,
    *,
    force_entry: bool = False,
    qnet_path: Path = DEFAULT_QNET,
    qnet_theme_path: Path = DEFAULT_QNET_THEME,
    qnet_fix_manifest_path: Path = DEFAULT_QNET_FIX_MANIFEST,
) -> tuple[Path, dict, Path, dict]:
    packet_path, packet = load_canonical_packet(selector, packet_argument)
    envelope = packet["root_envelope_id"]
    check_pinned_evidence(envelope, language, force_entry=force_entry)
    furuq_path = require_project_path(furuq_path, "Furuq database")
    if not furuq_path.is_file():
        raise ContractError(f"Missing Furuq database: {furuq_path}")
    expected_evidence_dir = (
        PROJECT / "v2/output/branch_evidence" / envelope
    ).resolve()
    if evidence_dir is not None and evidence_dir.resolve() != expected_evidence_dir:
        raise ContractError(
            f"Entry workflow requires canonical evidence directory "
            f"{expected_evidence_dir}, got {evidence_dir.resolve()}"
        )

    alignment_path = PROJECT / "v2/output/alignments" / f"{envelope}.json"
    crosswalk = build_attachment_crosswalk(packet)
    validate_attachment_crosswalk(packet, crosswalk)
    write_crosswalk(alignment_path, crosswalk, check=False)

    occurrence_path = PROJECT / "v2/output/occurrences" / f"{envelope}.{language}.md"
    occurrence_content = render_occurrences(packet, packet_path, language, crosswalk)
    write_occurrences(occurrence_path, occurrence_content, check=False)

    index, packages = build_packages(
        packet,
        packet_path,
        furuq_path,
        qnet_path,
        qnet_theme_path,
        qnet_fix_manifest_path,
    )
    evidence_dir = expected_evidence_dir
    write_packages(evidence_dir, index, packages, check=False)
    return packet_path, packet, evidence_dir / "index.json", index


def _observed_transliterations(
    language: str,
) -> tuple[
    dict[tuple[str, str, str], set[str]],
    dict[tuple[str, str, str], set[str]],
]:
    reviewed: dict[tuple[str, str, str], set[str]] = {}
    suggestions: dict[tuple[str, str, str], set[str]] = {}

    def add(
        target: dict[tuple[str, str, str], set[str]],
        kind: str,
        ref: str,
        arabic: str,
        value: str,
    ) -> None:
        if arabic and isinstance(value, str) and value.strip():
            target.setdefault((kind, ref, arabic), set()).add(value.strip())

    paths = sorted((PROJECT / "v2/entries" / language).glob("*.json"))
    paths.extend(sorted((PROJECT / "v2/examples").glob(f"*.{language}.entry.json")))
    for path in paths:
        try:
            entry = load_json(path)
        except (OSError, ContractError):
            continue
        if entry.get("language") != language:
            continue
        target = (
            reviewed
            if entry.get("status") in {"reviewed", "published"}
            else suggestions
        )
        envelope = entry.get("root_envelope_id", "")
        profile = entry.get("root_profile", {})
        add(target, "root", envelope, envelope, profile.get("transliteration", ""))
        for branch in entry.get("branches", []):
            ref = f"{branch.get('root_id', '')}/{branch.get('branch_id', '')}"
            add(
                target,
                "branch",
                ref,
                branch.get("branch_image_ar", ""),
                branch.get("image_transliteration", ""),
            )
            for neighbor in branch.get("arabic_neighbor_distinctions", []):
                neighbor_ref = (
                    f"{neighbor.get('neighbor_root_id', '')}/"
                    f"{neighbor.get('neighbor_branch_id', '')}"
                )
                add(
                    target,
                    "neighbor",
                    neighbor_ref,
                    neighbor.get("expression_ar", ""),
                    neighbor.get("expression_transliteration", ""),
                )
    return reviewed, suggestions


def build_transliteration_inputs(
    index: dict, packages: list[dict], language: str
) -> dict:
    reviewed, observed_suggestions = _observed_transliterations(language)
    values: dict[str, str] = {}
    suggestions: dict[str, str] = {}
    gaps: list[dict] = []

    def resolve(key: str, arabic: str, candidates: list[tuple[str, str, str]]) -> None:
        for kind, ref, lookup_arabic in candidates:
            found = reviewed.get((kind, ref, lookup_arabic), set())
            if len(found) == 1:
                values[key] = next(iter(found))
                return
            if found:
                break
        for kind, ref, lookup_arabic in candidates:
            found = observed_suggestions.get((kind, ref, lookup_arabic), set())
            if len(found) == 1:
                suggestions[key] = next(iter(found))
                break
            if found:
                break
        gaps.append({"key": key, "arabic": arabic})

    packet_path = Path(index["packet_path"])
    if not packet_path.is_absolute():
        packet_path = PROJECT / packet_path
    packet = load_json(packet_path)
    envelope = index["root_envelope_id"]
    resolve(
        "root_profile",
        packet.get("root_norm", " / ".join(index.get("root_ids", []))),
        [("root", envelope, envelope)],
    )
    seen_neighbors: set[str] = set()
    for package in packages:
        focus = package["branch"]
        ref = f"{focus['root_id']}/{focus['branch_id']}"
        resolve(
            f"branch:{ref}",
            focus["branch_image_ar"],
            [
                ("branch", ref, focus["branch_image_ar"]),
                ("neighbor", ref, focus["branch_image_ar"]),
            ],
        )
        for candidate in package["furuq_candidates"]:
            neighbor_ref = f"{candidate['root_id']}/{candidate['branch_id']}"
            if neighbor_ref in seen_neighbors:
                continue
            seen_neighbors.add(neighbor_ref)
            resolve(
                f"neighbor:{neighbor_ref}",
                candidate["branch_image_ar"],
                [
                    ("branch", neighbor_ref, candidate["branch_image_ar"]),
                    ("neighbor", neighbor_ref, candidate["branch_image_ar"]),
                ],
            )
    return {
        "format": "dictionary-v2-transliteration-inputs-v1",
        "root_envelope_id": envelope,
        "language": language,
        "values": values,
        "suggestions": suggestions,
        "gaps": gaps,
    }


def prepare_initial_tasks(
    index_path: Path,
    index: dict,
    language: str,
    work_dir: Path,
) -> list[Path]:
    packages = []
    for row in index["branches"]:
        evidence_path = (index_path.parent / row["path"]).resolve()
        package = load_json(evidence_path)
        focus = package.get("branch", {})
        ref = f"{row['root_id']}/{row['branch_id']}"
        if focus.get("status") != "accepted" or focus.get("contaminated") != "no":
            raise ContractError(
                "needs_evidence: focus branch is not accepted and uncontaminated: "
                + ref
            )
        if not package.get("furuq_candidates"):
            raise ContractError(
                "needs_evidence: no accepted, uncontaminated Furuq comparison "
                f"candidate for {ref}"
            )
        packages.append(package)

    name_policy_path = (
        PROTECTED_NAME_POLICY_DIR / f"{index['root_envelope_id']}.json"
    )
    rendering_policy = load_rendering_policy(
        name_policy_path, index["root_envelope_id"], packages
    )
    transliterations = build_transliteration_inputs(index, packages, language)
    transliteration_path = work_dir / "inputs/transliterations.json"
    atomic_write(transliteration_path, json_content(transliterations))
    evidence_path = work_dir / "inputs/root_evidence.json"
    atomic_write(
        evidence_path,
        compact_json_content(agent_root_evidence(packages, rendering_policy)),
    )
    task = common_task("root_writer", index["root_envelope_id"], language)
    task.update(
        {
            "branch_roster": [
                f"{row['root_id']}/{row['branch_id']}" for row in index["branches"]
            ],
            "evidence": binding(evidence_path),
            "coordinator": {
                "evidence_index": binding(index_path),
                "name_policy": binding(name_policy_path),
            },
        }
    )
    task_path = work_dir / "tasks/root_writer.json"
    write_task(task_path, task)
    return [task_path]


def check_output_targets(
    entry_path: Path,
    markdown_path: Path,
    *,
    force_entry: bool,
) -> None:
    if entry_path.exists() and not force_entry:
        try:
            existing = load_json(entry_path)
        except (OSError, ContractError) as error:
            raise ContractError(
                f"Refusing to replace unreadable entry without --force-entry: {entry_path}"
            ) from error
        if not isinstance(existing, dict) or existing.get("generated_by") != (
            "v2/scripts/assemble_entry.py"
        ):
            raise ContractError(
                f"Refusing to replace unmarked entry without --force-entry: {entry_path}"
            )
        if existing.get("status") != "draft":
            raise ContractError(
                f"Refusing to replace {existing.get('status')!r} entry without "
                f"--force-entry: {entry_path}"
            )
    if markdown_path.exists() and not force_entry:
        first = markdown_path.read_text(encoding="utf-8").splitlines()[:1]
        if not first or not first[0].startswith(
            "<!-- generated-by: v2/scripts/render_entry.py schema="
        ):
            raise ContractError(
                f"Refusing to replace unmarked Markdown without --force-entry: "
                f"{markdown_path}"
            )


def check_pinned_evidence(
    envelope: str,
    language: str,
    *,
    force_entry: bool,
) -> None:
    try:
        protect_pinned_entries(
            PROJECT,
            envelope,
            ("en", "tr"),
            force=force_entry,
            scope="shared branch or occurrence evidence",
        )
    except ValueError as error:
        message = str(error).replace("--force", "--force-entry")
        raise ContractError(message) from error


def backup_path(target: Path) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.backup.", dir=target.parent)
    os.close(descriptor)
    path = Path(name)
    path.unlink()
    return path


def publish_pair(
    candidate_entry: Path,
    candidate_markdown: Path,
    entry_path: Path,
    markdown_path: Path,
    *,
    force_entry: bool,
) -> None:
    check_output_targets(entry_path, markdown_path, force_entry=force_entry)
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    targets = ((candidate_entry, entry_path), (candidate_markdown, markdown_path))
    backups: dict[Path, Path] = {}
    installed: list[Path] = []
    try:
        for _candidate, target in targets:
            if target.exists():
                backup = backup_path(target)
                os.replace(target, backup)
                backups[target] = backup
        for candidate, target in targets:
            os.replace(candidate, target)
            installed.append(target)
    except OSError:
        for target in installed:
            if target.exists():
                target.unlink()
        for target, backup in backups.items():
            if backup.exists():
                os.replace(backup, target)
        raise
    else:
        for backup in backups.values():
            if backup.exists():
                backup.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Root ID, envelope, Arabic root, or Arabic word")
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--furuq", type=Path, default=DEFAULT_FURUQ)
    parser.add_argument("--qnet", type=Path, default=DEFAULT_QNET)
    parser.add_argument("--qnet-theme", type=Path, default=DEFAULT_QNET_THEME)
    parser.add_argument(
        "--qnet-fix-manifest", type=Path, default=DEFAULT_QNET_FIX_MANIFEST
    )
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--entry", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--force-entry",
        action="store_true",
        help="Explicitly allow replacement of reviewed, published, invalid, or unmarked outputs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        _preview_packet_path, preview_packet = load_canonical_packet(
            args.root, args.packet
        )
        envelope = preview_packet["root_envelope_id"]
        work_dir = (
            args.work_dir.resolve()
            if args.work_dir
            else PROJECT / "v2/work/entry_creation" / envelope / args.language
        )
        entry_path = (
            args.entry.resolve()
            if args.entry
            else PROJECT / "v2/entries" / args.language / f"{envelope}.json"
        )
        markdown_path = (
            args.markdown.resolve()
            if args.markdown
            else PROJECT / "v2/entries" / args.language / f"{envelope}.md"
        )
        check_output_targets(
            entry_path,
            markdown_path,
            force_entry=args.force_entry,
        )
        check_pinned_evidence(
            envelope,
            args.language,
            force_entry=args.force_entry,
        )
        _packet_path, packet, index_path, index = prepare_inputs(
            args.root,
            args.language,
            args.packet,
            args.furuq.resolve(),
            args.evidence_dir.resolve() if args.evidence_dir else None,
            force_entry=args.force_entry,
            qnet_path=args.qnet.resolve(),
            qnet_theme_path=args.qnet_theme.resolve(),
            qnet_fix_manifest_path=args.qnet_fix_manifest.resolve(),
        )
        prepare_initial_tasks(index_path, index, args.language, work_dir)
    except (OSError, ContractError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(
        f"Prepared one root-writer task in {work_dir}. No model call was made; "
        "hand control to the v2 orchestration agent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
