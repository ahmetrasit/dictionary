#!/usr/bin/env python3
"""Build a static, token-efficient agent access layer for root packets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
WHITESPACE_RE = re.compile(r"\s+")
ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06ff]")
STATUS_RANK = {"candidate": 0, "strong": 1, "exact": 2}
HAMZA_ALIF_CHARS = set("ءأإؤئآاٱ")
WEAK_CHARS = ("و", "ي", "ى", "ا")

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


def normalize_arabic(value: str) -> str:
    """Normalize only for candidate retrieval; never use this as identity."""
    value = ARABIC_DIACRITICS_RE.sub("", value)
    value = value.replace("ـ", "")
    value = value.replace("ٱ", "ا")
    value = value.replace("أ", "ء").replace("إ", "ء").replace("ؤ", "ء").replace("ئ", "ء")
    value = value.replace("آ", "ا").replace("ى", "ي")
    return WHITESPACE_RE.sub(" ", value).strip()


def compact_arabic(value: str) -> str:
    return normalize_arabic(value).replace(" ", "")


def fold_hamza_alif(value: str) -> str:
    """Candidate-only fold for common hamza/alif user input variants."""
    value = ARABIC_DIACRITICS_RE.sub("", value)
    value = value.replace("ـ", "")
    for char in HAMZA_ALIF_CHARS:
        value = value.replace(char, "ا")
    value = value.replace("ى", "ي")
    return WHITESPACE_RE.sub(" ", value).strip()


def compact_fold_hamza_alif(value: str) -> str:
    return fold_hamza_alif(value).replace(" ", "")


def weak_root_variants(root_norm: str) -> list[str]:
    letters = [letter for letter in root_norm.split() if letter]
    if not 2 <= len(letters) <= 5:
        return []
    variants: set[str] = set()
    for index, letter in enumerate(letters):
        if letter not in WEAK_CHARS:
            continue
        for replacement in WEAK_CHARS:
            if replacement == letter:
                continue
            candidate = letters.copy()
            candidate[index] = replacement
            variants.add(" ".join(candidate))
    return sorted(variants)


def buckwalter_root(root_norm: str) -> str:
    letters = [letter for letter in root_norm.split() if letter]
    return "-".join(BUCKWALTER.get(letter, letter) for letter in letters)


def text_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def first_values(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        value = text_or_empty(value)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
        if len(out) >= limit:
            break
    return out


def alias_bucket(raw_alias: str, prefix_len: int) -> str:
    value = ARABIC_DIACRITICS_RE.sub("", raw_alias)
    value = value.replace("ـ", "")
    value = "".join(value.strip().lower().split())
    if not value:
        return "empty"
    codepoints = [f"u{ord(char):04x}" for char in value[:prefix_len]]
    return "-".join(codepoints)


def alias_bucket_path(rel_dir: str, bucket: str) -> str:
    return f"{rel_dir.rstrip('/')}/{bucket}.min.json"


def sorted_alias_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda item: (
            -STATUS_RANK.get(item.get("status", "candidate"), 0),
            item.get("root_id", ""),
            item.get("root_norm", ""),
        ),
    )


def qnet_keywords(packet: dict[str, Any], limit: int = 24) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for branch_qnet in packet.get("qnet", {}).values():
        for row in branch_qnet.get("keywords", []):
            keyword = text_or_empty(row.get("keyword"))
            if not keyword:
                continue
            counts[keyword] += int(row.get("replicate_votes") or 1)
    return [
        keyword
        for keyword, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def branch_record(packet: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    branch_ref = f"{branch.get('root_id')}/{branch.get('branch_id')}"
    qnet = packet.get("qnet", {}).get(branch_ref, {})
    keywords = [
        row.get("keyword")
        for row in qnet.get("keywords", [])
        if row.get("keyword_type") in {"core", "bridge"} and row.get("keyword")
    ]
    neighbors = [
        {
            "root_id": item.get("root_id"),
            "branch_id": item.get("branch_id"),
            "root_norm": item.get("root_norm"),
            "branch_image_ar": item.get("branch_image_ar"),
            "shared_consensus_core": item.get("shared_consensus_core", []),
        }
        for item in qnet.get("neighbors", [])[:8]
    ]
    return {
        "root_envelope_id": packet.get("root_envelope_id"),
        "root_norm": packet.get("root_norm"),
        "branch_ref": branch_ref,
        "branch_id": branch.get("branch_id"),
        "branch_image_ar": branch.get("branch_image_ar"),
        "branch_image_en": branch.get("branch_image_en"),
        "what_is_ar": branch.get("what_is_ar"),
        "what_is_not_ar": branch.get("what_is_not_ar"),
        "source_phrase_ar": branch.get("source_phrase_ar"),
        "status": branch.get("status"),
        "sources": branch.get("source_refs"),
        "keywords": first_values(keywords, 16),
        "neighbors": neighbors,
    }


def branch_source_filename(branch: dict[str, Any]) -> str:
    root_id = text_or_empty(branch.get("root_id"))
    branch_id = text_or_empty(branch.get("branch_id"))
    return f"{root_id}--{branch_id}.source.json"


def branch_select_record(packet: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    branch_ref = f"{branch.get('root_id')}/{branch.get('branch_id')}"
    source = f"branch/{branch_source_filename(branch)}"
    return {
        "root_envelope_id": packet.get("root_envelope_id"),
        "root_norm": packet.get("root_norm"),
        "branch_ref": branch_ref,
        "branch_id": branch.get("branch_id"),
        "branch_image_ar": branch.get("branch_image_ar"),
        "branch_image_en": branch.get("branch_image_en"),
        "what_is_ar": branch.get("what_is_ar"),
        "what_is_not_ar": branch.get("what_is_not_ar"),
        "status": branch.get("status"),
        "source": source,
        "source_path": f"root/{packet.get('root_envelope_id')}/{source}",
    }


def branch_source_record(packet: dict[str, Any], branch: dict[str, Any]) -> dict[str, Any]:
    branch_ref = f"{branch.get('root_id')}/{branch.get('branch_id')}"
    return {
        "root_envelope_id": packet.get("root_envelope_id"),
        "root_norm": packet.get("root_norm"),
        "branch_ref": branch_ref,
        "branch_id": branch.get("branch_id"),
        "branch_image_ar": branch.get("branch_image_ar"),
        "branch_image_en": branch.get("branch_image_en"),
        "what_is_ar": branch.get("what_is_ar"),
        "what_is_not_ar": branch.get("what_is_not_ar"),
        "source_phrase_ar": branch.get("source_phrase_ar"),
        "source_refs": branch.get("source_refs"),
        "review_note": branch.get("review_note"),
        "status": branch.get("status"),
    }


def route_note_fields(route_note: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    normalized = route_note.replace(":", ";")
    for part in normalized.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        if key:
            fields[key] = value.strip()
    return fields


def route_record(source: dict[str, Any]) -> dict[str, Any]:
    route_note = text_or_empty(source.get("route_note"))
    fields = route_note_fields(route_note)
    return {
        "root_id": source.get("root_id"),
        "source_id": source.get("source_id"),
        "route_status": source.get("route_status"),
        "match_method": fields.get("match_method", ""),
        "role": fields.get("role", ""),
        "route_basis": fields.get("route_basis", ""),
        "route_source": fields.get("route_source", ""),
        "db_root_norm": source.get("db_root_norm"),
        "headword": source.get("headword"),
        "lemma": source.get("lemma"),
        "source_ref": source.get("source_ref"),
        "route_note": route_note,
    }


def route_summary(route_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in route_rows:
        status = text_or_empty(row.get("route_status")) or "unknown"
        method = text_or_empty(row.get("match_method"))
        role = text_or_empty(row.get("role"))
        key = status
        if method:
            key = f"{key}:{method}"
        elif role:
            key = f"{key}:role={role}"
        counts[key] += 1
    return dict(sorted(counts.items()))


def occurrence_record(packet: dict[str, Any], occurrence: dict[str, Any]) -> dict[str, Any]:
    return {
        "root_envelope_id": packet.get("root_envelope_id"),
        "root_norm": packet.get("root_norm"),
        "qac_ref": occurrence.get("qac_ref"),
        "surah": occurrence.get("surah"),
        "ayah": occurrence.get("ayah"),
        "word_index": occurrence.get("word_index"),
        "surface_ar": occurrence.get("surface_ar"),
        "stem_ar": occurrence.get("stem_ar"),
        "lemma_ar": occurrence.get("lemma_ar"),
        "root_ar": occurrence.get("root_ar"),
        "pos": occurrence.get("pos"),
        "measure": occurrence.get("measure"),
        "morph_features": occurrence.get("morph_features"),
    }


def root_card(packet: dict[str, Any], rel_root: str, source_path: str, raw_url: str) -> str:
    root_id = packet["root_envelope_id"]
    root_norm = packet.get("root_norm", "")
    join_key = packet.get("root_join_key", "")
    v4_roots = packet.get("v4_roots", [])
    branches = packet.get("branches", [])
    lexical = packet.get("lexical_senses", [])
    keywords = qnet_keywords(packet)
    source_roots = first_values(
        [row.get("source_root_norm", "") for row in v4_roots] + [root_norm],
        8,
    )

    lines = [
        f"# {root_id} - {root_norm}",
        "",
        "This is the compact agent card. Use it before opening branches or the full packet.",
        "",
        "## Identity",
        "",
        f"- Canonical envelope ID: `{root_id}`",
        f"- Canonical Arabic root: `{root_norm}`",
        f"- Arabic join key: `{join_key}`",
        f"- Source root variants: {', '.join(f'`{item}`' for item in source_roots) or '-'}",
        f"- Full packet source path: `{source_path}`",
        f"- Full packet raw URL: `{raw_url}`",
        f"- Static full metadata: `{rel_root}/full.json`",
        f"- V4 route summary: `{rel_root}/routes.min.json`",
        f"- Branch selection: `{rel_root}/branches.select.min.json`",
        f"- Branch details: `{rel_root}/branches.json`",
        f"- Compact occurrences: `{rel_root}/occurrences.compact.json`",
        "",
        "## Lookup Safety",
        "",
        "Arabic-script identity is authoritative. Strict transliteration aliases are lookup aids.",
        "Loose ASCII should only produce candidates; it must not silently decide the root.",
        "",
        "## Branch Images",
        "",
    ]
    for branch in branches[:32]:
        lines.append(
            f"- `{branch.get('branch_id')}`: {branch.get('branch_image_ar')} / "
            f"{branch.get('branch_image_en')} [{branch.get('status')}]"
        )
    if len(branches) > 32:
        lines.append(f"- ... {len(branches) - 32} more branches in `branches.json`")

    route_rows = [route_record(source) for source in packet.get("dictionary_sources", [])]
    if route_rows:
        lines.extend(["", "## V4 Routes", ""])
        lines.append("Open `routes.min.json` before deciding whether a source root is dominant, weak, or composite.")
        v4_roots = packet.get("v4_roots", [])
        for item in v4_roots[:12]:
            lines.append(
                f"- `{item.get('root_id')}`: source `{item.get('source_root_norm')}`; "
                f"registry `{item.get('registry_status')}`"
            )
        summary = route_summary(route_rows)
        for key, count in list(summary.items())[:16]:
            lines.append(f"- route `{key}`: {count}")

    lines.extend(["", "## Lexical Units", ""])
    for item in lexical[:24]:
        lines.append(
            f"- `{item.get('lexical_unit_id')}`: {item.get('expression_ar')} - {item.get('sense_en')}"
        )
    if len(lexical) > 24:
        lines.append(f"- ... {len(lexical) - 24} more lexical units in `full.json`")

    if keywords:
        lines.extend(["", "## QNet Keywords", "", ", ".join(f"`{k}`" for k in keywords)])

    lines.extend(
        [
            "",
            "## Retrieval Rule",
            "",
            "If the user query is Latin/ASCII or otherwise ambiguous, use",
            "`aliases.index.min.json` shards first, then compare every plausible candidate card.",
            "If the root is known and only a branch audit is needed, open `branches.select.min.json`,",
            "choose the matching branch by `branch_image_ar` and `what_is_ar`, then open only",
            "the branch `source` path for source evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def add_alias(
    aliases: dict[str, list[dict[str, Any]]],
    raw_alias: str,
    root_id: str,
    root_norm: str,
    scheme: str,
    status: str,
    _note: str = "",
) -> None:
    raw_alias = text_or_empty(raw_alias)
    if not raw_alias:
        return
    bucket = aliases[raw_alias]
    for candidate in bucket:
        if candidate["root_id"] == root_id and candidate["root_norm"] == root_norm:
            schemes = set(candidate.get("schemes", []))
            schemes.add(scheme)
            candidate["schemes"] = sorted(schemes)
            if STATUS_RANK.get(status, 0) > STATUS_RANK.get(candidate.get("status", "candidate"), 0):
                candidate["status"] = status
            return
    bucket.append(
        {
            "root_id": root_id,
            "root_norm": root_norm,
            "status": status,
            "schemes": [scheme],
        }
    )


def add_alias_many(
    stores: list[dict[str, list[dict[str, Any]]]],
    raw_alias: str,
    root_id: str,
    root_norm: str,
    scheme: str,
    status: str,
    note: str = "",
) -> None:
    for store in stores:
        add_alias(store, raw_alias, root_id, root_norm, scheme, status, note)


def add_root_alias(
    aliases: dict[str, list[dict[str, Any]]],
    lookup_aliases: dict[str, list[dict[str, Any]]],
    raw_alias: str,
    root_id: str,
    root_norm: str,
    scheme: str,
    status: str,
    note: str = "",
) -> None:
    add_alias(aliases, raw_alias, root_id, root_norm, scheme, status, note)
    if ARABIC_CHAR_RE.search(text_or_empty(raw_alias)):
        add_alias(lookup_aliases, raw_alias, root_id, root_norm, scheme, "candidate", note)


def add_root_alias_many(
    aliases: dict[str, list[dict[str, Any]]],
    lookup_aliases: dict[str, list[dict[str, Any]]],
    root_aliases: list[tuple[Any, str, str, str]],
    root_id: str,
    root_norm: str,
) -> None:
    for raw_alias, scheme, status, note in root_aliases:
        add_root_alias(
            aliases,
            lookup_aliases,
            str(raw_alias),
            root_id,
            root_norm,
            scheme,
            status,
            note,
        )


def add_arabic_recall_aliases(
    aliases: dict[str, list[dict[str, Any]]],
    value: str,
    root_id: str,
    root_norm: str,
    scheme_prefix: str,
) -> None:
    value = text_or_empty(value)
    if not value or not ARABIC_CHAR_RE.search(value):
        return
    add_alias(aliases, value, root_id, root_norm, f"{scheme_prefix}_exact", "candidate")
    add_alias(aliases, normalize_arabic(value), root_id, root_norm, f"{scheme_prefix}_normalized", "candidate")
    add_alias(aliases, compact_arabic(value), root_id, root_norm, f"{scheme_prefix}_normalized_compact", "candidate")
    add_alias(aliases, fold_hamza_alif(value), root_id, root_norm, f"{scheme_prefix}_hamza_alif_folded", "candidate")
    add_alias(
        aliases,
        compact_fold_hamza_alif(value),
        root_id,
        root_norm,
        f"{scheme_prefix}_hamza_alif_folded_compact",
        "candidate",
    )


def finalized_aliases(aliases: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {
        key: sorted_alias_candidates(value)
        for key, value in sorted(aliases.items())
        if key
    }


def write_alias_shards(
    output_dir: Path,
    aliases: dict[str, list[dict[str, Any]]],
    rel_dir: str,
    label: str,
    prefix_len: int,
    include_bucket_map: bool = True,
) -> dict[str, Any]:
    shard_dir = output_dir / rel_dir
    shard_dir.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for raw_alias, candidates in aliases.items():
        bucket = alias_bucket(raw_alias, prefix_len)
        buckets[bucket][raw_alias] = candidates

    bucket_meta: dict[str, dict[str, Any]] = {}
    for bucket, rows in sorted(buckets.items()):
        path = alias_bucket_path(rel_dir, bucket)
        (output_dir / path).write_text(
            json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        first_alias = next(iter(rows)).strip() if rows else ""
        first_alias_key = ARABIC_DIACRITICS_RE.sub("", first_alias).replace("ـ", "")
        bucket_meta[bucket] = {
            "prefix": "".join(first_alias_key.lower().split())[:prefix_len],
            "path": path,
            "alias_count": len(rows),
        }

    index = {
        "label": label,
        "shard_dir": rel_dir.rstrip("/"),
        "alias_count": len(aliases),
        "prefix_len": prefix_len,
        "bucket_rule": f"Open {rel_dir.rstrip('/')}/uXXXX...min.json using the first {prefix_len} lowercased, non-space, non-diacritic query characters. Shorter aliases use the available characters.",
        "hamza_alif_rule": "For ء أ إ ؤ ئ آ ا ٱ variants, also try the same bucket after candidate-only folding those letters to ا.",
        "bucket_count": len(bucket_meta),
    }
    if include_bucket_map:
        index["buckets"] = bucket_meta
    return index


def build(
    input_dir: Path,
    output_dir: Path,
    include_full: bool,
    include_bulk: bool,
    raw_base_url: str,
) -> None:
    packets = sorted(input_dir.glob("root_*.json"))
    if not packets:
        raise SystemExit(f"No root packet JSON files found in {input_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    roots_dir = output_dir / "root"
    roots_dir.mkdir()

    aliases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lookup_aliases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    roots: list[dict[str, Any]] = []
    branches_jsonl: list[str] = []
    occurrences_jsonl: list[str] = []
    concepts: dict[str, list[dict[str, str]]] = defaultdict(list)

    for packet_path in packets:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        root_id = packet["root_envelope_id"]
        root_norm = text_or_empty(packet.get("root_norm"))
        join_key = text_or_empty(packet.get("root_join_key"))
        branch_count = len(packet.get("branches", []))
        lexical_count = len(packet.get("lexical_senses", []))
        rel_root = f"root/{root_id}"
        source_path = packet_path.as_posix()
        raw_url = f"{raw_base_url.rstrip('/')}/{packet_path.name}"
        root_out = roots_dir / root_id
        root_out.mkdir(parents=True, exist_ok=True)

        keywords = qnet_keywords(packet, limit=16)
        roots.append(
            {
                "root_id": root_id,
                "root_norm": root_norm,
                "root_join_key": join_key,
                "branch_count": branch_count,
                "lexical_count": lexical_count,
                "keywords": keywords,
                "card": f"{rel_root}/card.md",
                "routes": f"{rel_root}/routes.min.json",
                "branch_select": f"{rel_root}/branches.select.min.json",
                "branches": f"{rel_root}/branches.json",
                "occurrences": f"{rel_root}/occurrences.compact.json",
                "full_metadata": f"{rel_root}/full.json",
                "source_packet": source_path,
                "raw_packet": raw_url,
            }
        )

        root_aliases = [
            (root_id, "root_id", "exact", "Opaque root envelope ID."),
            (root_norm, "arabic_root_exact", "exact", "Arabic root with spaces."),
            (join_key, "arabic_join_key", "exact", "Arabic root compact join key from packet."),
            (root_norm.replace(" ", ""), "arabic_root_compact_exact", "exact", "Arabic root without spaces."),
            (normalize_arabic(root_norm), "arabic_normalized", "candidate", "Arabic normalized for recall, not identity."),
            (compact_arabic(root_norm), "arabic_normalized_compact", "candidate", "Compact normalized Arabic for recall, not identity."),
            (fold_hamza_alif(root_norm), "arabic_hamza_alif_folded", "candidate", "Hamza/alif-folded Arabic recall alias."),
            (compact_fold_hamza_alif(root_norm), "arabic_hamza_alif_folded_compact", "candidate", "Compact hamza/alif-folded Arabic recall alias."),
            (buckwalter_root(root_norm), "buckwalter_root", "strong", "Reversible machine alias; not reader-facing."),
        ]
        for v4_root in packet.get("v4_roots", []):
            source_root = text_or_empty(v4_root.get("source_root_norm"))
            root_aliases.extend(
                [
                    (v4_root.get("root_id"), "v4_root_id", "exact", "V4 root ID contained by this envelope."),
                    (source_root, "source_root_exact", "exact", "Source root variant from v4_roots."),
                    (source_root.replace(" ", ""), "source_root_compact_exact", "exact", "Compact source-root variant from v4_roots."),
                    (compact_arabic(source_root), "source_root_normalized_compact", "candidate", "Normalized source-root recall alias."),
                    (fold_hamza_alif(source_root), "source_root_hamza_alif_folded", "candidate", "Hamza/alif-folded source-root recall alias."),
                    (compact_fold_hamza_alif(source_root), "source_root_hamza_alif_folded_compact", "candidate", "Compact hamza/alif-folded source-root recall alias."),
                    (buckwalter_root(source_root), "source_root_buckwalter", "strong", "Reversible source-root machine alias."),
                ]
            )
            for weak_variant in weak_root_variants(source_root):
                root_aliases.extend(
                    [
                        (weak_variant, "source_root_weak_variant", "candidate", "Weak-letter source-root recall alias."),
                        (weak_variant.replace(" ", ""), "source_root_weak_variant_compact", "candidate", "Compact weak-letter source-root recall alias."),
                        (normalize_arabic(weak_variant), "source_root_weak_variant_normalized", "candidate", "Normalized weak-letter source-root recall alias."),
                        (compact_arabic(weak_variant), "source_root_weak_variant_normalized_compact", "candidate", "Compact normalized weak-letter source-root recall alias."),
                        (fold_hamza_alif(weak_variant), "source_root_weak_variant_hamza_alif_folded", "candidate", "Hamza/alif-folded weak-letter source-root recall alias."),
                        (compact_fold_hamza_alif(weak_variant), "source_root_weak_variant_hamza_alif_folded_compact", "candidate", "Compact hamza/alif-folded weak-letter source-root recall alias."),
                    ]
                )
        add_root_alias_many(aliases, lookup_aliases, root_aliases, root_id, root_norm)

        for weak_variant in weak_root_variants(root_norm):
            for raw_alias, scheme in (
                (weak_variant, "arabic_weak_variant"),
                (weak_variant.replace(" ", ""), "arabic_weak_variant_compact"),
                (normalize_arabic(weak_variant), "arabic_weak_variant_normalized"),
                (compact_arabic(weak_variant), "arabic_weak_variant_normalized_compact"),
                (fold_hamza_alif(weak_variant), "arabic_weak_variant_hamza_alif_folded"),
                (
                    compact_fold_hamza_alif(weak_variant),
                    "arabic_weak_variant_hamza_alif_folded_compact",
                ),
            ):
                add_root_alias(
                    aliases,
                    lookup_aliases,
                    raw_alias,
                    root_id,
                    root_norm,
                    scheme,
                    "candidate",
                    "Weak-letter variant for recall only.",
                )
        for lexical in packet.get("lexical_senses", []):
            expression = text_or_empty(lexical.get("expression_ar"))
            if len(expression) <= 80:
                add_arabic_recall_aliases(
                    lookup_aliases,
                    expression,
                    root_id,
                    root_norm,
                    "lexical_expression",
                )

        branch_rows = [branch_record(packet, branch) for branch in packet.get("branches", [])]
        branch_select_rows = [
            branch_select_record(packet, branch) for branch in packet.get("branches", [])
        ]
        occurrence_rows = [
            occurrence_record(packet, occurrence)
            for occurrence in packet.get("qac", {}).get("occurrences", [])
        ]
        for occurrence in occurrence_rows:
            for field in ("surface_ar", "stem_ar", "lemma_ar", "root_ar"):
                value = text_or_empty(occurrence.get(field))
                if len(value) <= 80:
                    add_arabic_recall_aliases(
                        lookup_aliases,
                        value,
                        root_id,
                        root_norm,
                        f"qac_{field}",
                    )
        for row in branch_rows:
            branches_jsonl.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            for keyword in row.get("keywords", []):
                concepts[keyword].append(
                    {
                        "root_id": root_id,
                        "root_norm": root_norm,
                        "branch_ref": row["branch_ref"],
                        "branch_image_ar": row.get("branch_image_ar") or "",
                    }
                )
        for row in occurrence_rows:
            occurrences_jsonl.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))

        (root_out / "card.md").write_text(
            root_card(packet, rel_root, source_path, raw_url),
            encoding="utf-8",
        )
        route_rows = [route_record(source) for source in packet.get("dictionary_sources", [])]
        (root_out / "routes.min.json").write_text(
            json.dumps(
                {
                    "root_envelope_id": root_id,
                    "root_norm": root_norm,
                    "v4_roots": packet.get("v4_roots", []),
                    "summary": route_summary(route_rows),
                    "routes": route_rows,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        (root_out / "branches.json").write_text(
            json.dumps(branch_rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (root_out / "branches.select.min.json").write_text(
            json.dumps(
                {
                    "root_envelope_id": root_id,
                    "root_norm": root_norm,
                    "branches": branch_select_rows,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        branch_source_dir = root_out / "branch"
        branch_source_dir.mkdir()
        for branch in packet.get("branches", []):
            branch_id = text_or_empty(branch.get("branch_id"))
            if not branch_id:
                continue
            (branch_source_dir / branch_source_filename(branch)).write_text(
                json.dumps(
                    branch_source_record(packet, branch),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
        (root_out / "occurrences.compact.json").write_text(
            json.dumps(
                {
                    "root_envelope_id": root_id,
                    "root_norm": root_norm,
                    "qac_summary": packet.get("qac", {}).get("summary", {}),
                    "occurrences": occurrence_rows,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        if include_full:
            shutil.copy2(packet_path, root_out / "full.json")
        else:
            (root_out / "full.json").write_text(
                json.dumps(
                    {
                        "root_envelope_id": root_id,
                        "root_norm": root_norm,
                        "source": source_path,
                        "raw_url": raw_url,
                        "note": "Full packet copying is disabled in the compact build. Fetch the exact raw_url when full evidence is necessary, or rebuild with --include-full.",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    aliases_out = finalized_aliases(aliases)
    lookup_aliases_out = finalized_aliases(lookup_aliases)
    alias_shards_index = write_alias_shards(
        output_dir,
        aliases_out,
        "aliases/by-initial",
        "Root/root-id aliases only.",
        2,
    )
    lookup_shards_index = write_alias_shards(
        output_dir,
        lookup_aliases_out,
        "lookup/by-initial",
        "Root aliases plus lexical and QAC Arabic forms.",
        4,
        include_bucket_map=False,
    )
    manifest = {
        "version": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root_count": len(roots),
        "branch_count": len(branches_jsonl),
        "occurrence_count": len(occurrences_jsonl),
        "root_alias_count": len(aliases_out),
        "lookup_alias_count": len(lookup_aliases_out),
        "identity_policy": "root_id and Arabic root fields are authoritative; ASCII/Latin aliases are candidate lookup aids only.",
        "entrypoints": {
            "start_here": "START_HERE.md",
            "roots": "roots.min.json",
            "aliases": "aliases.min.json",
            "alias_shards": "aliases.index.min.json",
            "lookup_shards": "lookup.index.min.json",
            "lookup_help": "aliases.index.md",
        },
    }
    if include_bulk:
        manifest["entrypoints"].update(
            {
                "branches": "branches.min.jsonl",
                "occurrences": "occurrences.min.jsonl",
                "concepts": "concepts.min.json",
            }
        )

    (output_dir / "manifest.min.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output_dir / "roots.min.json").write_text(
        json.dumps(roots, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output_dir / "aliases.min.json").write_text(
        json.dumps(aliases_out, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output_dir / "aliases.index.min.json").write_text(
        json.dumps(alias_shards_index, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output_dir / "lookup.index.min.json").write_text(
        json.dumps(lookup_shards_index, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output_dir / "aliases.index.md").write_text(
        alias_index_text(alias_shards_index, lookup_shards_index),
        encoding="utf-8",
    )
    if include_bulk:
        (output_dir / "branches.min.jsonl").write_text(
            "\n".join(branches_jsonl) + "\n",
            encoding="utf-8",
        )
        (output_dir / "occurrences.min.jsonl").write_text(
            "\n".join(occurrences_jsonl) + "\n",
            encoding="utf-8",
        )
        (output_dir / "concepts.min.json").write_text(
            json.dumps(concepts, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    (output_dir / "START_HERE.md").write_text(start_here_text(manifest), encoding="utf-8")
    (output_dir / "index.html").write_text(index_html(manifest), encoding="utf-8")
    (output_dir.parent / "index.html").write_text(
        root_index_html(output_dir.name, manifest),
        encoding="utf-8",
    )


def alias_index_text(alias_index: dict[str, Any], lookup_index: dict[str, Any]) -> str:
    return f"""# Alias Shards

Use these shard indexes when opening a whole multi-megabyte alias map would waste
context.

## Root Lookup

1. If the query is already a `root_...` ID, open `root/<root_id>/card.md`.
2. Otherwise open `aliases.index.min.json`.
3. For the first two lowercased, non-space, non-diacritic query characters,
   compute Unicode code points in four hex digits. Example: `ح م` -> `u062d-u0645`.
4. Open `aliases/by-initial/uXXXX-uYYYY.min.json`.
5. For hamza/alif variants (`ء أ إ ؤ ئ آ ا ٱ`), also try the same bucket after
   candidate-only folding those letters to `ا`, then compare plausible cards.

Root alias count: {alias_index["alias_count"]}

## Form Lookup

Use `lookup.index.min.json` when the user provides an Arabic surface, stem,
lemma, or lexical expression rather than a root. It includes root aliases plus
Arabic lexical and QAC recall forms. These aliases are retrieval candidates, not
identity.

For form lookup, use the first four non-space, non-diacritic query characters.
For hamza/alif forms, open the exact four-character bucket and the candidate
folded four-character bucket.

Examples:

- Root `ح م م` -> `aliases/by-initial/u062d-u0645.min.json`
- Root `أ ت ي` -> exact `aliases/by-initial/u0623-u062a.min.json`, folded `aliases/by-initial/u0627-u062a.min.json`
- Root `د ع ي` may be a weak-letter candidate for `د ع و`; compare every candidate card.
- Form `ٱتَّقُ` -> exact `lookup/by-initial/u0671-u062a-u0642.min.json`, folded `lookup/by-initial/u0627-u062a-u0642.min.json`

Lookup alias count: {lookup_index["alias_count"]}
"""


def start_here_text(manifest: dict[str, Any]) -> str:
    return f"""# Dictionary Agent Access

This static directory is optimized for mobile ChatGPT, Claude, and other agents
that need token-efficient root lookup.

## Retrieval Ladder

1. Open `manifest.min.json`.
2. Resolve exact Arabic/root IDs through `aliases.index.min.json` shards, or
   `aliases.min.json` if whole-file search is available.
3. Open the compact card at `root/<root_id>/card.md`.
4. If variant strength, source-root provenance, or composite-root membership
   matters, open `root/<root_id>/routes.min.json`.
5. For branch audit, open `root/<root_id>/branches.select.min.json`, choose the
   branch by `branch_image_ar`, `what_is_ar`, and `what_is_not_ar`, then open
   only the selected row's `source` path.
6. Open `root/<root_id>/branches.json` only when QNet branch evidence is needed.
7. Open `root/<root_id>/occurrences.compact.json` when Qur'anic usage is needed.
8. Open `root/<root_id>/full.json` for full-packet metadata and exact raw URL.

## Batch Root Check

If the user says "check my dictionary repo for roots x, y, z":

1. Resolve each requested root separately through the root-alias shard rule below.
2. Open each matching `root/<root_id>/card.md`.
3. If the card says the root is composite or variant-sensitive, open
   `root/<root_id>/routes.min.json`.
4. Report every candidate root ID you inspected, and say which one matched each
   requested root. Do not open full packets unless the card, routes, branch
   selection, and occurrences are insufficient.

## Alternate Form Lookup

If the user gives an Arabic surface, stem, lemma, or lexical expression instead
of a root, use `lookup.index.min.json` shards. These aliases are candidate-level
recall aids; confirm identity with candidate root cards.

## Shard Examples

- Root `ح م م`: `aliases/by-initial/u062d-u0645.min.json`
- Root `أ ت ي`: exact `aliases/by-initial/u0623-u062a.min.json`; folded `aliases/by-initial/u0627-u062a.min.json`
- Weak final query `د ع ي`: inspect weak-letter candidates such as `د ع و` by card comparison.
- Form `ٱتَّقُ`: exact `lookup/by-initial/u0671-u062a-u0642.min.json`; folded `lookup/by-initial/u0627-u062a-u0642.min.json`

## Identity Rule

Arabic-script identity and opaque root IDs are authoritative. ASCII or Latin
aliases are lookup candidates only. If an alias has status `candidate`, compare
all returned root cards before analysis.
Bare alif `ا` is never authoritative identity for radical hamza `ء`; hamza/alif
folding is candidate recall only. Use `routes.min.json` to audit exact vs
variant V4 routes.

Root count: {manifest["root_count"]}
Branch count: {manifest["branch_count"]}
Occurrence count: {manifest["occurrence_count"]}
Root alias count: {manifest["root_alias_count"]}
Form lookup alias count: {manifest["lookup_alias_count"]}
"""


def index_html(manifest: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Dictionary Agent Access</title>
<body>
<main>
  <h1>Dictionary Agent Access</h1>
  <p>Static, token-efficient access files for agents.</p>
  <p>Start with these small entrypoints. Do not open global bulk files for normal lookup.</p>
  <ul>
    <li><a href="START_HERE.md">START_HERE.md</a></li>
    <li><a href="manifest.min.json">manifest.min.json</a></li>
    <li><a href="aliases.index.md">aliases.index.md</a></li>
    <li><a href="aliases.index.min.json">aliases.index.min.json</a></li>
    <li><a href="lookup.index.min.json">lookup.index.min.json</a></li>
  </ul>
  <p>Roots: {manifest["root_count"]}; branches: {manifest["branch_count"]}; occurrences: {manifest["occurrence_count"]}.</p>
</main>
</body>
</html>
"""


def root_index_html(agent_dir_name: str, manifest: dict[str, Any]) -> str:
    agent_dir = agent_dir_name.rstrip("/") or "agent"
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={agent_dir}/">
<title>Dictionary</title>
<body>
<main>
  <h1>Dictionary</h1>
  <p>This GitHub Pages site is optimized for agent root lookup.</p>
  <p><a href="{agent_dir}/">Open the agent gateway</a></p>
  <p><a href="{agent_dir}/START_HERE.md">Open START_HERE.md</a></p>
  <p>Roots: {manifest["root_count"]}; branches: {manifest["branch_count"]}; occurrences: {manifest["occurrence_count"]}.</p>
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/output/root_packets", type=Path)
    parser.add_argument("--output-dir", default="public/agent", type=Path)
    parser.add_argument(
        "--include-full",
        action="store_true",
        help="Copy full root packet JSON files into public/agent/root/<id>/full.json.",
    )
    parser.add_argument(
        "--include-bulk",
        action="store_true",
        help="Write global branches/occurrences/concepts indexes. Omit for the default agent Pages artifact.",
    )
    parser.add_argument(
        "--raw-base-url",
        default="https://raw.githubusercontent.com/ahmetrasit/dictionary/main/data/output/root_packets",
        help="Base URL used in compact builds to point agents to exact full-packet raw files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build(args.input_dir, args.output_dir, args.include_full, args.include_bulk, args.raw_base_url)


if __name__ == "__main__":
    main()
