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
    value = value.replace("أ", "ء").replace("إ", "ء").replace("ؤ", "ء").replace("ئ", "ء")
    value = value.replace("آ", "ا").replace("ى", "ي")
    return WHITESPACE_RE.sub(" ", value).strip()


def compact_arabic(value: str) -> str:
    return normalize_arabic(value).replace(" ", "")


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
            "If the user query is Latin/ASCII or otherwise ambiguous, inspect `aliases.min.json` candidates",
            "and compare this card with every candidate card before analysis.",
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
    note: str,
) -> None:
    raw_alias = text_or_empty(raw_alias)
    if not raw_alias:
        return
    candidate = {
        "root_id": root_id,
        "root_norm": root_norm,
        "scheme": scheme,
        "status": status,
        "note": note,
    }
    bucket = aliases[raw_alias]
    if candidate not in bucket:
        bucket.append(candidate)


def build(input_dir: Path, output_dir: Path, include_full: bool, raw_base_url: str) -> None:
    packets = sorted(input_dir.glob("root_*.json"))
    if not packets:
        raise SystemExit(f"No root packet JSON files found in {input_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    roots_dir = output_dir / "root"
    roots_dir.mkdir()

    aliases: dict[str, list[dict[str, Any]]] = defaultdict(list)
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
            (normalize_arabic(root_norm), "arabic_normalized", "candidate", "Arabic normalized for recall, not identity."),
            (compact_arabic(root_norm), "arabic_normalized_compact", "candidate", "Compact normalized Arabic for recall, not identity."),
            (buckwalter_root(root_norm), "buckwalter_root", "strong", "Reversible machine alias; not reader-facing."),
        ]
        for v4_root in packet.get("v4_roots", []):
            source_root = text_or_empty(v4_root.get("source_root_norm"))
            root_aliases.extend(
                [
                    (v4_root.get("root_id"), "v4_root_id", "exact", "V4 root ID contained by this envelope."),
                    (source_root, "source_root_exact", "exact", "Source root variant from v4_roots."),
                    (compact_arabic(source_root), "source_root_normalized_compact", "candidate", "Normalized source-root recall alias."),
                    (buckwalter_root(source_root), "source_root_buckwalter", "strong", "Reversible source-root machine alias."),
                ]
            )
        for raw_alias, scheme, status, note in root_aliases:
            add_alias(aliases, str(raw_alias), root_id, root_norm, scheme, status, note)

        branch_rows = [branch_record(packet, branch) for branch in packet.get("branches", [])]
        occurrence_rows = [
            occurrence_record(packet, occurrence)
            for occurrence in packet.get("qac", {}).get("occurrences", [])
        ]
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
        (root_out / "branches.json").write_text(
            json.dumps(branch_rows, ensure_ascii=False, indent=2) + "\n",
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

    aliases_out = {key: value for key, value in sorted(aliases.items())}
    manifest = {
        "version": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root_count": len(roots),
        "branch_count": len(branches_jsonl),
        "occurrence_count": len(occurrences_jsonl),
        "identity_policy": "root_id and Arabic root fields are authoritative; ASCII/Latin aliases are candidate lookup aids only.",
        "entrypoints": {
            "start_here": "START_HERE.md",
            "roots": "roots.min.json",
            "aliases": "aliases.min.json",
            "branches": "branches.min.jsonl",
            "occurrences": "occurrences.min.jsonl",
            "concepts": "concepts.min.json",
        },
    }

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


def start_here_text(manifest: dict[str, Any]) -> str:
    return f"""# Dictionary Agent Access

This static directory is optimized for mobile ChatGPT, Claude, and other agents
that need token-efficient root lookup.

## Retrieval Ladder

1. Open `manifest.min.json`.
2. Resolve exact Arabic/root IDs through `aliases.min.json`.
3. Open the compact card at `root/<root_id>/card.md`.
4. Open `root/<root_id>/branches.json` only when branch evidence is needed.
5. Open `root/<root_id>/occurrences.compact.json` when Qur'anic usage is needed.
6. Open `root/<root_id>/full.json` for full-packet metadata and exact raw URL.

## Identity Rule

Arabic-script identity and opaque root IDs are authoritative. ASCII or Latin
aliases are lookup candidates only. If an alias has status `candidate`, compare
all returned root cards before analysis.

Root count: {manifest["root_count"]}
Branch count: {manifest["branch_count"]}
Occurrence count: {manifest["occurrence_count"]}
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
  <ul>
    <li><a href="START_HERE.md">START_HERE.md</a></li>
    <li><a href="manifest.min.json">manifest.min.json</a></li>
    <li><a href="roots.min.json">roots.min.json</a></li>
    <li><a href="aliases.min.json">aliases.min.json</a></li>
    <li><a href="branches.min.jsonl">branches.min.jsonl</a></li>
    <li><a href="occurrences.min.jsonl">occurrences.min.jsonl</a></li>
    <li><a href="concepts.min.json">concepts.min.json</a></li>
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
        "--raw-base-url",
        default="https://raw.githubusercontent.com/ahmetrasit/dictionary/main/data/output/root_packets",
        help="Base URL used in compact builds to point agents to exact full-packet raw files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build(args.input_dir, args.output_dir, args.include_full, args.raw_base_url)


if __name__ == "__main__":
    main()
