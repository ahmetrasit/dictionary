#!/usr/bin/env python3
"""Smoke-test the raw/link-gated dictionary agent access layer."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ENTRYPOINT_MAX_BYTES = 20_000
TERMINAL_MAX_BYTES = 15_000
LINK_RE = re.compile(r"^- \[(?P<label>[^\]]+)\]\((?P<target>[^)]+)\)")


@dataclass
class Fetch:
    path: Path
    text: str

    @property
    def bytes(self) -> int:
        return len(self.text.encode("utf-8"))


class LinkGatedHarness:
    def __init__(self, root: Path):
        self.root = root
        self.allowed: set[Path] = set()
        self.fetches: list[Fetch] = []

    def fetch_entrypoint(self) -> Fetch:
        return self._fetch(self.root / "LOOKUP.md", entrypoint=True)

    def fetch_link(self, current: Fetch, target: str) -> Fetch:
        path = (current.path.parent / target).resolve()
        if path not in self.allowed:
            raise AssertionError(f"constructed or unseen URL blocked: {target}")
        return self._fetch(path)

    def _fetch(self, path: Path, entrypoint: bool = False) -> Fetch:
        path = path.resolve()
        if not path.is_file():
            raise AssertionError(f"missing fetch target: {path}")
        text = path.read_text(encoding="utf-8")
        fetch = Fetch(path=path, text=text)
        limit = ENTRYPOINT_MAX_BYTES if entrypoint else TERMINAL_MAX_BYTES
        if fetch.bytes > limit:
            raise AssertionError(f"{path} is {fetch.bytes} bytes, above {limit}")
        self.fetches.append(fetch)
        for _label, target in links(text):
            if target.startswith("http://") or target.startswith("https://"):
                continue
            self.allowed.add((path.parent / target).resolve())
        return fetch


def links(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = LINK_RE.match(line)
        if match:
            out.append((match.group("label"), match.group("target")))
    return out


def query_prefix(query: str) -> str:
    if query.startswith("root_"):
        return f"id:{query[:9]}:"
    first = query[:1]
    if "\u0600" <= first <= "\u06ff":
        return f"ar:u{ord(first):04x}:"
    if first.isascii() and first.isalnum():
        return f"la:{first.lower()}:"
    return f"sy:u{ord(first):04x}:"


def label_contains(label: str, query: str) -> bool:
    parts = label.split(":", 2)
    if len(parts) != 3:
        return False
    range_part = parts[2]
    if ".." not in range_part:
        return False
    start, end = range_part.split("..", 1)
    compact_query = query.replace(" ", "")
    return start <= compact_query <= end


def find_bucket(lookup: Fetch, query: str) -> str:
    prefix = query_prefix(query)
    candidates = []
    for label, target in links(lookup.text):
        if label.startswith(prefix) and label_contains(label, query):
            candidates.append(target)
    if not candidates:
        raise AssertionError(f"no visible bucket link for {query!r}")
    if len(candidates) > 1:
        # Ranges can overlap for exact Arabic spaced/compact aliases; the first visible link is enough.
        return candidates[0]
    return candidates[0]


def assert_query(root: Path, query: str, must_contain: list[str], ambiguous: bool = False) -> str:
    root = root.resolve()
    harness = LinkGatedHarness(root)
    lookup = harness.fetch_entrypoint()
    bucket_target = find_bucket(lookup, query)
    bucket = harness.fetch_link(lookup, bucket_target)
    section = f"## `{query}`"
    if section not in bucket.text:
        raise AssertionError(f"{query!r} missing from {bucket.path}")
    for needle in must_contain:
        if needle not in bucket.text:
            raise AssertionError(f"{query!r} expected {needle!r} in {bucket.path}")
    if ambiguous and "- Ambiguous roots:" not in bucket.text:
        raise AssertionError(f"{query!r} should be structurally ambiguous")
    if not ambiguous and "- Ambiguous roots:" in bucket.text.split(section, 1)[1].split("\n## `", 1)[0]:
        raise AssertionError(f"{query!r} unexpectedly ambiguous")
    return f"{query}: {len(harness.fetches)} fetches, {sum(item.bytes for item in harness.fetches)} bytes, bucket={bucket.path.relative_to(root)}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("docs/agent"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = [
        ("قلب", ["`root_001248`", "ق ل ب", "`exact; arabic_join_key`"], False),
        ("ق ل ب", ["`root_001248`", "ق ل ب", "`exact; arabic_spaced`"], False),
        ("qalb", ["`root_001248`", "B001 القلب والفؤاد", "`candidate; latin_romanized`"], False),
        ("qlb", ["`root_001248`", "B004 رد الشيء عن وجهه"], False),
        ("q-l-b", ["`root_001248`", "B007 القليب البئر"], False),
        ("ḳ-l-b", ["`root_001248`", "ق ل ب"], False),
        ("kalb", ["`root_001248`", "`root_001312`", "ك ل ب"], True),
        ("kalp", ["`root_001248`", "`root_001312`", "ك ل ب"], True),
        ("root_001248", ["`root_001248`", "ق ل ب", "`exact; root_id`"], False),
    ]
    results = [assert_query(args.root, query, needles, ambiguous) for query, needles, ambiguous in cases]
    report = "\n".join(["# Agent Access Smoke Results", ""] + [f"- {line}" for line in results]) + "\n"
    report_path = args.root / "reports" / "smoke-results.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
