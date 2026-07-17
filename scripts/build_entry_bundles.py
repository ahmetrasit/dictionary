#!/usr/bin/env python3
"""Split one root packet into a root bundle and one bundle per V4 branch."""

import argparse
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path


HAMZA = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ؤ": "ء", "ئ": "ء", "ٱ": "ء"})


def root_key(text):
    text = unicodedata.normalize("NFKD", text or "").translate(HAMZA)
    return "".join(
        c for c in text
        if not c.isspace() and c != "ـ" and unicodedata.category(c) != "Mn"
    )


def packet_sha256(packet):
    payload = json.dumps(
        packet,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def selector_matches(packet, selector):
    if not selector:
        return True
    root_rows = packet.get("v4_roots", [])
    root_ids = {row["root_id"] for row in root_rows}
    envelope = packet.get("root_envelope_id") or "--".join(
        row["root_id"] for row in root_rows
    )
    return (
        selector == envelope
        or selector in root_ids
        or root_key(selector) == packet.get("root_join_key")
    )


def cell(value):
    return " ".join(str(value or "").split()).replace("|", "\\|")


def json_block(value):
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def load_packet(project, selector, explicit_path):
    if explicit_path:
        path = explicit_path
        if not path.is_file():
            raise SystemExit(f"Missing packet: {path}")
        return path, json.loads(path.read_text(encoding="utf-8"))

    packet_dir = project / "data/output/root_packets"
    for path in sorted(packet_dir.glob("*.json")):
        packet = json.loads(path.read_text(encoding="utf-8"))
        root_ids = {row["root_id"] for row in packet.get("v4_roots", [])}
        if (
            selector == packet.get("root_envelope_id")
            or selector in root_ids
            or root_key(selector) == packet.get("root_join_key")
        ):
            return path, packet
    raise SystemExit(
        f"No root packet found for: {selector}\n"
        f"Run scripts/root_packet.py {selector!r} first."
    )


def root_bundle(packet, packet_path):
    summary = packet["qac"]["summary"]
    lines = [
        f"# Root evidence bundle: {packet['root_norm']}",
        "",
        f"Root envelope ID: `{packet['root_envelope_id']}`",
        "",
        f"Full packet: `{packet_path}`",
        "",
        "> V4 branches are frozen. QAC and attachments are root-level observation "
        "only. QNet is discovery only.",
        "",
        "## V4 root records",
        "",
        json_block(packet["v4_roots"]),
        "",
        f"## Complete branch roster ({len(packet['branches'])})",
        "",
        "| V4 branch | Arabic image | What it is | What it is not |",
        "|---|---|---|---|",
    ]
    for branch in packet["branches"]:
        lines.append(
            f"| {branch['root_id']}/{branch['branch_id']} | "
            f"{cell(branch['branch_image_ar'])} | {cell(branch['what_is_ar'])} | "
            f"{cell(branch['what_is_not_ar'])} |"
        )

    lines += [
        "",
        "## Quran census",
        "",
        json_block(summary),
        "",
        "## Complete Quran occurrences",
        "",
        "| QAC ref | Surface | Lemma | POS | Measure | Morphology |",
        "|---|---|---|---|---|---|",
    ]
    for row in packet["qac"]["occurrences"]:
        lines.append(
            f"| {row['qac_ref']} | {cell(row['surface_ar'])} | "
            f"{cell(row['lemma_ar'])} | {cell(row['pos'])} | "
            f"{cell(row['measure'])} | {cell(row['morph_features'])} |"
        )

    lines += ["", "## Full Arabic ayah contexts", ""]
    for ayah in packet["qac"].get("ayah_contexts", []):
        lines += [f"### {ayah['ref']}", "", ayah["surface_ar"], ""]

    attachments = packet["attachments"]
    lines += [
        "## Attachment evidence",
        "",
        f"- Verb instances: {len(attachments['verb_instances'])}",
        f"- Noun instances: {len(attachments['noun_instances'])}",
        f"- Linked attachment rows: {len(attachments['attachments'])}",
        f"- Aggregate verb frames: {len(attachments['verb_valency_frames'])}",
        f"- Aggregate noun patterns: {len(attachments['noun_governing_patterns'])}",
        "",
        "### Aggregate verb frames",
        "",
        json_block(attachments["verb_valency_frames"]),
        "",
        "### Aggregate noun patterns",
        "",
        json_block(attachments["noun_governing_patterns"]),
        "",
        "The complete verb, noun, and attachment rows remain in the full packet JSON.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def branch_bundle(packet, branch, packet_path, linked_senses):
    ref = f"{branch['root_id']}/{branch['branch_id']}"
    sources = [
        source for source in packet["dictionary_sources"]
        if source["root_id"] == branch["root_id"]
    ]
    lines = [
        f"# Branch evidence bundle: {ref}",
        "",
        f"Full packet: `{packet_path}`",
        "",
        "> This is a frozen V4 branch. Write its encyclopedia entry; do not "
        "re-adjudicate, merge, or activate it.",
        "",
        "## Focus V4 record",
        "",
        json_block(branch),
        "",
        "## Linked lexical units",
        "",
        json_block(linked_senses),
        "",
        "## Complete sibling roster",
        "",
        "| V4 branch | Arabic image | What it is | What it is not |",
        "|---|---|---|---|",
    ]
    for sibling in packet["branches"]:
        lines.append(
            f"| {sibling['root_id']}/{sibling['branch_id']} | "
            f"{cell(sibling['branch_image_ar'])} | {cell(sibling['what_is_ar'])} | "
            f"{cell(sibling['what_is_not_ar'])} |"
        )

    lines += ["", "## Classical dictionary entries for this V4 root record", ""]
    for source in sources:
        metadata = {key: value for key, value in source.items() if key != "entry_text_clean"}
        lines += [
            f"### {source['source_id']} — {source['headword']}",
            "",
            json_block(metadata),
            "",
            source["entry_text_clean"].strip(),
            "",
        ]

    lines += [
        "## QNet discovery material",
        "",
        "> Candidate material below is not evidence. Verify every published "
        "contrast against V4 and classical sources.",
        "",
        json_block(packet["qnet"].get(ref, {"keywords": [], "neighbors": []})),
        "",
        "## Root-level Quran evidence",
        "",
        "QAC occurrences and attachments belong to the root observatory, not this "
        "branch. Do not use them to claim that this branch is activated.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        help="V4 root_id, root envelope ID, or Arabic root selector",
    )
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    packet_path, packet = load_packet(project, args.root, args.packet)
    if args.packet and not selector_matches(packet, args.root):
        raise SystemExit(
            f"Root selector {args.root!r} does not match explicit packet {packet_path}"
        )
    root_envelope_id = packet.get("root_envelope_id") or "--".join(
        row["root_id"] for row in packet["v4_roots"]
    )
    packet["root_envelope_id"] = root_envelope_id
    output_dir = (
        args.output_dir
        or project / "data/output/entry_bundles" / root_envelope_id
    )
    branch_dir = output_dir / "branches"
    branch_dir.mkdir(parents=True, exist_ok=True)

    senses = {
        (row["root_id"], row["lexical_unit_id"]): row
        for row in packet["lexical_senses"]
    }
    links = defaultdict(list)
    for link in packet["branch_lexical_links"]:
        sense = senses.get((link["root_id"], link["lexical_unit_id"]))
        if sense:
            links[(link["root_id"], link["branch_id"])].append(sense)

    (output_dir / "ROOT.md").write_text(
        root_bundle(packet, packet_path), encoding="utf-8"
    )
    index = [f"# Entry bundles: {packet['root_norm']}", "", "- [Root bundle](ROOT.md)"]
    for branch in packet["branches"]:
        name = f"{branch['root_id']}--{branch['branch_id']}.md"
        path = branch_dir / name
        path.write_text(
            branch_bundle(
                packet,
                branch,
                packet_path,
                links[(branch["root_id"], branch["branch_id"])],
            ),
            encoding="utf-8",
        )
        index.append(f"- [{branch['root_id']}/{branch['branch_id']}](branches/{name})")
    (output_dir / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    generated_files = [output_dir / "ROOT.md", output_dir / "INDEX.md"] + [
        branch_dir / f"{branch['root_id']}--{branch['branch_id']}.md"
        for branch in packet["branches"]
    ]
    manifest = {
        "format": 1,
        "root_envelope_id": root_envelope_id,
        "packet": str(packet_path),
        "packet_sha256": packet_sha256(packet),
        "branches": [
            f"{branch['root_id']}/{branch['branch_id']}" for branch in packet["branches"]
        ],
        "files": {
            str(path.relative_to(output_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in generated_files
        },
    }
    (output_dir / ".entry-bundle-generated.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote {output_dir / 'ROOT.md'}")
    print(f"Wrote {len(packet['branches'])} branch bundles under {branch_dir}")
    print(f"Root envelope ID: {root_envelope_id}")


if __name__ == "__main__":
    main()
