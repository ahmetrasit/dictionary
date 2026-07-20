#!/usr/bin/env python3
"""Validate per-root, per-focus water secondary-resonance reports."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = REPO_ROOT / "data" / "output" / "water_secondary_resonance"
INDEX_PATH = RUN_DIR / "resonance_index.json"
REPORT_DIR = RUN_DIR / "secondary_reports"
ADJUDICATION_PATHS = (
    RUN_DIR / "adjudication" / "water.md",
    RUN_DIR / "adjudication" / "sea_drink.md",
    RUN_DIR / "adjudication" / "remaining.md",
)
FOCUS_HEADING = re.compile(r"^## (\d+:\d+)\s*$", re.MULTILINE)
FIELD_PATTERNS = {
    "window": re.compile(r"\*\*Pencere:\*\*"),
    "target": re.compile(r"\*\*Hedef(?:ler| \d+)?:\*\*"),
    "primary": re.compile(r"\*\*(?:Türkçe )?[Bb]irincil anlam:\*\*"),
    "surprise": re.compile(
        r"\*\*(?:Türkçe )?[Bb]eş[- ]ayet(?:lik)? "
        r"(?:sürpriz(?:i)?|şaşırtıcılık):\*\*"
        r"|\*\*Şaşırtıcı unsur:\*\*"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Validate only this root id; may be supplied more than once.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    expected: dict[str, set[str]] = defaultdict(set)
    records_by_root_focus: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for record in index["records"]:
        root_id = record["root_envelope_id"]
        focus_ref = record["focus_ref"]
        expected[root_id].add(focus_ref)
        records_by_root_focus[(root_id, focus_ref)].append(record)

    if args.roots:
        selected = set(args.roots)
        unknown = sorted(selected - set(expected))
        if unknown:
            raise SystemExit(f"Unknown root ids: {', '.join(unknown)}")
        expected = {root_id: expected[root_id] for root_id in sorted(selected)}

    errors: list[str] = []
    actual_files = {path.stem: path for path in REPORT_DIR.glob("root_*.md")}
    if not args.roots and set(actual_files) != set(expected):
        missing = sorted(set(expected) - set(actual_files))
        extra = sorted(set(actual_files) - set(expected))
        if missing:
            errors.append(f"missing root reports: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected root reports: {', '.join(extra)}")

    section_count = 0
    for root_id, focus_refs in sorted(expected.items()):
        path = actual_files.get(root_id)
        if path is None:
            continue
        text = path.read_text(encoding="utf-8")
        matches = list(FOCUS_HEADING.finditer(text))
        found = [match.group(1) for match in matches]
        if len(found) != len(set(found)):
            errors.append(f"{path}: duplicate focus heading")
        missing_refs = sorted(focus_refs - set(found))
        extra_refs = sorted(set(found) - focus_refs)
        if missing_refs:
            errors.append(f"{path}: missing focus refs {', '.join(missing_refs)}")
        if extra_refs:
            errors.append(f"{path}: unexpected focus refs {', '.join(extra_refs)}")

        for number, match in enumerate(matches):
            end = matches[number + 1].start() if number + 1 < len(matches) else len(text)
            section = text[match.end() : end]
            for field, pattern in FIELD_PATTERNS.items():
                if not pattern.search(section):
                    errors.append(f"{path}:{match.group(1)} missing {field} field")
            records = records_by_root_focus[(root_id, match.group(1))]
            candidate_count = sum(
                len(record["retained_branches"]) for record in records
            )
            candidate_blocks = sum(
                1
                for line in section.splitlines()
                if (
                    ("**Aday" in line and re.search(r"B\d{3}", line))
                    or re.match(r"^\*\*[^*\n]*B\d{3}\b", line)
                )
            )
            if candidate_blocks != candidate_count:
                errors.append(
                    f"{path}:{match.group(1)} has {candidate_blocks} candidate "
                    f"blocks for {candidate_count} indexed candidates"
                )
            for record in records:
                qac_ref = str(record["qac_ref"])
                if qac_ref not in section:
                    errors.append(f"{path}:{match.group(1)} missing target {qac_ref}")
                for retained in record["retained_branches"]:
                    branch = str(retained["branch"])
                    if branch not in section and branch.rsplit("/", 1)[-1] not in section:
                        errors.append(
                            f"{path}:{match.group(1)} missing candidate {branch}"
                        )
            section_count += 1

    if not args.roots:
        expected_grades: Counter[str] = Counter()
        for path in ADJUDICATION_PATHS:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.startswith("|"):
                    continue
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                if not any(re.match(r"^\d+:\d+", cell) for cell in cells):
                    continue
                for cell in cells:
                    if cell in {"A", "B", "C", "Reject"}:
                        expected_grades[cell] += 1

        report_text = "\n".join(
            path.read_text(encoding="utf-8") for path in actual_files.values()
        )
        actual_grades = Counter(
            {
                "A": report_text.count("A — güçlü"),
                "B": report_text.count("B — destekli"),
                "C": report_text.count("C — keşifsel/zayıf"),
                "Reject": report_text.count("REJECT — reddedildi"),
            }
        )
        if actual_grades != expected_grades:
            errors.append(
                f"grade counts differ: reports={dict(actual_grades)}, "
                f"adjudication={dict(expected_grades)}"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"validated {len(expected)} root reports with "
        f"{section_count} family-level focus sections"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
