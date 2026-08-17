#!/usr/bin/env python3
"""Build a raw-GitHub and Pages friendly access layer for root packets."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_FETCH_BYTES = 15_000
ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
SAFE_PATH_RE = re.compile(r"[^A-Za-z0-9_.-]+")

BUCKWALTER = {
    "ء": "'",
    "آ": "|",
    "أ": ">",
    "ؤ": "&",
    "إ": "<",
    "ئ": "}",
    "ا": "A",
    "ب": "b",
    "ة": "p",
    "ت": "t",
    "ث": "v",
    "ج": "j",
    "ح": "H",
    "خ": "x",
    "د": "d",
    "ذ": "*",
    "ر": "r",
    "ز": "z",
    "س": "s",
    "ش": "$",
    "ص": "S",
    "ض": "D",
    "ط": "T",
    "ظ": "Z",
    "ع": "E",
    "غ": "g",
    "ف": "f",
    "ق": "q",
    "ك": "k",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "ه": "h",
    "و": "w",
    "ى": "Y",
    "ي": "y",
}

ROMAN = {
    "ء": [""],
    "ا": ["a"],
    "ب": ["b"],
    "ت": ["t"],
    "ث": ["th"],
    "ج": ["j"],
    "ح": ["h"],
    "خ": ["kh"],
    "د": ["d"],
    "ذ": ["dh"],
    "ر": ["r"],
    "ز": ["z"],
    "س": ["s"],
    "ش": ["sh"],
    "ص": ["s"],
    "ض": ["d"],
    "ط": ["t"],
    "ظ": ["z"],
    "ع": [""],
    "غ": ["gh"],
    "ف": ["f"],
    "ق": ["q", "k", "ḳ"],
    "ك": ["k"],
    "ل": ["l"],
    "م": ["m"],
    "ن": ["n"],
    "ه": ["h"],
    "و": ["w"],
    "ي": ["y"],
    "ى": ["y"],
}


@dataclass
class RootSummary:
    root_id: str
    safe_id: str
    root_norm: str
    join_key: str
    source_path: str
    raw_url: str
    branch_count: int
    lexical_count: int
    branches: list[dict[str, Any]]
    top_keywords: list[str]


@dataclass
class Candidate:
    root_id: str
    root_norm: str
    join_key: str
    status: str
    scheme: str
    note: str


@dataclass
class AliasEntry:
    alias: str
    candidates: dict[str, Candidate] = field(default_factory=dict)

    def add(self, root: RootSummary, status: str, scheme: str, note: str) -> None:
        existing = self.candidates.get(root.root_id)
        if existing and existing.status == "exact" and status != "exact":
            return
        self.candidates[root.root_id] = Candidate(
            root_id=root.root_id,
            root_norm=root.root_norm,
            join_key=root.join_key,
            status=status,
            scheme=scheme,
            note=note,
        )

    @property
    def is_ambiguous(self) -> bool:
        return len(self.candidates) > 1


def normalize_arabic(value: str) -> str:
    value = ARABIC_DIACRITICS_RE.sub("", value)
    value = value.replace("ـ", "")
    value = value.replace("أ", "ء").replace("إ", "ء").replace("ؤ", "ء").replace("ئ", "ء")
    value = value.replace("آ", "ا").replace("ى", "ي")
    return " ".join(value.split())


def compact_arabic(value: str) -> str:
    return normalize_arabic(value).replace(" ", "")


def safe_path_id(value: str) -> str:
    safe = SAFE_PATH_RE.sub("-", value).strip("-")
    return safe or "empty"


def escape_html(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def estimated_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def write_text(path: Path, text: str, sizes: dict[str, dict[str, int]], root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    rel = path.relative_to(root).as_posix()
    sizes[rel] = {"bytes": len(text.encode("utf-8")), "estimated_tokens": estimated_tokens(text)}


def buckwalter_root(root_norm: str) -> str:
    return "-".join(BUCKWALTER.get(letter, letter) for letter in root_norm.split())


def roman_forms(root_norm: str) -> set[str]:
    letters = [letter for letter in root_norm.split() if letter]
    pools = [ROMAN.get(letter, [letter]) for letter in letters]
    forms: set[str] = set()

    def walk(index: int, acc: list[str]) -> None:
        if index == len(pools):
            parts = [part for part in acc if part]
            if not parts:
                return
            compact = "".join(parts).lower()
            hyphen = "-".join(parts).lower()
            forms.add(compact)
            forms.add(hyphen)
            if len(parts) == 3:
                forms.add(f"{parts[0]}a{parts[1]}{parts[2]}".lower())
                if parts[2] == "b":
                    forms.add(f"{parts[0]}a{parts[1]}p".lower())
            return
        for value in pools[index][:3]:
            walk(index + 1, acc + [value])

    walk(0, [])
    return {item for item in forms if item and len(item) <= 24}


def qnet_top_keywords(packet: dict[str, Any], limit: int = 12) -> list[str]:
    scores: dict[str, int] = defaultdict(int)
    for branch_qnet in packet.get("qnet", {}).values():
        for row in branch_qnet.get("keywords", []):
            keyword = str(row.get("keyword") or "").strip()
            keyword_type = row.get("keyword_type")
            if not keyword or keyword_type not in {"core", "bridge"}:
                continue
            scores[keyword] += int(row.get("replicate_votes") or 1)
    return [key for key, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def branch_gist(branch: dict[str, Any]) -> str:
    ar = branch.get("branch_image_ar") or ""
    en = branch.get("branch_image_en") or ""
    status = branch.get("status") or ""
    return f"{branch.get('branch_id')}: {ar} / {en} [{status}]"


def load_roots(input_dir: Path, raw_base_url: str) -> list[RootSummary]:
    roots: list[RootSummary] = []
    for packet_path in sorted(input_dir.glob("root_*.json")):
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        root_id = packet["root_envelope_id"]
        root_norm = str(packet.get("root_norm") or "")
        join_key = str(packet.get("root_join_key") or compact_arabic(root_norm))
        roots.append(
            RootSummary(
                root_id=root_id,
                safe_id=safe_path_id(root_id),
                root_norm=root_norm,
                join_key=join_key,
                source_path=packet_path.as_posix(),
                raw_url=f"{raw_base_url.rstrip('/')}/{packet_path.name}",
                branch_count=len(packet.get("branches", [])),
                lexical_count=len(packet.get("lexical_senses", [])),
                branches=packet.get("branches", []),
                top_keywords=qnet_top_keywords(packet),
            )
        )
    return roots


def add_alias(
    aliases: dict[str, AliasEntry],
    alias: str,
    root: RootSummary,
    status: str,
    scheme: str,
    note: str,
) -> None:
    alias = alias.strip().lower() if alias.isascii() else alias.strip()
    if not alias:
        return
    aliases.setdefault(alias, AliasEntry(alias)).add(root, status, scheme, note)


def build_aliases(roots: list[RootSummary]) -> dict[str, AliasEntry]:
    aliases: dict[str, AliasEntry] = {}
    for root in roots:
        add_alias(aliases, root.root_id, root, "exact", "root_id", "Opaque root envelope ID.")
        add_alias(aliases, root.root_norm, root, "exact", "arabic_spaced", "Arabic root with spaces.")
        add_alias(aliases, root.join_key, root, "exact", "arabic_join_key", "Arabic compact root key.")
        add_alias(aliases, normalize_arabic(root.root_norm), root, "candidate", "arabic_normalized", "Normalized Arabic recall key; not identity.")
        add_alias(aliases, compact_arabic(root.root_norm), root, "candidate", "arabic_compact_normalized", "Compact normalized Arabic recall key; not identity.")
        add_alias(aliases, buckwalter_root(root.root_norm), root, "candidate", "buckwalter", "Strict machine transliteration; candidate only.")
        for form in roman_forms(root.root_norm):
            add_alias(aliases, form, root, "candidate", "latin_romanized", "Human Latin recall alias; candidate only.")
    return aliases


def alias_category(alias: str) -> tuple[str, str]:
    if alias.startswith("root_"):
        return ("root-id", alias[:9])
    first = alias[:1]
    if not first:
        return ("other", "empty")
    if "\u0600" <= first <= "\u06ff":
        return ("arabic", f"u{ord(first):04x}")
    if first.isascii() and first.isalnum():
        return ("latin", first.lower())
    return ("symbol", f"u{ord(first):04x}")


def candidate_block(entry: AliasEntry, roots_by_id: dict[str, RootSummary]) -> str:
    candidates = [entry.candidates[key] for key in sorted(entry.candidates)]
    status = "ambiguous" if entry.is_ambiguous else candidates[0].status
    lines = [
        f"## `{entry.alias}`",
        f"status: `{status}`; primary: `none`",
    ]
    if entry.is_ambiguous:
        lines.append("- Ambiguous roots: " + ", ".join(f"`{candidate.root_id}`" for candidate in candidates))
    for candidate in candidates:
        root = roots_by_id[candidate.root_id]
        gist = "; ".join(
            f"{branch.get('branch_id')} {branch.get('branch_image_ar') or ''}"
            for branch in root.branches
        )
        lines.append(
            f"- `{root.root_id}` {root.root_norm} (`{candidate.status}; {candidate.scheme}`): {gist}"
        )
        lines.append(
            f"  Links: [card](../root/{root.safe_id}/card.md), "
            f"[branches](../root/{root.safe_id}/branches.md)"
        )
    lines.append("")
    return "\n".join(lines)


def render_bucket(title: str, entries: list[AliasEntry], roots_by_id: dict[str, RootSummary]) -> str:
    lines = [
        f"# {title}",
        "",
        "Latin aliases are recall candidates only. Arabic/root IDs are authoritative.",
        "If a section says `ambiguous`, do not choose a primary root without Arabic evidence.",
        "",
        "[Back to LOOKUP](../LOOKUP.md)",
        "",
    ]
    for entry in entries:
        lines.append(candidate_block(entry, roots_by_id))
    return "\n".join(lines)


def write_lookup_buckets(
    output_dir: Path,
    aliases: dict[str, AliasEntry],
    roots_by_id: dict[str, RootSummary],
    sizes: dict[str, dict[str, int]],
) -> list[tuple[str, str, str, str, int]]:
    grouped: dict[tuple[str, str], list[AliasEntry]] = defaultdict(list)
    for entry in aliases.values():
        grouped[alias_category(entry.alias)].append(entry)

    lookup_links: list[tuple[str, str, str, str, int]] = []
    for (category, key), entries in sorted(grouped.items()):
        entries = sorted(entries, key=alias_sort_key)
        chunk: list[AliasEntry] = []
        chunk_start = ""
        chunk_index = 1
        file_prefix = lookup_file_prefix(category, key)
        for entry in entries:
            trial = chunk + [entry]
            entry_label = alias_sort_key(entry)
            title = f"Lookup {category} {key}: {chunk_start or entry_label} to {entry_label}"
            rendered = render_bucket(title, trial, roots_by_id)
            if chunk and len(rendered.encode("utf-8")) > MAX_FETCH_BYTES:
                last = alias_sort_key(chunk[-1])
                filename = f"b/{file_prefix}-{chunk_index:03d}.md"
                title = f"Lookup {category} {key}: {chunk_start} to {last}"
                text = render_bucket(title, chunk, roots_by_id)
                write_text(output_dir / filename, text, sizes, output_dir)
                lookup_links.append((filename, category, key, f"{chunk_start} to {last}", len(chunk)))
                chunk = [entry]
                chunk_start = entry_label
                chunk_index += 1
            else:
                if not chunk:
                    chunk_start = entry_label
                chunk = trial
        if chunk:
            last = alias_sort_key(chunk[-1])
            filename = f"b/{file_prefix}-{chunk_index:03d}.md"
            title = f"Lookup {category} {key}: {chunk_start} to {last}"
            text = render_bucket(title, chunk, roots_by_id)
            write_text(output_dir / filename, text, sizes, output_dir)
            lookup_links.append((filename, category, key, f"{chunk_start} to {last}", len(chunk)))
    return lookup_links


def alias_sort_key(entry: AliasEntry) -> str:
    if entry.alias and "\u0600" <= entry.alias[:1] <= "\u06ff":
        return entry.alias.replace(" ", "")
    return entry.alias


def lookup_file_prefix(category: str, key: str) -> str:
    category_prefix = {"arabic": "a", "latin": "l", "root-id": "r", "symbol": "s"}.get(category, "x")
    key = key.removeprefix("u").replace("root_", "r")
    return f"{category_prefix}{key}"


def write_root_files(output_dir: Path, roots: list[RootSummary], sizes: dict[str, dict[str, int]]) -> None:
    for root in roots:
        lines = [
            f"# {root.root_id} - {root.root_norm}",
            "",
            f"- Join key: `{root.join_key}`",
            f"- Source path: `{root.source_path}`",
            f"- Raw packet: [{Path(root.source_path).name}]({root.raw_url})",
            f"- Branch details: [branches.md](branches.md)",
            "",
            "## Branch Gist",
            "",
        ]
        for branch in root.branches:
            lines.append(f"- {branch_gist(branch)}")
        lines.append("")
        write_text(output_dir / "root" / root.safe_id / "card.md", "\n".join(lines), sizes, output_dir)

        detail_header = [
            f"# Branches for {root.root_id} - {root.root_norm}",
            "",
            f"[Back to card](card.md)",
            "",
        ]
        detail_blocks: list[str] = []
        for branch in root.branches:
            detail_blocks.append(
                "\n".join(
                    [
                        f"## {branch.get('branch_id')} - {branch.get('branch_image_ar')}",
                        "",
                        f"- English image: {branch.get('branch_image_en') or ''}",
                        f"- Status: `{branch.get('status') or ''}`",
                        f"- Source phrase: {branch.get('source_phrase_ar') or ''}",
                        f"- What is: {branch.get('what_is_ar') or ''}",
                        f"- What is not: {branch.get('what_is_not_ar') or ''}",
                        "",
                    ]
                )
            )
        write_branch_detail(output_dir / "root" / root.safe_id, detail_header, detail_blocks, sizes, output_dir)


def write_branch_detail(
    root_dir: Path,
    header: list[str],
    blocks: list[str],
    sizes: dict[str, dict[str, int]],
    output_dir: Path,
) -> None:
    full_text = "\n".join(header + blocks)
    if len(full_text.encode("utf-8")) <= MAX_FETCH_BYTES:
        write_text(root_dir / "branches.md", full_text, sizes, output_dir)
        return
    index_lines = header + ["This root has many branch details, split into fetch-sized shards.", ""]
    chunk: list[str] = []
    chunk_index = 1
    for block in blocks:
        trial = chunk + [block]
        text = "\n".join(header + trial)
        if chunk and len(text.encode("utf-8")) > MAX_FETCH_BYTES:
            filename = f"branches-{chunk_index:03d}.md"
            text = "\n".join(header + chunk)
            write_text(root_dir / filename, text, sizes, output_dir)
            index_lines.append(f"- [Branch detail shard {chunk_index}]({filename})")
            chunk = [block]
            chunk_index += 1
        else:
            chunk = trial
    if chunk:
        filename = f"branches-{chunk_index:03d}.md"
        text = "\n".join(header + chunk)
        write_text(root_dir / filename, text, sizes, output_dir)
        index_lines.append(f"- [Branch detail shard {chunk_index}]({filename})")
    write_text(root_dir / "branches.md", "\n".join(index_lines) + "\n", sizes, output_dir)


def write_root_indexes(output_dir: Path, roots: list[RootSummary], sizes: dict[str, dict[str, int]]) -> None:
    buckets: dict[str, list[RootSummary]] = defaultdict(list)
    for root in roots:
        first = root.join_key[:1]
        key = f"u{ord(first):04x}" if first else "empty"
        buckets[key].append(root)

    links: list[tuple[str, str, int]] = []
    for key, bucket in sorted(buckets.items()):
        bucket = sorted(bucket, key=lambda item: item.root_id)
        chunk: list[str] = []
        chunk_index = 1
        for root in bucket:
            row = (
                f"- `{root.root_id}` {root.root_norm}: "
                f"[card](../root/{root.safe_id}/card.md), "
                f"[branches](../root/{root.safe_id}/branches.md), "
                f"[raw]({root.raw_url})"
            )
            trial = chunk + [row]
            text = "\n".join([f"# Root Index {key}", "", "[Back to root index](index.md)", ""] + trial) + "\n"
            if chunk and len(text.encode("utf-8")) > MAX_FETCH_BYTES:
                filename = f"roots/{key}-{chunk_index:03d}.md"
                text = "\n".join([f"# Root Index {key}", "", "[Back to root index](index.md)", ""] + chunk) + "\n"
                write_text(output_dir / filename, text, sizes, output_dir)
                links.append((filename, key, len(chunk)))
                chunk = [row]
                chunk_index += 1
            else:
                chunk = trial
        if chunk:
            filename = f"roots/{key}-{chunk_index:03d}.md"
            text = "\n".join([f"# Root Index {key}", "", "[Back to root index](index.md)", ""] + chunk) + "\n"
            write_text(output_dir / filename, text, sizes, output_dir)
            links.append((filename, key, len(chunk)))

    index_lines = ["# Root Index", "", "Fallback browsing by first Arabic radical.", ""]
    for filename, key, count in links:
        index_lines.append(f"- [{key}]({Path(filename).name}) ({count} roots)")
    write_text(output_dir / "roots/index.md", "\n".join(index_lines) + "\n", sizes, output_dir)


def write_keyword_index(output_dir: Path, roots: list[RootSummary], sizes: dict[str, dict[str, int]]) -> None:
    keyword_rows: dict[str, list[str]] = defaultdict(list)
    for root in roots:
        for keyword in root.top_keywords[:5]:
            keyword_rows[keyword].append(
                f"- `{root.root_id}` {root.root_norm}: [card](../root/{root.safe_id}/card.md), [branches](../root/{root.safe_id}/branches.md)"
            )
    links: list[tuple[str, str, int]] = []
    for keyword, rows in sorted(keyword_rows.items()):
        if len(rows) > 80:
            continue
        key = safe_path_id(keyword.lower())[:40] or "keyword"
        filename = f"keyword/{key}.md"
        text = "\n".join([f"# Keyword: {keyword}", "", "Top-ranked branch keyword index only.", ""] + rows[:80]) + "\n"
        write_text(output_dir / filename, text, sizes, output_dir)
        links.append((filename, keyword, len(rows[:80])))
    index = ["# Keyword Index", "", "Only top-ranked branch keywords are emitted; broad noisy keywords are skipped.", ""]
    chunk: list[str] = []
    chunk_index = 1
    index_links: list[tuple[str, int]] = []
    for filename, keyword, count in links:
        row = f"- [{keyword}]({filename}) ({count})"
        trial = chunk + [row]
        text = "\n".join(["# Keyword Index Shard", "", "[Back to keyword index](index.md)", ""] + trial) + "\n"
        if chunk and len(text.encode("utf-8")) > MAX_FETCH_BYTES:
            shard = f"keyword/index-{chunk_index:03d}.md"
            text = "\n".join(["# Keyword Index Shard", "", "[Back to keyword index](index.md)", ""] + chunk) + "\n"
            write_text(output_dir / shard, text, sizes, output_dir)
            index_links.append((shard, len(chunk)))
            chunk = [row]
            chunk_index += 1
        else:
            chunk = trial
    if chunk:
        shard = f"keyword/index-{chunk_index:03d}.md"
        text = "\n".join(["# Keyword Index Shard", "", "[Back to keyword index](index.md)", ""] + chunk) + "\n"
        write_text(output_dir / shard, text, sizes, output_dir)
        index_links.append((shard, len(chunk)))
    for shard, count in index_links:
        index.append(f"- [{Path(shard).name}]({Path(shard).name}) ({count})")
    write_text(output_dir / "keyword/index.md", "\n".join(index) + "\n", sizes, output_dir)


def write_lookup_entrypoint(
    output_dir: Path,
    lookup_links: list[tuple[str, str, str, str, int]],
    sizes: dict[str, dict[str, int]],
) -> None:
    lines = [
        "# Dictionary Agent Lookup",
        "",
        "Use this as the first file for mobile/sandbox agents.",
        "Every terminal lookup bucket is linked below; do not construct URLs when your fetch tool blocks them.",
        "",
        "Resolution rules:",
        "- Arabic root strings and root IDs are authoritative.",
        "- Latin, Turkish-informed, and Buckwalter forms are candidate-only.",
        "- If a bucket entry says `ambiguous`, there is no primary root. Compare Arabic evidence before analysis.",
        "",
        "## Lookup Buckets",
        "",
    ]
    for filename, category, key, label, count in lookup_links:
        short_category = {"arabic": "ar", "latin": "la", "root-id": "id", "symbol": "sy"}.get(category, category)
        short_label = label.replace(" to ", "..").replace(" ", "")
        lines.append(f"- [{short_category}:{key}:{short_label}]({filename})")
    lines.extend(
        [
            "",
            "## Secondary Browsing",
            "",
            "- [Root index](roots/index.md)",
            "- [Keyword index](keyword/index.md)",
            "- [START_HERE](START_HERE.md)",
            "",
        ]
    )
    write_text(output_dir / "LOOKUP.md", "\n".join(lines), sizes, output_dir)


def write_start_here(output_dir: Path, manifest: dict[str, Any], sizes: dict[str, dict[str, int]]) -> None:
    text = f"""# Dictionary Agent Access

This directory is optimized for agents with small fetch budgets, raw-GitHub-only
network access, or link-gated fetching.

Primary entrypoint: [LOOKUP.md](LOOKUP.md)

Cold-start target:
- <=2 fetches to root identity plus branch gist.
- <=3 fetches to grounded branch detail.
- No constructed URL is required.
- Individual lookup files target <=15KB.

Counts:
- Roots: {manifest["root_count"]}
- Branches: {manifest["branch_count"]}
- Lookup aliases: {manifest["alias_count"]}

If Pages is available, use the same linked flow. If Pages is blocked, use the
raw GitHub copy under `docs/agent`.
"""
    write_text(output_dir / "START_HERE.md", text, sizes, output_dir)


def write_reports(
    output_dir: Path,
    aliases: dict[str, AliasEntry],
    sizes: dict[str, dict[str, int]],
) -> None:
    collisions = [entry for entry in aliases.values() if entry.is_ambiguous]
    lines = ["# Alias Collision Report", "", f"Ambiguous aliases: {len(collisions)}", ""]
    chunk: list[str] = []
    chunk_index = 1
    chunk_links: list[tuple[str, int]] = []
    for entry in sorted(collisions, key=lambda item: item.alias):
        roots = ", ".join(f"`{candidate.root_id}` {candidate.root_norm}" for candidate in entry.candidates.values())
        row = f"- `{entry.alias}` -> {roots}"
        trial = chunk + [row]
        text = "\n".join(["# Alias Collision Report Shard", "", "[Back to collision report](alias-collisions.md)", ""] + trial) + "\n"
        if chunk and len(text.encode("utf-8")) > MAX_FETCH_BYTES:
            filename = f"reports/alias-collisions-{chunk_index:03d}.md"
            text = "\n".join(["# Alias Collision Report Shard", "", "[Back to collision report](alias-collisions.md)", ""] + chunk) + "\n"
            write_text(output_dir / filename, text, sizes, output_dir)
            chunk_links.append((filename, len(chunk)))
            chunk = [row]
            chunk_index += 1
        else:
            chunk = trial
    if chunk:
        filename = f"reports/alias-collisions-{chunk_index:03d}.md"
        text = "\n".join(["# Alias Collision Report Shard", "", "[Back to collision report](alias-collisions.md)", ""] + chunk) + "\n"
        write_text(output_dir / filename, text, sizes, output_dir)
        chunk_links.append((filename, len(chunk)))
    for filename, count in chunk_links:
        lines.append(f"- [{Path(filename).name}]({Path(filename).name}) ({count})")
    write_text(output_dir / "reports/alias-collisions.md", "\n".join(lines) + "\n", sizes, output_dir)


def write_manifest(output_dir: Path, manifest: dict[str, Any], sizes: dict[str, dict[str, int]]) -> None:
    text = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n"
    write_text(output_dir / "manifest.min.json", text, sizes, output_dir)


def prune_untracked_generated_files(output_dir: Path, sizes: dict[str, dict[str, int]]) -> None:
    keep = set(sizes)
    keep.add("manifest.min.json")
    for path in sorted(output_dir.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            rel = path.relative_to(output_dir).as_posix()
            if rel not in keep:
                path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def write_pages_root(output_dir: Path, sizes: dict[str, dict[str, int]]) -> None:
    docs_dir = output_dir.parent
    text = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=agent/LOOKUP.md">
<title>Dictionary Agent Lookup</title>
<body>
<main>
  <h1>Dictionary Agent Lookup</h1>
  <p><a href="agent/LOOKUP.md">Open LOOKUP.md</a></p>
  <p><a href="agent/START_HERE.md">Open START_HERE.md</a></p>
</main>
</body>
</html>
"""
    write_text(docs_dir / "index.html", text, sizes, docs_dir)


def remove_generated_tree(path: Path) -> None:
    if not path.exists():
        return
    for child in sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    path.rmdir()


def build(input_dir: Path, output_dir: Path, raw_base_url: str) -> None:
    if output_dir.exists():
        for attempt in range(5):
            try:
                remove_generated_tree(output_dir)
                break
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(0.2)
    output_dir.mkdir(parents=True)

    sizes: dict[str, dict[str, int]] = {}
    roots = load_roots(input_dir, raw_base_url)
    roots_by_id = {root.root_id: root for root in roots}
    aliases = build_aliases(roots)

    write_root_files(output_dir, roots, sizes)
    write_root_indexes(output_dir, roots, sizes)
    write_keyword_index(output_dir, roots, sizes)
    lookup_links = write_lookup_buckets(output_dir, aliases, roots_by_id, sizes)
    write_lookup_entrypoint(output_dir, lookup_links, sizes)

    manifest = {
        "version": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root_count": len(roots),
        "branch_count": sum(root.branch_count for root in roots),
        "alias_count": len(aliases),
        "max_fetch_bytes": MAX_FETCH_BYTES,
        "entrypoint": "LOOKUP.md",
        "identity_policy": "Arabic/root_id exact; Latin and Turkish-informed aliases are candidate-only; collisions are structurally ambiguous.",
    }
    write_start_here(output_dir, manifest, sizes)
    write_reports(output_dir, aliases, sizes)
    prune_untracked_generated_files(output_dir, sizes)
    write_manifest(output_dir, manifest, sizes)
    write_pages_root(output_dir, sizes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/output/root_packets", type=Path)
    parser.add_argument("--output-dir", default="docs/agent", type=Path)
    parser.add_argument(
        "--raw-base-url",
        default="https://raw.githubusercontent.com/ahmetrasit/dictionary/main/data/output/root_packets",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build(args.input_dir, args.output_dir, args.raw_base_url)


if __name__ == "__main__":
    main()
