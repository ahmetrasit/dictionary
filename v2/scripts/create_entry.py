#!/usr/bin/env python3
"""Prepare or run the minimal resumable agent workflow for one v2 entry."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import copy
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    FRAGMENT_SCHEMAS,
    agent_branch_evidence,
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
from v2.scripts.render_entry import MARKER as ENTRY_MARKER
from v2.scripts.render_entry import render as render_entry
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
PROMPTS = {
    "branch_writer": PROJECT / "v2/prompts/branch-writer.md",
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


def materialize_agent_task(task: dict, workspace: Path) -> dict:
    verify_task_bindings(task)
    result = copy.deepcopy(task)
    inputs_dir = workspace / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[tuple[str, str], str] = {}
    ordinal = 0

    def visit(value: Any) -> None:
        nonlocal ordinal
        if isinstance(value, dict):
            if set(("path", "sha256")).issubset(value) and isinstance(value["path"], str):
                source = binding_path(value["path"])
                key = (str(source), value["sha256"])
                relative = copied.get(key)
                if relative is None:
                    ordinal += 1
                    name = re.sub(r"[^A-Za-z0-9._-]+", "_", source.name) or "input"
                    destination = inputs_dir / f"{ordinal:03d}-{name}"
                    shutil.copyfile(source, destination)
                    if sha256_file(destination) != value["sha256"]:
                        raise ContractError(f"Copied task input changed: {source}")
                    relative = str(destination.relative_to(workspace))
                    copied[key] = relative
                value["path"] = relative
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result


def confined_agent_command(command: list[str], workspace: Path) -> list[str]:
    sandbox_exec = shutil.which("sandbox-exec")
    if sandbox_exec:
        escaped_project = str(PROJECT.resolve()).replace("\\", "\\\\").replace(
            '"', '\\"'
        )
        profile = workspace / "repository-read.sb"
        atomic_write(
            profile,
            "(version 1)\n"
            "(allow default)\n"
            f'(deny file-read* (subpath "{escaped_project}"))\n',
        )
        return [sandbox_exec, "-f", str(profile), *command]

    bubblewrap = shutil.which("bwrap")
    if bubblewrap:
        return [
            bubblewrap,
            "--ro-bind",
            "/",
            "/",
            "--tmpfs",
            str(PROJECT.resolve()),
            "--chdir",
            str(workspace),
            "--",
            *command,
        ]
    raise ContractError(
        "No supported repository read-confinement tool found; install "
        "sandbox-exec (macOS) or bubblewrap before running agents"
    )


def stop_process(process: subprocess.Popen, *, kill: bool = False) -> None:
    if process.poll() is not None:
        return
    sig = signal.SIGKILL if kill else signal.SIGTERM
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


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
    *,
    force_entry: bool = False,
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

    index, packages = build_packages(packet, packet_path, furuq_path)
    evidence_dir = expected_evidence_dir
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
        focus = package.get("branch", {})
        if focus.get("status") != "accepted" or focus.get("contaminated") != "no":
            raise ContractError(
                "needs_evidence: focus branch is not accepted and uncontaminated: "
                f"{row['root_id']}/{row['branch_id']}"
            )
        if not package.get("furuq_candidates"):
            raise ContractError(
                "needs_evidence: no accepted, uncontaminated Furuq comparison "
                f"candidate for {row['root_id']}/{row['branch_id']}"
            )
        stem = f"{row['root_id']}--{row['branch_id']}"
        agent_evidence_path = work_dir / "inputs/branches" / f"{stem}.json"
        atomic_write(agent_evidence_path, json_content(agent_branch_evidence(package)))
        task = common_task("branch_writer", index["root_envelope_id"], language)
        task.update(
            {
                "root_id": row["root_id"],
                "branch_id": row["branch_id"],
                "evidence": {
                    "path": path_ref(agent_evidence_path),
                    "sha256": sha256_file(agent_evidence_path),
                },
            }
        )
        task_path = work_dir / "tasks/branches" / f"{stem}.json"
        write_task(task_path, task)
        task_paths.append(task_path)

    return task_paths


def fragment_path_for(task_path: Path, work_dir: Path) -> Path:
    task = load_json(task_path)
    role = task["role"]
    if role == "branch_writer":
        return work_dir / "fragments/branches" / task_path.name
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
    task = common_task("root_profile_writer", index["root_envelope_id"], language)
    task.update(
        {
            "root_ids": index["root_ids"],
            "branch_count": len(index["branches"]),
            "dependencies": {"branch_fragments": dependencies},
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
    else:
        if response.get("root_envelope_id") != task["root_envelope_id"]:
            raise ContractError(f"{role}: response root envelope does not match task")
        if role == "root_profile_writer":
            profile = response["root_profile"]
            if profile["branch_count"] != task["branch_count"]:
                raise ContractError(
                    "root_profile_writer: response branch_count does not match task"
                )


def task_prompt(
    task: dict,
    repair_error: str | None,
    base_dir: Path = PROJECT,
) -> str:
    prompt_binding = task["prompt"]
    prompt_path = binding_path(prompt_binding["path"], base_dir)
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
    failure_dir = work_dir / "failures"
    failure = failure_dir / f"{stem}.attempt-{attempt}.txt"
    ordinal = 1
    while failure.exists():
        ordinal += 1
        failure = failure_dir / f"{stem}.attempt-{attempt}.{ordinal}.txt"
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
    agent_timeout: int = 1800,
    active_processes: set[Any] | None = None,
    process_lock: threading.Lock | None = None,
    stop_event: threading.Event | None = None,
) -> Path:
    task = load_json(task_path)
    verify_task_bindings(task)
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

    last_error = repair_error
    for attempt in range(1, max_repairs + 2):
        if stop_event is not None and stop_event.is_set():
            raise ContractError(f"{role} cancelled after another agent task failed")
        fragment_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, output_name = tempfile.mkstemp(
            prefix=f".{fragment_path.stem}.",
            suffix=".response.json",
            dir=fragment_path.parent,
        )
        os.close(descriptor)
        output_path = Path(output_name)
        try:
            with tempfile.TemporaryDirectory(prefix="dictionary-v2-agent-") as directory:
                workspace = Path(directory)
                agent_task = materialize_agent_task(task, workspace)
                schema_path = binding_path(
                    agent_task["response_schema"]["path"], workspace
                )
                agent_output = workspace / "response.json"
                command = [
                    codex_binary,
                    "exec",
                    "--ephemeral",
                    "--ignore-user-config",
                    "--ignore-rules",
                    "--skip-git-repo-check",
                    "--sandbox",
                    "read-only",
                    "-C",
                    str(workspace),
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(agent_output),
                    "-",
                ]
                if model:
                    command[2:2] = ["--model", model]
                command = confined_agent_command(command, workspace)
                process = None
                try:
                    process = subprocess.Popen(
                        command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=workspace,
                        start_new_session=True,
                    )
                    if active_processes is not None and process_lock is not None:
                        with process_lock:
                            if stop_event is not None and stop_event.is_set():
                                stop_process(process)
                            else:
                                active_processes.add(process)
                    stdout, stderr = process.communicate(
                        input=task_prompt(agent_task, last_error, workspace),
                        timeout=agent_timeout,
                    )
                except subprocess.TimeoutExpired as error:
                    if process is not None:
                        stop_process(process, kill=True)
                        process.communicate()
                    message = (
                        f"{role} timed out after {agent_timeout} seconds; "
                        "operational failures are not retried"
                    )
                    preserve_failure(work_dir, task_path, attempt, message)
                    raise ContractError(message) from error
                finally:
                    if (
                        process is not None
                        and active_processes is not None
                        and process_lock is not None
                    ):
                        with process_lock:
                            active_processes.discard(process)
                if process.returncode != 0:
                    message = (
                        f"codex exec exited {process.returncode}; operational failures "
                        "are not retried: "
                        f"{stderr.strip() or stdout.strip()}"
                    )
                    preserve_failure(work_dir, task_path, attempt, message)
                    raise ContractError(message)
                shutil.copyfile(agent_output, output_path)
            response = load_json(output_path)
            if not isinstance(response, dict):
                raise ContractError(f"{role}: response must be a JSON object")
            validate_fragment(response, role, output_path)
            validate_response_identity(response, task)
            stored = {"inputs_sha256": canonical_sha256(task), **response}
            atomic_write(fragment_path, json_content(stored))
            return fragment_path
        except (OSError, KeyError, TypeError) as error:
            last_error = str(error)
            raw = ""
            if output_path.is_file():
                raw = output_path.read_text(encoding="utf-8", errors="replace")
            preserve_failure(work_dir, task_path, attempt, last_error, raw)
            if attempt > max_repairs:
                raise ContractError(
                    f"{role} failed after {attempt} attempts: {last_error}"
                ) from error
        except ContractError as error:
            if "operational failures are not retried" in str(error):
                raise
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
    agent_timeout: int,
) -> None:
    active_processes: set[Any] = set()
    process_lock = threading.Lock()
    stop_event = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                run_agent_task,
                task,
                work_dir,
                codex_binary=codex_binary,
                model=model,
                max_repairs=max_repairs,
                agent_timeout=agent_timeout,
                active_processes=active_processes,
                process_lock=process_lock,
                stop_event=stop_event,
            ): task
            for task in task_paths
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as error:
                stop_event.set()
                for pending in futures:
                    pending.cancel()
                with process_lock:
                    running = list(active_processes)
                for process in running:
                    stop_process(process)
                for process in running:
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        stop_process(process, kill=True)
                raise ContractError(f"Agent task failed: {futures[future]}: {error}") from error


def repair_owners(error: str, index: dict) -> tuple[set[int], bool]:
    deterministic_markers = (
        ".dictionary_basis",
        "$.provenance",
        ".artifact_path",
        ".artifact_sha256",
        "exact packet roster",
        "evidence index",
        "digest mismatch",
        "source roster mismatch",
    )
    if any(marker in error for marker in deterministic_markers):
        return set(), False
    branch_indexes = {
        int(match)
        for match in re.findall(r"\$\.branches\[([0-9]+)\]", error)
        if int(match) < len(index["branches"])
    }
    root = "$.root_profile" in error
    return branch_indexes, root


def repair_fragments(
    error: str,
    index: dict,
    language: str,
    work_dir: Path,
    *,
    codex_binary: str,
    model: str | None,
    max_repairs: int,
    agent_timeout: int,
) -> None:
    branch_indexes, root = repair_owners(error, index)
    if not branch_indexes and not root:
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
            agent_timeout=agent_timeout,
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
        agent_timeout=agent_timeout,
    )


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
    force_entry: bool = False,
    agent_timeout: int = 1800,
) -> None:
    check_output_targets(entry_path, markdown_path, force_entry=force_entry)
    run_initial_tasks(
        task_paths,
        work_dir,
        codex_binary=codex_binary,
        model=model,
        workers=workers,
        max_repairs=max_repairs,
        agent_timeout=agent_timeout,
    )
    root_task = prepare_root_task(index, language, work_dir)
    run_agent_task(
        root_task,
        work_dir,
        codex_binary=codex_binary,
        model=model,
        max_repairs=max_repairs,
        agent_timeout=agent_timeout,
    )

    entry_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.ExitStack() as stack:
        entry_stage = Path(
            stack.enter_context(
                tempfile.TemporaryDirectory(
                    prefix=f".{entry_path.name}.publication.", dir=entry_path.parent
                )
            )
        ) / entry_path.name
        markdown_stage = Path(
            stack.enter_context(
                tempfile.TemporaryDirectory(
                    prefix=f".{markdown_path.name}.publication.",
                    dir=markdown_path.parent,
                )
            )
        ) / markdown_path.name
        for repair_round in range(max_repairs + 1):
            try:
                assemble(
                    index_path,
                    work_dir,
                    language,
                    entry_stage,
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
                    agent_timeout=agent_timeout,
                )
        render_entry(entry_stage, markdown_stage)
        render_entry(entry_stage, markdown_stage, check=True)
        publish_pair(
            entry_stage,
            markdown_stage,
            entry_path,
            markdown_path,
            force_entry=force_entry,
        )


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
    parser.add_argument(
        "--agent-timeout",
        type=int,
        default=1800,
        help="Maximum seconds for one Codex process (default: 1800)",
    )
    parser.add_argument(
        "--force-entry",
        action="store_true",
        help="Explicitly allow replacement of reviewed, published, invalid, or unmarked outputs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.max_repairs < 0:
        raise SystemExit("--max-repairs cannot be negative")
    if args.agent_timeout < 1:
        raise SystemExit("--agent-timeout must be at least 1")
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
            force_entry=args.force_entry,
            agent_timeout=args.agent_timeout,
        )
    except (OSError, ContractError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    print(f"Completed {entry_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
