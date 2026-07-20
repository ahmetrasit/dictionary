#!/usr/bin/env python3
"""Index and mechanically summarize water secondary-resonance responses."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = PROJECT / "data/output/water_secondary_resonance"
CASE_HEADING = re.compile(r"^## (\d+):(\d+) — ", re.MULTILINE)
TARGET_HEADING = re.compile(r"^### .+ — .+$", re.MULTILINE)
BRANCH_CITATION = re.compile(r"root_\d{6}/B\d{3}")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_sections(text: str, pattern: re.Pattern[str]) -> list[str]:
    matches = list(pattern.finditer(text))
    return [
        text[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        for index, match in enumerate(matches)
    ]


def field(block: str, label: str, next_label: str | None) -> str:
    marker = f"**{label}.**"
    if marker not in block:
        return ""
    value = block.split(marker, 1)[1]
    if next_label:
        value = value.split(f"**{next_label}.**", 1)[0]
    return " ".join(value.split())


def branch_labels(case: dict[str, Any], family_id: str) -> dict[str, str]:
    inventory = next(
        item for item in case["target_root_inventories"] if item["family_id"] == family_id
    )
    return {
        f"{branch['root_id']}/{branch['branch_id']}": branch["image_ar"]
        for branch in inventory["branches"]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    manifest = read_json(args.run_dir / "manifest.json")
    records: list[dict[str, Any]] = []
    frozen_runs = []
    prompt_path = PROJECT / "prompts/water-secondary-resonance-reader.md"

    for batch in manifest["batches"]:
        packet_path = PROJECT / batch["packet"]
        response_path = args.run_dir / "responses" / f"{batch['batch_id']}.md"
        if not response_path.is_file():
            if args.require_complete:
                raise SystemExit(f"missing response: {response_path}")
            continue
        packet = read_json(packet_path)
        text = response_path.read_text(encoding="utf-8")
        case_sections = split_sections(text, CASE_HEADING)
        if len(case_sections) != len(packet["cases"]):
            raise SystemExit(f"case mismatch in {response_path}")
        for case, case_block in zip(packet["cases"], case_sections):
            target_sections = split_sections(case_block, TARGET_HEADING)
            if len(target_sections) != len(case["focus_targets"]):
                raise SystemExit(f"target mismatch in {response_path} at {case['focus_ref']}")
            for target, target_block in zip(case["focus_targets"], target_sections):
                resonance = field(target_block, "Water-root resonance", "Activation trace")
                labels = branch_labels(case, target["family_id"])
                citations = sorted(set(BRANCH_CITATION.findall(resonance)))
                records.append(
                    {
                        "batch_id": batch["batch_id"],
                        "focus_ref": case["focus_ref"],
                        "window": case["window"],
                        "qac_ref": target["qac_ref"],
                        "family_id": target["family_id"],
                        "label_ar": target["label_ar"],
                        "surface_ar": target["surface_ar"],
                        "lemma_ar": target["lemma_ar"],
                        "root_envelope_id": target["root_envelope_id"],
                        "root_norm": target["root_norm"],
                        "primary_reading": field(target_block, "Primary reading", "Ayah-level surprise"),
                        "ayah_level_surprise": field(
                            target_block, "Ayah-level surprise", "Water-root resonance"
                        ),
                        "water_root_resonance": resonance,
                        "activation_trace": field(
                            target_block, "Activation trace", "Negative evidence"
                        ),
                        "negative_evidence": field(target_block, "Negative evidence", None),
                        "explicit_no_secondary": (
                            "No secondary water-root branch retained." in resonance
                        ),
                        "retained_branches": [
                            {"branch": citation, "image_ar": labels.get(citation, "")}
                            for citation in citations
                        ],
                    }
                )
        frozen_runs.append(
            {
                "batch_id": batch["batch_id"],
                "prompt_sha256": sha256(prompt_path),
                "packet": str(packet_path.relative_to(PROJECT)),
                "packet_sha256": sha256(packet_path),
                "response": str(response_path.relative_to(PROJECT)),
                "response_sha256": sha256(response_path),
            }
        )

    family_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        family_records[record["family_id"]].append(record)
    family_summary = []
    family_order = {row["family_id"]: index for index, row in enumerate(manifest["family_stats"])}
    for family_id, items in sorted(family_records.items(), key=lambda item: family_order[item[0]]):
        branch_counts: Counter[tuple[str, str]] = Counter()
        for item in items:
            branch_counts.update(
                (branch["branch"], branch["image_ar"]) for branch in item["retained_branches"]
            )
        family_summary.append(
            {
                "family_id": family_id,
                "label_ar": items[0]["label_ar"],
                "target_morphemes": len(items),
                "focus_ayat": len({item["focus_ref"] for item in items}),
                "targets_with_secondary": sum(bool(item["retained_branches"]) for item in items),
                "targets_with_explicit_none": sum(item["explicit_no_secondary"] for item in items),
                "retained_branch_mentions": sum(len(item["retained_branches"]) for item in items),
                "branch_counts": [
                    {"branch": branch, "image_ar": image, "target_count": count}
                    for (branch, image), count in branch_counts.most_common()
                ],
            }
        )

    index = {
        "protocol": "water-secondary-resonance-v1",
        "completed_batches": len(frozen_runs),
        "indexed_targets": len(records),
        "family_summary": family_summary,
        "records": records,
    }
    write_json(args.run_dir / "resonance_index.json", index)
    write_json(
        args.run_dir / "frozen_responses.json",
        {
            "protocol": "water-secondary-resonance-v1",
            "prompt": str(prompt_path.relative_to(PROJECT)),
            "completed_batches": len(frozen_runs),
            "runs": frozen_runs,
        },
    )

    lines = [
        "# Mechanical Resonance Summary",
        "",
        "> Counts below index reader decisions; they do not adjudicate evidentiary strength.",
        "",
        "| Family | Targets | Focus ayat | With secondary | Explicit none | Branch mentions |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in family_summary:
        lines.append(
            f"| {row['label_ar']} (`{row['family_id']}`) | {row['target_morphemes']} | "
            f"{row['focus_ayat']} | {row['targets_with_secondary']} | "
            f"{row['targets_with_explicit_none']} | {row['retained_branch_mentions']} |"
        )
    lines.extend(["", "## Branch Counts", ""])
    for row in family_summary:
        lines.append(f"### {row['label_ar']} (`{row['family_id']}`)")
        if not row["branch_counts"]:
            lines.extend(["", "No secondary branches retained.", ""])
            continue
        lines.append("")
        for branch in row["branch_counts"]:
            lines.append(
                f"- `{branch['branch']}` ({branch['image_ar']}): {branch['target_count']} targets"
            )
        lines.append("")
    (args.run_dir / "mechanical_summary.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )
    print(f"indexed {len(records)} targets from {len(frozen_runs)} response files")


if __name__ == "__main__":
    main()
