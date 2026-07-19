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

from v2.scripts.validate_entry import ContractError, project_path, validate_entry


GENERATOR = "v2/scripts/render_entry.py"
MARKER = f"<!-- generated-by: {GENERATOR} schema=2 -->"

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


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def codes(values: list[str]) -> str:
    return "; ".join(f"`{cell(value)}`" for value in values)


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
    root_text = " / ".join(roots[root_id] for root_id in entry["root_ids"])
    profile = entry["root_profile"]
    lines = [
        MARKER,
        f"# {root_text} ({profile['transliteration']}): {label['title']}",
        "",
        f"- **{label['identity']}:** `{entry['entry_id']}`",
        f"- **{label['roots']}:** "
        + ", ".join(f"`{root_id}` (`{roots[root_id]}`)" for root_id in entry["root_ids"]),
        f"- **{label['status']}:** `{entry['status']}`",
        "",
        f"## {label['profile']}",
        "",
        profile["summary"],
        "",
        f"- **{label['organization']}:** `{profile['polysemy']}` / `{profile['organization']}`; "
        f"{profile['branch_count']} {label['branch'].lower()}",
        f"- **{label['collocation']}:** `{profile['collocation_weight']}`. "
        f"{profile['collocation_note']}",
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
                f"`{frozen['branch_image_ar']}` ({branch['image_transliteration']})",
                branch["summary"],
            ]
        )
    lines.extend(table([label["branch"], label["image"], label["summary"]], overview))

    for branch in entry["branches"]:
        frozen = packet_branches[(branch["root_id"], branch["branch_id"])]
        branch_key = f"{branch['root_id']}/{branch['branch_id']}"
        lines.extend(
            [
                "",
                f"## {branch['branch_id']}: {frozen['branch_image_ar']}",
                "",
                f"- **{label['identity']}:** `{branch_key}`",
                f"- **{label['image']}:** `{frozen['branch_image_ar']}` "
                f"({branch['image_transliteration']})",
                "",
                f"### {label['dictionary_basis']}",
                "",
            ]
        )
        basis = branch["dictionary_basis"]
        names = ", ".join(source["dictionary_name"] for source in basis["sources"])
        lines.append(
            label["dictionary_basis_line"].format(
                dictionaries=basis["dictionary_count"],
                passages=basis["passage_count"],
                names=names,
            )
        )
        lines.append("")
        source_rows = [
            [
                source["dictionary_name"],
                ", ".join(f"`{role}`" for role in source["roles"]),
                source["contribution"],
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

        discussion = branch["source_discussion"]
        lines.extend(["", f"### {label['source_discussion']}", "", discussion["discussion"]])
        if discussion["examples"]:
            lines.extend(["", f"**{label['examples']}:**", ""])
            for example in discussion["examples"]:
                lines.append(
                    f"- `{example['arabic']}`: {example['note']} "
                    f"({codes(example['source_refs'])})"
                )
        lines.extend(["", f"**{label['disagreement']}:** "])
        if discussion["disagreement"] is None:
            lines[-1] += label["no_disagreement"]
        else:
            disagreement = discussion["disagreement"]
            lines[-1] += (
                f"{disagreement['summary']} ({codes(disagreement['source_refs'])})"
            )

        lines.extend(["", f"### {label['selected']}", ""])
        selected_rows = []
        for gloss in sorted(branch["glosses"]["selected"], key=lambda row: row["rank"]):
            error = gloss["error_profile"]
            selected_rows.append(
                [
                    gloss["rank"],
                    f"**{gloss['text']}**",
                    f"`{gloss['loanword_status']}`",
                    f"`{error['fit']}`",
                    error["preserves"],
                    f"{error['loses']} / {error['adds']}",
                    error["collision"],
                ]
            )
        lines.extend(
            table(
                [
                    label["rank"],
                    label["gloss"],
                    label["loanword"],
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
                    f"**{gloss['text']}**",
                    f"`{gloss['category']}`",
                    gloss["exclusion_reason"],
                    f"`{error['fit']}`; {error['preserves']} {error['loses']} "
                    f"{error['adds']} {error['collision']}",
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
            neighbor_rows.append(
                [
                    f"`{neighbor['expression_ar']}` ({neighbor['expression_transliteration']}); "
                    f"**{neighbor['gloss']}** (`{target}`)",
                    neighbor["shared_zone"],
                    neighbor["distinction"],
                    codes(neighbor["evidence_refs"]),
                ]
            )
        lines.extend(
            table(
                [label["neighbor"], label["shared"], label["distinction"], label["refs"]],
                neighbor_rows,
            )
        )

    lines.extend(["", f"## {label['occurrence_notes']}", ""])
    observations = entry["occurrence_evidence"]["observations"]
    if observations:
        for observation in observations:
            lines.append(
                f"- **`{observation['category']}`:** {observation['statement']} "
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
        if first != [MARKER]:
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
