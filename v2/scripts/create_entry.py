#!/usr/bin/env python3
"""Prepare or run the minimal resumable agent workflow for one v2 entry."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    FRAGMENT_SCHEMAS,
    canonical_sha256,
    load_task_fragment,
    project_relative,
    sha256_file,
    validate_fragment,
    assemble,
)
from v2.scripts.build_branch_evidence import (
    DEFAULT_FURUQ,
    build_packages,
    write_packages,
)
from v2.scripts.render_entry import render as render_entry
from v2.scripts.render_occurrences import (
    load_packet,
    render_markdown as render_occurrences,
    validate_packet,
    write_generated as write_occurrences,
)
from v2.scripts.validate_entry import ContractError, load_json


GENERATOR = "v2/scripts/create_entry.py"
PROMPTS = {
    "branch_writer": PROJECT / "v2/prompts/branch-writer.md",
    "occurrence_observer": PROJECT / "v2/prompts/occurrence-observer.md",
    "root_profile_writer": PROJECT / "v2/prompts/root-profile-writer.md",
}
ENTRY_SCHEMA = PROJECT / "v2/schema/encyclopedia-entry.schema.json"
ORCHESTRATION_SPEC = PROJECT / "v2/orchestration/entry-creation.spec.md"
TRANSLITERATION_POLICY = PROJECT / "TRANSLITERATION_POLICY.md"


def json_content(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def path_ref(path: Path) -> str:
    return project_relative(path)


def binding(path: Path) -> dict:
    return {"path": path_ref(path), "sha256": sha256_file(path)}


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


def write_task(path: Path, task: dict) -> None:
    if path.exists():
        current = load_json(path)
        if current.get("generated_by") != GENERATOR:
            raise ContractError(f"Refusing to replace unmarked task: {path}")
    atomic_write(path, json_content(task))


def common_task(role: str, envelope: str, language: str) -> dict:
    return {
        "format": 1,
        "generated_by": GENERATOR,
        "role": role,
        "root_envelope_id": envelope,
        "language": language,
        "prompt": binding(PROMPTS[role]),
        "response_schema": binding(FRAGMENT_SCHEMAS[role]),
        "entry_contract": {
            "schema": binding(ENTRY_SCHEMA),
            "orchestration_spec": binding(ORCHESTRATION_SPEC),
            "transliteration_policy": binding(TRANSLITERATION_POLICY),
        },
    }


def prepare_inputs(
    selector: str,
    language: str,
    packet_argument: Path | None,
    furuq_path: Path,
    evidence_dir: Path | None,
) -> tuple[Path, dict, Path, dict]:
    packet_path, packet = load_packet(PROJECT, selector, packet_argument)
    validate_packet(packet)
    if not furuq_path.is_file():
        raise ContractError(f"Missing Furuq database: {furuq_path}")
    envelope = packet["root_envelope_id"]

    occurrence_path = PROJECT / "v2/output/occurrences" / f"{envelope}.{language}.md"
    occurrence_content = render_occurrences(packet, packet_path, language)
    write_occurrences(occurrence_path, occurrence_content, check=False)

    index, packages = build_packages(packet, packet_path, furuq_path)
    evidence_dir = evidence_dir or PROJECT / "v2/output/branch_evidence" / envelope
    write_packages(evidence_dir, index, packages, check=False)
    return packet_path, packet, evidence_dir / "index.json", index


def prepare_initial_tasks(
    index_path: Path,
    index: dict,
    language: str,
    work_dir: Path,
) -> list[Path]:
    task_paths = []
    for row in index["branches"]:
        evidence_path = (index_path.parent / row["path"]).resolve()
        package = load_json(evidence_path)
        if not package.get("furuq_candidates"):
            raise ContractError(
                "needs_evidence: no accepted, uncontaminated Furuq comparison "
                f"candidate for {row['root_id']}/{row['branch_id']}"
            )
        task = common_task("branch_writer", index["root_envelope_id"], language)
        task.update(
            {
                "root_id": row["root_id"],
                "branch_id": row["branch_id"],
                "evidence": {
                    "path": path_ref(evidence_path),
                    "sha256": row["sha256"],
                },
            }
        )
        stem = f"{row['root_id']}--{row['branch_id']}"
        task_path = work_dir / "tasks/branches" / f"{stem}.json"
        write_task(task_path, task)
        task_paths.append(task_path)

    occurrence_path = (
        PROJECT
        / "v2/output/occurrences"
        / f"{index['root_envelope_id']}.{language}.md"
    )
    occurrence_task = common_task(
        "occurrence_observer", index["root_envelope_id"], language
    )
    occurrence_task.update(
        {
            "packet": {
                "path": index["packet_path"],
                "sha256": index["packet_sha256"],
            },
            "occurrence_artifact": binding(occurrence_path),
        }
    )
    occurrence_task_path = work_dir / "tasks/occurrence_observations.json"
    write_task(occurrence_task_path, occurrence_task)
    task_paths.append(occurrence_task_path)
    return task_paths


def fragment_path_for(task_path: Path, work_dir: Path) -> Path:
    task = load_json(task_path)
    role = task["role"]
    if role == "branch_writer":
        return work_dir / "fragments/branches" / task_path.name
    if role == "occurrence_observer":
        return work_dir / "fragments/occurrence_observations.json"
    if role == "root_profile_writer":
        return work_dir / "fragments/root_profile.json"
    raise ContractError(f"Unknown task role: {role}")


def prepare_root_task(index: dict, language: str, work_dir: Path) -> Path:
    dependencies = []
    for row in index["branches"]:
        stem = f"{row['root_id']}--{row['branch_id']}"
        task_path = work_dir / "tasks/branches" / f"{stem}.json"
        fragment_path = work_dir / "fragments/branches" / f"{stem}.json"
        _task, _fragment = load_task_fragment(task_path, fragment_path, "branch_writer")
        dependencies.append(
            {
                "root_id": row["root_id"],
                "branch_id": row["branch_id"],
                "path": path_ref(fragment_path),
                "sha256": sha256_file(fragment_path),
            }
        )
    occurrence_task = work_dir / "tasks/occurrence_observations.json"
    occurrence_fragment = work_dir / "fragments/occurrence_observations.json"
    load_task_fragment(
        occurrence_task,
        occurrence_fragment,
        "occurrence_observer",
    )

    task = common_task("root_profile_writer", index["root_envelope_id"], language)
    task.update(
        {
            "root_ids": index["root_ids"],
            "branch_count": len(index["branches"]),
            "dependencies": {
                "branch_fragments": dependencies,
                "occurrence_fragment": {
                    "path": path_ref(occurrence_fragment),
                    "sha256": sha256_file(occurrence_fragment),
                },
            },
        }
    )
    task_path = work_dir / "tasks/root_profile.json"
    write_task(task_path, task)
    return task_path


def validate_response_identity(response: dict, task: dict) -> None:
    role = task["role"]
    if response.get("language") != task["language"]:
        raise ContractError(f"{role}: response language does not match task")
    if role == "branch_writer":
        for field in ("root_id", "branch_id"):
            if response.get(field) != task[field]:
                raise ContractError(f"branch_writer: response {field} does not match task")
        evidence_path = Path(task["evidence"]["path"])
        if not evidence_path.is_absolute():
            evidence_path = PROJECT / evidence_path
        package = load_json(evidence_path)
        expected = [row["source_id"] for row in package["dictionary_basis"]["sources"]]
        actual = [row["source_id"] for row in response["dictionary_annotations"]]
        if len(actual) != len(set(actual)) or set(actual) != set(expected):
            raise ContractError(
                f"branch_writer: dictionary annotation roster must be {expected}, got {actual}"
            )
    else:
        if response.get("root_envelope_id") != task["root_envelope_id"]:
            raise ContractError(f"{role}: response root envelope does not match task")
        if role == "root_profile_writer":
            profile = response["root_profile"]
            if profile["branch_count"] != task["branch_count"]:
                raise ContractError(
                    "root_profile_writer: response branch_count does not match task"
                )


def task_prompt(task: dict, repair_error: str | None) -> str:
    prompt_binding = task["prompt"]
    prompt_path = Path(prompt_binding["path"])
    if not prompt_path.is_absolute():
        prompt_path = PROJECT / prompt_path
    instructions = prompt_path.read_text(encoding="utf-8")
    sections = [
        instructions.rstrip(),
        "\n## Task manifest\n",
        "```json\n" + json.dumps(task, ensure_ascii=False, indent=2) + "\n```",
        (
            "Read only the files named by the task. The task manifest and those "
            "files are the complete authority for this response."
        ),
    ]
    if repair_error:
        sections.extend(
            [
                "\n## Required repair\n",
                (
                    "The previous response failed validation. Correct only the "
                    "owned fields implicated by this error:\n\n" + repair_error
                ),
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def preserve_failure(
    work_dir: Path,
    task_path: Path,
    attempt: int,
    message: str,
    output: str = "",
) -> None:
    stem = task_path.stem.replace("--", "-")
    failure = work_dir / "failures" / f"{stem}.attempt-{attempt}.txt"
    atomic_write(failure, f"{message}\n\n{output}".rstrip() + "\n")


def run_agent_task(
    task_path: Path,
    work_dir: Path,
    *,
    codex_binary: str,
    model: str | None,
    repair_error: str | None = None,
    force: bool = False,
    max_repairs: int = 2,
) -> Path:
    task = load_json(task_path)
    role = task["role"]
    fragment_path = fragment_path_for(task_path, work_dir)
    if fragment_path.is_file() and not force:
        try:
            _stored_task, response = load_task_fragment(
                task_path, fragment_path, role
            )
            validate_response_identity(response, task)
            return fragment_path
        except (ContractError, OSError, KeyError, TypeError):
            pass

    schema_path = FRAGMENT_SCHEMAS[role]
    last_error = repair_error
    for attempt in range(1, max_repairs + 2):
        fragment_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, output_name = tempfile.mkstemp(
            prefix=f".{fragment_path.stem}.",
            suffix=".response.json",
            dir=fragment_path.parent,
        )
        os.close(descriptor)
        output_path = Path(output_name)
        command = [
            codex_binary,
            "exec",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "-C",
            str(PROJECT),
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        if model:
            command[2:2] = ["--model", model]
        result = subprocess.run(
            command,
            input=task_prompt(task, last_error),
            text=True,
            capture_output=True,
            cwd=PROJECT,
        )
        try:
            if result.returncode != 0:
                raise ContractError(
                    f"codex exec exited {result.returncode}: "
                    f"{result.stderr.strip() or result.stdout.strip()}"
                )
            response = load_json(output_path)
            if not isinstance(response, dict):
                raise ContractError(f"{role}: response must be a JSON object")
            validate_fragment(response, role, output_path)
            validate_response_identity(response, task)
            stored = {"inputs_sha256": canonical_sha256(task), **response}
            atomic_write(fragment_path, json_content(stored))
            return fragment_path
        except (ContractError, OSError, KeyError, TypeError) as error:
            last_error = str(error)
            raw = ""
            if output_path.is_file():
                raw = output_path.read_text(encoding="utf-8", errors="replace")
            preserve_failure(work_dir, task_path, attempt, last_error, raw)
            if attempt > max_repairs:
                raise ContractError(
                    f"{role} failed after {attempt} attempts: {last_error}"
                ) from error
        finally:
            if output_path.exists():
                output_path.unlink()
    raise AssertionError("unreachable")


def run_initial_tasks(
    task_paths: list[Path],
    work_dir: Path,
    *,
    codex_binary: str,
    model: str | None,
    workers: int,
    max_repairs: int,
) -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                run_agent_task,
                task,
                work_dir,
                codex_binary=codex_binary,
                model=model,
                max_repairs=max_repairs,
            ): task
            for task in task_paths
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as error:
                for pending in futures:
                    pending.cancel()
                raise ContractError(f"Agent task failed: {futures[future]}: {error}") from error


def repair_owners(error: str, index: dict) -> tuple[set[int], bool, bool]:
    branch_indexes = {
        int(match)
        for match in re.findall(r"\$\.branches\[([0-9]+)\]", error)
        if int(match) < len(index["branches"])
    }
    occurrence = "$.occurrence_evidence.observations" in error
    root = "$.root_profile" in error
    return branch_indexes, occurrence, root


def repair_fragments(
    error: str,
    index: dict,
    language: str,
    work_dir: Path,
    *,
    codex_binary: str,
    model: str | None,
    max_repairs: int,
) -> None:
    branch_indexes, occurrence, root = repair_owners(error, index)
    if not branch_indexes and not occurrence and not root:
        raise ContractError(
            "Validation failure belongs to the deterministic pipeline and cannot "
            f"be repaired by an agent:\n{error}"
        )
    for branch_index in sorted(branch_indexes):
        row = index["branches"][branch_index]
        stem = f"{row['root_id']}--{row['branch_id']}"
        task_path = work_dir / "tasks/branches" / f"{stem}.json"
        run_agent_task(
            task_path,
            work_dir,
            codex_binary=codex_binary,
            model=model,
            repair_error=error,
            force=True,
            max_repairs=max_repairs,
        )
    if occurrence:
        run_agent_task(
            work_dir / "tasks/occurrence_observations.json",
            work_dir,
            codex_binary=codex_binary,
            model=model,
            repair_error=error,
            force=True,
            max_repairs=max_repairs,
        )
    root_task = prepare_root_task(index, language, work_dir)
    run_agent_task(
        root_task,
        work_dir,
        codex_binary=codex_binary,
        model=model,
        repair_error=error if root else "A dependency changed after validation repair.",
        force=True,
        max_repairs=max_repairs,
    )


def run_workflow(
    index_path: Path,
    index: dict,
    language: str,
    work_dir: Path,
    entry_path: Path,
    markdown_path: Path,
    task_paths: list[Path],
    *,
    codex_binary: str,
    model: str | None,
    workers: int,
    max_repairs: int,
) -> None:
    run_initial_tasks(
        task_paths,
        work_dir,
        codex_binary=codex_binary,
        model=model,
        workers=workers,
        max_repairs=max_repairs,
    )
    root_task = prepare_root_task(index, language, work_dir)
    run_agent_task(
        root_task,
        work_dir,
        codex_binary=codex_binary,
        model=model,
        max_repairs=max_repairs,
    )

    for repair_round in range(max_repairs + 1):
        try:
            assemble(
                index_path,
                work_dir,
                language,
                entry_path,
                force=True,
            )
            break
        except ContractError as error:
            if repair_round >= max_repairs:
                raise
            repair_fragments(
                str(error),
                index,
                language,
                work_dir,
                codex_binary=codex_binary,
                model=model,
                max_repairs=max_repairs,
            )
    render_entry(entry_path, markdown_path)
    render_entry(entry_path, markdown_path, check=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Root ID, envelope, Arabic root, or Arabic word")
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--furuq", type=Path, default=DEFAULT_FURUQ)
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--entry", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--run-agents", action="store_true")
    parser.add_argument("--codex-binary", default="codex")
    parser.add_argument("--model")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-repairs", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.max_repairs < 0:
        raise SystemExit("--max-repairs cannot be negative")
    try:
        _packet_path, packet, index_path, index = prepare_inputs(
            args.root,
            args.language,
            args.packet,
            args.furuq.resolve(),
            args.evidence_dir.resolve() if args.evidence_dir else None,
        )
        envelope = packet["root_envelope_id"]
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
        task_paths = prepare_initial_tasks(index_path, index, args.language, work_dir)
        if not args.run_agents:
            print(
                f"Prepared {len(task_paths)} initial tasks in {work_dir}. "
                "No model calls were made; add --run-agents to execute them."
            )
            return 0
        codex_binary = shutil.which(args.codex_binary)
        if not codex_binary:
            raise ContractError(f"Codex executable not found: {args.codex_binary}")
        run_workflow(
            index_path,
            index,
            args.language,
            work_dir,
            entry_path,
            markdown_path,
            task_paths,
            codex_binary=codex_binary,
            model=args.model,
            workers=args.workers,
            max_repairs=args.max_repairs,
        )
    except (OSError, ContractError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Completed {entry_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
