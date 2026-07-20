#!/usr/bin/env python3
"""Build strict five-ayah packets for water-word resonance readers."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT_PACKETS = PROJECT / "data/output/root_packets"
DEFAULT_QAC = PROJECT / "data/working/qac.sqlite"
DEFAULT_BRANCHES = PROJECT / "data/working/furuq_v4.sqlite"
DEFAULT_OUTPUT = PROJECT / "data/output/water_secondary_resonance"

HAMZA = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ؤ": "ء", "ئ": "ء", "ٱ": "ء"})


def root_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "").translate(HAMZA)
    return "".join(
        character
        for character in normalized
        if not character.isspace()
        and character != "ـ"
        and unicodedata.category(character) != "Mn"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ayah_ref(row: dict[str, Any]) -> str:
    return f"{row['surah']}:{row['ayah']}"


def include_all(_: dict[str, Any]) -> bool:
    return True


def lemma_is(value: str) -> Callable[[dict[str, Any]], bool]:
    return lambda row: row["lemma_ar"] == value


def ref_is(*values: str) -> Callable[[dict[str, Any]], bool]:
    allowed = set(values)
    return lambda row: ayah_ref(row) in allowed


def exclude_refs(*values: str) -> Callable[[dict[str, Any]], bool]:
    excluded = set(values)
    return lambda row: ayah_ref(row) not in excluded


def hot_hamim(row: dict[str, Any]) -> bool:
    friend_refs = {"26:101", "40:18", "41:34", "69:35", "70:10"}
    return row["lemma_ar"] == "حَمِيم" and ayah_ref(row) not in friend_refs


FAMILIES: list[dict[str, Any]] = [
    {"id": "water", "label_ar": "ماء", "packet": "root_001458", "include": include_all},
    {"id": "sea", "label_ar": "بحر", "packet": "root_000086", "include": lemma_is("بَحْر")},
    {"id": "drink", "label_ar": "شرب", "packet": "root_000783", "include": include_all},
    {"id": "water_give", "label_ar": "سقي", "packet": "root_000722", "include": include_all},
    {"id": "drown", "label_ar": "غرق", "packet": "root_001080", "include": include_all},
    {"id": "hot_water", "label_ar": "حميم", "packet": "root_000001", "include": hot_hamim},
    {"id": "rain", "label_ar": "مطر", "packet": "root_001431", "include": include_all},
    {"id": "great_water", "label_ar": "يم", "packet": "root_001697", "include": lemma_is("يَمّ")},
    {"id": "wave", "label_ar": "موج", "packet": "root_001455", "include": include_all},
    {"id": "life_rain", "label_ar": "غيث", "packet": "root_001118", "include": include_all},
    {"id": "salty_bitter", "label_ar": "أجاج", "packet": "root_000014", "include": include_all},
    {"id": "fresh_sweet", "label_ar": "فرات", "packet": "root_001137", "include": include_all},
    {"id": "torrent", "label_ar": "سيل", "packet": "root_000770", "include": exclude_refs("34:12")},
    {"id": "downpour", "label_ar": "وابل", "packet": "root_001619", "include": lemma_is("وَابِل")},
    {"id": "rain_drop", "label_ar": "ودق", "packet": "root_001636", "include": include_all},
    {"id": "water_arrival", "label_ar": "ورد الماء", "packet": "root_001640", "include": ref_is("12:19", "28:23")},
    {"id": "stale_water", "label_ar": "آسن", "packet": "root_000033", "include": include_all},
    {"id": "well", "label_ar": "بئر", "packet": "root_000078", "include": include_all},
    {"id": "split_emergence", "label_ar": "انبجاس", "packet": "root_000084", "include": include_all},
    {"id": "pouring", "label_ar": "ثجاج", "packet": "root_000195", "include": include_all},
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def target_branch_inventory(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "root_id": branch["root_id"],
            "branch_id": branch["branch_id"],
            "image_ar": branch["branch_image_ar"],
            "image_en": branch["branch_image_en"],
            "scope_ar": branch["what_is_ar"],
            "scope_en": branch["what_is_en"],
            "excludes_ar": branch["what_is_not_ar"],
            "review_note": branch["review_note"],
        }
        for branch in packet["branches"]
        if branch["status"] == "accepted" and branch["contaminated"] == "no"
    ]


def collect_targets(root_packets: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    packet_meta: dict[str, Any] = {}
    for family_order, family in enumerate(FAMILIES):
        path = root_packets / f"{family['packet']}.json"
        packet = read_json(path)
        packet_meta[family["id"]] = {
            "family_order": family_order,
            "family_id": family["id"],
            "label_ar": family["label_ar"],
            "packet_file": str(path.relative_to(PROJECT)),
            "root_envelope_id": packet["root_envelope_id"],
            "root_norm": packet["root_norm"],
            "branches": target_branch_inventory(packet),
        }
        for occurrence in packet["qac"]["occurrences"]:
            if not family["include"](occurrence):
                continue
            targets.append(
                {
                    "family_order": family_order,
                    "family_id": family["id"],
                    "label_ar": family["label_ar"],
                    "root_envelope_id": packet["root_envelope_id"],
                    "root_norm": packet["root_norm"],
                    "ref": ayah_ref(occurrence),
                    "qac_ref": occurrence["qac_ref"],
                    "qac_word_ref": occurrence["qac_word_ref"],
                    "word_index": occurrence["word_index"],
                    "morpheme_index": occurrence["morpheme_index"],
                    "surface_ar": occurrence["surface_ar"],
                    "stem_ar": occurrence["stem_ar"],
                    "lemma_ar": occurrence["lemma_ar"],
                    "pos": occurrence["pos"],
                    "measure": occurrence["measure"],
                    "morph_features": occurrence["morph_features"],
                }
            )
    return targets, packet_meta


def open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def surah_lengths(qac: sqlite3.Connection) -> dict[int, int]:
    return {
        row["surah"]: row["last_ayah"]
        for row in qac.execute(
            "SELECT surah, MAX(ayah) AS last_ayah FROM qac_words GROUP BY surah"
        )
    }


def window_for(ref: str, lengths: dict[int, int]) -> list[str]:
    surah, ayah = (int(piece) for piece in ref.split(":"))
    start = max(1, ayah - 2)
    end = min(lengths[surah], ayah + 2)
    return [f"{surah}:{number}" for number in range(start, end + 1)]


def load_ayah(qac: sqlite3.Connection, ref: str) -> dict[str, Any]:
    surah, ayah = (int(piece) for piece in ref.split(":"))
    words = [
        dict(row)
        for row in qac.execute(
            """SELECT qac_word_ref, word_index, surface_ar, root_join_keys,
                      lemmas_ar, pos_tags, measures
               FROM qac_words WHERE surah=? AND ayah=? ORDER BY word_index""",
            (surah, ayah),
        )
    ]
    morphemes = [
        dict(row)
        for row in qac.execute(
            """SELECT qac_ref, qac_word_ref, word_index, morpheme_index,
                      surface_ar, stem_ar, lemma_ar, root_join_key, root_ar,
                      pos, measure, aspect, mood, voice, morph_features
               FROM qac_morphemes WHERE surah=? AND ayah=?
               ORDER BY word_index, morpheme_index""",
            (surah, ayah),
        )
    ]
    return {
        "ref": ref,
        "text_ar": " ".join(word["surface_ar"] for word in words),
        "words": words,
        "root_occurrences": [row for row in morphemes if row["root_join_key"]],
    }


def merge_branch(branches: list[dict[str, Any]], row: sqlite3.Row) -> None:
    variant = {
        "root_id": row["root_id"],
        "image_ar": row["branch_image_ar"],
        "image_en": row["branch_image_en"],
        "scope_ar": row["what_is_ar"],
        "scope_en": row["what_is_en"],
        "excludes_ar": row["what_is_not_ar"],
        "review_note": row["review_note"],
    }
    for branch in branches:
        if branch["branch_id"] == row["branch_id"]:
            branch["variants"].append(variant)
            return
    branches.append({"branch_id": row["branch_id"], "variants": [variant]})


def load_branch_map(branch_db: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows = branch_db.execute(
        """SELECT root_id, root_norm, branch_id, branch_image_ar,
                  branch_image_en, what_is_ar, what_is_en, what_is_not_ar,
                  review_note
           FROM branch_images
           WHERE status='accepted' AND contaminated='no'
           ORDER BY root_norm, CAST(SUBSTR(branch_id, 2) AS INTEGER), id"""
    )
    for row in rows:
        merge_branch(result[root_key(row["root_norm"])], row)
    return result


def case_roots(ayat: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for ayah in ayat:
        for occurrence in ayah["root_occurrences"]:
            key = occurrence["root_join_key"]
            if key and key not in seen:
                seen.add(key)
                result.append({"root_join_key": key, "root_ar": occurrence["root_ar"]})
    return result


def make_cases(
    targets: list[dict[str, Any]],
    packet_meta: dict[str, Any],
    qac: sqlite3.Connection,
    branch_map: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        by_ref[target["ref"]].append(target)
    lengths = surah_lengths(qac)
    cases: list[dict[str, Any]] = []
    for ref, focus_targets in by_ref.items():
        focus_targets.sort(key=lambda row: (row["word_index"], row["morpheme_index"], row["family_order"]))
        window = window_for(ref, lengths)
        ayat = [load_ayah(qac, window_ref) for window_ref in window]
        roots = case_roots(ayat)
        inventories = []
        missing = []
        for root in roots:
            branches = branch_map.get(root["root_join_key"], [])
            if branches:
                inventories.append({**root, "branches": branches})
            else:
                missing.append(root)
        family_ids = list(dict.fromkeys(target["family_id"] for target in focus_targets))
        cases.append(
            {
                "focus_ref": ref,
                "window": window,
                "focus_targets": [
                    {key: value for key, value in target.items() if key != "family_order"}
                    for target in focus_targets
                ],
                "target_root_inventories": [packet_meta[family_id] for family_id in family_ids],
                "ayat": ayat,
                "branch_inventories": inventories,
                "missing_branch_inventories": missing,
                "sort_key": (
                    min(target["family_order"] for target in focus_targets),
                    int(ref.split(":")[0]),
                    int(ref.split(":")[1]),
                ),
            }
        )
    return sorted(cases, key=lambda case: case["sort_key"])


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-packets", type=Path, default=DEFAULT_ROOT_PACKETS)
    parser.add_argument("--qac", type=Path, default=DEFAULT_QAC)
    parser.add_argument("--branches", type=Path, default=DEFAULT_BRANCHES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()
    if not 5 <= args.batch_size <= 10:
        parser.error("--batch-size must be from 5 to 10")

    source_paths = [args.qac, args.branches]
    source_paths.extend(args.root_packets / f"{family['packet']}.json" for family in FAMILIES)
    missing_paths = [path for path in source_paths if not path.is_file()]
    if missing_paths:
        parser.error(f"missing source files: {missing_paths}")

    targets, packet_meta = collect_targets(args.root_packets)
    qac = open_readonly(args.qac)
    branch_db = open_readonly(args.branches)
    cases = make_cases(targets, packet_meta, qac, load_branch_map(branch_db))
    qac.close()
    branch_db.close()

    packets_dir = args.output / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    resource_hashes = {str(path.relative_to(PROJECT)): sha256(path) for path in source_paths}
    batch_records = []
    for offset in range(0, len(cases), args.batch_size):
        batch_number = offset // args.batch_size + 1
        batch_id = f"batch_{batch_number:03d}"
        batch_cases = cases[offset : offset + args.batch_size]
        for case in batch_cases:
            case.pop("sort_key", None)
        packet = {
            "protocol": "water-secondary-resonance-v1",
            "batch_id": batch_id,
            "case_count": len(batch_cases),
            "case_isolation_rule": "Each case may use only its own five-ayah window.",
            "cases": batch_cases,
            "provenance": {
                "target_policy": "strict-water-word-v1",
                "branch_filter": {"status": "accepted", "contaminated": "no"},
                "resource_sha256": resource_hashes,
            },
        }
        packet_path = packets_dir / f"{batch_id}.json"
        write_json(packet_path, packet)
        batch_records.append(
            {
                "batch_id": batch_id,
                "packet": str(packet_path.relative_to(PROJECT)),
                "focus_refs": [case["focus_ref"] for case in batch_cases],
                "case_count": len(batch_cases),
                "target_count": sum(len(case["focus_targets"]) for case in batch_cases),
            }
        )

    family_stats = []
    for family in FAMILIES:
        family_targets = [target for target in targets if target["family_id"] == family["id"]]
        family_stats.append(
            {
                "family_id": family["id"],
                "label_ar": family["label_ar"],
                "root_packet": family["packet"],
                "target_morphemes": len(family_targets),
                "focus_ayat": len({target["ref"] for target in family_targets}),
            }
        )
    manifest = {
        "protocol": "water-secondary-resonance-v1",
        "target_policy": "strict-water-word-v1",
        "batch_size": args.batch_size,
        "target_morpheme_count": len(targets),
        "distinct_focus_ayah_count": len(cases),
        "family_focus_assignment_count": sum(row["focus_ayat"] for row in family_stats),
        "family_stats": family_stats,
        "batches": batch_records,
        "resource_sha256": resource_hashes,
    }
    write_json(args.output / "manifest.json", manifest)
    print(
        f"wrote {len(batch_records)} packets for {len(cases)} focus ayat "
        f"and {len(targets)} target morphemes"
    )


if __name__ == "__main__":
    main()
