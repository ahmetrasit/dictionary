#!/usr/bin/env python3
"""Generate missing V4 root packets from canonical representatives."""

import argparse
import sqlite3
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT / "scripts"))

from root_packet import root_key


def open_db(path):
    db = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def grouped_envelopes(rows, origin_corpus):
    grouped = defaultdict(list)
    root_norms = {}
    for row in rows:
        key = root_key(row["root_norm"])
        grouped[key].append(row["root_id"])
        root_norms.setdefault(key, row["root_norm"])
    return [
        {
            "representative": root_ids[0],
            "envelope": "--".join(root_ids),
            "root_norm": root_norms[key],
            "origin_corpus": origin_corpus,
        }
        for key, root_ids in sorted(
            grouped.items(), key=lambda item: item[1][0]
        )
    ]


def root_envelopes(project):
    db = open_db(project / "data/working/furuq_v4.sqlite")
    quranic_rows = db.execute(
        """
        SELECT DISTINCT r.root_norm, r.root_id
        FROM roots AS r
        JOIN branch_images AS b ON b.root_id = r.root_id
        WHERE b.origin_corpus = 'quranic'
        ORDER BY r.root_id
        """
    ).fetchall()
    furuq_rows = db.execute(
        """
        SELECT DISTINCT r.root_norm, r.root_id
        FROM roots AS r
        JOIN dictionary_entries AS d ON d.root_id = r.root_id
        WHERE d.origin_corpus = 'furuq'
        ORDER BY r.root_id
        """
    ).fetchall()
    return (
        grouped_envelopes(quranic_rows, "quranic")
        + grouped_envelopes(furuq_rows, "furuq")
    )


def select_envelopes(envelopes, output_dir, args):
    selected = []
    for envelope in envelopes:
        representative = envelope["representative"]
        if args.start_root_id and representative < args.start_root_id:
            continue
        if args.end_root_id and representative > args.end_root_id:
            continue
        packet_path = output_dir / f"{envelope['envelope']}.json"
        if packet_path.exists() and not args.force:
            continue
        selected.append(envelope)
        if args.limit and len(selected) >= args.limit:
            break
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-root-id", help="first representative root_id to consider")
    parser.add_argument("--end-root-id", help="last representative root_id to consider")
    parser.add_argument("--limit", type=int, help="maximum packets to generate")
    parser.add_argument("--dry-run", action="store_true", help="print selected roots only")
    parser.add_argument("--force", action="store_true", help="regenerate existing packets")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT / "data/output/root_packets",
        help="root packet output directory",
    )
    args = parser.parse_args()

    envelopes = root_envelopes(PROJECT)
    selected = select_envelopes(envelopes, args.output_dir, args)
    existing = len(envelopes) - len(select_envelopes(envelopes, args.output_dir, argparse.Namespace(
        start_root_id=None,
        end_root_id=None,
        limit=None,
        force=False,
    )))

    print(f"total_v4_envelopes={len(envelopes)}")
    print(f"existing_packet_json={existing}")
    print(f"selected_for_generation={len(selected)}")

    if args.dry_run:
        for envelope in selected:
            print(
                f"DRY {envelope['representative']} -> "
                f"{envelope['envelope']} {envelope['root_norm']} "
                f"origin={envelope['origin_corpus']}"
            )
        return

    failures = []
    for index, envelope in enumerate(selected, 1):
        representative = envelope["representative"]
        command = ["python3", "scripts/root_packet.py", representative]
        if args.force:
            command.append("--force")
        print(
            f"[{index}/{len(selected)}] "
            f"{representative} -> {envelope['envelope']} {envelope['root_norm']} "
            f"origin={envelope['origin_corpus']}",
            flush=True,
        )
        result = subprocess.run(command, cwd=PROJECT)
        if result.returncode != 0:
            failures.append((envelope, result.returncode))

    remaining = select_envelopes(
        envelopes,
        args.output_dir,
        argparse.Namespace(
            start_root_id=None,
            end_root_id=None,
            limit=None,
            force=False,
        ),
    )
    print(f"generated_or_skipped={len(selected) - len(failures)}")
    print(f"failed={len(failures)}")
    print(f"remaining_missing={len(remaining)}")
    for envelope, returncode in failures:
        print(
            f"FAIL {envelope['representative']} -> "
            f"{envelope['envelope']} origin={envelope['origin_corpus']} "
            f"returncode={returncode}"
        )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
