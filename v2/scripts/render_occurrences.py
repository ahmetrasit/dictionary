#!/usr/bin/env python3
"""Render root occurrences by QAC form with word-level attachment evidence."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from v2.scripts.output_protection import protect_pinned_entries
MARKER = "<!-- generated-by: v2/scripts/render_occurrences.py schema=1 -->"
FORM_KEY_FIELDS = ("lemma_ar", "surface_ar", "pos", "morph_features")
ROOT_ID_RE = re.compile(r"root_[0-9]{6}")
BRANCH_ID_RE = re.compile(r"B[0-9]{3}")
ENVELOPE_RE = re.compile(r"root_[0-9]{6}(?:--root_[0-9]{6})*")

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
            "words. They nominate patterns for downstream analysis."
        ),
        "relation": "Relation",
        "focus_role": "Focus role",
        "counterpart": "Counterpart",
        "preposition": "Preposition",
        "forms_column": "Forms",
        "refs": "Word refs",
        "status": "Status",
        "confidence": "Confidence",
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
            "Sonraki analiz katmanı için örüntü adayı sunarlar."
        ),
        "relation": "İlişki",
        "focus_role": "Odağın rolü",
        "counterpart": "Karşı öğe",
        "preposition": "Edat",
        "forms_column": "Biçimler",
        "refs": "Kelime konumları",
        "status": "Durum",
        "confidence": "Güven",
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
        "qac_crosswalk": "QAC crosswalk",
        "exact_word_unit": "exact word-unit",
        "corroborated_root_form": "corroborated root/form",
        "no_attachment_instance": "no attachment instance",
        "unresolved_form_mismatch": "unresolved form mismatch",
        "unresolved_ambiguous": "unresolved ambiguity",
    },
    "tr": {
        "qac_crosswalk": "QAC çapraz eşlemesi",
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
    return [
        item.strip()
        for item in re.split(r"[;,]", str(value or ""))
        if item.strip()
    ]


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
    envelope = packet["root_envelope_id"]
    if ENVELOPE_RE.fullmatch(envelope) is None:
        raise ValueError(f"Invalid root envelope ID: {envelope!r}")
    roots = packet.get("v4_roots", [])
    if roots:
        root_ids = [row.get("root_id", "") for row in roots]
        if any(ROOT_ID_RE.fullmatch(root_id) is None for root_id in root_ids):
            raise ValueError("Packet contains an invalid root ID")
        if len(root_ids) != len(set(root_ids)):
            raise ValueError("Packet contains duplicate root IDs")
        if envelope != "--".join(root_ids):
            raise ValueError("Packet root envelope does not match its root roster")
    branch_keys = []
    for branch in packet.get("branches", []):
        root_id = branch.get("root_id", "")
        branch_id = branch.get("branch_id", "")
        if ROOT_ID_RE.fullmatch(root_id) is None or BRANCH_ID_RE.fullmatch(branch_id) is None:
            raise ValueError(f"Packet contains an invalid branch ID: {root_id}/{branch_id}")
        branch_keys.append((root_id, branch_id))
    if len(branch_keys) != len(set(branch_keys)):
        raise ValueError("Packet contains duplicate branch IDs")
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

    occurrence_order = []
    for row in qac["occurrences"]:
        try:
            position = tuple(
                int(row[field])
                for field in ("surah", "ayah", "word_index", "morpheme_index")
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Packet contains an invalid QAC occurrence position") from error
        expected_ref = ":".join(str(value) for value in position)
        if row.get("qac_ref") != expected_ref:
            raise ValueError(
                f"QAC ref {row.get('qac_ref')!r} does not match occurrence position "
                f"{expected_ref!r}"
            )
        if row.get("qac_word_ref") != ":".join(str(value) for value in position[:3]):
            raise ValueError(f"QAC word ref does not match occurrence {expected_ref}")
        occurrence_order.append(position)
    if occurrence_order != sorted(occurrence_order):
        raise ValueError("QAC occurrences are not in Quran order")

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

    context_order = []
    context_word_refs = []
    for ayah in qac["ayah_contexts"]:
        try:
            position = (int(ayah["surah"]), int(ayah["ayah"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Packet contains an invalid ayah context position") from error
        if ayah.get("ref") != f"{position[0]}:{position[1]}":
            raise ValueError(f"Ayah context ref does not match position: {ayah.get('ref')!r}")
        context_order.append(position)
        context_word_refs.extend(word.get("qac_word_ref") for word in ayah.get("words", []))
    if context_order != sorted(context_order) or len(context_order) != len(set(context_order)):
        raise ValueError("Ayah contexts are duplicated or not in Quran order")
    if any(not ref for ref in context_word_refs) or len(context_word_refs) != len(
        set(context_word_refs)
    ):
        raise ValueError("Ayah contexts contain empty or duplicate QAC word refs")

    expected_summary = {
        "morpheme_count": len(qac["occurrences"]),
        "word_count": len({row["qac_word_ref"] for row in qac["occurrences"]}),
        "ayah_count": len(
            {(int(row["surah"]), int(row["ayah"])) for row in qac["occurrences"]}
        ),
        "surah_count": len({int(row["surah"]) for row in qac["occurrences"]}),
    }
    summary = qac.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("Packet must contain qac.summary")
    for field, expected in expected_summary.items():
        if summary.get(field) != expected:
            raise ValueError(
                f"QAC summary {field} is {summary.get(field)!r}; expected {expected}"
            )

    attachment_rows = attachments["attachments"]
    attachment_ids = [row.get("unit_id", "") for row in attachment_rows]
    if any(not unit_id for unit_id in attachment_ids):
        raise ValueError("Packet contains an attachment row without a unit ID")
    if len(attachment_ids) != len(set(attachment_ids)):
        raise ValueError("Packet contains duplicate attachment unit IDs")
    instance_ids = []
    referenced_attachment_ids = set()
    for instance in attachments["noun_instances"] + attachments["verb_instances"]:
        identity = instance.get("unit_id", "")
        if not identity:
            raise ValueError("Packet contains an attachment instance without a unit ID")
        instance_ids.append(identity)
        grammar = " ".join(str(instance.get("grammar", "")).split())
        if local_source_grammar(grammar) != grammar:
            raise ValueError(
                f"Attachment instance {identity} contains a corpus-wide count claim"
            )
        for field, _role in INSTANCE_ATTACHMENT_FIELDS:
            referenced_attachment_ids.update(split_ids(instance.get(field, "")))
    if len(instance_ids) != len(set(instance_ids)):
        raise ValueError("Packet contains duplicate attachment instance IDs")
    dangling = sorted(referenced_attachment_ids - set(attachment_ids))
    if dangling:
        raise ValueError(f"Attachment instances reference missing rows: {dangling[:5]}")


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
        contextual = normalize_arabic(row.get("_context_surface", ""), drop_article=True)
        if contextual:
            values.add(contextual)
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


def attachment_pos_compatible(qac_rows: list[dict], instance: dict) -> bool:
    qac_pos = {str(row.get("pos", "")) for row in qac_rows}
    tag = str(instance.get("form_tag", ""))
    if "V" in qac_pos:
        return tag in {"PV", "IMPV"} or tag.startswith("VERB")
    return tag not in {"PV", "IMPV"} and not tag.startswith("VERB")


def alignment_quality(qac_rows: list[dict], instance: dict) -> int | None:
    """Score a lexical match without treating source word numbers as identities."""
    if not roots_match(qac_rows, instance):
        return None
    qac_forms = qac_word_forms(qac_rows)
    attachment_forms = instance_forms(instance)
    qac_span = tuple(qac_rows[0].get("_qac_char_span", ()))
    span_match = any(
        qac_span
        and start < qac_span[1]
        and end > qac_span[0]
        for start, end in instance.get("_qac_char_spans", [])
    )
    if qac_forms.intersection(attachment_forms):
        base = 500 if span_match else 300
        return base if attachment_pos_compatible(qac_rows, instance) else base - 100
    if span_match:
        return 400 if attachment_pos_compatible(qac_rows, instance) else 300
    similarity = max(
        (
            difflib.SequenceMatcher(None, qac_form, attachment_form).ratio()
            for qac_form in qac_forms
            for attachment_form in attachment_forms
        ),
        default=0.0,
    )
    if similarity < 0.55:
        return None
    return int(similarity * 100) + (
        100 if attachment_pos_compatible(qac_rows, instance) else 0
    )


def ordered_alignment(
    qac_units: list[tuple[str, list[dict]]], instances: list[dict]
) -> tuple[tuple[tuple[int, int], ...], bool]:
    """Return the best monotonic lexical alignment and whether it is ambiguous."""
    qualities = [
        [alignment_quality(rows, instance) for instance in instances]
        for _unit, rows in qac_units
    ]

    @lru_cache(maxsize=None)
    def solve(i: int, j: int) -> tuple[tuple[int, int], tuple[tuple[tuple[int, int], ...], ...]]:
        if i == len(qac_units) or j == len(instances):
            return (0, 0), ((),)
        options = [solve(i + 1, j), solve(i, j + 1)]
        quality = qualities[i][j]
        if quality is not None:
            score, paths = solve(i + 1, j + 1)
            options.append(
                (
                    (score[0] + 1, score[1] + quality),
                    tuple((((i, j),) + path) for path in paths),
                )
            )
        best_score = max(score for score, _paths in options)
        unique_paths: list[tuple[tuple[int, int], ...]] = []
        for score, paths in options:
            if score != best_score:
                continue
            for path in paths:
                if path not in unique_paths:
                    unique_paths.append(path)
                if len(unique_paths) == 2:
                    return best_score, tuple(unique_paths)
        return best_score, tuple(unique_paths)

    _score, paths = solve(0, 0)
    return paths[0], len(paths) > 1


def build_attachment_crosswalk(packet: dict) -> dict:
    """Build a deterministic attachment-to-QAC map with QAC as canonical identity."""
    ayah_text: dict[tuple[str, str], str] = {}
    word_metadata: dict[str, dict] = {}
    for ayah in packet["qac"]["ayah_contexts"]:
        ayah_key = (str(ayah["surah"]), str(ayah["ayah"]))
        cursor = 0
        pieces = []
        for word in ayah.get("words", []):
            normalized = normalize_arabic(word.get("surface_ar", ""))
            start = cursor
            cursor += len(normalized)
            pieces.append(normalized)
            word_metadata[word["qac_word_ref"]] = {
                "surface_ar": word.get("surface_ar", ""),
                "char_span": (start, cursor),
            }
        ayah_text[ayah_key] = "".join(pieces)

    qac_by_ayah: dict[tuple[str, str], dict[str, list[dict]]] = {}
    for occurrence in packet["qac"]["occurrences"]:
        ayah_key = (str(occurrence["surah"]), str(occurrence["ayah"]))
        unit = occurrence_unit_id(occurrence)
        enriched = dict(occurrence)
        metadata = word_metadata.get(occurrence["qac_word_ref"], {})
        enriched["_context_surface"] = metadata.get("surface_ar", "")
        enriched["_qac_char_span"] = metadata.get("char_span", ())
        qac_by_ayah.setdefault(ayah_key, {}).setdefault(unit, []).append(enriched)

    instances_by_ayah: dict[tuple[str, str], list[dict]] = {}
    for instance in (
        packet["attachments"].get("verb_instances", [])
        + packet["attachments"].get("noun_instances", [])
    ):
        key = (str(instance.get("sura", "")), str(instance.get("ayah", "")))
        enriched = dict(instance)
        text = ayah_text.get(key, "")
        spans = set()
        for form in instance_forms(instance):
            start = text.find(form)
            while start >= 0:
                spans.add((start, start + len(form)))
                start = text.find(form, start + 1)
        enriched["_qac_char_spans"] = sorted(spans)
        instances_by_ayah.setdefault(key, []).append(enriched)

    rows: list[dict] = []
    for ayah_key, qac_units in qac_by_ayah.items():
        ordered_qac = list(qac_units.items())
        source_candidates = instances_by_ayah.get(ayah_key, [])
        candidates = [
            row
            for _index, row in sorted(
                enumerate(source_candidates),
                key=lambda item: (
                    int(item[1].get("wid"))
                    if str(item[1].get("wid", "")).isdigit()
                    else item[0],
                    item[0],
                ),
            )
        ]
        pairs, ambiguous = ordered_alignment(ordered_qac, candidates)
        paired_qac = {qac_index for qac_index, _instance_index in pairs}
        for qac_index, instance_index in pairs:
            qac_unit, qac_rows = ordered_qac[qac_index]
            instance = candidates[instance_index]
            quality = alignment_quality(qac_rows, instance)
            qac_span = list(qac_rows[0].get("_qac_char_span", ()))
            attachment_spans = [
                list(span)
                for span in instance.get("_qac_char_spans", [])
                if qac_span and span[0] < qac_span[1] and span[1] > qac_span[0]
            ]
            compatible_ids = [
                instance_identity(candidate)
                for candidate in candidates
                if alignment_quality(qac_rows, candidate) is not None
            ]
            rows.append(
                {
                    "qac_word_ref": qac_unit.removeprefix("q:"),
                    "qac_unit_id": qac_unit,
                    "attachment_unit_id": instance_identity(instance),
                    "attachment_word_unit_id": str(instance.get("word_unit_id", "")),
                    "status": "ambiguous" if ambiguous else "aligned",
                    "method": (
                        "qac_character_span_root_form_monotonic"
                        if attachment_spans
                        else "root_form_monotonic"
                    ),
                    "confidence": "medium" if ambiguous or (quality or 0) < 400 else "high",
                    "qac_char_span": qac_span,
                    "attachment_char_spans": attachment_spans,
                    **(
                        {"candidate_attachment_unit_ids": compatible_ids}
                        if ambiguous
                        else {}
                    ),
                }
            )
        for qac_index, (qac_unit, qac_rows) in enumerate(ordered_qac):
            if qac_index in paired_qac:
                continue
            root_candidates = [
                instance_identity(instance)
                for instance in candidates
                if roots_match(qac_rows, instance)
            ]
            rows.append(
                {
                    "qac_word_ref": qac_unit.removeprefix("q:"),
                    "qac_unit_id": qac_unit,
                    "attachment_unit_id": "",
                    "attachment_word_unit_id": "",
                    "status": "unmatched",
                    "method": "no_compatible_form",
                    "confidence": "high",
                    "qac_char_span": list(qac_rows[0].get("_qac_char_span", ())),
                    "attachment_char_spans": [],
                    "candidate_attachment_unit_ids": root_candidates,
                }
            )
    rows.sort(key=lambda row: tuple(int(value) for value in row["qac_word_ref"].split(":")))
    return {
        "format": 1,
        "generated_by": "v2/scripts/render_occurrences.py",
        "canonical_identity": "qac_word_ref",
        "rows": rows,
    }


def validate_attachment_crosswalk(packet: dict, crosswalk: dict) -> None:
    if crosswalk.get("canonical_identity") != "qac_word_ref":
        raise ValueError("Attachment crosswalk must use qac_word_ref as canonical identity")
    expected = list(
        dict.fromkeys(occurrence_unit_id(row) for row in packet["qac"]["occurrences"])
    )
    rows = crosswalk.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Attachment crosswalk rows must be an array")
    actual = [row.get("qac_unit_id") for row in rows]
    if actual != expected:
        raise ValueError("Attachment crosswalk QAC roster or order differs from packet")
    attachment_ids = {
        instance_identity(instance)
        for instance in (
            packet["attachments"].get("verb_instances", [])
            + packet["attachments"].get("noun_instances", [])
        )
    }
    aligned = []
    for row in rows:
        expected_ref = str(row.get("qac_unit_id", "")).removeprefix("q:")
        if row.get("qac_word_ref") != expected_ref:
            raise ValueError(f"Crosswalk QAC identity mismatch: {row}")
        attachment_id = row.get("attachment_unit_id", "")
        if attachment_id:
            if attachment_id not in attachment_ids:
                raise ValueError(f"Crosswalk references unknown attachment: {attachment_id}")
            aligned.append(attachment_id)
    if len(aligned) != len(set(aligned)):
        raise ValueError("Attachment crosswalk reuses an attachment instance")


def link_occurrences(packet: dict, crosswalk: dict | None = None) -> dict[str, dict]:
    """Resolve attachment instances through the QAC-keyed crosswalk."""
    crosswalk = crosswalk or build_attachment_crosswalk(packet)
    validate_attachment_crosswalk(packet, crosswalk)
    instances = {
        instance_identity(instance): instance
        for instance in (
            packet["attachments"].get("verb_instances", [])
            + packet["attachments"].get("noun_instances", [])
        )
    }
    links: dict[str, dict] = {}
    for row in crosswalk["rows"]:
        qac_unit = row["qac_unit_id"]
        attachment_id = row.get("attachment_unit_id", "")
        if row["status"] == "aligned" and attachment_id in instances:
            links[qac_unit] = {
                "method": "qac_crosswalk",
                "instances": [instances[attachment_id]],
            }
        elif row["status"] == "ambiguous":
            candidates = [
                instances[candidate]
                for candidate in row.get("candidate_attachment_unit_ids", [attachment_id])
                if candidate in instances
            ]
            links[qac_unit] = {
                "method": "unresolved_ambiguous",
                "reason": "ambiguous_form",
                "instances": candidates,
            }
        else:
            candidate_ids = row.get("candidate_attachment_unit_ids", [])
            candidates = [instances[value] for value in candidate_ids if value in instances]
            links[qac_unit] = {
                "method": "unresolved_form_mismatch" if candidates else "no_attachment_instance",
                "reason": "form_mismatch" if candidates else "no_instance",
                "instances": candidates,
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
        grammar = cell(local_source_grammar(instance.get("grammar", "")))
        if grammar and grammar not in values:
            values.append(grammar)
    return "; ".join(values)


def structured_occurrence_data(packet: dict, crosswalk: dict) -> dict:
    """Build normalized machine evidence without exposing ayahs to an agent."""
    validate_attachment_crosswalk(packet, crosswalk)
    links = link_occurrences(packet, crosswalk)
    rows_by_id = attachment_rows_by_id(packet)
    alignment_by_unit = {row["qac_unit_id"]: row for row in crosswalk["rows"]}
    forms = group_forms(packet["qac"]["occurrences"])
    form_by_ref: dict[str, str] = {}
    form_rows = []
    for form in forms:
        first = form["occurrences"][0]
        for occurrence in form["occurrences"]:
            form_by_ref[occurrence["qac_ref"]] = form["id"]
        form_rows.append(
            {
                "form_id": form["id"],
                "lemma_ar": first.get("lemma_ar", ""),
                "stem_ar": first.get("stem_ar", ""),
                "pos": first.get("pos", ""),
                "measure": first.get("measure", ""),
                "morph_features": first.get("morph_features", ""),
                "occurrence_count": len(form["occurrences"]),
            }
        )

    records = []
    qac_fields = (
        "qac_ref",
        "qac_word_ref",
        "surah",
        "ayah",
        "word_index",
        "morpheme_index",
        "surface_ar",
        "stem_ar",
        "lemma_ar",
        "source_pos",
        "pos",
        "morpheme_role",
        "measure",
        "aspect",
        "mood",
        "voice",
        "morph_features",
    )
    for occurrence in packet["qac"]["occurrences"]:
        unit = occurrence_unit_id(occurrence)
        alignment = alignment_by_unit[unit]
        link = links[unit]
        record = {field: occurrence.get(field, "") for field in qac_fields}
        record["ayah_ref"] = f"{occurrence['surah']}:{occurrence['ayah']}"
        record["form_id"] = form_by_ref[occurrence["qac_ref"]]
        record["alignment"] = {
            "status": alignment["status"],
            "method": alignment["method"],
            "confidence": alignment["confidence"],
            "attachment_unit_id": alignment.get("attachment_unit_id", ""),
            "attachment_word_unit_id": alignment.get("attachment_word_unit_id", ""),
            "qac_char_span": alignment.get("qac_char_span", []),
            "attachment_char_spans": alignment.get("attachment_char_spans", []),
            "source_grammar": linked_source_grammar(link),
            "attachments": linked_attachment_details(link, rows_by_id),
        }
        records.append(record)

    summary = packet["qac"].get("summary", {})
    return {
        "summary": {
            "morpheme_count": summary.get("morpheme_count", len(records)),
            "word_count": summary.get(
                "word_count", len({row["qac_word_ref"] for row in records})
            ),
            "ayah_count": summary.get(
                "ayah_count", len({row["ayah_ref"] for row in records})
            ),
            "surah_count": summary.get(
                "surah_count", len({row["surah"] for row in records})
            ),
        },
        "forms": form_rows,
        "ayahs": [
            {"ayah_ref": row["ref"], "surface_ar": row["surface_ar"]}
            for row in packet["qac"]["ayah_contexts"]
        ],
        "occurrences": records,
    }


GLOBAL_GRAMMAR_CLAIMS = (
    re.compile(r"(?:^|;\s*)COUNT\s+\d+[^.;]*", re.IGNORECASE),
    re.compile(r"\bThe word appears\s+\d+\s+times?\s+in\s+the\s+Quran[^.]*\.?", re.IGNORECASE),
    re.compile(r"\s*[—-]\s*always appears[^.;]*\(\d+\s+occurrences?\)", re.IGNORECASE),
    re.compile(
        r"(?:^|(?<=[.;]))\s*[^.;]*\b\d+\s+(?:Quranic\s+)?occurrences?\b[^.;]*[.;]?",
        re.IGNORECASE,
    ),
)


def local_source_grammar(value: object) -> str:
    """Keep local grammar while removing unverified corpus-wide assertions."""
    text = " ".join(str(value or "").split())
    for pattern in GLOBAL_GRAMMAR_CLAIMS:
        text = pattern.sub("", text)
    return text.strip(" ;.—-")


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


def render_markdown(
    packet: dict,
    packet_path: Path,
    language: str,
    crosswalk: dict | None = None,
) -> str:
    text = LABELS[language]
    occurrences = packet["qac"]["occurrences"]
    forms = group_forms(occurrences)
    links = link_occurrences(packet, crosswalk)
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
        f"| {text['relation']} | {text['focus_role']} | {text['counterpart']} | {text['preposition']} | {text['status']} | {text['confidence']} | {text['count']} | {text['forms_column']} | {text['refs']} |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for pattern in patterns:
        detail = pattern["detail"]
        relation = RELATION_LABELS[language].get(detail["relation"], detail["relation"])
        role = ROLE_LABELS[language].get(detail["focus_role"], detail["focus_role"])
        counterpart = pattern["counterpart_key"] or detail["other_unit_id"] or "?"
        if detail["other_root"]:
            counterpart += f" ({detail['other_root']})"
        statuses = ", ".join(
            STATUS_LABELS[language].get(value, value)
            for value in sorted(pattern["statuses"])
        ) or text["none"]
        confidences = ", ".join(
            CONFIDENCE_LABELS[language].get(value, value)
            for value in sorted(pattern["confidences"])
        ) or text["none"]
        lines.append(
            f"| {cell(relation)} | {cell(role)} | {cell(counterpart)} | "
            f"{cell(detail['prep_base'] or text['none'])} | {cell(statuses)} | "
            f"{cell(confidences)} | {pattern['count']} | "
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


def write_crosswalk(path: Path, crosswalk: dict, *, check: bool) -> None:
    content = json.dumps(crosswalk, ensure_ascii=False, indent=2) + "\n"
    if check:
        if not path.is_file():
            raise ValueError(f"Missing generated crosswalk: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Stale generated crosswalk: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("generated_by") != crosswalk["generated_by"]:
            raise ValueError(f"Refusing to replace unmarked crosswalk: {path}")
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of canonical evidence pinned by a reviewed entry",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        packet_path, packet = load_packet(PROJECT, args.root, args.packet)
        validate_packet(packet)
        canonical_output = (
            PROJECT
            / "v2/output/occurrences"
            / f"{packet['root_envelope_id']}.{args.language}.md"
        )
        output = (args.output or canonical_output).resolve()
        crosswalk = build_attachment_crosswalk(packet)
        validate_attachment_crosswalk(packet, crosswalk)
        if output == canonical_output.resolve():
            protect_pinned_entries(
                PROJECT,
                packet["root_envelope_id"],
                (args.language,),
                force=args.force or args.check,
                scope="canonical occurrence evidence",
            )
            alignment_output = (
                PROJECT / "v2/output/alignments" / f"{packet['root_envelope_id']}.json"
            )
            write_crosswalk(alignment_output, crosswalk, check=args.check)
        content = render_markdown(packet, packet_path, args.language, crosswalk)
        write_generated(output, content, check=args.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
