#!/usr/bin/env python3
"""Audit v2 entry workflow completion without modifying campaign artifacts."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.accept_root_review import (
    response_body as review_response_body,
    validate_review,
)
from v2.scripts.assemble_entry import canonical_sha256, validate_fragment
from v2.scripts.check_root_writer import check as check_root_writer
from v2.scripts.create_entry import verify_task_bindings
from v2.scripts.render_entry import render
from v2.scripts.validate_entry import ContractError, load_json, validate_entry


AUDIT_FORMAT = "dictionary-v2-entry-campaign-audit-v1"
STATE_ORDER = (
    "published_valid",
    "publication_stale",
    "repair_required",
    "editorial_review",
    "structural_review_required",
    "review_invalid",
    "review_missing",
    "writer_invalid",
    "writer_missing",
    "unstarted",
)
ROOT_ID_RE = re.compile(r"root_([0-9]{6})")
ROOT_ENVELOPE_RE = re.compile(r"^root_[0-9]{6}(--root_[0-9]{6})*$")
QURANIC_ORIGIN_RE = re.compile(rb'"origin_corpus"\s*:\s*"quranic"')
DEFAULT_JOBS = min(16, max(1, os.cpu_count() or 1))


def envelope_sort_key(envelope: str) -> tuple[int, ...]:
    values = tuple(int(value) for value in ROOT_ID_RE.findall(envelope))
    if not values:
        raise ContractError(f"Invalid root envelope ID: {envelope!r}")
    return values


def relative_path(project: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def diagnostic(error: Exception) -> str:
    return str(error).strip() or type(error).__name__


def result(
    project: Path,
    envelope: str,
    language: str,
    state: str,
    detail: str,
    *,
    artifact: Path | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "root_envelope_id": envelope,
        "language": language,
        "state": state,
        "detail": detail,
    }
    if artifact is not None:
        value["artifact"] = relative_path(project, artifact)
    return value


def check_current_review(work_dir: Path) -> dict:
    task_path = work_dir / "review/input/task.json"
    response_path = work_dir / "review/output/root_review.json"
    task = load_json(task_path)
    verify_task_bindings(task, base_dir=task_path.parent)
    adjusted = copy.deepcopy(task)
    adjusted["evidence"]["path"] = str(
        (task_path.parent / task["evidence"]["path"]).resolve()
    )
    response = review_response_body(response_path)
    validate_fragment(response, "root_reviewer", response_path)
    validate_review(response, adjusted)
    return response


def audit_root(project: Path, envelope: str, language: str) -> dict[str, Any]:
    work_dir = project / "v2/work/entry_creation" / envelope / language
    writer_task = work_dir / "tasks/root_writer.json"
    writer_fragment = work_dir / "fragments" / f"{envelope}_entry.json"
    writer_output = work_dir / "output" / f"{envelope}_entry.json"
    review_task = work_dir / "tasks/root_reviewer.json"
    review_input_task = work_dir / "review/input/task.json"
    review_output = work_dir / "review/output/root_review.json"
    entry_path = project / "v2/entries" / language / f"{envelope}.json"
    markdown_path = project / "v2/entries" / language / f"{envelope}.md"

    if not writer_fragment.is_file():
        if work_dir.exists() or writer_task.exists() or writer_output.exists():
            return result(
                project,
                envelope,
                language,
                "writer_missing",
                "No canonical writer fragment is present.",
                artifact=writer_output if writer_output.exists() else work_dir,
            )
        return result(
            project,
            envelope,
            language,
            "unstarted",
            "No root/language work directory is present.",
        )

    if not writer_task.is_file():
        return result(
            project,
            envelope,
            language,
            "writer_invalid",
            "The canonical writer task is missing.",
            artifact=writer_fragment,
        )
    try:
        writer = check_root_writer(writer_task, writer_fragment)
        writer_task_hash = canonical_sha256(load_json(writer_task))
    except (OSError, ContractError, KeyError, TypeError) as error:
        return result(
            project,
            envelope,
            language,
            "writer_invalid",
            diagnostic(error),
            artifact=writer_fragment,
        )

    if any(
        branch.get("identity_judgment", {}).get("status")
        == "structural_review_required"
        for branch in writer.get("branches", [])
    ):
        return result(
            project,
            envelope,
            language,
            "structural_review_required",
            "Writer identity judgment requires branch-graph curation.",
            artifact=writer_fragment,
        )

    if not review_output.is_file():
        return result(
            project,
            envelope,
            language,
            "review_missing",
            "No current semantic-review output is present.",
            artifact=writer_fragment,
        )
    if not review_input_task.is_file():
        return result(
            project,
            envelope,
            language,
            "review_invalid",
            "The staged semantic-review task is missing.",
            artifact=review_output,
        )
    try:
        review = check_current_review(work_dir)
    except (OSError, ContractError, KeyError, TypeError) as error:
        return result(
            project,
            envelope,
            language,
            "review_invalid",
            diagnostic(error),
            artifact=review_output,
        )

    verdict = review["verdict"]
    if verdict == "editorial_review":
        return result(
            project,
            envelope,
            language,
            "editorial_review",
            "The current bound semantic review requires editor judgment.",
            artifact=review_output,
        )
    if verdict not in {"pass", "repair"}:
        return result(
            project,
            envelope,
            language,
            "review_invalid",
            f"Unknown semantic-review verdict: {verdict!r}.",
            artifact=review_output,
        )

    if not entry_path.is_file() or not markdown_path.is_file():
        missing = [
            relative_path(project, path)
            for path in (entry_path, markdown_path)
            if not path.is_file()
        ]
        return result(
            project,
            envelope,
            language,
            "publication_stale",
            f"Missing published artifact(s): {', '.join(missing)}.",
            artifact=entry_path.parent,
        )

    try:
        entry, _packet = validate_entry(entry_path)
        published_hash = entry["provenance"]["root_task_sha256"]
        if published_hash != writer_task_hash:
            raise ContractError(
                "Published entry is not bound to the current accepted writer task: "
                f"expected {writer_task_hash!r}, got {published_hash!r}"
            )
        render(entry_path, markdown_path, check=True)
    except (OSError, ContractError, KeyError, TypeError, sqlite3.Error) as error:
        return result(
            project,
            envelope,
            language,
            "publication_stale",
            diagnostic(error),
            artifact=entry_path,
        )

    return result(
        project,
        envelope,
        language,
        "published_valid",
        "Current writer, review, entry, and Markdown all validate.",
        artifact=entry_path,
    )


def packet_is_quranic(path: Path) -> bool:
    # Packets are generated JSON. Scanning the unescaped enum token avoids
    # deserializing hundreds of megabytes solely to select the campaign queue.
    return QURANIC_ORIGIN_RE.search(path.read_bytes()) is not None


def packet_path(project: Path, envelope: str) -> Path:
    if not ROOT_ENVELOPE_RE.fullmatch(envelope):
        raise ContractError(f"Invalid root envelope ID: {envelope!r}")
    return project / "data/output/root_packets" / f"{envelope}.json"


def packet_envelopes(project: Path, scope: str) -> list[str]:
    envelopes: list[str] = []
    for path in (project / "data/output/root_packets").glob("root_*.json"):
        envelope = path.stem
        if not ROOT_ENVELOPE_RE.fullmatch(envelope):
            continue
        if scope == "quranic" and not packet_is_quranic(path):
            continue
        envelopes.append(envelope)
    return sorted(set(envelopes), key=envelope_sort_key)


def selected_envelopes(
    project: Path,
    scope: str,
    roots: list[str] | None,
) -> list[str]:
    if not roots:
        return packet_envelopes(project, scope)
    selected = sorted(set(roots), key=envelope_sort_key)
    missing: list[str] = []
    for envelope in selected:
        path = packet_path(project, envelope)
        if not path.is_file() or (scope == "quranic" and not packet_is_quranic(path)):
            missing.append(envelope)
    if missing:
        raise ContractError(
            f"Root envelope(s) are absent from {scope!r} scope: {missing}"
        )
    return selected


def audit_roots(
    project: Path,
    language: str,
    envelopes: list[str],
    *,
    jobs: int,
    progress: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    if jobs < 1:
        raise ContractError(f"Audit jobs must be at least 1, got {jobs}")
    if not envelopes:
        return []
    if jobs == 1 or len(envelopes) == 1:
        rows = []
        for done, envelope in enumerate(envelopes, start=1):
            rows.append(audit_root(project, envelope, language))
            if progress:
                progress(done, len(envelopes))
        return rows

    by_envelope: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(jobs, len(envelopes))) as executor:
        futures = {
            executor.submit(audit_root, project, envelope, language): envelope
            for envelope in envelopes
        }
        for done, future in enumerate(as_completed(futures), start=1):
            envelope = futures[future]
            by_envelope[envelope] = future.result()
            if progress:
                progress(done, len(envelopes))
    return [by_envelope[envelope] for envelope in envelopes]


def audit_campaign(
    project: Path,
    language: str,
    scope: str,
    roots: list[str] | None = None,
    *,
    jobs: int = DEFAULT_JOBS,
    progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    selected = selected_envelopes(project, scope, roots)
    rows = audit_roots(
        project,
        language,
        selected,
        jobs=jobs,
        progress=progress,
    )
    counts = Counter(row["state"] for row in rows)
    successful = bool(rows) and counts["published_valid"] == len(rows)
    return {
        "format": AUDIT_FORMAT,
        "scope": scope,
        "language": language,
        "successful": successful,
        "root_count": len(rows),
        "counts": {
            state: counts[state]
            for state in STATE_ORDER
            if counts[state]
        },
        "roots": rows,
    }


def print_summary(audit: dict[str, Any], detail_limit: int) -> None:
    print(
        f"V2 entry campaign audit: scope={audit['scope']} "
        f"language={audit['language']} roots={audit['root_count']}"
    )
    for state in STATE_ORDER:
        count = audit["counts"].get(state)
        if count:
            print(f"{state}: {count}")
    failures = [
        row for row in audit["roots"] if row["state"] != "published_valid"
    ]
    if failures and detail_limit:
        print()
        shown = failures if detail_limit < 0 else failures[:detail_limit]
        for row in shown:
            first_line = row["detail"].splitlines()[0]
            print(f"{row['root_envelope_id']}: {row['state']}: {first_line}")
        remaining = len(failures) - len(shown)
        if remaining:
            print(f"... {remaining} more non-successful roots; use --json for all details")
    print()
    print("SUCCESS" if audit["successful"] else "INCOMPLETE")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("en", "tr"), required=True)
    parser.add_argument("--scope", choices=("quranic", "all"), default="quranic")
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Audit one packet envelope; repeat for an explicit list",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write the complete machine-readable audit to stdout",
    )
    parser.add_argument(
        "--detail-limit",
        type=int,
        default=20,
        help="Maximum failed roots in the readable summary; -1 shows all",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=DEFAULT_JOBS,
        help=f"Concurrent read-only root checks (default: {DEFAULT_JOBS})",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Do not report audit progress on stderr",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    def progress(done: int, total: int) -> None:
        if done == 1 or done == total or done % 100 == 0:
            print(f"Audited {done}/{total} roots", file=sys.stderr, flush=True)

    try:
        audit = audit_campaign(
            PROJECT,
            args.language,
            args.scope,
            args.roots,
            jobs=args.jobs,
            progress=None if args.no_progress else progress,
        )
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    if args.json:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    else:
        print_summary(audit, args.detail_limit)
    return 0 if audit["successful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
