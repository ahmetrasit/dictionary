#!/usr/bin/env python3
"""Validate water secondary-resonance manifests and batch packets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = PROJECT / "data/output/water_secondary_resonance"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref_parts(ref: str) -> tuple[int, int]:
    pieces = ref.split(":")
    if len(pieces) != 2 or not all(piece.isdigit() for piece in pieces):
        raise ValueError(f"invalid ayah reference: {ref}")
    return int(pieces[0]), int(pieces[1])


def validate_case(case: dict[str, Any], errors: list[str]) -> None:
    focus = case["focus_ref"]
    window = case["window"]
    label = f"case {focus}"
    if focus not in window:
        errors.append(f"{label}: focus absent from window")
    if not 3 <= len(window) <= 5:
        errors.append(f"{label}: window has {len(window)} ayat")
    positions = [ref_parts(ref) for ref in window]
    focus_surah, focus_ayah = ref_parts(focus)
    if any(surah != focus_surah for surah, _ in positions):
        errors.append(f"{label}: window crosses surah boundary")
    ayah_numbers = [ayah for _, ayah in positions]
    if ayah_numbers != list(range(ayah_numbers[0], ayah_numbers[-1] + 1)):
        errors.append(f"{label}: window is not contiguous")
    if any(abs(ayah - focus_ayah) > 2 for ayah in ayah_numbers):
        errors.append(f"{label}: window exceeds two-ayah radius")
    packet_refs = [ayah["ref"] for ayah in case["ayat"]]
    if packet_refs != window:
        errors.append(f"{label}: ayat do not match declared window")
    if not case["focus_targets"]:
        errors.append(f"{label}: no target words")
    for target in case["focus_targets"]:
        target_ref = ":".join(target["qac_ref"].split(":")[:2])
        if target["ref"] != focus or target_ref != focus:
            errors.append(f"{label}: target {target['qac_ref']} is not focus-anchored")
    target_families = {target["family_id"] for target in case["focus_targets"]}
    inventory_families = {
        inventory["family_id"] for inventory in case["target_root_inventories"]
    }
    if target_families != inventory_families:
        errors.append(f"{label}: target root inventories do not match target families")
    for inventory in case["target_root_inventories"]:
        branch_ids = [branch["branch_id"] for branch in inventory["branches"]]
        if not branch_ids:
            errors.append(f"{label}: target family {inventory['family_id']} has no branches")
        if len(branch_ids) != len(set(branch_ids)):
            errors.append(f"{label}: duplicate target branch IDs for {inventory['family_id']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    manifest_path = args.run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    errors: list[str] = []
    if manifest.get("protocol") != "water-secondary-resonance-v1":
        errors.append("manifest protocol mismatch")

    focus_refs: list[str] = []
    qac_refs: list[str] = []
    family_focuses: dict[str, set[str]] = {}
    for record in manifest["batches"]:
        packet_path = PROJECT / record["packet"]
        if not packet_path.is_file():
            errors.append(f"missing packet: {packet_path}")
            continue
        packet = read_json(packet_path)
        if packet.get("batch_id") != record["batch_id"]:
            errors.append(f"{packet_path}: batch ID mismatch")
        if packet.get("case_count") != len(packet.get("cases", [])):
            errors.append(f"{packet_path}: case count mismatch")
        if packet.get("case_isolation_rule") != "Each case may use only its own five-ayah window.":
            errors.append(f"{packet_path}: isolation rule mismatch")
        packet_focuses = [case["focus_ref"] for case in packet["cases"]]
        if packet_focuses != record["focus_refs"]:
            errors.append(f"{packet_path}: focus refs mismatch manifest")
        for case in packet["cases"]:
            validate_case(case, errors)
            focus_refs.append(case["focus_ref"])
            for target in case["focus_targets"]:
                qac_refs.append(target["qac_ref"])
                family_focuses.setdefault(target["family_id"], set()).add(case["focus_ref"])

    if len(focus_refs) != len(set(focus_refs)):
        errors.append("a focus ayah appears in more than one case")
    if len(qac_refs) != len(set(qac_refs)):
        errors.append("a target morpheme appears more than once")
    if len(focus_refs) != manifest["distinct_focus_ayah_count"]:
        errors.append("distinct focus count mismatch")
    if len(qac_refs) != manifest["target_morpheme_count"]:
        errors.append("target morpheme count mismatch")
    assignment_count = sum(len(refs) for refs in family_focuses.values())
    if assignment_count != manifest["family_focus_assignment_count"]:
        errors.append("family focus assignment count mismatch")
    for row in manifest["family_stats"]:
        actual = len(family_focuses.get(row["family_id"], set()))
        if actual != row["focus_ayat"]:
            errors.append(f"family count mismatch for {row['family_id']}")

    for relative_path, expected_hash in manifest["resource_sha256"].items():
        path = PROJECT / relative_path
        if not path.is_file():
            errors.append(f"missing hashed resource: {relative_path}")
        elif sha256(path) != expected_hash:
            errors.append(f"resource hash mismatch: {relative_path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(
        f"validated {len(manifest['batches'])} packets, {len(focus_refs)} focus ayat, "
        f"and {len(qac_refs)} target morphemes"
    )


if __name__ == "__main__":
    main()
