#!/usr/bin/env python3
"""Migrate existing authored v2 material to the schema-3 data contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.assemble_entry import (
    assemble,
    canonical_sha256,
    load_evidence,
    sha256_file,
    split_refs,
)
from v2.scripts.build_branch_evidence import DEFAULT_FURUQ
from v2.scripts.create_entry import (
    prepare_initial_tasks,
    prepare_inputs,
    prepare_root_task,
)
from v2.scripts.render_entry import render as render_entry
from v2.scripts.render_occurrences import (
    build_attachment_crosswalk,
    render_markdown as render_occurrences,
    write_crosswalk,
    write_generated as write_occurrences,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def usage_role(gloss: dict) -> str:
    text = gloss["text"]
    if gloss["loanword_status"] != "none":
        return "technical_term"
    if any(marker in text for marker in (" Nehri", " bölgesi", " adlı ")):
        return "proper_name"
    words = text.split()
    if len(words) >= 4 or " veya " in text:
        return "explanatory"
    if gloss["rank"] == 1 and gloss["error_profile"]["fit"] == "none":
        return "general"
    return "contextual"


APPLICABILITY = {
    "general": "Dal etkin olduğunda doğrudan karşılık adayıdır; hata profilindeki kayıp ve eklemeler bağlamda denetlenmelidir.",
    "contextual": "Yalnız hata profilinde belirtilen daralma, genişleme ve çağrışımlar somut bağlama uyduğunda kullanılmalıdır.",
    "explanatory": "Anlam alanını açıklamak için uygundur; akıcı çeviride daha doğal bir bağlamsal karşılık tercih edilebilir.",
    "technical_term": "Yerleşik terimin hedef bağlamda gerçekten etkin olduğu kullanımlarda tercih edilmelidir.",
    "proper_name": "Kaynağın belirli kişi, yer veya nesne adını gösterdiği bağlamlarda kullanılmalıdır.",
}


def migrate_authored_branch(branch: dict, *, legacy_neighbor: bool) -> None:
    branch.setdefault("usage_notes", [])
    disagreement = branch["source_discussion"]["disagreement"]
    qualifiers = branch.setdefault("evidence_qualifiers", [])
    if disagreement and not any(row["type"] == "disputed" for row in qualifiers):
        qualifiers.append(
            {
                "type": "disputed",
                "statement": disagreement["summary"],
                "source_refs": disagreement["source_refs"],
            }
        )
    glosses = branch["glosses"]
    glosses.setdefault("semantic_definition", branch["summary"])
    for gloss in glosses["selected"]:
        role = gloss.setdefault("usage_role", usage_role(gloss))
        gloss.setdefault("applicability", APPLICABILITY[role])
    branch.setdefault(
        "neighbor_coverage",
        {
            "assessment": (
                "legacy_minimum_unverified"
                if legacy_neighbor and len(branch["arabic_neighbor_distinctions"]) == 1
                else "complete"
            ),
            "note": (
                "Bu kayıt eski asgari-seçim iş akışından taşınmıştır; mevcut karşılaştırma korunmuş, aday kapsamı henüz yeniden doğrulanmamıştır."
                if legacy_neighbor and len(branch["arabic_neighbor_distinctions"]) == 1
                else "Paketlenmiş adaylar maddi ayrım bakımından değerlendirilmiş ve yararlı karşılaştırmalar kaydedilmiştir."
            ),
        },
    )


def correct_ghayth_attribution(fragment: dict) -> None:
    if (fragment.get("root_id"), fragment.get("branch_id")) != ("root_001118", "B004"):
        return
    refs = fragment["source_discussion"]["evidence_refs"]
    fragment["source_discussion"]["disagreement"] = {
        "summary": "ʿAyn yardım kullanımını غ ي ث maddesinde verirken Mufradāt أَغَاثَ biçimini غ و ث yardım köküne bağlar; kök nispeti kaynaklar arasında açıkça ayrışır.",
        "source_refs": refs,
    }
    for annotation in fragment.get("dictionary_annotations", []):
        if annotation["source_id"] == "mufradat" and "disagreement" not in annotation["roles"]:
            annotation["roles"].append("disagreement")
    fragment["evidence_qualifiers"] = [
        row for row in fragment.get("evidence_qualifiers", []) if row["type"] != "disputed"
    ]
    fragment["evidence_qualifiers"].append(
        {
            "type": "disputed",
            "statement": fragment["source_discussion"]["disagreement"]["summary"],
            "source_refs": refs,
        }
    )


def correct_bahr_glosses(fragment: dict) -> None:
    if (fragment.get("root_id"), fragment.get("branch_id")) != ("root_000086", "B001"):
        return
    glosses = fragment["glosses"]
    ocean = next((row for row in glosses["excluded"] if row["text"] == "okyanus"), None)
    if ocean:
        glosses["excluded"].remove(ocean)
        glosses["selected"].append(
            {
                "rank": 3,
                "text": "okyanus",
                "loanword_status": "none",
                "usage_role": "contextual",
                "applicability": "Su kütlesinin çok geniş, açık ve okyanus ölçeğinde olduğu bağlamlarda kullanılmalıdır.",
                "error_profile": ocean["error_profile"],
            }
        )
    if not any(row["text"] == "büyük göl" for row in glosses["selected"]):
        glosses["selected"].append(
            {
                "rank": 4,
                "text": "büyük göl",
                "loanword_status": "none",
                "usage_role": "contextual",
                "applicability": "Su kütlesinin karayla çevrili ve göl niteliğinde olduğu açık bağlamlarda kullanılmalıdır.",
                "error_profile": {
                    "fit": "narrowing",
                    "preserves": "Geniş ve çok su içeren karayla çevrili su kütlesi olasılığını korur.",
                    "loses": "Deniz, okyanus ve büyük nehir kapsamlarını dışarıda bırakır.",
                    "adds": "Kapalı veya iç havzada bulunma beklentisini belirginleştirir.",
                    "collision": "Genel göl adıyla ve küçüklük bildiren بُحَيْرَة biçimiyle karışabilir.",
                },
            }
        )


def migrate_fragment(task_path: Path, fragment_path: Path, *, branch: bool = False) -> None:
    task = load(task_path)
    fragment = load(fragment_path)
    if branch:
        migrate_authored_branch(fragment, legacy_neighbor=True)
        correct_ghayth_attribution(fragment)
        correct_bahr_glosses(fragment)
    fragment["inputs_sha256"] = canonical_sha256(task)
    write(fragment_path, fragment)


def migrate_entry(envelope: str, language: str = "tr") -> None:
    packet_path, _packet, index_path, index = prepare_inputs(
        envelope,
        language,
        None,
        DEFAULT_FURUQ,
        None,
        force_entry=True,
    )
    work_dir = PROJECT / "v2/work/entry_creation" / envelope / language
    prepare_initial_tasks(index_path, index, language, work_dir)
    for row in index["branches"]:
        name = f"{row['root_id']}--{row['branch_id']}.json"
        migrate_fragment(
            work_dir / "tasks/branches" / name,
            work_dir / "fragments/branches" / name,
            branch=True,
        )
    migrate_fragment(
        work_dir / "tasks/occurrence_observations.json",
        work_dir / "fragments/occurrence_observations.json",
    )
    root_task = prepare_root_task(index, language, work_dir)
    migrate_fragment(root_task, work_dir / "fragments/root_profile.json")
    entry_path = PROJECT / "v2/entries" / language / f"{envelope}.json"
    markdown_path = PROJECT / "v2/entries" / language / f"{envelope}.md"
    assemble(index_path, work_dir, language, entry_path, force=True)
    render_entry(entry_path, markdown_path)
    print(f"Migrated {entry_path.relative_to(PROJECT)} from {packet_path.relative_to(PROJECT)}")


def lexical_realizations(package: dict) -> list[dict]:
    result = []
    for unit in package.get("lexical_units", []):
        quran_form = None
        if unit.get("resolved_quran_stem_ar") and unit.get("resolved_quran_tag"):
            quran_form = {
                "stem_ar": unit["resolved_quran_stem_ar"],
                "tag": unit["resolved_quran_tag"],
            }
        result.append(
            {
                "lexical_unit_id": unit["lexical_unit_id"],
                "expression_ar": unit["expression_ar"],
                "unit_kind": unit["unit_kind"],
                "sense_ar": unit["sense_ar"],
                "evidence_refs": split_refs(unit.get("source_refs", "")),
                "quran_form": quran_form,
            }
        )
    return result


def migrate_example(path: Path) -> None:
    entry = load(path)
    packet_path, packet, index_path, _prepared_index = prepare_inputs(
        entry["root_envelope_id"],
        entry["language"],
        None,
        DEFAULT_FURUQ,
        None,
        force_entry=True,
    )
    _index, packages = load_evidence(index_path)
    package_map = {
        (package["branch"]["root_id"], package["branch"]["branch_id"]): package
        for _row, package, _package_path in packages
    }
    for branch in entry["branches"]:
        migrate_authored_branch(branch, legacy_neighbor=True)
        package = package_map[(branch["root_id"], branch["branch_id"])]
        branch["lexical_realizations"] = lexical_realizations(package)
        branch["neighbor_coverage"] = {
            **branch["neighbor_coverage"],
            "candidate_count": len(package["furuq_candidates"]),
        }
    crosswalk = build_attachment_crosswalk(packet)
    alignment_path = PROJECT / "v2/output/alignments" / f"{entry['root_envelope_id']}.json"
    write_crosswalk(alignment_path, crosswalk, check=False)
    occurrence_path = PROJECT / entry["occurrence_evidence"]["artifact_path"]
    write_occurrences(
        occurrence_path,
        render_occurrences(packet, packet_path, entry["language"], crosswalk),
        check=False,
    )
    entry["schema_version"] = 3
    entry["provenance"].update(
        {
            "packet_sha256": sha256_file(packet_path),
            "evidence_index_sha256": sha256_file(index_path),
        }
    )
    entry["occurrence_evidence"].update(
        {
            "artifact_sha256": sha256_file(occurrence_path),
            "alignment_path": str(alignment_path.relative_to(PROJECT)),
            "alignment_sha256": sha256_file(alignment_path),
            "alignment_generator": "v2/scripts/render_occurrences.py",
        }
    )
    write(path, entry)
    render_entry(path, path.with_suffix(".md"))
    print(f"Migrated {path.relative_to(PROJECT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelopes", nargs="*")
    parser.add_argument("--include-example", action="store_true")
    args = parser.parse_args()
    envelopes = args.envelopes or [path.stem for path in sorted((PROJECT / "v2/entries/tr").glob("*.json"))]
    for envelope in envelopes:
        migrate_entry(envelope)
    if args.include_example:
        migrate_example(PROJECT / "v2/examples/root_000858.tr.entry.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
