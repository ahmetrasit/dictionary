"""Protect evidence pinned by reviewed or published v2 entries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def protect_pinned_entries(
    project: Path,
    envelope: str,
    languages: Iterable[str],
    *,
    force: bool,
    scope: str,
) -> None:
    if force:
        return
    for language in languages:
        path = project / "v2/entries" / language / f"{envelope}.json"
        if not path.exists():
            continue
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Refusing to replace {scope} pinned by unreadable entry without "
                f"--force: {path}"
            ) from error
        if not isinstance(entry, dict):
            raise ValueError(
                f"Refusing to replace {scope} pinned by invalid entry without "
                f"--force: {path}"
            )
        if entry.get("status") in {"reviewed", "published"}:
            raise ValueError(
                f"Refusing to replace {scope} pinned by {entry['status']!r} entry "
                f"without --force: {path}"
            )
