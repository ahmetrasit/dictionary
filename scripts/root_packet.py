#!/usr/bin/env python3
"""Make a readable evidence packet for every V4 branch of one Quranic root."""

import argparse
import csv
import json
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.render_occurrences import local_source_grammar


HAMZA = str.maketrans({"أ": "ء", "إ": "ء", "آ": "ء", "ؤ": "ء", "ئ": "ء", "ٱ": "ء"})


def root_key(text):
    text = unicodedata.normalize("NFKD", text or "").translate(HAMZA)
    return "".join(
        c for c in text
        if not c.isspace() and c != "ـ" and unicodedata.category(c) != "Mn"
    )


def open_db(path):
    db = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def fetch(db, query, values=()):
    return [dict(row) for row in db.execute(query, values)]


def tsv_matches(path, target, fields):
    with path.open(encoding="utf-8", newline="") as handle:
        rows = []
        for source_row in csv.DictReader(handle, delimiter="\t"):
            if not any(root_key(source_row.get(field, "")) == target for field in fields):
                continue
            row = dict(source_row)
            if "grammar" in row:
                row["grammar"] = local_source_grammar(row["grammar"])
            rows.append(row)
        return rows


def find_roots(db, query):
    roots = fetch(db, "SELECT * FROM roots ORDER BY root_id")
    if query.startswith("root_"):
        match = next((row for row in roots if row["root_id"] == query), None)
        if not match:
            raise SystemExit(f"Unknown V4 root_id: {query}")
        target = root_key(match["root_norm"])
    else:
        target = root_key(query)
    quranic = {
        row["root_id"] for row in db.execute(
            "SELECT DISTINCT root_id FROM branch_images WHERE origin_corpus='quranic'"
        )
    }
    matches = [
        row for row in roots
        if row["root_id"] in quranic and root_key(row["root_norm"]) == target
    ]
    if not matches:
        raise SystemExit(f"No Quranic V4 root found for: {query}")
    return target, matches


def qnet_for_branches(db, branches, branch_lookup, top_n):
    result = {}
    for branch in branches:
        node = (branch["root_id"], branch["branch_id"])
        keywords = fetch(
            db,
            """SELECT keyword_type, keyword, replicate_votes FROM branch_keywords
               WHERE root_id=? AND branch_id=?
               ORDER BY keyword_type DESC, replicate_votes DESC, keyword""",
            node,
        )
        core = [
            row["keyword"] for row in keywords
            if row["keyword_type"] == "core" and row["replicate_votes"] == 2
        ]
        shared = defaultdict(set)
        if core:
            marks = ",".join("?" for _ in core)
            candidates = db.execute(
                f"""SELECT root_id, branch_id, keyword FROM branch_keywords
                    WHERE keyword_type='core' AND replicate_votes=2
                      AND keyword IN ({marks})
                      AND NOT (root_id=? AND branch_id=?)""",
                (*core, *node),
            )
            for row in candidates:
                shared[(row["root_id"], row["branch_id"])].add(row["keyword"])
        ranked = sorted(
            ((candidate, words) for candidate, words in shared.items() if len(words) >= 2),
            key=lambda item: (-len(item[1]), item[0]),
        )[:top_n]
        neighbors = []
        for candidate, words in ranked:
            meta = branch_lookup.get(candidate, {})
            neighbors.append({
                "root_id": candidate[0],
                "branch_id": candidate[1],
                "root_norm": meta.get("root_norm", ""),
                "branch_image_ar": meta.get("branch_image_ar", ""),
                "what_is_ar": meta.get("what_is_ar", ""),
                "what_is_not_ar": meta.get("what_is_not_ar", ""),
                "source_refs": meta.get("source_refs", ""),
                "status": meta.get("status", ""),
                "contaminated": meta.get("contaminated", ""),
                "shared_consensus_core": sorted(words),
            })
        result[f"{node[0]}/{node[1]}"] = {"keywords": keywords, "neighbors": neighbors}
    return result


def clean(text):
    return " ".join(str(text or "").split()).replace("|", "\\|")


def render(packet):
    qac = packet["qac"]["summary"]
    roots = ", ".join(
        f"{row['root_id']} ({row['source_root_norm']})" for row in packet["v4_roots"]
    )
    senses = {
        (row["root_id"], row["lexical_unit_id"]): row
        for row in packet["lexical_senses"]
    }
    linked = defaultdict(list)
    for link in packet["branch_lexical_links"]:
        sense = senses.get((link["root_id"], link["lexical_unit_id"]))
        if sense:
            linked[(link["root_id"], link["branch_id"])].append(sense)

    out = [
        f"# Root packet: {packet['root_norm']}", "", f"V4 records: {roots}", "",
        f"Root envelope ID: `{packet['root_envelope_id']}`", "",
        "> QAC and attachments are root-level evidence, not branch assignments. "
        "QNet neighbors are discovery prompts, not lexical decisions.", "",
        f"## V4 branches ({len(packet['branches'])})", "",
    ]
    for branch in packet["branches"]:
        node = (branch["root_id"], branch["branch_id"])
        ref = "/".join(node)
        out += [
            f"### {ref} — {branch['branch_image_ar']}", "",
            f"- Record: status={branch['status']}; contaminated={branch['contaminated']}",
            f"- Is: {clean(branch['what_is_ar'])}",
            f"- Is not: {clean(branch['what_is_not_ar'])}",
            f"- English scaffold: {clean(branch['branch_image_en'])}",
            f"- V4 source phrase: {clean(branch['source_phrase_ar'])}",
            f"- V4 source references: {clean(branch['source_refs'])}",
        ]
        if branch["review_note"]:
            out.append(f"- Review note: {clean(branch['review_note'])}")
        units = linked[node]
        if units:
            out.append("- Lexical units: " + "; ".join(
                f"{clean(unit['expression_ar'])} — {clean(unit['sense_ar'])}" for unit in units
            ))
        network = packet["qnet"][ref]
        consensus = [
            row["keyword"] for row in network["keywords"] if row["replicate_votes"] == 2
        ]
        if consensus:
            out.append("- QNet consensus keywords: " + ", ".join(consensus))
        if network["neighbors"]:
            out.append("- QNet discovery neighbors: " + "; ".join(
                f"{n['root_id']}/{n['branch_id']} {clean(n['branch_image_ar'])} "
                f"[{', '.join(n['shared_consensus_core'])}]"
                for n in network["neighbors"]
            ))
        out.append("")

    out += [
        "## Quran occurrences (root level)", "",
        f"{qac['morpheme_count']} rooted morphemes in {qac['word_count']} words, "
        f"{qac['ayah_count']} ayahs, and {qac['surah_count']} surahs.", "",
        "Lemmas: " + "; ".join(f"{lemma}: {count}" for lemma, count in qac["lemmas"].items()),
        "", "| Ref | Surface | Lemma | POS | Measure |", "|---|---|---|---|---|",
    ]
    for row in packet["qac"]["occurrences"]:
        out.append(
            f"| {row['qac_ref']} | {clean(row['surface_ar'])} | {clean(row['lemma_ar'])} | "
            f"{clean(row['pos'])} | {clean(row['measure'])} |"
        )

    attachments = packet["attachments"]
    out += [
        "", "## Attachment enrichment (root level)", "",
        f"Verb instances: {len(attachments['verb_instances'])}; "
        f"noun instances: {len(attachments['noun_instances'])}; "
        f"linked attachments: {len(attachments['attachments'])}; "
        f"verb frames: {len(attachments['verb_valency_frames'])}; "
        f"noun patterns: {len(attachments['noun_governing_patterns'])}.", "",
        "Complete attachment rows are in the JSON packet.", "",
        f"## Classical dictionary entries ({len(packet['dictionary_sources'])})", "",
    ]
    for source in packet["dictionary_sources"]:
        out += [
            f"### {source['root_id']} — {source['source_id']} — {source['headword']}", "",
            f"Reference: {clean(source['source_ref'])}", "",
            source["entry_text_clean"].strip(), "",
        ]
    return "\n".join(out).rstrip() + "\n"


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Arabic root, spaced or unspaced; or a V4 root_id")
    parser.add_argument("--top-neighbors", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=project / "data/output/root_packets")
    args = parser.parse_args()

    furuq = open_db(project / "data/working/furuq_v4.sqlite")
    qac_db = open_db(project / "data/working/qac.sqlite")
    qnet_db = open_db(
        project / "data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite"
    )
    target, root_rows = find_roots(furuq, args.root)
    root_ids = [row["root_id"] for row in root_rows]
    root_envelope_id = "--".join(root_ids)
    marks = ",".join("?" for _ in root_ids)

    branches = fetch(furuq, f"""SELECT root_id, branch_id, branch_image_ar,
        branch_image_en, image_en_fit, image_en_gap_note, what_is_ar, what_is_en,
        what_is_not_ar, source_refs, source_phrase_ar, status, review_note,
        origin_corpus, contaminated
        FROM branch_images WHERE origin_corpus='quranic' AND root_id IN ({marks})
        ORDER BY root_id, branch_id""", root_ids)
    sources = fetch(furuq, f"""SELECT root_id, source_id, source_ref, db_root_norm,
        headword, lemma, section_path, page_or_volume_ref, entry_text_clean,
        route_status, route_note, origin_corpus FROM dictionary_entries
        WHERE origin_corpus='quranic' AND root_id IN ({marks})
        ORDER BY root_id, source_id, source_ref""", root_ids)
    senses = fetch(furuq, f"""SELECT root_id, lexical_unit_id, expression_ar,
        unit_kind, branch_ids, sense_ar, sense_en, sense_en_fit,
        sense_en_gap_note, source_refs, branch_source_refs, source_phrase_ar,
        status, review_note, corpus_link_status, corpus_link_count,
        resolved_quran_stem_ar, resolved_quran_tag, origin_corpus
        FROM lexical_unit_senses WHERE origin_corpus='quranic' AND root_id IN ({marks})
        ORDER BY root_id, lexical_unit_id""", root_ids)
    links = fetch(furuq, f"""SELECT root_id, branch_id, lexical_unit_id, link_source
        FROM branch_lexical_unit_links WHERE root_id IN ({marks})
        ORDER BY root_id, branch_id, lexical_unit_id""", root_ids)

    occurrences = fetch(qac_db, """SELECT qac_ref, qac_word_ref, surah, ayah,
        word_index, morpheme_index, surface_bw, surface_ar, stem_ar, lemma_bw,
        lemma_ar, root_raw, root_ar, source_pos, pos, morpheme_role, measure,
        aspect, mood, voice, morph_features FROM qac_morphemes
        WHERE root_join_key=? ORDER BY surah, ayah, word_index, morpheme_index""", (target,))
    context_words = fetch(qac_db, """SELECT w.qac_word_ref, w.surah, w.ayah,
        w.word_index, w.surface_bw, w.surface_ar, w.root_join_keys, w.lemmas_ar,
        w.pos_tags, w.measures FROM qac_words AS w
        WHERE EXISTS (
          SELECT 1 FROM qac_morphemes AS m
          WHERE m.root_join_key=? AND m.surah=w.surah AND m.ayah=w.ayah
        ) ORDER BY w.surah, w.ayah, w.word_index""", (target,))
    context_groups = defaultdict(list)
    for word in context_words:
        context_groups[(word["surah"], word["ayah"])].append(word)
    ayah_contexts = [
        {
            "ref": f"{surah}:{ayah}",
            "surah": surah,
            "ayah": ayah,
            "surface_ar": " ".join(word["surface_ar"] for word in words),
            "words": words,
        }
        for (surah, ayah), words in context_groups.items()
    ]
    counts = lambda field: dict(sorted(Counter(row[field] or "—" for row in occurrences).items()))
    qac_summary = {
        "morpheme_count": len(occurrences),
        "word_count": len({row["qac_word_ref"] for row in occurrences}),
        "ayah_count": len({(row["surah"], row["ayah"]) for row in occurrences}),
        "surah_count": len({row["surah"] for row in occurrences}),
        "lemmas": counts("lemma_ar"), "parts_of_speech": counts("pos"),
        "measures": counts("measure"),
    }

    attachments_dir = project / "data/upstream/attachments/final_v3"
    attachments = {
        "verb_instances": tsv_matches(attachments_dir / "verb_instances.tsv", target, ("root_norm",)),
        "noun_instances": tsv_matches(attachments_dir / "noun_instances.tsv", target, ("root_norm",)),
        "attachments": tsv_matches(
            attachments_dir / "attachments.tsv", target, ("dep_root_norm", "head_root_norm")
        ),
        "verb_valency_frames": tsv_matches(
            attachments_dir / "verb_valency_frames.tsv", target, ("root_norm",)
        ),
        "noun_governing_patterns": tsv_matches(
            attachments_dir / "noun_governing_patterns.tsv", target, ("root_norm",)
        ),
    }
    branch_lookup = {
        (row["root_id"], row["branch_id"]): dict(row)
        for row in furuq.execute(
            "SELECT root_id, branch_id, root_norm, branch_image_ar, what_is_ar, "
            "what_is_not_ar, source_refs, status, contaminated "
            "FROM branch_images"
        )
    }
    packet = {
        "root_envelope_id": root_envelope_id,
        "root_join_key": target, "root_norm": root_rows[0]["root_norm"],
        "v4_roots": root_rows, "branches": branches, "dictionary_sources": sources,
        "lexical_senses": senses, "branch_lexical_links": links,
        "qac": {
            "summary": qac_summary,
            "occurrences": occurrences,
            "ayah_contexts": ayah_contexts,
        },
        "attachments": attachments,
        "qnet": qnet_for_branches(qnet_db, branches, branch_lookup, args.top_neighbors),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{root_envelope_id}.json"
    md_path = args.output_dir / f"{root_envelope_id}.md"
    json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render(packet), encoding="utf-8")
    print(f"Wrote {md_path}\nWrote {json_path}")
    print(
        f"{root_envelope_id}: {len(branches)} branches; "
        f"{len(occurrences)} QAC morphemes"
    )


if __name__ == "__main__":
    main()
