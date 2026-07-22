#!/usr/bin/env python3
"""Build the static entry manifest consumed by the GitHub Pages viewer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.create_entry import atomic_write, json_content


MANIFEST_FORMAT = "dictionary-v2-entry-manifest-v1"


def load_candidate(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if not isinstance(value.get("branches"), list) or not value["branches"]:
        return None
    if not isinstance(value.get("root_profile"), dict):
        return None
    envelope = value.get("root_envelope_id")
    language = value.get("language")
    if not isinstance(envelope, str) or not isinstance(language, str):
        return None
    if value.get("schema_version") == 4:
        kind = "entry"
        priority = 0
    elif value.get("artifact_format") == "dictionary-v2-root-entry-draft-v1":
        kind = "draft"
        priority = 1
    else:
        return None
    return {
        "root_envelope_id": envelope,
        "language": language,
        "kind": kind,
        "path": path.resolve().relative_to(PROJECT).as_posix(),
        "priority": priority,
    }


def build_manifest() -> dict:
    candidates = [
        *sorted((PROJECT / "v2/entries").glob("*/*.json")),
        *sorted((PROJECT / "v2/work/entry_creation").glob("*/**/output/root_*_entry.json")),
    ]
    selected: dict[tuple[str, str], dict] = {}
    for path in candidates:
        item = load_candidate(path)
        if item is None:
            continue
        key = (item["root_envelope_id"], item["language"])
        previous = selected.get(key)
        if previous is None or item["priority"] < previous["priority"]:
            selected[key] = item
    entries = sorted(
        (
            {key: value for key, value in item.items() if key != "priority"}
            for item in selected.values()
        ),
        key=lambda item: (
            item["root_envelope_id"],
            item["language"],
            item["kind"],
            item["path"],
        ),
    )
    return {"format": MANIFEST_FORMAT, "entries": entries}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "v2/entries/index.json",
    )
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    content = json_content(build_manifest())
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != content:
            raise SystemExit(f"Stale entry manifest: {output}")
        print(f"Checked {output}")
        return 0
    atomic_write(output, content)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
