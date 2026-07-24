#!/usr/bin/env python3
"""Render a validated v2 encyclopedia entry as target-language Markdown."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.branch_lexicalization import branch_lexicalization_profile
from v2.scripts.validate_entry import ContractError, project_path, validate_entry


GENERATOR = "v2/scripts/render_entry.py"
MARKER = f"<!-- generated-by: {GENERATOR} schema=4 -->"

LABELS = {
    "en": {
        "title": "encyclopedia entry",
        "identity": "Entry identity",
        "roots": "Roots",
        "status": "Status",
        "profile": "Root profile",
        "branches": "Branch overview",
        "branch": "Branch",
        "image": "Arabic branch image",
        "summary": "Short summary",
        "organization": "Organization",
        "collocation": "Collocation profile",
        "source_discussion": "Dictionary discussion",
        "arabic_definition": "Arabic branch definition",
        "arabic_boundary": "Arabic exclusion boundary",
        "source_phrase": "Arabic source phrase",
        "identity_judgment": "Branch identity judgment",
        "identity_boundary": "Authored identity boundary",
        "definition": "Semantic definition",
        "lexicalization": "Lexicalization",
        "lexicalization_scope": "Authored lexicalization scope",
        "non_bare": "non-bare",
        "concept_map": "Concept-map facets",
        "facet_role": "Facet role",
        "lexical_realizations": "Lexical realizations",
        "usage_notes": "Structured usage notes",
        "qualifiers": "Evidence qualifiers",
        "expression": "Arabic expression",
        "sense": "Recorded sense",
        "target_gloss": "Target-language rendering",
        "quran_form": "QAC-linked form",
        "usage_role": "Usage role",
        "applicability": "Applicability",
        "examples": "Main source examples",
        "disagreement": "Source disagreement",
        "no_disagreement": "No source disagreement is recorded.",
        "dictionary_basis": "Dictionary basis",
        "dictionary_basis_line": "{dictionaries} dictionaries, {passages} passages: {names}.",
        "dictionary": "Dictionary",
        "roles": "Role",
        "contribution": "Contribution to this branch",
        "refs": "Evidence handles",
        "selected": "Selected target-language glosses",
        "rank": "Rank",
        "gloss": "Gloss",
        "loanword": "Loanword status",
        "fit": "Error type",
        "preserves": "Preserves",
        "loss_addition": "Loss / addition",
        "collision": "Collision risk",
        "excluded": "Excluded or confusable glosses",
        "category": "Category",
        "reason": "Why excluded",
        "neighbors": "Arabic neighbor distinctions",
        "no_useful_neighbors": "No materially useful neighbor distinction was selected.",
        "neighbor_coverage": "Neighbor coverage",
        "neighbor": "Arabic neighbor (link target)",
        "shared": "Shared zone",
        "distinction": "Significant distinction",
        "occurrence_notes": "Translator-facing occurrence observations",
        "no_observations": "No supported recurring observation was added.",
        "occurrence_appendix": "Occurrence forms, grammar, and attachments",
        "occurrence_notice": (
            "The appendix is generated evidence. It does not assign Quran "
            "occurrences to dictionary branches or senses."
        ),
    },
    "tr": {
        "title": "ansiklopedi maddesi",
        "identity": "Madde kimliği",
        "roots": "Kökler",
        "status": "Durum",
        "profile": "Kök profili",
        "branches": "Dal özeti",
        "branch": "Dal",
        "image": "Arapça dal imgesi",
        "summary": "Kısa özet",
        "organization": "Örgütlenme",
        "collocation": "Eşdizim profili",
        "source_discussion": "Sözlük tartışması",
        "arabic_definition": "Arapça dal tanımı",
        "arabic_boundary": "Arapça dışlama sınırı",
        "source_phrase": "Arapça kaynak ifadesi",
        "identity_judgment": "Dal kimliği kararı",
        "identity_boundary": "Yazılmış kimlik sınırı",
        "definition": "Anlam tanımı",
        "lexicalization": "Sözlüksel yapı",
        "lexicalization_scope": "Yazılmış sözlüksel kapsam",
        "non_bare": "çıplak olmayan",
        "concept_map": "Kavram haritası öğeleri",
        "facet_role": "Öğe rolü",
        "lexical_realizations": "Sözlüksel gerçekleşmeler",
        "usage_notes": "Yapılandırılmış kullanım notları",
        "qualifiers": "Kanıt niteleyicileri",
        "expression": "Arapça ifade",
        "sense": "Kaydedilen anlam",
        "target_gloss": "Hedef dil anlatımı",
        "quran_form": "QAC bağlantılı biçim",
        "usage_role": "Kullanım rolü",
        "applicability": "Uygulanabilirlik",
        "examples": "Ana kaynak örnekleri",
        "disagreement": "Kaynak ihtilafı",
        "no_disagreement": "Kaynaklar arasında açık bir ihtilaf kaydedilmemiştir.",
        "dictionary_basis": "Sözlük temeli",
        "dictionary_basis_line": "{dictionaries} sözlük, {passages} pasaj: {names}.",
        "dictionary": "Sözlük",
        "roles": "Rol",
        "contribution": "Bu dala katkısı",
        "refs": "Kanıt tutamakları",
        "selected": "Seçilen hedef-dil karşılıkları",
        "rank": "Sıra",
        "gloss": "Karşılık",
        "loanword": "Alıntı durumu",
        "fit": "Hata türü",
        "preserves": "Koruduğu",
        "loss_addition": "Kaybı / eklemesi",
        "collision": "Çakışma riski",
        "excluded": "Elenen veya karışabilecek karşılıklar",
        "category": "Kategori",
        "reason": "Neden elendi",
        "neighbors": "Arapça komşu ayrımları",
        "no_useful_neighbors": "Anlam sınırını belirginleştiren yararlı bir komşu ayrımı seçilmedi.",
        "neighbor_coverage": "Komşu kapsamı",
        "neighbor": "Arapça komşu (bağlantı hedefi)",
        "shared": "Ortak alan",
        "distinction": "Belirgin ayrım",
        "occurrence_notes": "Çevirmen için oluşum gözlemleri",
        "no_observations": "Destekli bir yinelenen gözlem eklenmemiştir.",
        "occurrence_appendix": "Oluşum biçimleri, dilbilgisi ve bağlantılar",
        "occurrence_notice": (
            "Ek, üretilmiş kanıttır. Kur'an oluşumlarını sözlük dallarına veya "
            "anlamlara atamaz."
        ),
    },
}

ENUM_LABELS = {
    "en": {
        "draft": "draft",
        "reviewed": "reviewed",
        "published": "published",
        "monosemic": "monosemic",
        "polysemic": "polysemic",
        "radial": "radial",
        "multi_branch": "multiple branches",
        "mixed": "mixed",
        "uncertain": "uncertain",
        "low": "low",
        "moderate": "moderate",
        "high": "high",
        "unknown": "unknown",
        "base_definition": "base definition",
        "corroboration": "corroboration",
        "boundary": "boundary",
        "derivation": "derivation",
        "example": "example",
        "disagreement": "disagreement",
        "sole_attestation": "sole attestation",
        "reading": "reading",
        "none": "none",
        "common": "common",
        "specialist": "specialist",
        "narrowing": "narrowing",
        "broadening": "broadening",
        "displacement": "displacement",
        "drifted_loanword": "drifted loanword",
        "alternative": "alternative",
        "common_loanword": "common loanword",
        "confusable": "confusable",
        "recurrent_pattern": "recurrent pattern",
        "exception": "exception",
        "grammar": "grammar",
        "translation_risk": "translation risk",
        "synonym": "synonym",
        "near_synonym": "near synonym",
        "antonym": "antonym",
        "polarity_pair": "polarity pair",
        "near_neighbor": "near neighbor",
        "same_field": "same field",
        "thematic": "thematic",
        "none_useful": "none useful",
        "other": "other",
        "bare": "bare",
        "collocation": "collocation",
        "mixed_non_bare": "mixed non-bare",
        "non_bare": "non-bare",
        "unresolved": "unresolved",
        "accepted": "accepted",
        "qualified": "qualified",
        "reframed": "reframed",
        "structural_review_required": "structural review required",
    },
    "tr": {
        "draft": "taslak",
        "reviewed": "incelenmiş",
        "published": "yayımlanmış",
        "monosemic": "tek anlamlı",
        "polysemic": "çok anlamlı",
        "radial": "radyal",
        "multi_branch": "çok dallı",
        "mixed": "karma",
        "uncertain": "belirsiz",
        "low": "düşük",
        "moderate": "orta",
        "high": "yüksek",
        "unknown": "bilinmiyor",
        "base_definition": "temel tanım",
        "corroboration": "destek",
        "boundary": "sınır",
        "derivation": "iştikak",
        "example": "örnek",
        "disagreement": "ihtilaf",
        "sole_attestation": "tek tanıklık",
        "reading": "okuyuş",
        "none": "yok",
        "common": "yaygın",
        "specialist": "uzmanlık alanı",
        "narrowing": "daralma",
        "broadening": "genişleme",
        "displacement": "yer değiştirme",
        "drifted_loanword": "anlamı kaymış alıntı",
        "alternative": "alternatif",
        "common_loanword": "yaygın alıntı",
        "confusable": "karışabilir",
        "recurrent_pattern": "yinelenen örüntü",
        "exception": "istisna",
        "grammar": "dilbilgisi",
        "translation_risk": "çeviri riski",
        "synonym": "eş anlamlı",
        "near_synonym": "yakın anlamlı",
        "antonym": "karşıt anlamlı",
        "polarity_pair": "kutupsal karşıt",
        "near_neighbor": "yakın komşu",
        "same_field": "aynı anlam alanı",
        "thematic": "tematik",
        "none_useful": "yararlı ayrım yok",
        "other": "diğer",
        "bare": "çıplak",
        "collocation": "eşdizim",
        "mixed_non_bare": "karma çıplak olmayan",
        "non_bare": "çıplak olmayan",
        "unresolved": "çözümlenmemiş",
        "accepted": "kabul edildi",
        "qualified": "kayıtlı kabul",
        "reframed": "yeniden çerçevelendi",
        "structural_review_required": "yapısal inceleme gerekli",
    },
}


def plain_text(value: Any) -> str:
    text = " ".join(str(value).replace("\r", " ").replace("\n", " ").split())
    for character in ("\\", "`", "*", "_", "{", "}", "[", "]", "<", ">", "#"):
        text = text.replace(character, f"\\{character}")
    return text


def enum_label(language: str, value: str) -> str:
    return ENUM_LABELS[language].get(value, plain_text(value.replace("_", " ")))


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def codes(values: list[str]) -> str:
    return "; ".join(f"`{cell(str(value).replace('`', '&#96;'))}`" for value in values)


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    result = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    result.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return result


def occurrence_appendix(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("<!-- generated-by: v2/scripts/render_occurrences.py"):
        raise ContractError(f"Unrecognized occurrence artifact: {path}")
    result = []
    skipped_title = False
    for line in lines[1:]:
        if not skipped_title and line.startswith("# "):
            skipped_title = True
            continue
        match = re.match(r"^(#{2,6})( .*)$", line)
        if match:
            hashes = match.group(1)
            line = f"{'#' * min(6, len(hashes) + 1)}{match.group(2)}"
        result.append(line)
    while result and not result[0]:
        result.pop(0)
    return result


def render_markdown(entry: dict, packet: dict) -> str:
    language = entry["language"]
    label = LABELS[language]
    roots = {row["root_id"]: row["root_norm"] for row in packet["v4_roots"]}
    packet_branches = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    root_text = " / ".join(plain_text(roots[root_id]) for root_id in entry["root_ids"])
    profile = entry["root_profile"]
    lines = [
        MARKER,
        f"# {root_text} ({plain_text(profile['transliteration'])}): {label['title']}",
        "",
        f"- **{label['identity']}:** `{entry['entry_id']}`",
        f"- **{label['roots']}:** "
        + ", ".join(f"`{root_id}` (`{roots[root_id]}`)" for root_id in entry["root_ids"]),
        f"- **{label['status']}:** {enum_label(language, entry['status'])}",
        "",
        f"## {label['profile']}",
        "",
        plain_text(profile["summary"]),
        "",
        f"- **{label['organization']}:** {enum_label(language, profile['polysemy'])} / "
        f"{enum_label(language, profile['organization'])}; "
        f"{profile['branch_count']} {label['branch'].lower()}",
        f"- **{label['collocation']}:** {enum_label(language, profile['collocation_weight'])}. "
        f"{plain_text(profile['collocation_note'])}",
        "",
        f"## {label['branches']}",
        "",
    ]
    overview = []
    for branch in entry["branches"]:
        frozen = packet_branches[(branch["root_id"], branch["branch_id"])]
        overview.append(
            [
                f"`{branch['root_id']}/{branch['branch_id']}`",
                f"`{plain_text(frozen['branch_image_ar'])}` ({plain_text(branch['image_transliteration'])})",
                plain_text(branch["summary"]),
            ]
        )
    lines.extend(table([label["branch"], label["image"], label["summary"]], overview))

    for branch in entry["branches"]:
        frozen = packet_branches[(branch["root_id"], branch["branch_id"])]
        branch_key = f"{branch['root_id']}/{branch['branch_id']}"
        lexicalization_profile = branch.get(
            "lexicalization_profile"
        ) or branch_lexicalization_profile(branch["lexical_realizations"])
        lines.extend(
            [
                "",
                f"## {branch['branch_id']}: {plain_text(frozen['branch_image_ar'])}",
                "",
                f"- **{label['identity']}:** `{branch_key}`",
                f"- **{label['image']}:** `{plain_text(frozen['branch_image_ar'])}` "
                f"({plain_text(branch['image_transliteration'])})",
                f"- **{label['arabic_definition']}:** `{plain_text(branch['what_is_ar'])}`",
                f"- **{label['arabic_boundary']}:** `{plain_text(branch['what_is_not_ar'])}`",
                f"- **{label['source_phrase']}:** `{plain_text(branch['source_phrase_ar'])}`",
                f"- **{label['definition']}:** "
                f"{plain_text(branch['glosses']['semantic_definition'])}",
                f"- **{label['lexicalization']}:** "
                f"{enum_label(language, lexicalization_profile['branch_kind'])}; "
                f"{label['non_bare']}="
                f"{str(lexicalization_profile['has_non_bare']).lower()}",
            ]
        )
        identity = branch.get("identity_judgment")
        if identity:
            lines.extend(
                [
                    f"- **{label['identity_judgment']}:** "
                    f"{enum_label(language, identity['status'])}. "
                    f"{plain_text(identity['rationale'])}",
                    f"- **{label['identity_boundary']}:** "
                    f"{plain_text(identity['boundary_note'])}",
                ]
            )
        lexicalization_scope = branch.get("lexicalization_scope")
        if lexicalization_scope:
            lines.append(
                f"- **{label['lexicalization_scope']}:** "
                f"{enum_label(language, lexicalization_scope['branch_kind'])}. "
                f"{plain_text(lexicalization_scope['note'])}"
            )
        if "concept_map" in branch:
            lines.extend(["", f"### {label['concept_map']}", ""])
            lines.extend(
                table(
                    [label["facet_role"], label["summary"], label["refs"]],
                    [
                        [
                            enum_label(language, facet["role"]),
                            plain_text(facet["statement"]),
                            ", ".join(facet["claim_ids"]),
                        ]
                        for facet in branch["concept_map"]["facets"]
                    ],
                )
            )
        lines.extend(["", f"### {label['lexical_realizations']}", ""])
        lexical_rows = []
        for unit in branch["lexical_realizations"]:
            quran_form = unit["quran_form"]
            lexical_rows.append(
                [
                    f"`{plain_text(unit['expression_ar'])}`",
                    plain_text(unit["sense_ar"]),
                    plain_text(unit.get("target_gloss", "-")),
                    (
                        f"`{plain_text(quran_form['stem_ar'])}` ({plain_text(quran_form['tag'])})"
                        if quran_form
                        else "-"
                    ),
                    codes(unit["evidence_refs"]),
                ]
            )
        if lexical_rows:
            lines.extend(
                table(
                    [
                        label["expression"],
                        label["sense"],
                        label["target_gloss"],
                        label["quran_form"],
                        label["refs"],
                    ],
                    lexical_rows,
                )
            )
        else:
            lines.append("-")
        if branch["usage_notes"]:
            lines.extend(["", f"### {label['usage_notes']}", ""])
            for note in branch["usage_notes"]:
                lines.append(
                    f"- **{enum_label(language, note['kind'])}:** "
                    f"{plain_text(note['statement'])} ({codes(note['evidence_refs'])})"
                )
        if branch["evidence_qualifiers"]:
            lines.extend(["", f"### {label['qualifiers']}", ""])
            for qualifier in branch["evidence_qualifiers"]:
                lines.append(
                    f"- **{enum_label(language, qualifier['type'])}:** "
                    f"{plain_text(qualifier['statement'])} ({codes(qualifier['source_refs'])})"
                )
        lines.extend(
            [
                "",
                f"### {label['dictionary_basis']}",
                "",
            ]
        )
        basis = branch["dictionary_basis"]
        names = ", ".join(plain_text(source["dictionary_name"]) for source in basis["sources"])
        lines.append(
            label["dictionary_basis_line"].format(
                dictionaries=basis["dictionary_count"],
                passages=basis["passage_count"],
                names=names,
            )
        )
        lines.append("")
        if any("roles" in source for source in basis["sources"]):
            source_rows = [
                [
                    plain_text(source["dictionary_name"]),
                    ", ".join(
                        enum_label(language, role) for role in source.get("roles", [])
                    ),
                    plain_text(source.get("contribution", "-")),
                    codes(source["source_refs"]),
                ]
                for source in basis["sources"]
            ]
            lines.extend(
                table(
                    [label["dictionary"], label["roles"], label["contribution"], label["refs"]],
                    source_rows,
                )
            )
        else:
            lines.extend(
                table(
                    [label["dictionary"], label["refs"]],
                    [
                        [plain_text(source["dictionary_name"]), codes(source["source_refs"])]
                        for source in basis["sources"]
                    ],
                )
            )

        discussion = branch["source_discussion"]
        lines.extend(
            ["", f"### {label['source_discussion']}", "", plain_text(discussion["discussion"])]
        )
        source_names = {
            source["source_id"]: plain_text(source["dictionary_name"])
            for source in branch["dictionary_basis"]["sources"]
        }
        for detail in discussion.get("details", []):
            lines.append(
                f"- **{enum_label(language, detail['kind'])}:** "
                f"[{', '.join(source_names[source_id] for source_id in detail['source_ids'])}] "
                f"{plain_text(detail['summary'])} ({codes(detail['source_refs'])})"
            )
        if discussion["examples"]:
            lines.extend(["", f"**{label['examples']}:**", ""])
            for example in discussion["examples"]:
                lines.append(
                    f"- `{plain_text(example['arabic'])}`: {plain_text(example['note'])} "
                    f"({codes(example['source_refs'])})"
                )
        lines.extend(["", f"**{label['disagreement']}:** "])
        if discussion["disagreement"] is None:
            lines[-1] += label["no_disagreement"]
        else:
            disagreement = discussion["disagreement"]
            lines[-1] += (
                f"{plain_text(disagreement['summary'])} ({codes(disagreement['source_refs'])})"
            )

        lines.extend(["", f"### {label['selected']}", ""])
        selected_rows = []
        for gloss in sorted(branch["glosses"]["selected"], key=lambda row: row["rank"]):
            error = gloss["error_profile"]
            selected_rows.append(
                [
                    gloss["rank"],
                    f"**{plain_text(gloss['text'])}**",
                    enum_label(language, gloss["loanword_status"]),
                    enum_label(language, gloss["usage_role"]),
                    plain_text(gloss["applicability"]),
                    enum_label(language, error["fit"]),
                    plain_text(error["preserves"]),
                    f"{plain_text(error['loses']) if error['loses'] else '-'} / "
                    f"{plain_text(error['adds']) if error['adds'] else '-'}",
                    plain_text(error["collision"]) if error["collision"] else "-",
                ]
            )
        lines.extend(
            table(
                [
                    label["rank"],
                    label["gloss"],
                    label["loanword"],
                    label["usage_role"],
                    label["applicability"],
                    label["fit"],
                    label["preserves"],
                    label["loss_addition"],
                    label["collision"],
                ],
                selected_rows,
            )
        )

        lines.extend(["", f"### {label['excluded']}", ""])
        excluded_rows = []
        for gloss in branch["glosses"]["excluded"]:
            error = gloss["error_profile"]
            excluded_rows.append(
                [
                    f"**{plain_text(gloss['text'])}**",
                    enum_label(language, gloss["category"]),
                    plain_text(gloss["exclusion_reason"]),
                    f"{enum_label(language, error['fit'])}; {plain_text(error['preserves'])} "
                    f"{plain_text(error['loses']) if error['loses'] else ''} "
                    f"{plain_text(error['adds']) if error['adds'] else ''} "
                    f"{plain_text(error['collision']) if error['collision'] else ''}",
                ]
            )
        lines.extend(
            table(
                [label["gloss"], label["category"], label["reason"], label["fit"]],
                excluded_rows,
            )
        )

        lines.extend(["", f"### {label['neighbors']}", ""])
        neighbor_rows = []
        for neighbor in branch["arabic_neighbor_distinctions"]:
            target = f"{neighbor['neighbor_root_id']}/{neighbor['neighbor_branch_id']}"
            relation = (
                f"; {enum_label(language, neighbor['relation_type'])}"
                if "relation_type" in neighbor
                else ""
            )
            neighbor_rows.append(
                [
                    f"`{plain_text(neighbor['expression_ar'])}` "
                    f"({plain_text(neighbor['expression_transliteration'])}); "
                    f"**{plain_text(neighbor['gloss'])}** (`{target}`{relation})",
                    plain_text(neighbor["shared_zone"]),
                    plain_text(neighbor["distinction"]),
                    codes(neighbor["evidence_refs"]),
                ]
            )
        if neighbor_rows:
            lines.extend(
                table(
                    [
                        label["neighbor"],
                        label["shared"],
                        label["distinction"],
                        label["refs"],
                    ],
                    neighbor_rows,
                )
            )
        else:
            lines.append(label["no_useful_neighbors"])
        coverage = branch["neighbor_coverage"]
        lines.extend(
            [
                "",
                f"**{label['neighbor_coverage']}:** "
                f"{coverage['candidate_count']}; "
                f"{enum_label(language, coverage['assessment'])}. "
                f"{plain_text(coverage['note'])}",
            ]
        )

    lines.extend(["", f"## {label['occurrence_notes']}", ""])
    observations = entry["occurrence_evidence"]["observations"]
    if observations:
        for observation in observations:
            lines.append(
                f"- **{enum_label(language, observation['category'])}:** "
                f"{plain_text(observation['statement'])} "
                f"({codes(observation['evidence_refs'])})"
            )
    else:
        lines.append(label["no_observations"])

    lines.extend(
        [
            "",
            f"## {label['occurrence_appendix']}",
            "",
            f"> {label['occurrence_notice']}",
            "",
        ]
    )
    artifact = project_path(entry["occurrence_evidence"]["artifact_path"])
    lines.extend(occurrence_appendix(artifact))
    return "\n".join(lines).rstrip() + "\n"


def write_rendered(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file():
            raise ContractError(f"Missing rendered entry: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise ContractError(f"Stale rendered entry: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        first = path.read_text(encoding="utf-8").splitlines()[:1]
        if not first or not first[0].startswith(
            f"<!-- generated-by: {GENERATOR} schema="
        ):
            raise ContractError(f"Refusing to replace unmarked Markdown: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def render(entry_path: Path, output_path: Path, *, check: bool = False) -> str:
    entry, packet = validate_entry(entry_path.resolve())
    content = render_markdown(entry, packet)
    write_rendered(output_path.resolve(), content, check=check)
    return content


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output or args.entry.with_suffix(".md")
    try:
        content = render(args.entry, output, check=args.check)
    except (OSError, ContractError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from error
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {output} ({len(content.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
