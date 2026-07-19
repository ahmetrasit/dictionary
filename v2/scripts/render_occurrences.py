#!/usr/bin/env python3
"""Render root occurrences by QAC form with word-level attachment evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
MARKER = "<!-- generated-by: v2/scripts/render_occurrences.py schema=1 -->"
FORM_KEY_FIELDS = ("lemma_ar", "surface_ar", "pos", "morph_features")

FORM_HAMZA = str.maketrans(
    {
        "أ": "ء",
        "إ": "ء",
        "آ": "ءا",
        "ؤ": "ء",
        "ئ": "ء",
        "ٱ": "ا",
    }
)
ROOT_HAMZA = str.maketrans(
    {
        "أ": "ء",
        "إ": "ء",
        "آ": "ء",
        "ؤ": "ء",
        "ئ": "ء",
        "ٱ": "ا",
    }
)

INSTANCE_ATTACHMENT_FIELDS = (
    ("dependent_attachment_ids", "dependent"),
    ("head_attachment_ids", "head"),
    ("modifier_attachment_ids", "head"),
    ("prep_attachment_ids", "participant"),
    ("object_attachment_ids", "head"),
    ("subject_attachment_id", "head"),
    ("clausal_attachment_ids", "head"),
)

LABELS = {
    "en": {
        "title": "Quran occurrences",
        "notice": (
            "This is deterministic root-level evidence. Forms and attachments "
            "do not assign an occurrence to a dictionary branch or sense."
        ),
        "packet": "Packet",
        "envelope": "Root envelope",
        "root": "Root",
        "census": "Census",
        "morphemes": "rooted morphemes",
        "words": "rooted words",
        "ayahs": "ayahs",
        "surahs": "surahs",
        "forms": "QAC occurrence forms",
        "joins": "Attachment joins",
        "form_summary": "Occurrence-form summary",
        "form_note": (
            "A form is the exact `(lemma, root surface, POS, morphology)` tuple. "
            "Forms follow first-occurrence order; occurrences within each form "
            "remain in Quran order."
        ),
        "form": "Form",
        "lemma": "Lemma",
        "root_surface": "Root surface",
        "morphology": "Morphology",
        "count": "Count",
        "qac_ref": "QAC ref",
        "word_surface": "Contextual word",
        "source_grammar": "Attachment grammar (source text)",
        "join": "Attachment join",
        "attachments": "Attachments",
        "patterns": "Grouped attachment patterns",
        "patterns_note": (
            "These are mechanical counts over successfully linked occurrence "
            "words. They nominate patterns for later agent review."
        ),
        "relation": "Relation",
        "focus_role": "Focus role",
        "counterpart": "Counterpart",
        "preposition": "Preposition",
        "forms_column": "Forms",
        "refs": "Word refs",
        "unresolved": "Unresolved attachment joins",
        "unresolved_note": (
            "Unresolved rows remain visible and receive no guessed attachments."
        ),
        "reason": "Reason",
        "candidates": "Candidate instances",
        "contexts": "Full Arabic ayah contexts",
        "none": "none",
        "no_rows": "no linked attachment rows",
    },
    "tr": {
        "title": "Kur'an oluşumları",
        "notice": (
            "Bu bölüm deterministik kök düzeyi kanıtıdır. Biçimler ve bağlantılar "
            "hiçbir oluşumu sözlük dalına veya anlama atamaz."
        ),
        "packet": "Paket",
        "envelope": "Kök zarfı",
        "root": "Kök",
        "census": "Sayım",
        "morphemes": "köklü morfem",
        "words": "köklü kelime",
        "ayahs": "ayet",
        "surahs": "sure",
        "forms": "QAC oluşum biçimi",
        "joins": "Bağlantı eşlemeleri",
        "form_summary": "Oluşum biçimi özeti",
        "form_note": (
            "Biçim, tam `(lemma, kök yüzeyi, sözcük türü, morfoloji)` demetidir. "
            "Biçimler ilk oluşum sırasını, her biçimin oluşumları Kur'an sırasını korur."
        ),
        "form": "Biçim",
        "lemma": "Lemma",
        "root_surface": "Kök yüzeyi",
        "morphology": "Morfoloji",
        "count": "Sayı",
        "qac_ref": "QAC konumu",
        "word_surface": "Ayet içindeki kelime",
        "source_grammar": "Bağlantı dilbilgisi (kaynak metin)",
        "join": "Bağlantı eşlemesi",
        "attachments": "Bağlantılar",
        "patterns": "Gruplanmış bağlantı örüntüleri",
        "patterns_note": (
            "Bunlar başarıyla eşlenen oluşum kelimelerinin mekanik sayımlarıdır. "
            "Daha sonraki ajan incelemesi için örüntü adayı sunarlar."
        ),
        "relation": "İlişki",
        "focus_role": "Odağın rolü",
        "counterpart": "Karşı öğe",
        "preposition": "Edat",
        "forms_column": "Biçimler",
        "refs": "Kelime konumları",
        "unresolved": "Çözülemeyen bağlantı eşlemeleri",
        "unresolved_note": (
            "Çözülemeyen satırlar görünür kalır ve bunlara tahminî bağlantı eklenmez."
        ),
        "reason": "Gerekçe",
        "candidates": "Aday oluşumlar",
        "contexts": "Tam Arapça ayet bağlamları",
        "none": "yok",
        "no_rows": "bağlı ilişki satırı yok",
    },
}

POS_LABELS = {
    "en": {"N": "noun", "PN": "proper noun", "V": "verb", "ADJ": "adjective"},
    "tr": {"N": "isim", "PN": "özel isim", "V": "fiil", "ADJ": "sıfat"},
}

FEATURE_LABELS = {
    "en": {
        "M": "masculine",
        "F": "feminine",
        "MS": "masculine singular",
        "FS": "feminine singular",
        "MP": "masculine plural",
        "FP": "feminine plural",
        "INDEF": "indefinite",
        "NOM": "nominative",
        "ACC": "accusative",
        "GEN": "genitive",
        "PERF": "perfect (PERF)",
        "IMPF": "imperfect (IMPF)",
        "IMPV": "imperative (IMPV)",
        "PASS": "passive",
        "ACT": "active",
        "IND": "indicative",
        "SUBJ": "subjunctive",
        "JUS": "jussive",
        "1S": "first person singular",
        "1P": "first person plural",
        "2MS": "second person masculine singular",
        "2FS": "second person feminine singular",
        "2D": "second person dual",
        "2MP": "second person masculine plural",
        "2FP": "second person feminine plural",
        "3MS": "third person masculine singular",
        "3FS": "third person feminine singular",
        "3D": "third person dual",
        "3MP": "third person masculine plural",
        "3FP": "third person feminine plural",
    },
    "tr": {
        "M": "eril",
        "F": "dişil",
        "MS": "eril tekil",
        "FS": "dişil tekil",
        "MP": "eril çoğul",
        "FP": "dişil çoğul",
        "INDEF": "belirsiz",
        "NOM": "merfu",
        "ACC": "mansup",
        "GEN": "mecrur",
        "PERF": "tamamlanmış görünüş (PERF)",
        "IMPF": "tamamlanmamış görünüş (IMPF)",
        "IMPV": "emir (IMPV)",
        "PASS": "edilgen",
        "ACT": "etken",
        "IND": "haber kipi",
        "SUBJ": "mansup muzari",
        "JUS": "meczum muzari",
        "1S": "1. tekil kişi",
        "1P": "1. çoğul kişi",
        "2MS": "2. tekil eril kişi",
        "2FS": "2. tekil dişil kişi",
        "2D": "2. ikil kişi",
        "2MP": "2. çoğul eril kişi",
        "2FP": "2. çoğul dişil kişi",
        "3MS": "3. tekil eril kişi",
        "3FS": "3. tekil dişil kişi",
        "3D": "3. ikil kişi",
        "3MP": "3. çoğul eril kişi",
        "3FP": "3. çoğul dişil kişi",
    },
}

RELATION_LABELS = {
    "en": {
        "adjective": "adjective",
        "adverbial": "adverbial",
        "apposition": "apposition",
        "circumstantial": "circumstantial qualifier",
        "conjoined": "coordination",
        "direct_object": "direct object",
        "idafa": "iḍāfa",
        "particle_complement": "particle complement",
        "predication": "predication",
        "prep_complement": "prepositional complement",
        "subject": "subject",
    },
    "tr": {
        "adjective": "sıfat",
        "adverbial": "zarf",
        "apposition": "bedel/açıklayıcı",
        "circumstantial": "hâl",
        "conjoined": "atıf",
        "direct_object": "doğrudan nesne",
        "idafa": "izafet",
        "particle_complement": "edat tamamlayıcısı",
        "predication": "yüklemleme",
        "prep_complement": "harf-i cer tamamlayıcısı",
        "subject": "özne/fail",
    },
}

ROLE_LABELS = {
    "en": {"head": "head", "dependent": "dependent", "participant": "participant"},
    "tr": {"head": "yönetici", "dependent": "bağımlı", "participant": "katılımcı"},
}

JOIN_LABELS = {
    "en": {
        "exact_word_unit": "exact word-unit",
        "corroborated_root_form": "corroborated root/form",
        "no_attachment_instance": "no attachment instance",
        "unresolved_form_mismatch": "unresolved form mismatch",
        "unresolved_ambiguous": "unresolved ambiguity",
    },
    "tr": {
        "exact_word_unit": "tam kelime kimliği",
        "corroborated_root_form": "kök/biçim doğrulamalı",
        "no_attachment_instance": "bağlantı oluşumu yok",
        "unresolved_form_mismatch": "biçim uyuşmazlığı çözülemedi",
        "unresolved_ambiguous": "belirsizlik çözülemedi",
    },
}

REASON_LABELS = {
    "en": {
        "multiple_exact": "multiple root-matching instances share the exact word-unit ID",
        "ambiguous_form": (
            "multiple QAC words or attachment instances remain form-compatible"
        ),
        "form_mismatch": (
            "root-matching attachment instances lack a unique corroborating form"
        ),
        "no_instance": "no unused root-matching attachment instance exists in the ayah",
    },
    "tr": {
        "multiple_exact": (
            "aynı tam kelime kimliğini paylaşan birden çok kök uyumlu oluşum var"
        ),
        "ambiguous_form": (
            "birden çok QAC kelimesi veya bağlantı oluşumu biçimle uyumlu kalıyor"
        ),
        "form_mismatch": (
            "kök uyumlu bağlantı oluşumlarının tekil bir doğrulayıcı biçimi yok"
        ),
        "no_instance": "ayette kullanılmamış kök uyumlu bağlantı oluşumu yok",
    },
}

STATUS_LABELS = {
    "en": {
        "accepted": "accepted",
        "ambiguous": "ambiguous",
        "rejected": "rejected",
        "review": "review",
        "strongly_licensed": "strongly licensed",
        "syntactically_forced": "syntactically forced",
    },
    "tr": {
        "accepted": "kabul edilmiş",
        "ambiguous": "belirsiz",
        "rejected": "reddedilmiş",
        "review": "inceleme",
        "strongly_licensed": "güçlü biçimde destekli",
        "syntactically_forced": "sözdizimsel olarak zorunlu",
    },
}

CONFIDENCE_LABELS = {
    "en": {
        "high": "high confidence",
        "medium": "medium confidence",
        "low": "low confidence",
    },
    "tr": {
        "high": "yüksek güven",
        "medium": "orta güven",
        "low": "düşük güven",
    },
}


def cell(value: object) -> str:
    return " ".join(str(value or "").split()).replace("|", "\\|")


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,]", value or "") if item.strip()]


def normalize_arabic(value: str, *, drop_article: bool = False) -> str:
    text = unicodedata.normalize(
        "NFKD", (value or "").replace("\u0670", "ا").translate(FORM_HAMZA)
    )
    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
        and not character.isspace()
        and character != "ـ"
    )
    if drop_article and text.startswith("ال"):
        text = text[2:]
    return text


def normalize_root(value: str) -> str:
    text = unicodedata.normalize("NFKD", (value or "").translate(ROOT_HAMZA))
    return "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
        and not character.isspace()
        and character != "ـ"
    )


def normalize_pattern_surface(value: str) -> str:
    """Return a case-insensitive display key without loosening occurrence joins."""
    normalized = normalize_arabic(value, drop_article=True)
    if "\u064b" in (value or "") and normalized.endswith("ا"):
        normalized = normalized[:-1]
    return normalized


def selector_matches(packet: dict, selector: str) -> bool:
    root_ids = {row.get("root_id", "") for row in packet.get("v4_roots", [])}
    envelope = packet.get("root_envelope_id") or "--".join(
        row.get("root_id", "") for row in packet.get("v4_roots", [])
    )
    selector_form = normalize_arabic(selector, drop_article=True)
    occurrence_forms = {
        normalize_arabic(row.get(field, ""), drop_article=True)
        for row in packet.get("qac", {}).get("occurrences", [])
        for field in ("lemma_ar", "surface_ar", "stem_ar")
    }
    occurrence_forms.discard("")
    return (
        selector == envelope
        or selector in root_ids
        or normalize_root(selector) == normalize_root(packet.get("root_join_key", ""))
        or selector_form in occurrence_forms
    )


def load_packet(project: Path, selector: str, explicit_path: Path | None) -> tuple[Path, dict]:
    if explicit_path:
        path = explicit_path.resolve()
        if not path.is_file():
            raise ValueError(f"Missing packet: {path}")
        packet = json.loads(path.read_text(encoding="utf-8"))
        if not selector_matches(packet, selector):
            raise ValueError(f"Root selector {selector!r} does not match packet {path}")
        return path, packet

    packet_dir = project / "data/output/root_packets"
    for path in sorted(packet_dir.glob("*.json")):
        packet = json.loads(path.read_text(encoding="utf-8"))
        if selector_matches(packet, selector):
            return path, packet
    raise ValueError(
        f"No root packet found for {selector!r}. "
        "Build its root packet first with scripts/root_packet.py "
        "<Arabic-root-or-root_id>."
    )


def validate_packet(packet: dict) -> None:
    if not isinstance(packet, dict):
        raise ValueError("Packet must be a JSON object")
    for key in ("root_envelope_id", "root_join_key", "root_norm"):
        if not isinstance(packet.get(key), str) or not packet[key]:
            raise ValueError(f"Packet field {key!r} must be a nonempty string")
    qac = packet.get("qac")
    attachments = packet.get("attachments")
    if not isinstance(qac, dict) or not isinstance(qac.get("occurrences"), list):
        raise ValueError("Packet must contain qac.occurrences")
    if not isinstance(qac.get("ayah_contexts"), list):
        raise ValueError("Packet must contain qac.ayah_contexts")
    if not isinstance(attachments, dict):
        raise ValueError("Packet must contain attachments")
    for key in ("noun_instances", "verb_instances", "attachments"):
        if not isinstance(attachments.get(key), list):
            raise ValueError(f"Packet attachments.{key} must be a list")

    refs = [row.get("qac_ref") for row in qac["occurrences"]]
    if any(not ref for ref in refs):
        raise ValueError("Packet contains an empty QAC ref")
    if len(refs) != len(set(refs)):
        raise ValueError("Packet contains duplicate QAC refs")

    word_refs = {
        word.get("qac_word_ref")
        for ayah in qac["ayah_contexts"]
        for word in ayah.get("words", [])
    }
    missing = sorted(
        {row.get("qac_word_ref") for row in qac["occurrences"]} - word_refs
    )
    if missing:
        raise ValueError(f"QAC occurrence words are absent from ayah contexts: {missing[:5]}")


def occurrence_unit_id(occurrence: dict) -> str:
    return f"q:{occurrence['surah']}:{occurrence['ayah']}:{occurrence['word_index']}"


def occurrence_form_key(occurrence: dict) -> tuple[str, str, str, str]:
    return tuple(str(occurrence.get(field, "")) for field in FORM_KEY_FIELDS)


def group_forms(occurrences: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, str], list[dict]] = {}
    for occurrence in occurrences:
        grouped.setdefault(occurrence_form_key(occurrence), []).append(occurrence)
    return [
        {"id": f"F{ordinal:03d}", "key": key, "occurrences": rows}
        for ordinal, (key, rows) in enumerate(grouped.items(), start=1)
    ]


def qac_word_forms(rows: list[dict]) -> set[str]:
    values = set()
    for row in rows:
        for field in ("surface_ar", "stem_ar", "lemma_ar"):
            normalized = normalize_arabic(row.get(field, ""), drop_article=True)
            if normalized:
                values.add(normalized)
    return values


def instance_forms(instance: dict) -> set[str]:
    values = set()
    for field in ("surface", "stem"):
        normalized = normalize_arabic(instance.get(field, ""), drop_article=True)
        if normalized:
            values.add(normalized)
    return values


def roots_match(qac_rows: list[dict], instance: dict) -> bool:
    roots = {normalize_root(row.get("root_ar", "")) for row in qac_rows}
    roots.discard("")
    return bool(roots) and normalize_root(instance.get("root_norm", "")) in roots


def instance_identity(instance: dict) -> str:
    return str(instance.get("unit_id") or instance.get("word_unit_id") or id(instance))


def link_occurrences(packet: dict) -> dict[str, dict]:
    """Join QAC word units to attachment instances without ambiguous guessing."""
    qac_by_ayah: dict[tuple[str, str], dict[str, list[dict]]] = {}
    for occurrence in packet["qac"]["occurrences"]:
        ayah_key = (str(occurrence["surah"]), str(occurrence["ayah"]))
        unit = occurrence_unit_id(occurrence)
        qac_by_ayah.setdefault(ayah_key, {}).setdefault(unit, []).append(occurrence)

    instances_by_ayah: dict[tuple[str, str], list[dict]] = {}
    for instance in (
        packet["attachments"].get("verb_instances", [])
        + packet["attachments"].get("noun_instances", [])
    ):
        key = (str(instance.get("sura", "")), str(instance.get("ayah", "")))
        instances_by_ayah.setdefault(key, []).append(instance)

    links: dict[str, dict] = {}
    for ayah_key, qac_units in qac_by_ayah.items():
        candidates = instances_by_ayah.get(ayah_key, [])
        used: set[str] = set()

        for qac_unit, rows in qac_units.items():
            exact = [
                candidate
                for candidate in candidates
                if candidate.get("word_unit_id") == qac_unit
                and roots_match(rows, candidate)
            ]
            if len(exact) == 1:
                links[qac_unit] = {"method": "exact_word_unit", "instances": exact}
                used.add(instance_identity(exact[0]))
            elif len(exact) > 1:
                links[qac_unit] = {
                    "method": "unresolved_ambiguous",
                    "reason": "multiple_exact",
                    "instances": exact,
                }

        pending = [unit for unit in qac_units if unit not in links]
        compatible: dict[str, list[dict]] = {}
        for qac_unit in pending:
            rows = qac_units[qac_unit]
            forms = qac_word_forms(rows)
            compatible[qac_unit] = [
                candidate
                for candidate in candidates
                if instance_identity(candidate) not in used
                and roots_match(rows, candidate)
                and bool(forms & instance_forms(candidate))
            ]

        while True:
            assignments: list[tuple[str, dict]] = []
            candidate_owners = Counter(
                instance_identity(candidate)
                for unit in pending
                for candidate in compatible[unit]
            )
            for unit in pending:
                options = compatible[unit]
                if len(options) == 1 and candidate_owners[instance_identity(options[0])] == 1:
                    assignments.append((unit, options[0]))
            if not assignments:
                break
            assigned_units = set()
            for unit, candidate in assignments:
                links[unit] = {
                    "method": "corroborated_root_form",
                    "instances": [candidate],
                }
                used.add(instance_identity(candidate))
                assigned_units.add(unit)
            pending = [unit for unit in pending if unit not in assigned_units]
            for unit in pending:
                compatible[unit] = [
                    candidate
                    for candidate in compatible[unit]
                    if instance_identity(candidate) not in used
                ]

        for qac_unit in pending:
            rows = qac_units[qac_unit]
            root_candidates = [
                candidate
                for candidate in candidates
                if instance_identity(candidate) not in used and roots_match(rows, candidate)
            ]
            options = compatible[qac_unit]
            if options:
                links[qac_unit] = {
                    "method": "unresolved_ambiguous",
                    "reason": "ambiguous_form",
                    "instances": options,
                }
            elif root_candidates:
                links[qac_unit] = {
                    "method": "unresolved_form_mismatch",
                    "reason": "form_mismatch",
                    "instances": root_candidates,
                }
            else:
                links[qac_unit] = {
                    "method": "no_attachment_instance",
                    "reason": "no_instance",
                    "instances": [],
                }
    return links


def attachment_rows_by_id(packet: dict) -> dict[str, dict]:
    return {
        row.get("unit_id", ""): row
        for row in packet["attachments"].get("attachments", [])
        if row.get("unit_id")
    }


def instance_attachment_pairs(instance: dict) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for field, role in INSTANCE_ATTACHMENT_FIELDS:
        for attachment_id in split_ids(instance.get(field, "")):
            if attachment_id not in seen:
                result.append((attachment_id, role))
                seen.add(attachment_id)
    return result


def attachment_detail(row: dict, instance: dict, role_hint: str) -> dict:
    instance_unit = instance.get("word_unit_id", "")
    if instance_unit and row.get("head_unit_id") == instance_unit:
        focus_role = "head"
    elif instance_unit and row.get("dep_unit_id") == instance_unit:
        focus_role = "dependent"
    else:
        focus_root = normalize_root(instance.get("root_norm", ""))
        dep_matches = normalize_root(row.get("dep_root_norm", "")) == focus_root
        head_matches = normalize_root(row.get("head_root_norm", "")) == focus_root
        if head_matches and not dep_matches:
            focus_role = "head"
        elif dep_matches and not head_matches:
            focus_role = "dependent"
        else:
            focus_role = role_hint

    if focus_role == "head":
        other_prefix = "dep"
    elif focus_role == "dependent":
        other_prefix = "head"
    else:
        other_prefix = "dep"
    return {
        "attachment_id": row.get("unit_id", ""),
        "relation": row.get("relation", ""),
        "focus_role": focus_role,
        "other_unit_id": row.get(f"{other_prefix}_unit_id", ""),
        "other_surface": row.get(f"{other_prefix}_surface", ""),
        "other_root": row.get(f"{other_prefix}_root_norm", ""),
        "other_form_tag": row.get(f"{other_prefix}_form_tag", ""),
        "prep_base": row.get("prep_base", ""),
        "status": row.get("status", ""),
        "confidence": row.get("confidence", ""),
        "evidence": row.get("evidence", ""),
    }


def linked_attachment_details(link: dict, rows_by_id: dict[str, dict]) -> list[dict]:
    if link["method"].startswith("unresolved") or link["method"] == "no_attachment_instance":
        return []
    result: list[dict] = []
    seen: set[str] = set()
    for instance in link.get("instances", []):
        for attachment_id, role_hint in instance_attachment_pairs(instance):
            if attachment_id in seen:
                continue
            row = rows_by_id.get(attachment_id)
            if row:
                result.append(attachment_detail(row, instance, role_hint))
                seen.add(attachment_id)
    return result


def linked_source_grammar(link: dict) -> str:
    if (
        link["method"].startswith("unresolved")
        or link["method"] == "no_attachment_instance"
    ):
        return ""
    values = []
    for instance in link.get("instances", []):
        grammar = cell(instance.get("grammar", ""))
        if grammar and grammar not in values:
            values.append(grammar)
    return "; ".join(values)


def morphology_label(occurrence: dict, language: str) -> str:
    labels = FEATURE_LABELS[language]
    parts = [POS_LABELS[language].get(occurrence.get("pos", ""), occurrence.get("pos", ""))]
    ignored_prefixes = ("POS:", "LEM:", "ROOT:", "MOOD:")
    ignored_tokens = {"", "STEM"}
    for token in str(occurrence.get("morph_features", "")).split("|"):
        if token in ignored_tokens or token.startswith(ignored_prefixes):
            continue
        if token.startswith("(") and token.endswith(")"):
            continue
        rendered = labels.get(token, token)
        if rendered and rendered not in parts:
            parts.append(rendered)
    measure = occurrence.get("measure", "")
    if measure:
        measure_label = f"Form {measure}" if language == "en" else f"{measure}. bâb/form"
        if measure_label not in parts:
            parts.append(measure_label)
    return "; ".join(parts)


def join_label(link: dict, language: str) -> str:
    label = JOIN_LABELS[language].get(link["method"], link["method"])
    if link.get("reason"):
        reason = REASON_LABELS[language].get(link["reason"], link["reason"])
        return f"{label}: {reason}"
    return label


def attachment_label(detail: dict, language: str) -> str:
    relation = RELATION_LABELS[language].get(detail["relation"], detail["relation"])
    role = ROLE_LABELS[language].get(detail["focus_role"], detail["focus_role"])
    counterpart = detail["other_surface"] or detail["other_unit_id"] or "?"
    if detail["other_root"]:
        counterpart += f" ({detail['other_root']})"
    prep = f"; prep={detail['prep_base']}" if detail["prep_base"] else ""
    status = STATUS_LABELS[language].get(detail["status"], detail["status"])
    confidence = CONFIDENCE_LABELS[language].get(
        detail["confidence"], detail["confidence"]
    )
    audit = ", ".join(value for value in (status, confidence) if value)
    audit = f"; {audit}" if audit else ""
    return (
        f"{relation}; {role} → {counterpart}{prep}{audit}; "
        f"`{detail['attachment_id']}`"
    )


def word_surface_map(packet: dict) -> dict[str, str]:
    return {
        word["qac_word_ref"]: word["surface_ar"]
        for ayah in packet["qac"]["ayah_contexts"]
        for word in ayah.get("words", [])
    }


def display_path(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT)
    except ValueError:
        return path


def group_attachment_patterns(
    qac_units: list[str],
    links: dict[str, dict],
    rows_by_id: dict[str, dict],
    form_by_unit: dict[str, set[str]],
) -> list[dict]:
    patterns: dict[tuple, dict] = {}
    for unit in qac_units:
        link = links[unit]
        for detail in linked_attachment_details(link, rows_by_id):
            counterpart_key = (
                normalize_pattern_surface(detail["other_surface"])
                or detail["other_form_tag"]
                or detail["other_unit_id"]
            )
            key = (
                detail["relation"],
                detail["focus_role"],
                normalize_root(detail["other_root"]),
                counterpart_key,
                normalize_arabic(detail["prep_base"]),
            )
            pattern = patterns.setdefault(
                key,
                {
                    "detail": detail,
                    "counterpart_key": counterpart_key,
                    "count": 0,
                    "forms": set(),
                    "refs": [],
                    "statuses": set(),
                    "confidences": set(),
                },
            )
            pattern["count"] += 1
            pattern["forms"].update(form_by_unit[unit])
            pattern["refs"].append(unit.removeprefix("q:"))
            if detail["status"]:
                pattern["statuses"].add(detail["status"])
            if detail["confidence"]:
                pattern["confidences"].add(detail["confidence"])
    return sorted(
        patterns.values(),
        key=lambda item: (
            -item["count"],
            item["detail"]["relation"],
            item["detail"]["other_root"],
        ),
    )


def render_markdown(packet: dict, packet_path: Path, language: str) -> str:
    text = LABELS[language]
    occurrences = packet["qac"]["occurrences"]
    forms = group_forms(occurrences)
    links = link_occurrences(packet)
    rows_by_id = attachment_rows_by_id(packet)
    surfaces = word_surface_map(packet)
    form_by_unit: dict[str, set[str]] = {}
    for form in forms:
        for occurrence in form["occurrences"]:
            form_by_unit.setdefault(occurrence_unit_id(occurrence), set()).add(form["id"])

    qac_units = list(dict.fromkeys(occurrence_unit_id(row) for row in occurrences))
    join_counts = Counter(links[unit]["method"] for unit in qac_units)
    join_summary = "; ".join(
        f"{JOIN_LABELS[language].get(method, method)}={count}"
        for method, count in sorted(join_counts.items())
    ) or text["none"]
    summary = packet["qac"].get("summary", {})
    lines = [
        MARKER,
        f"# {packet['root_norm']}: {text['title']}",
        "",
        f"> {text['notice']}",
        "",
        f"- {text['packet']}: `{display_path(packet_path)}`",
        f"- {text['envelope']}: `{packet['root_envelope_id']}`",
        f"- {text['root']}: `{packet['root_norm']}`",
        "",
        f"## {text['census']}",
        "",
        f"- {summary.get('morpheme_count', len(occurrences))} {text['morphemes']}",
        f"- {summary.get('word_count', len(qac_units))} {text['words']}",
        f"- {summary.get('ayah_count', len({(r['surah'], r['ayah']) for r in occurrences}))} {text['ayahs']}",
        f"- {summary.get('surah_count', len({r['surah'] for r in occurrences}))} {text['surahs']}",
        f"- {len(forms)} {text['forms']}",
        f"- {text['joins']}: {join_summary}",
        "",
        f"## {text['form_summary']}",
        "",
        text["form_note"],
        "",
        f"| {text['form']} | {text['lemma']} | {text['root_surface']} | {text['morphology']} | {text['count']} |",
        "|---|---|---|---|---:|",
    ]
    for form in forms:
        lemma, root_surface, _pos, _features = form["key"]
        lines.append(
            f"| `{form['id']}` | `{cell(lemma)}` | `{cell(root_surface)}` | "
            f"{cell(morphology_label(form['occurrences'][0], language))} | "
            f"{len(form['occurrences'])} |"
        )

    for form in forms:
        _lemma, root_surface, _pos, _features = form["key"]
        lines += [
            "",
            f"### {form['id']}: `{cell(root_surface)}`",
            "",
            f"| {text['qac_ref']} | {text['word_surface']} | {text['morphology']} | {text['source_grammar']} | {text['join']} | {text['attachments']} |",
            "|---|---|---|---|---|---|",
        ]
        for occurrence in form["occurrences"]:
            unit = occurrence_unit_id(occurrence)
            link = links[unit]
            details = linked_attachment_details(link, rows_by_id)
            rendered_details = "<br>".join(
                cell(attachment_label(detail, language)) for detail in details
            ) or text["no_rows"]
            lines.append(
                f"| `{occurrence['qac_ref']}` | "
                f"`{cell(surfaces[occurrence['qac_word_ref']])}` | "
                f"{cell(morphology_label(occurrence, language))} | "
                f"{cell(linked_source_grammar(link) or text['none'])} | "
                f"{cell(join_label(link, language))} | {rendered_details} |"
            )

    patterns = group_attachment_patterns(qac_units, links, rows_by_id, form_by_unit)

    lines += [
        "",
        f"## {text['patterns']}",
        "",
        text["patterns_note"],
        "",
        f"| {text['relation']} | {text['focus_role']} | {text['counterpart']} | {text['preposition']} | {text['count']} | {text['forms_column']} | {text['refs']} |",
        "|---|---|---|---|---:|---|---|",
    ]
    for pattern in patterns:
        detail = pattern["detail"]
        relation = RELATION_LABELS[language].get(detail["relation"], detail["relation"])
        role = ROLE_LABELS[language].get(detail["focus_role"], detail["focus_role"])
        counterpart = pattern["counterpart_key"] or detail["other_unit_id"] or "?"
        if detail["other_root"]:
            counterpart += f" ({detail['other_root']})"
        lines.append(
            f"| {cell(relation)} | {cell(role)} | {cell(counterpart)} | "
            f"{cell(detail['prep_base'] or text['none'])} | {pattern['count']} | "
            f"{cell(', '.join(sorted(pattern['forms'])))} | "
            f"{cell(', '.join(pattern['refs']))} |"
        )

    unresolved_units = [
        unit
        for unit in qac_units
        if links[unit]["method"].startswith("unresolved")
        or links[unit]["method"] == "no_attachment_instance"
    ]
    lines += [
        "",
        f"## {text['unresolved']}",
        "",
        text["unresolved_note"],
        "",
        f"| {text['refs']} | {text['join']} | {text['reason']} | {text['candidates']} |",
        "|---|---|---|---|",
    ]
    if unresolved_units:
        for unit in unresolved_units:
            link = links[unit]
            candidates = ", ".join(
                str(instance.get("word_unit_id") or instance.get("unit_id", ""))
                for instance in link.get("instances", [])
            ) or text["none"]
            lines.append(
                f"| `{unit.removeprefix('q:')}` | "
                f"{cell(JOIN_LABELS[language].get(link['method'], link['method']))} | "
                f"{cell(REASON_LABELS[language].get(link.get('reason', ''), link.get('reason', '')))} | "
                f"{cell(candidates)} |"
            )
    else:
        lines.append(f"| {text['none']} | {text['none']} | {text['none']} | {text['none']} |")

    lines += ["", f"## {text['contexts']}", ""]
    for ayah in packet["qac"]["ayah_contexts"]:
        lines += [f"### {ayah['ref']}", "", ayah["surface_ar"], ""]
    return "\n".join(lines).rstrip() + "\n"


def write_generated(path: Path, content: str, *, check: bool) -> None:
    if check:
        if not path.is_file():
            raise ValueError(f"Missing generated output: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Stale generated output: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        first_line = path.read_text(encoding="utf-8").splitlines()[:1]
        if first_line != [MARKER]:
            raise ValueError(f"Refusing to replace unmarked file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        help="V4 root ID, root-envelope ID, Arabic root, or Arabic word selector",
    )
    parser.add_argument("--packet", type=Path, help="Explicit existing root packet")
    parser.add_argument("--language", choices=("en", "tr"), default="tr")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        packet_path, packet = load_packet(PROJECT, args.root, args.packet)
        validate_packet(packet)
        output = args.output or (
            PROJECT
            / "v2/output/occurrences"
            / f"{packet['root_envelope_id']}.{args.language}.md"
        )
        content = render_markdown(packet, packet_path, args.language)
        write_generated(output, content, check=args.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
