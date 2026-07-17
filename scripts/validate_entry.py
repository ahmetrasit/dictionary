#!/usr/bin/env python3
"""Validate a completed Markdown entry against its root evidence packet."""

import argparse
import json
import re
from pathlib import Path

try:
    from .build_entry_bundles import load_packet, selector_matches
    from .build_entry_scaffolds import (
        aggregate_columns,
        attachment_links,
        attachment_rows_by_id,
        branch_ref,
        branch_source_rows,
        cell,
        forms_rows,
        linked_senses,
        packet_envelope,
        render_frame,
        validate_packet,
        occurrence_unit_id,
    )
except ImportError:
    from build_entry_bundles import load_packet, selector_matches
    from build_entry_scaffolds import (
        aggregate_columns,
        attachment_links,
        attachment_rows_by_id,
        branch_ref,
        branch_source_rows,
        cell,
        forms_rows,
        linked_senses,
        packet_envelope,
        render_frame,
        validate_packet,
        occurrence_unit_id,
    )


BRANCH_REF_RE = r"root_\d{6}/B\d{3}"
REVIEW_MARKER_RE = re.compile(r"\[REVIEW REQUIRED(?:: [^\]]+)?\]")
ROLE_VALUES = {"primary", "alternative", "recognition"}
FIT_VALUES = {"none", "narrowing", "broadening", "displacement", "drifted_loanword"}
SOURCE_RELATIONSHIPS = {
    "explicit_support",
    "compatible_support",
    "additional_nuance",
    "explicit_disagreement",
    "sole_attestation",
    "no_located_attestation",
}


class Markdown:
    def __init__(self, text):
        self.text = text
        self.lines = text.splitlines()
        self.code_lines = self._code_lines()
        self.headings = []
        for index, line in enumerate(self.lines):
            if self.code_lines[index]:
                continue
            match = re.match(r"^(#{1,6}) (.+?)\s*$", line)
            if match:
                self.headings.append((index, len(match.group(1)), match.group(2)))

    def _code_lines(self):
        result = []
        fence_character = None
        fence_length = 0
        for line in self.lines:
            stripped = line.lstrip()
            match = re.match(r"^(`{3,}|~{3,})", stripped)
            marker = match.group(1) if match else None
            result.append(fence_character is not None or marker is not None)
            if marker and fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif (
                marker
                and marker[0] == fence_character
                and len(marker) >= fence_length
            ):
                fence_character = None
                fence_length = 0
        return result

    def heading_ranges(self, level, title):
        positions = [
            index
            for index, heading_level, heading_title in self.headings
            if heading_level == level and heading_title == title
        ]
        ranges = []
        for start in positions:
            end = len(self.lines)
            for index, heading_level, _ in self.headings:
                if index > start and heading_level <= level:
                    end = index
                    break
            ranges.append((start, end))
        return ranges

    def unique_range(self, level, title, errors, label=None):
        ranges = self.heading_ranges(level, title)
        if len(ranges) != 1:
            errors.append(
                f"{label or title}: expected one level-{level} heading, found {len(ranges)}"
            )
            return None
        return ranges[0]

    def child_headings(self, bounds, level):
        start, end = bounds
        return [
            (index, title)
            for index, heading_level, title in self.headings
            if start < index < end and heading_level == level
        ]

    def body(self, bounds):
        return "\n".join(self.lines[bounds[0] + 1 : bounds[1]])


def markdown_cells(line):
    raw = line.strip()
    if not raw.startswith("|") or not raw.endswith("|"):
        return []
    return [
        value.strip().replace("\\|", "|")
        for value in re.split(r"(?<!\\)\|", raw[1:-1])
    ]


def parse_table(document, bounds, headers, errors, label):
    index = bounds[0] + 1
    while index < bounds[1] and not document.lines[index].strip():
        index += 1
    if index >= bounds[1]:
        errors.append(f"{label}: missing table")
        return []
    actual_headers = markdown_cells(document.lines[index])
    if actual_headers != headers:
        errors.append(f"{label}: table headers differ: {actual_headers}")
        return []
    index += 1
    if index >= bounds[1]:
        errors.append(f"{label}: missing table delimiter")
        return []
    delimiters = markdown_cells(document.lines[index])
    if len(delimiters) != len(headers) or any(
        not re.fullmatch(r":?-{3,}:?", value) for value in delimiters
    ):
        errors.append(f"{label}: malformed table delimiter")
        return []
    index += 1
    rows = []
    while index < bounds[1]:
        line = document.lines[index]
        if not line.strip():
            break
        if document.code_lines[index] or not line.strip().startswith("|"):
            break
        row = markdown_cells(line)
        if len(row) != len(headers):
            errors.append(f"{label}: expected {len(headers)} columns, found {len(row)}")
        else:
            rows.append(row)
        index += 1
    trailing = [
        document.lines[position].strip()
        for position in range(index, bounds[1])
        if document.lines[position].strip()
        and not document.code_lines[position]
        and not document.lines[position].strip().startswith("<!--")
    ]
    if trailing:
        errors.append(f"{label}: unexpected content after canonical table")
    return rows


def normalized_line(value):
    return " ".join(str(value or "").split())


def list_field(label, value):
    rendered = cell(value)
    return f"- {label}: {rendered}" if rendered else f"- {label}:"


def exact_line_indexes(document, line, bounds=None):
    start, end = bounds or (0, len(document.lines))
    return [
        index
        for index in range(start, end)
        if not document.code_lines[index] and document.lines[index] == line
    ]


def exact_field_prefix(line):
    field_starts = (
        "- ",
        "English transliteration:",
        "Türkçe çevriyazı:",
        "English explanation:",
        "Türkçe açıklama:",
        "Examples or special analysis:",
    )
    if not line.startswith(field_starts):
        return None
    separator = line.find(":")
    if separator < 0:
        return None
    if separator + 1 < len(line) and line[separator + 1] != " ":
        return None
    return line[: separator + 1]


def require_exact_line(document, line, errors, label, bounds=None):
    prefix = exact_field_prefix(line)
    if prefix:
        start, end = bounds or (0, len(document.lines))
        candidates = [
            document.lines[index]
            for index in range(start, end)
            if not document.code_lines[index]
            and (
                document.lines[index] == prefix
                or document.lines[index].startswith(prefix + " ")
            )
        ]
        if candidates != [line]:
            errors.append(
                f"{label}: expected one {prefix!r} field equal to {line!r}; "
                f"found {candidates}"
            )
        return
    count = len(exact_line_indexes(document, line, bounds))
    if count != 1:
        errors.append(f"{label}: expected exact line once, found {count}: {line}")


def nonempty_section(document, bounds):
    content = []
    for index in range(bounds[0] + 1, bounds[1]):
        line = document.lines[index].strip()
        if (
            line
            and not document.code_lines[index]
            and not line.startswith("<!--")
            and not line.startswith("#")
        ):
            content.append(line)
    return bool(content)


def labeled_values(document, bounds, prefix):
    return [
        document.lines[index][len(prefix) :].strip()
        for index in range(bounds[0] + 1, bounds[1])
        if not document.code_lines[index] and document.lines[index].startswith(prefix)
    ]


def require_labeled_value(document, bounds, prefix, errors, label):
    values = labeled_values(document, bounds, prefix)
    if len(values) != 1 or not values[0]:
        errors.append(f"{label}: expected one nonempty {prefix!r} field")
        return None
    return values[0]


def expected_roster(packet):
    return [branch_ref(branch) for branch in packet["branches"]]


def validate_root(packet, packet_path, document, errors):
    expected_h1 = packet["root_norm"]
    h1s = [title for _, level, title in document.headings if level == 1]
    if h1s != [expected_h1]:
        errors.append(f"root title: expected {[expected_h1]}, found {h1s}")
    require_exact_line(
        document,
        "<!-- dictionary-entry-schema: 1 -->",
        errors,
        "schema marker",
    )
    root_bounds = document.unique_range(2, "Root identity", errors)
    if not root_bounds:
        return
    h1_positions = [index for index, level, _ in document.headings if level == 1]
    if h1_positions:
        preamble = (h1_positions[0], root_bounds[0])
        require_labeled_value(
            document, preamble, "- English transliteration: ", errors, "root preamble"
        )
        require_labeled_value(
            document, preamble, "- Türkçe çevriyazı: ", errors, "root preamble"
        )
    require_labeled_value(
        document, root_bounds, "- English transliteration: ", errors, "root identity"
    )
    require_labeled_value(
        document, root_bounds, "- Türkçe çevriyazı: ", errors, "root identity"
    )
    roots = "; ".join(
        f"{row['root_id']} ({row['source_root_norm']})" for row in packet["v4_roots"]
    )
    summary = packet["qac"]["summary"]
    fields = (
        f"- Root envelope ID: `{packet['root_envelope_id']}`",
        f"- Normalized root: `{packet['root_join_key']}`",
        f"- Arabic root: `{packet['root_norm']}`",
        f"- V4 root records: {roots}",
        f"- Frozen branch records: {len(packet['branches'])}",
        f"- QAC rooted morphemes: {summary['morpheme_count']}",
    )
    for field in fields:
        require_exact_line(document, field, errors, "root identity", root_bounds)
    snapshot = require_labeled_value(
        document, root_bounds, "- Source snapshot: ", errors, "root identity"
    )
    if snapshot:
        value = snapshot[1:-1] if snapshot.startswith("`") and snapshot.endswith("`") else snapshot
        try:
            matches = Path(value).resolve() == packet_path.resolve()
        except OSError:
            matches = False
    else:
        matches = False
    if not matches:
        errors.append("root identity: source snapshot is missing, duplicated, or points elsewhere")

    bounds = document.unique_range(2, "Branch index", errors)
    if not bounds:
        return
    rows = parse_table(
        document,
        bounds,
        [
            "V4 branch",
            "Arabic branch image",
            "English transliteration",
            "Türkçe çevriyazı",
            "Cross-reference note",
        ],
        errors,
        "branch index",
    )
    expected = [
        (branch_ref(branch), normalized_line(branch["branch_image_ar"]))
        for branch in packet["branches"]
    ]
    actual = [(row[0], row[1]) for row in rows]
    if actual != expected:
        errors.append(f"branch index packet fields/order differ: {actual}")
    for row in rows:
        if len(row) == 5 and any(not value for value in row[2:]):
            errors.append(f"branch index {row[0]} has an empty review field")


def marker_blocks(document, errors):
    begins = []
    ends = []
    for index, line in enumerate(document.lines):
        if document.code_lines[index]:
            continue
        begin = re.fullmatch(rf"<!-- BEGIN BRANCH ({BRANCH_REF_RE}) -->", line)
        end = re.fullmatch(rf"<!-- END BRANCH ({BRANCH_REF_RE}) -->", line)
        if begin:
            begins.append((index, begin.group(1)))
        if end:
            ends.append((index, end.group(1)))
    blocks = []
    if [ref for _, ref in begins] != [ref for _, ref in ends]:
        errors.append("branch begin/end marker identities or order differ")
        return blocks, begins, ends
    for (start, ref), (end, end_ref) in zip(begins, ends):
        if ref != end_ref or start >= end:
            errors.append(f"malformed branch marker pair for {ref}")
            continue
        blocks.append((ref, start, end))
    for (_, _, previous_end), (_, next_start, _) in zip(blocks, blocks[1:]):
        if next_start <= previous_end:
            errors.append("branch blocks overlap")
    return blocks, begins, ends


def validate_rendering_table(
    branch_doc, heading, errors, ref, allow_placeholders=False
):
    bounds = branch_doc.unique_range(3, heading, errors, f"{ref}: {heading}")
    if not bounds:
        return
    if heading.startswith("English"):
        headers = [
            "Rendering",
            "Role",
            "Preserves",
            "Loses",
            "Adds",
            "Fit error",
            "Collision or misleading concept",
        ]
    else:
        headers = [
            "Karşılık",
            "Rol",
            "Koruduğu",
            "Eksilttiği",
            "Eklediği",
            "Uyum hatası",
            "Karıştırdığı kavram veya yanıltıcı sonuç",
        ]
    rows = parse_table(branch_doc, bounds, headers, errors, f"{ref}: {heading}")
    if not 1 <= len(rows) <= 3:
        errors.append(f"{ref}: {heading} must contain 1-3 rows; found {len(rows)}")
        return
    for number, row in enumerate(rows, start=1):
        if any(not value for value in row):
            errors.append(f"{ref}: {heading} row {number} has an empty cell")
        if allow_placeholders and any(REVIEW_MARKER_RE.fullmatch(value) for value in row):
            continue
        if row[1] not in ROLE_VALUES:
            errors.append(f"{ref}: {heading} row {number} has invalid role {row[1]!r}")
        if row[5] not in FIT_VALUES:
            errors.append(f"{ref}: {heading} row {number} has invalid fit {row[5]!r}")
    if (
        rows
        and rows[0][1] != "primary"
        and not (allow_placeholders and REVIEW_MARKER_RE.fullmatch(rows[0][1]))
    ):
        errors.append(f"{ref}: {heading} first row must be primary")


def validate_lexical_units(packet, branch, branch_doc, errors):
    ref = branch_ref(branch)
    bounds = branch_doc.unique_range(3, "Lexical units and examples", errors, ref)
    if not bounds:
        return
    rows = parse_table(
        branch_doc,
        bounds,
        [
            "Arabic expression",
            "English transliteration",
            "Türkçe çevriyazı",
            "Kind/form",
            "Meaning in this branch",
            "Source/example",
        ],
        errors,
        f"{ref}: lexical units",
    )
    all_senses = linked_senses(packet)
    senses = all_senses[(branch["root_id"], branch["branch_id"])]
    if len(rows) != len(senses):
        errors.append(f"{ref}: expected {len(senses)} lexical rows, found {len(rows)}")
        return
    for row, sense in zip(rows, senses):
        meaning = (
            f"V4 Arabic: {sense.get('sense_ar', '')}; "
            f"English scaffold: {sense.get('sense_en', '')}"
        )
        source = (
            f"{sense.get('source_refs', '')}; phrase: {sense.get('source_phrase_ar', '')}"
        )
        fixed = [
            normalized_line(sense.get("expression_ar")),
            normalized_line(sense.get("unit_kind")),
            normalized_line(meaning),
            normalized_line(source),
        ]
        actual = [row[0], row[3], row[4], row[5]]
        if actual != fixed:
            errors.append(f"{ref}: lexical packet-backed cells differ for {sense['lexical_unit_id']}")
        if not row[1] or not row[2]:
            errors.append(f"{ref}: lexical transliteration is empty for {sense['lexical_unit_id']}")


def validate_source_audit(packet, branch, branch_doc, errors, allow_placeholders):
    ref = branch_ref(branch)
    source_bounds = branch_doc.unique_range(3, "Source audit", errors, ref)
    if not source_bounds:
        return
    sources, unmatched, gaps = branch_source_rows(packet, branch)
    expected_titles = [
        f"{source.get('source_id') or 'unknown-source'} — "
        f"{source.get('headword') or '-'} — passage {number}"
        for number, source in enumerate(sources, start=1)
    ]
    if unmatched:
        expected_titles.append("Unmatched V4 source handles")
    if gaps:
        expected_titles.append("Packet routing gaps")
    actual_titles = [title for _, title in branch_doc.child_headings(source_bounds, 4)]
    if actual_titles != expected_titles:
        errors.append(f"{ref}: source-audit subsection roster/order differs: {actual_titles}")

    for number, source in enumerate(sources, start=1):
        title = expected_titles[number - 1]
        bounds = branch_doc.unique_range(4, title, errors, ref)
        if not bounds:
            continue
        for line in (
            f"- Route status (generated): `{cell(source.get('route_status'))}`",
            f"- Route note (generated): {cell(source.get('route_note'))}",
            f"- Reference (generated): `{cell(source.get('source_ref'))}`",
        ):
            require_exact_line(branch_doc, line, errors, ref, bounds)
        relationship = require_labeled_value(
            branch_doc, bounds, "- Relationship: ", errors, ref
        )
        if (
            relationship
            and relationship not in SOURCE_RELATIONSHIPS
            and not (allow_placeholders and REVIEW_MARKER_RE.fullmatch(relationship))
        ):
            errors.append(f"{ref}: invalid source relationship {relationship!r}")
        for prefix in (
            "- Contribution: ",
            "English transliteration: ",
            "Türkçe çevriyazı: ",
            "English explanation: ",
            "Türkçe açıklama: ",
            "Examples or special analysis: ",
        ):
            require_labeled_value(branch_doc, bounds, prefix, errors, ref)
        quote_paragraphs = []
        current_quote = []
        for index in range(bounds[0] + 1, bounds[1]):
            line = branch_doc.lines[index]
            if not branch_doc.code_lines[index] and line.startswith("> "):
                current_quote.append(line[2:].strip())
            elif current_quote:
                quote_paragraphs.append(normalized_line(" ".join(current_quote)))
                current_quote = []
        if current_quote:
            quote_paragraphs.append(normalized_line(" ".join(current_quote)))
        if len(quote_paragraphs) != 1 or not quote_paragraphs[0]:
            errors.append(f"{ref}: {title} requires one nonempty source quotation")

    if unmatched:
        bounds = branch_doc.unique_range(4, "Unmatched V4 source handles", errors, ref)
        if bounds:
            for handle in unmatched:
                require_exact_line(branch_doc, f"- `{normalized_line(handle)}`", errors, ref, bounds)
    if gaps:
        bounds = branch_doc.unique_range(4, "Packet routing gaps", errors, ref)
        if bounds:
            require_exact_line(
                branch_doc,
                "| Source | Route status | Route note |",
                errors,
                ref,
                bounds,
            )
            require_exact_line(branch_doc, "|---|---|---|", errors, ref, bounds)
            for source in gaps:
                row = (
                    f"| {cell(source.get('source_id'))} | "
                    f"{cell(source.get('route_status'))} | "
                    f"{cell(source.get('route_note'))} |"
                )
                require_exact_line(branch_doc, row, errors, ref, bounds)


def validate_branch(packet, branch, block_text, errors, allow_placeholders=False):
    ref = branch_ref(branch)
    branch_doc = Markdown(block_text)
    expected_title = f"Branch {ref} — {branch['branch_image_ar']}"
    h2s = [title for _, level, title in branch_doc.headings if level == 2]
    if h2s != [expected_title]:
        errors.append(f"{ref}: branch title differs: {h2s}")
    identity = branch_doc.unique_range(3, "V4 identity", errors, ref)
    bundle = (
        Path("data/output/entry_bundles")
        / packet["root_envelope_id"]
        / "branches"
        / f"{branch['root_id']}--{branch['branch_id']}.md"
    )
    fields = (
        f"- Root record: `{branch['root_id']}`",
        f"- Branch record: `{branch['branch_id']}`",
        f"- Arabic image: {normalized_line(branch['branch_image_ar'])}",
        f"- English scaffold: {cell(branch.get('branch_image_en'))}",
        f"- English scaffold fit: `{cell(branch.get('image_en_fit'))}`",
        list_field("English scaffold gap note", branch.get("image_en_gap_note")),
        "- V4 provenance: "
        f"`origin_corpus={normalized_line(branch.get('origin_corpus'))}; "
        f"status={normalized_line(branch.get('status'))}; "
        f"contaminated={normalized_line(branch.get('contaminated'))}`",
        f"- V4 source references: {cell(branch.get('source_refs'))}",
        f"- V4 source phrase: {cell(branch.get('source_phrase_ar'))}",
        f"- V4 review note: {cell(branch.get('review_note'))}",
        f"- Required evidence bundle: `{bundle}`",
        "- QNet discovery: use only the required evidence bundle's QNet appendix; it is not evidence.",
    )
    if identity:
        for field in fields:
            require_exact_line(branch_doc, field, errors, ref, identity)
        require_labeled_value(
            branch_doc, identity, "- English transliteration: ", errors, ref
        )
        require_labeled_value(
            branch_doc, identity, "- Türkçe çevriyazı: ", errors, ref
        )

    h3_expected = [
        "V4 identity",
        "Concept and boundary",
        "Arabic contrasts",
        "Lexical units and examples",
        "Source audit",
        "English renderings and confusions",
        "Turkish renderings and confusions",
        "Target-language distinction notes",
    ]
    h3_actual = [title for _, level, title in branch_doc.headings if level == 3]
    if h3_actual != h3_expected:
        errors.append(f"{ref}: required level-3 heading order differs: {h3_actual}")

    concept = branch_doc.unique_range(3, "Concept and boundary", errors, ref)
    if concept:
        children = branch_doc.child_headings(concept, 4)
        if [title for _, title in children] != [
            "English",
            "Türkçe",
            "What belongs to the branch",
            "What does not belong to the branch",
        ]:
            errors.append(f"{ref}: concept subsection order differs")
        for position, (start, title) in enumerate(children):
            end = children[position + 1][0] if position + 1 < len(children) else concept[1]
            if not nonempty_section(branch_doc, (start, end)):
                errors.append(f"{ref}: concept subsection {title} is empty")
            if title in ("What belongs to the branch", "What does not belong to the branch"):
                immutable = (
                    f"- V4 Arabic boundary: {cell(branch.get('what_is_ar'))}"
                    if title == "What belongs to the branch"
                    else f"- V4 Arabic exclusion: {cell(branch.get('what_is_not_ar'))}"
                )
                require_exact_line(branch_doc, immutable, errors, ref, (start, end))
                editorial = [
                    branch_doc.lines[index]
                    for index in range(start + 1, end)
                    if not branch_doc.code_lines[index]
                    and branch_doc.lines[index].startswith("- ")
                    and branch_doc.lines[index] != immutable
                    and branch_doc.lines[index][2:].strip()
                ]
                if not editorial:
                    errors.append(f"{ref}: {title} lacks a reader-facing explanation")

    contrasts = branch_doc.unique_range(3, "Arabic contrasts", errors, ref)
    if contrasts:
        contrast_rows = parse_table(
            branch_doc,
            contrasts,
            [
                "Arabic neighbor",
                "English transliteration",
                "Türkçe çevriyazı",
                "Shared zone",
                "Distinguishing axis",
                "Evidence",
            ],
            errors,
            f"{ref}: Arabic contrasts",
        )
        if not contrast_rows:
            errors.append(f"{ref}: Arabic contrasts requires at least one explicit row")
        for number, row in enumerate(contrast_rows, start=1):
            if any(not value for value in row):
                errors.append(f"{ref}: Arabic contrasts row {number} has an empty cell")

    notes = branch_doc.unique_range(3, "Target-language distinction notes", errors, ref)
    if notes:
        children = branch_doc.child_headings(notes, 4)
        if [title for _, title in children] != ["English", "Türkçe"]:
            errors.append(f"{ref}: target-language note subsection order differs")
        for position, (start, title) in enumerate(children):
            end = children[position + 1][0] if position + 1 < len(children) else notes[1]
            if not nonempty_section(branch_doc, (start, end)):
                errors.append(f"{ref}: target-language note {title} is empty")

    validate_source_audit(packet, branch, branch_doc, errors, allow_placeholders)
    validate_lexical_units(packet, branch, branch_doc, errors)
    validate_rendering_table(
        branch_doc,
        "English renderings and confusions",
        errors,
        ref,
        allow_placeholders,
    )
    validate_rendering_table(
        branch_doc,
        "Turkish renderings and confusions",
        errors,
        ref,
        allow_placeholders,
    )


def validate_branches(packet, document, errors, allow_placeholders=False):
    roster = expected_roster(packet)
    blocks, begins, ends = marker_blocks(document, errors)
    if [ref for _, ref in begins] != roster:
        errors.append(f"branch begin-marker roster/order mismatch: {[ref for _, ref in begins]}")
    if [ref for _, ref in ends] != roster:
        errors.append(f"branch end-marker roster/order mismatch: {[ref for _, ref in ends]}")
    by_ref = {ref: (start, end) for ref, start, end in blocks}
    for branch in packet["branches"]:
        ref = branch_ref(branch)
        if ref not in by_ref:
            continue
        start, end = by_ref[ref]
        block_text = "\n".join(document.lines[start + 1 : end])
        validate_branch(packet, branch, block_text, errors, allow_placeholders)
    return blocks


def fixed_forms_rows(packet):
    links = attachment_links(packet)
    attachments = attachment_rows_by_id(packet)
    return forms_rows(packet, links, attachments)


def validate_forms(packet, observatory, errors):
    bounds = observatory.unique_range(3, "Forms and lemmas", errors)
    if not bounds:
        return
    rows = parse_table(
        observatory,
        bounds,
        [
            "Arabic lemma/form",
            "English transliteration",
            "Türkçe çevriyazı",
            "POS/morphology",
            "Count",
            "Observed constructions",
        ],
        errors,
        "Quran forms and lemmas",
    )
    expected = []
    for lemma, surface, pos, morphology, count, constructions in fixed_forms_rows(packet):
        expected.append(
            [
                f"lemma={lemma}; surface={surface}",
                f"{pos}; {morphology}",
                str(count),
                constructions,
            ]
        )
    actual = [[row[0], row[3], row[4], row[5]] for row in rows]
    if actual != expected:
        errors.append("Quran forms/lemmas packet-backed cells or order differ")
    for row in rows:
        if not row[1] or not row[2]:
            errors.append(f"Quran form {row[0]} has an empty transliteration")


def validate_aggregate_table(observatory, title, packet_rows, errors, parent_bounds):
    bounds = observatory.unique_range(4, title, errors)
    if not bounds:
        return
    if not (parent_bounds[0] < bounds[0] < parent_bounds[1]):
        errors.append(f"{title}: aggregate table is outside attachment observations")
        return
    if not packet_rows:
        body = observatory.body(bounds).strip()
        if body != "- No packet rows.":
            errors.append(f"{title}: expected exact empty-packet notice")
        return
    columns = aggregate_columns(packet_rows)
    rows = parse_table(observatory, bounds, columns, errors, title)
    expected = [[normalized_line(row.get(column, "")) for column in columns] for row in packet_rows]
    if rows != expected:
        errors.append(f"{title}: packet rows differ")


def validate_occurrences(packet, observatory, errors):
    bounds = observatory.unique_range(3, "Complete occurrences", errors)
    if not bounds:
        return
    rows = parse_table(
        observatory,
        bounds,
        [
            "QAC ref",
            "Arabic surface",
            "English transliteration",
            "Türkçe çevriyazı",
            "Lemma/form",
            "Morphology",
            "Observable frame/attachments",
            "Ayah context handle",
        ],
        errors,
        "Quran occurrences",
    )
    links = attachment_links(packet)
    attachments = attachment_rows_by_id(packet)
    expected = []
    for occurrence in packet["qac"]["occurrences"]:
        expected.append(
            [
                occurrence["qac_ref"],
                normalized_line(occurrence.get("surface_ar")),
                f"{occurrence.get('lemma_ar', '')}; measure={occurrence.get('measure') or '—'}",
                normalized_line(occurrence.get("morph_features")),
                render_frame(links.get(occurrence_unit_id(occurrence)), attachments),
                f"{occurrence['surah']}:{occurrence['ayah']}",
            ]
        )
    actual = [[row[0], row[1], row[4], row[5], row[6], row[7]] for row in rows]
    if actual != expected:
        errors.append("Quran occurrence packet-backed cells or order differ")
    for row in rows:
        if not row[2] or not row[3]:
            errors.append(f"Quran occurrence {row[0]} has an empty transliteration")


def validate_ayahs(packet, observatory, errors):
    parent = observatory.unique_range(3, "Full ayah contexts", errors)
    if not parent:
        return
    children = observatory.child_headings(parent, 4)
    expected_refs = [ayah["ref"] for ayah in packet["qac"].get("ayah_contexts", [])]
    if [title for _, title in children] != expected_refs:
        errors.append("full ayah context handles or order differ from packet")
        return
    for position, (start, ref) in enumerate(children):
        end = children[position + 1][0] if position + 1 < len(children) else parent[1]
        ayah = packet["qac"]["ayah_contexts"][position]
        expected_arabic = normalized_line(ayah["surface_ar"])
        index = start + 1
        while index < end and (
            observatory.code_lines[index] or not observatory.lines[index].strip()
        ):
            index += 1
        paragraph = []
        while index < end:
            if observatory.code_lines[index]:
                index += 1
                continue
            line = observatory.lines[index].strip()
            if not line:
                break
            paragraph.append(line)
            index += 1
        if normalized_line(" ".join(paragraph)) != expected_arabic:
            errors.append(f"{ref}: Arabic ayah context is missing or changed")
        english = [
            observatory.lines[line_index]
            for line_index in range(index, end)
            if not observatory.code_lines[line_index]
            and observatory.lines[line_index].startswith("English transliteration: ")
        ]
        turkish = [
            observatory.lines[line_index]
            for line_index in range(index, end)
            if not observatory.code_lines[line_index]
            and observatory.lines[line_index].startswith("Türkçe çevriyazı: ")
        ]
        if len(english) != 1 or not english[0].removeprefix("English transliteration: ").strip():
            errors.append(f"{ref}: requires one complete English transliteration line")
        if len(turkish) != 1 or not turkish[0].removeprefix("Türkçe çevriyazı: ").strip():
            errors.append(f"{ref}: requires one complete Turkish transliteration line")


def validate_observatory(packet, document, blocks, errors):
    bounds = document.unique_range(2, "Quran occurrence observatory", errors)
    if not bounds:
        return None
    if blocks and bounds[0] < blocks[-1][2]:
        errors.append("Quran occurrence observatory must follow all branch blocks")
    observatory = Markdown("\n".join(document.lines[bounds[0] : bounds[1]]))
    h3_expected = [
        "Census",
        "Forms and lemmas",
        "Attachment and construction observations",
        "Complete occurrences",
        "Full ayah contexts",
    ]
    h3_actual = [title for _, level, title in observatory.headings if level == 3]
    if h3_actual != h3_expected:
        errors.append(f"Quran observatory level-3 heading order differs: {h3_actual}")
    summary = packet["qac"]["summary"]
    census_bounds = observatory.unique_range(3, "Census", errors)
    for line in (
        f"- Rooted morphemes: {summary['morpheme_count']}",
        f"- Words: {summary['word_count']}",
        f"- Ayahs: {summary['ayah_count']}",
        f"- Surahs: {summary['surah_count']}",
    ):
        if census_bounds:
            require_exact_line(observatory, line, errors, "Quran census", census_bounds)
    attachments = packet["attachments"]
    attachment_bounds = observatory.unique_range(
        3, "Attachment and construction observations", errors
    )
    if attachment_bounds:
        aggregate_titles = [
            title for _, title in observatory.child_headings(attachment_bounds, 4)
        ]
        expected_aggregates = [
            "Aggregate verb frames (packet fields)",
            "Aggregate noun patterns (packet fields)",
        ]
        if aggregate_titles != expected_aggregates:
            errors.append(
                f"attachment aggregate subsection order differs: {aggregate_titles}"
            )
    for line in (
        f"- Verb instances: {len(attachments.get('verb_instances', []))}",
        f"- Noun instances: {len(attachments.get('noun_instances', []))}",
        f"- Attachment rows: {len(attachments.get('attachments', []))}",
        f"- Aggregate verb frames: {len(attachments.get('verb_valency_frames', []))}",
        f"- Aggregate noun patterns: {len(attachments.get('noun_governing_patterns', []))}",
    ):
        if attachment_bounds:
            require_exact_line(
                observatory, line, errors, "attachment census", attachment_bounds
            )
    validate_forms(packet, observatory, errors)
    if attachment_bounds:
        validate_aggregate_table(
            observatory,
            "Aggregate verb frames (packet fields)",
            attachments.get("verb_valency_frames", []),
            errors,
            attachment_bounds,
        )
        validate_aggregate_table(
            observatory,
            "Aggregate noun patterns (packet fields)",
            attachments.get("noun_governing_patterns", []),
            errors,
            attachment_bounds,
        )
    validate_occurrences(packet, observatory, errors)
    validate_ayahs(packet, observatory, errors)
    return bounds


def validate_bibliography(document, errors, observatory_bounds):
    bounds = document.unique_range(2, "Bibliography and evidence handles", errors)
    if not bounds:
        return
    if observatory_bounds and bounds[0] != observatory_bounds[1]:
        errors.append("bibliography must immediately follow the Quran observatory")
    if bounds[1] != len(document.lines):
        errors.append("bibliography must be the final level-2 section")
    children = document.child_headings(bounds, 3)
    expected = [
        "Classical dictionaries",
        "Quran morphology and attachment evidence",
        "Target-language usage sources",
    ]
    if [title for _, title in children] != expected:
        errors.append("bibliography subsection order differs")
    for position, (start, title) in enumerate(children):
        end = children[position + 1][0] if position + 1 < len(children) else bounds[1]
        if not nonempty_section(document, (start, end)):
            errors.append(f"bibliography subsection {title} is empty")


def validate_entry(packet, packet_path, text, allow_placeholders=False):
    validate_packet(packet)
    packet["root_envelope_id"] = packet_envelope(packet)
    errors = []
    document = Markdown(text)
    validate_root(packet, packet_path, document, errors)
    blocks = validate_branches(packet, document, errors, allow_placeholders)
    observatory_bounds = validate_observatory(packet, document, blocks, errors)
    validate_bibliography(document, errors, observatory_bounds)
    if not allow_placeholders:
        count = len(REVIEW_MARKER_RE.findall(text))
        if count:
            errors.append(f"unresolved REVIEW REQUIRED markers: {count}")
    return errors


def emit_result(result, as_json):
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("setup_error"):
        print(f"ERROR: {result['setup_error']}")
    elif result["errors"]:
        print(f"INVALID: {result['entry']}")
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print(f"VALID: {result['entry']}")


def main():
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", type=Path)
    parser.add_argument("--root", help="Root selector; required unless --packet is supplied")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = {
        "entry": str(args.entry),
        "root_envelope_id": None,
        "valid": False,
        "errors": [],
    }
    try:
        if not args.packet and not args.root:
            raise ValueError("--root is required unless --packet is supplied")
        if not args.entry.is_file():
            raise ValueError(f"Missing entry: {args.entry}")
        try:
            packet_path, packet = load_packet(project, args.root or "", args.packet)
        except SystemExit as error:
            raise ValueError(str(error)) from error
        validate_packet(packet)
        if args.root and not selector_matches(packet, args.root):
            raise ValueError(
                f"Root selector {args.root!r} does not match explicit packet {packet_path}"
            )
        packet["root_envelope_id"] = packet_envelope(packet)
        result["root_envelope_id"] = packet["root_envelope_id"]
        text = args.entry.read_text(encoding="utf-8")
        result["errors"] = validate_entry(
            packet, packet_path, text, args.allow_placeholders
        )
        result["valid"] = not result["errors"]
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        json.JSONDecodeError,
    ) as error:
        result["setup_error"] = str(error)
        emit_result(result, args.as_json)
        raise SystemExit(2)

    emit_result(result, args.as_json)
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
