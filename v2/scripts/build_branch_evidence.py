#!/usr/bin/env python3
"""Build deterministic, branch-scoped evidence packages for v2 entry agents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.render_occurrences import load_packet, validate_packet
from v2.scripts.validate_entry import DICTIONARY_NAMES, split_refs


GENERATOR = "v2/scripts/build_branch_evidence.py"
DEFAULT_FURUQ = PROJECT / "data/working/furuq_v4.sqlite"
DEFAULT_QNET = (
    PROJECT / "data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite"
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_content(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT))
    except ValueError:
        return str(path.resolve())


def write_generated(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file():
            raise ValueError(f"Missing generated evidence: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Stale generated evidence: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Refusing to replace invalid JSON: {path}") from error
        if current.get("generated_by") != GENERATOR:
            raise ValueError(f"Refusing to replace unmarked file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def packet_sources(packet: dict) -> dict[tuple[str, str], dict]:
    result: dict[tuple[str, str], dict] = {}
    for source in packet["dictionary_sources"]:
        source_ref = source.get("source_ref", "")
        if not source_ref or source_ref == "-":
            continue
        key = (source.get("root_id", ""), source_ref)
        if key in result:
            raise ValueError(f"Duplicate packet dictionary source: {key}")
        result[key] = source
    return result


def dictionary_basis(
    branch: dict,
    source_lookup: dict[tuple[str, str], dict],
) -> dict:
    grouped: dict[str, dict] = {}
    for source_ref in split_refs(branch.get("source_refs", "")):
        source = source_lookup.get((branch["root_id"], source_ref))
        if source is None:
            raise ValueError(
                f"Branch {branch['root_id']}/{branch['branch_id']} source is absent "
                f"from packet dictionary rows: {source_ref}"
            )
        if source.get("route_status") == "no_match":
            raise ValueError(f"Branch source cannot use a no_match row: {source_ref}")
        source_id = source["source_id"]
        group = grouped.setdefault(
            source_id,
            {
                "source_id": source_id,
                "dictionary_name": DICTIONARY_NAMES.get(source_id, source_id),
                "source_refs": [],
                "passages": [],
            },
        )
        group["source_refs"].append(source_ref)
        group["passages"].append(
            {
                "source_ref": source_ref,
                "headword": source.get("headword", ""),
                "route_status": source.get("route_status", ""),
                "entry_text_clean": source.get("entry_text_clean", ""),
                "origin_corpus": source.get("origin_corpus", ""),
                "section_path": source.get("section_path", ""),
                "page_or_volume_ref": source.get("page_or_volume_ref", ""),
            }
        )
    sources = list(grouped.values())
    return {
        "dictionary_count": len(sources),
        "passage_count": sum(len(source["source_refs"]) for source in sources),
        "sources": sources,
    }


def lexical_units(packet: dict, branch: dict) -> list[dict]:
    linked = {
        row["lexical_unit_id"]
        for row in packet["branch_lexical_links"]
        if row["root_id"] == branch["root_id"]
        and row["branch_id"] == branch["branch_id"]
    }
    fields = (
        "lexical_unit_id",
        "expression_ar",
        "unit_kind",
        "sense_ar",
        "source_phrase_ar",
        "source_refs",
        "branch_source_refs",
        "resolved_quran_stem_ar",
        "resolved_quran_tag",
        "status",
    )
    return [
        {field: row.get(field, "") for field in fields}
        for row in packet["lexical_senses"]
        if row["root_id"] == branch["root_id"]
        and row["lexical_unit_id"] in linked
    ]


def furuq_candidate_cards(
    db: sqlite3.Connection,
    packet: dict,
    branch: dict,
    qnet_rows: list[dict],
    supplemental_rows: list[dict],
) -> list[dict]:
    bases: dict[tuple[str, str], list[str]] = defaultdict(list)
    shared_keywords: dict[tuple[str, str], list[str]] = {}
    for neighbor in qnet_rows:
        key = (neighbor["root_id"], neighbor["branch_id"])
        bases[key].append("qnet_packet")
        shared_keywords[key] = neighbor.get("shared_consensus_core", [])
    for neighbor in supplemental_rows:
        key = (neighbor["root_id"], neighbor["branch_id"])
        bases[key].append("qnet_core_overlap")
        shared_keywords[key] = neighbor["shared_core_keywords"]
    for sibling in packet["branches"]:
        key = (sibling["root_id"], sibling["branch_id"])
        if key != (branch["root_id"], branch["branch_id"]):
            bases[key].append("sibling")

    fields = (
        "root_id",
        "branch_id",
        "root_norm",
        "branch_image_ar",
        "what_is_ar",
        "what_is_not_ar",
        "source_phrase_ar",
        "source_refs",
        "status",
        "contaminated",
    )
    result = []
    for (root_id, branch_id), discovery_basis in bases.items():
        row = db.execute(
            "SELECT root_id, branch_id, root_norm, branch_image_ar, what_is_ar, "
            "what_is_not_ar, source_phrase_ar, source_refs, status, contaminated "
            "FROM branch_images WHERE root_id=? AND branch_id=?",
            (root_id, branch_id),
        ).fetchone()
        if row is None:
            continue
        if row["status"] != "accepted" or row["contaminated"] != "no":
            continue
        card = {field: row[field] for field in fields}
        card["discovery_basis"] = discovery_basis
        card["shared_consensus_core"] = shared_keywords.get((root_id, branch_id), [])
        result.append(card)
    return result


def qnet_core_overlap_candidates(
    db: sqlite3.Connection,
    branch: dict,
    packet_candidates: list[dict],
    *,
    limit: int = 8,
) -> list[dict]:
    excluded = {
        (row["root_id"], row["branch_id"]) for row in packet_candidates
    }
    rows = db.execute(
        "WITH focus AS ("
        " SELECT keyword, replicate_votes FROM branch_keywords"
        " WHERE root_id=? AND branch_id=? AND keyword_type='core'"
        ")"
        " SELECT other.root_id, other.branch_id,"
        " COUNT(*) AS shared_keyword_count,"
        " SUM(CASE WHEN focus.replicate_votes=2"
        "          AND other.replicate_votes=2 THEN 1 ELSE 0 END)"
        "   AS consensus_keyword_count,"
        " GROUP_CONCAT(other.keyword, char(31)) AS shared_keywords"
        " FROM focus JOIN branch_keywords AS other"
        "   ON other.keyword=focus.keyword AND other.keyword_type='core'"
        " WHERE other.root_id<>?"
        " GROUP BY other.root_id, other.branch_id"
        " ORDER BY shared_keyword_count DESC, consensus_keyword_count DESC,"
        " other.root_id, other.branch_id",
        (branch["root_id"], branch["branch_id"], branch["root_id"]),
    ).fetchall()
    result = []
    for row in rows:
        key = (row["root_id"], row["branch_id"])
        if key in excluded:
            continue
        result.append(
            {
                "root_id": row["root_id"],
                "branch_id": row["branch_id"],
                "route": "raw_core_overlap",
                "shared_keyword_count": row["shared_keyword_count"],
                "consensus_keyword_count": row["consensus_keyword_count"],
                "shared_core_keywords": sorted(
                    keyword
                    for keyword in str(row["shared_keywords"] or "").split("\x1f")
                    if keyword
                ),
            }
        )
        if len(result) == limit:
            break
    return result


def build_packages(
    packet: dict,
    packet_path: Path,
    furuq_path: Path,
    qnet_path: Path = DEFAULT_QNET,
) -> tuple[dict, dict[str, dict]]:
    packet_digest = sha256_file(packet_path)
    furuq_digest = sha256_file(furuq_path)
    if not qnet_path.is_file():
        raise ValueError(f"Missing QNet incidence database: {qnet_path}")
    qnet_digest = sha256_file(qnet_path)
    source_lookup = packet_sources(packet)
    db = sqlite3.connect(f"file:{furuq_path.resolve()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    qnet_db = sqlite3.connect(f"file:{qnet_path.resolve()}?mode=ro", uri=True)
    qnet_db.row_factory = sqlite3.Row
    packages: dict[str, dict] = {}
    try:
        for branch in packet["branches"]:
            branch_ref = f"{branch['root_id']}/{branch['branch_id']}"
            qnet = packet["qnet"].get(branch_ref, {})
            qnet_rows = qnet.get("neighbors", [])
            supplemental_rows = qnet_core_overlap_candidates(
                qnet_db, branch, qnet_rows
            )
            filename = f"{branch['root_id']}--{branch['branch_id']}.json"
            package = {
                "format": 1,
                "generated_by": GENERATOR,
                "root_envelope_id": packet["root_envelope_id"],
                "packet_path": relative_path(packet_path),
                "packet_sha256": packet_digest,
                "furuq_path": relative_path(furuq_path),
                "furuq_sha256": furuq_digest,
                "qnet_path": relative_path(qnet_path),
                "qnet_sha256": qnet_digest,
                "branch": {
                    field: branch.get(field, "")
                    for field in (
                        "root_id",
                        "branch_id",
                        "branch_image_ar",
                        "what_is_ar",
                        "what_is_not_ar",
                        "source_phrase_ar",
                        "source_refs",
                        "status",
                        "contaminated",
                    )
                },
                "dictionary_basis": dictionary_basis(branch, source_lookup),
                "lexical_units": lexical_units(packet, branch),
                "qnet_candidates": qnet_rows,
                "qnet_core_overlap_candidates": supplemental_rows,
                "furuq_candidates": furuq_candidate_cards(
                    db, packet, branch, qnet_rows, supplemental_rows
                ),
            }
            packages[filename] = package
    finally:
        db.close()
        qnet_db.close()

    index = {
        "format": 1,
        "generated_by": GENERATOR,
        "root_envelope_id": packet["root_envelope_id"],
        "root_ids": [row["root_id"] for row in packet["v4_roots"]],
        "packet_path": relative_path(packet_path),
        "packet_sha256": packet_digest,
        "furuq_path": relative_path(furuq_path),
        "furuq_sha256": furuq_digest,
        "qnet_path": relative_path(qnet_path),
        "qnet_sha256": qnet_digest,
        "branches": [],
    }
    for filename, package in packages.items():
        content = json_content(package).encode("utf-8")
        index["branches"].append(
            {
                "root_id": package["branch"]["root_id"],
                "branch_id": package["branch"]["branch_id"],
                "path": f"branches/{filename}",
                "sha256": sha256_bytes(content),
            }
        )
    return index, packages


def write_packages(
    output_dir: Path,
    index: dict,
    packages: dict[str, dict],
    *,
    check: bool,
) -> None:
    for filename, package in packages.items():
        write_generated(
            output_dir / "branches" / filename,
            json_content(package),
            check=check,
        )
    write_generated(output_dir / "index.json", json_content(index), check=check)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Root ID, root envelope, Arabic root, or Arabic word")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--furuq", type=Path, default=DEFAULT_FURUQ)
    parser.add_argument("--qnet", type=Path, default=DEFAULT_QNET)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        packet_path, packet = load_packet(PROJECT, args.root, args.packet)
        validate_packet(packet)
        furuq_path = args.furuq.resolve()
        if not furuq_path.is_file():
            raise ValueError(f"Missing Furuq database: {furuq_path}")
        qnet_path = args.qnet.resolve()
        index, packages = build_packages(packet, packet_path, furuq_path, qnet_path)
        output_dir = args.output_dir or (
            PROJECT / "v2/output/branch_evidence" / packet["root_envelope_id"]
        )
        write_packages(output_dir.resolve(), index, packages, check=args.check)
    except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error) as error:
        raise SystemExit(str(error)) from error
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {output_dir} ({len(packages)} branch packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
