#!/usr/bin/env python3
"""Validate completed water secondary-resonance Markdown responses."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = PROJECT / "data/output/water_secondary_resonance"
CASE_HEADING = re.compile(r"^## (\d+):(\d+) — ", re.MULTILINE)
TARGET_HEADING = re.compile(r"^### .+ — .+$", re.MULTILINE)
BRANCH_CITATION = re.compile(r"root_\d{6}/B\d{3}")
REQUIRED_FIELDS = (
    "**Primary reading.**",
    "**Ayah-level surprise.**",
    "**Water-root resonance.**",
    "**Activation trace.**",
    "**Negative evidence.**",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sections(text: str) -> list[tuple[str, str]]:
    matches = list(CASE_HEADING.finditer(text))
    return [
        (
            f"{match.group(1)}:{match.group(2)}",
            text[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(text)],
        )
        for index, match in enumerate(matches)
    ]


def validate_response(packet: dict[str, Any], response_path: Path) -> list[str]:
    errors: list[str] = []
    text = response_path.read_text(encoding="utf-8")
    expected_title = f"# {packet['batch_id']} Water Secondary Resonance"
    if not text.startswith(expected_title):
        errors.append(f"{response_path.name}: title mismatch")
    parsed_sections = sections(text)
    actual_refs = [ref for ref, _ in parsed_sections]
    expected_refs = [case["focus_ref"] for case in packet["cases"]]
    if actual_refs != expected_refs:
        errors.append(
            f"{response_path.name}: focus heading mismatch; expected {expected_refs}, got {actual_refs}"
        )
        return errors
    for case, (ref, section) in zip(packet["cases"], parsed_sections):
        expected_targets = len(case["focus_targets"])
        target_matches = list(TARGET_HEADING.finditer(section))
        actual_targets = len(target_matches)
        if actual_targets != expected_targets:
            errors.append(
                f"{response_path.name} {ref}: expected {expected_targets} target sections, got {actual_targets}"
            )
        for field in REQUIRED_FIELDS:
            if section.count(field) != expected_targets:
                errors.append(
                    f"{response_path.name} {ref}: {field} count does not match targets"
                )
        target_blocks = [
            section[
                match.start() : target_matches[index + 1].start()
                if index + 1 < len(target_matches)
                else len(section)
            ]
            for index, match in enumerate(target_matches)
        ]
        for index, (target, block) in enumerate(
            zip(case["focus_targets"], target_blocks), start=1
        ):
            heading = block.splitlines()[0]
            expected_prefix = f"### {target['surface_ar']}"
            expected_root = f" — {target['root_norm']}"
            if not heading.startswith(expected_prefix) or expected_root not in heading:
                errors.append(
                    f"{response_path.name} {ref} target {index}: target heading/order mismatch"
                )
            if "**Water-root resonance.**" not in block or "**Activation trace.**" not in block:
                continue
            resonance_text = block.split("**Water-root resonance.**", 1)[1].split(
                "**Activation trace.**", 1
            )[0]
            has_none = "No secondary water-root branch retained." in resonance_text
            citations = set(BRANCH_CITATION.findall(resonance_text))
            has_branch = bool(citations)
            if not has_none and not has_branch:
                errors.append(
                    f"{response_path.name} {ref} target {index}: resonance has neither branch citation nor explicit none"
                )
            target_inventory = next(
                inventory
                for inventory in case["target_root_inventories"]
                if inventory["family_id"] == target["family_id"]
            )
            allowed = {
                f"{branch['root_id']}/{branch['branch_id']}"
                for branch in target_inventory["branches"]
            }
            invalid = citations - allowed
            if invalid:
                errors.append(
                    f"{response_path.name} {ref} target {index}: citations outside target inventory: {sorted(invalid)}"
                )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", type=Path, default=DEFAULT_RUN)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="fail unless every manifest batch has a response",
    )
    args = parser.parse_args()
    manifest = read_json(args.run_dir / "manifest.json")
    errors: list[str] = []
    validated = 0
    for record in manifest["batches"]:
        packet = read_json(PROJECT / record["packet"])
        response_path = args.run_dir / "responses" / f"{record['batch_id']}.md"
        if not response_path.is_file():
            if args.require_complete:
                errors.append(f"missing response: {response_path.name}")
            continue
        errors.extend(validate_response(packet, response_path))
        validated += 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"validated {validated} response files")


if __name__ == "__main__":
    main()
