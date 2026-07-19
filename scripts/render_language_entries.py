#!/usr/bin/env python3
"""Validate authored JSONL and render deterministic language-specific entries."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse


SCHEMA_VERSION = 1
GENERATED_MARKER = "<!-- generated-by: render_language_entries.py schema=1 -->"
LANGUAGES = ("en", "tr")
ROLE_VALUES = {"primary", "alternative", "recognition"}
FIT_VALUES = {
    "none",
    "narrowing",
    "broadening",
    "displacement",
    "drifted_loanword",
}
RELATIONSHIP_VALUES = {
    "explicit_support",
    "compatible_support",
    "additional_nuance",
    "explicit_disagreement",
    "sole_attestation",
    "no_located_attestation",
}
RECORD_TYPES = {
    "root",
    "branch",
    "branch_source",
    "lexical",
    "branch_lexical",
    "quran_form",
    "quran_ayah",
    "external_source",
}
ROOT_ID_RE = re.compile(r"root_[0-9]{6}(?:--root_[0-9]{6})*\Z")
EXTERNAL_ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*\Z")
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
GENERIC_FILLER = {"resolved", "todo", "tbd", "fixme", "placeholder"}
VERIFICATION_PLACEHOLDERS = {
    "-",
    "n/a",
    "na",
    "none",
    "not applicable",
    "not available",
    "not checked",
    "not yet checked",
    "not verified",
    "placeholder entry",
    "pending",
    "query",
    "query pending",
    "shell",
    "maintenance",
    "under maintenance",
    "unchecked",
    "unknown",
    "unavailable",
    "to be checked",
    "tbd after access",
}
VERIFICATION_STATUS_RE = re.compile(
    r"(?:"
    r"(?:to be|not yet) (?:checked|verified|accessed)"
    r"|unchecked"
    r"|(?:tbd|todo) after (?:access|verification|review)"
    r"|placeholder (?:entry|locator|excerpt)"
    r"|(?:query|shell|maintenance)(?: status)?"
    r"(?:[: -]+(?:pending|unavailable|failed|error|not available|not checked|unchecked))?"
    r")\Z"
)
SOURCE_LANGUAGE_VALUES = {"ar", "en", "tr"}
SOURCE_LANGUAGE_DISPLAY = {
    "en": {"ar": "Arabic", "en": "English", "tr": "Turkish"},
    "tr": {"ar": "Arapça", "en": "İngilizce", "tr": "Türkçe"},
}

ROLE_DISPLAY = {
    "en": {"primary": "Primary", "alternative": "Alternative", "recognition": "Recognition"},
    "tr": {"primary": "Birincil", "alternative": "Alternatif", "recognition": "Tanıma"},
}
FIT_DISPLAY = {
    "en": {
        "none": "No fit error",
        "narrowing": "Narrowing",
        "broadening": "Broadening",
        "displacement": "Displacement",
        "drifted_loanword": "Drifted loanword",
    },
    "tr": {
        "none": "Uyum hatası yok",
        "narrowing": "Daraltma",
        "broadening": "Genişletme",
        "displacement": "Anlam kayması",
        "drifted_loanword": "Anlamı kaymış alıntı",
    },
}
RELATIONSHIP_DISPLAY = {
    "en": {
        "explicit_support": "Explicit support",
        "compatible_support": "Compatible support",
        "additional_nuance": "Additional nuance",
        "explicit_disagreement": "Explicit disagreement",
        "sole_attestation": "Sole attestation",
        "no_located_attestation": "No located attestation",
    },
    "tr": {
        "explicit_support": "Açık destek",
        "compatible_support": "Uyumlu destek",
        "additional_nuance": "Ek nüans",
        "explicit_disagreement": "Açık uyuşmazlık",
        "sole_attestation": "Tek tanıklık",
        "no_located_attestation": "Saptanmış tanıklık yok",
    },
}
UNIT_KIND_DISPLAY = {
    "en": {
        "form": "Form",
        "collocation": "Collocation",
        "lexical_unit": "Lexical unit",
        "construction": "Construction",
        "review": "Review unit",
    },
    "tr": {
        "form": "Biçim",
        "collocation": "Eşdizim",
        "lexical_unit": "Sözlük birimi",
        "construction": "Yapı",
        "review": "İnceleme birimi",
    },
}
POS_DISPLAY = {
    "en": {"N": "Noun", "PN": "Proper noun", "V": "Verb", "ADJ": "Adjective", "ADV": "Adverb", "PRON": "Pronoun"},
    "tr": {"N": "İsim", "PN": "Özel ad", "V": "Fiil", "ADJ": "Sıfat", "ADV": "Zarf", "PRON": "Zamir"},
}
FEATURE_DISPLAY = {
    "en": {
        "STEM": "stem",
        "PERF": "perfect aspect",
        "IMPF": "imperfect aspect",
        "IMPV": "imperative",
        "PASS": "passive voice",
        "ACT": "active voice",
        "SUBJ": "subjunctive mood",
        "IND": "indicative mood",
        "JUS": "jussive mood",
        "NOM": "nominative",
        "ACC": "accusative",
        "GEN": "genitive",
        "M": "masculine",
        "F": "feminine",
        "S": "singular",
        "D": "dual",
        "P": "plural",
    },
    "tr": {
        "STEM": "gövde",
        "PERF": "tamamlanmış görünüş",
        "IMPF": "tamamlanmamış görünüş",
        "IMPV": "emir",
        "PASS": "edilgen çatı",
        "ACT": "etken çatı",
        "SUBJ": "istek kipi",
        "IND": "bildirme kipi",
        "JUS": "cezimli kip",
        "NOM": "yalın durum",
        "ACC": "belirtme durumu",
        "GEN": "tamlayan durumu",
        "M": "eril",
        "F": "dişil",
        "S": "tekil",
        "D": "ikil",
        "P": "çoğul",
    },
}
FORM_TAG_DISPLAY = {
    "en": {
        "CV": "Imperative verb",
        "IV": "Imperfect verb",
        "PV_PASS": "Passive perfect verb",
        "NOUN_ABSTRACT": "Abstract noun",
        "NOUN_CONCRETE": "Concrete noun",
        "NOUN_PROP": "Proper noun",
    },
    "tr": {
        "CV": "Emir fiili",
        "IV": "Tamamlanmamış fiil",
        "PV_PASS": "Edilgen tamamlanmış fiil",
        "NOUN_ABSTRACT": "Soyut isim",
        "NOUN_CONCRETE": "Somut isim",
        "NOUN_PROP": "Özel ad",
    },
}
ROUTE_STATUS_DISPLAY = {
    "en": {"exact": "Exact route", "variant": "Variant route", "no_match": "No routed match"},
    "tr": {"exact": "Tam yönlendirme", "variant": "Varyant yönlendirmesi", "no_match": "Yönlendirilmiş eşleşme yok"},
}
DICTIONARY_DISPLAY = {
    "ayn": "Kitāb al-ʿAyn",
    "jamhara": "Jamharat al-Lugha",
    "maqayis": "Maqāyīs al-Lugha",
    "mufradat": "al-Mufradāt fī Gharīb al-Qurʾān",
    "sihah": "al-Ṣiḥāḥ",
    "tahdhib": "Tahdhīb al-Lugha",
}

LABELS = {
    "en": {
        "title": "Root",
        "overview": "Branch Overview",
        "branch": "Branch",
        "primary": "Primary gloss",
        "concept": "Concept and Meaning",
        "scope": "Scope",
        "includes": "Includes",
        "excludes": "Excludes",
        "boundaries": "Semantic Boundaries",
        "lexical": "Forms and Lexical Units",
        "distinctions": "Structured Distinctions",
        "glosses": "Gloss Analysis",
        "audits": "Source Evidence",
        "note": "English Usage Note",
        "quran": "Quran Appendix",
        "census": "Census",
        "forms": "Forms and Lemmas",
        "occurrences": "Complete Occurrences",
        "constructions": "Construction Evidence",
        "ayahs": "Full Ayah Contexts",
        "quran_observations": "Root-level Observations",
        "bibliography": "Bibliography",
        "external": "External and Target-language Sources",
        "transliteration": "English transliteration",
        "branch_label": "Branch",
        "arabic_image": "Arabic image",
        "key": "Key",
        "arabic_expression": "Arabic expression",
        "kind": "Kind",
        "v4_sense": "Attested Arabic sense",
        "meaning": "Meaning in this branch",
        "analysis": "Analysis",
        "source_phrase": "Arabic source phrase",
        "source_handles": "Source handles",
        "neighbor": "Arabic neighbor",
        "shared_zone": "Shared zone",
        "distinction": "Distinguishing axis",
        "evidence": "Evidence",
        "rendering": "Rendering",
        "role": "Role",
        "preserves": "Preserves",
        "loses": "Loses",
        "adds": "Adds",
        "fit": "Fit",
        "collision": "Collision",
        "reference": "Reference",
        "dictionary": "Dictionary",
        "route_status": "Route status",
        "relationship": "Relationship",
        "selected_quote": "Selected Arabic quotation",
        "contribution": "Contribution",
        "explanation": "Explanation",
        "source_analysis": "Source analysis",
        "morphemes": "Rooted morphemes",
        "words": "Words",
        "ayah_count": "Ayahs",
        "surahs": "Surahs",
        "ordinal": "Ordinal",
        "lemma_surface": "Lemma / surface",
        "pos": "POS",
        "morphology": "Morphology",
        "count": "Count",
        "qac_refs": "Locations",
        "qac_ref": "Location",
        "surface": "Arabic surface",
        "lemma": "Lemma",
        "measure": "Measure",
        "ayah": "Ayah",
        "attachment_handles": "Syntactic evidence",
        "verb_frames": "Aggregate verb frames",
        "noun_patterns": "Aggregate noun patterns",
        "frame": "Frame",
        "instances": "Instances",
        "samples": "Sample locations",
        "profile": "Profile",
        "source_id": "Source",
        "source_note": "Source note",
        "accessed_on": "Accessed",
        "source_language": "Source language",
        "locator": "Location in source",
        "verified_excerpt": "Inspected excerpt",
        "none": "None.",
    },
    "tr": {
        "title": "Kök",
        "overview": "Dal Özeti",
        "branch": "Dal",
        "primary": "Birincil karşılık",
        "concept": "Kavram ve Anlam",
        "scope": "Kapsam",
        "includes": "Kapsadıkları",
        "excludes": "Kapsamadıkları",
        "boundaries": "Anlamsal Sınırlar",
        "lexical": "Biçimler ve Sözlük Birimleri",
        "distinctions": "Yapılandırılmış Ayrımlar",
        "glosses": "Karşılık Çözümlemesi",
        "audits": "Kaynak Kanıtları",
        "note": "Türkçe Kullanım Notu",
        "quran": "Kur'an Eki",
        "census": "Döküm",
        "forms": "Biçimler ve Sözlük Birimleri",
        "occurrences": "Bütün Geçişler",
        "constructions": "Yapı Kanıtı",
        "ayahs": "Tam Ayet Bağlamları",
        "quran_observations": "Kök Düzeyindeki Gözlemler",
        "bibliography": "Kaynakça",
        "external": "Dış ve Türkçe Kullanım Kaynakları",
        "transliteration": "Türkçe çevriyazı",
        "branch_label": "Dal",
        "arabic_image": "Arapça imge",
        "key": "Anahtar",
        "arabic_expression": "Arapça ifade",
        "kind": "Tür",
        "v4_sense": "Tanıklanmış Arapça anlam",
        "meaning": "Bu daldaki anlam",
        "analysis": "Çözümleme",
        "source_phrase": "Arapça kaynak ifadesi",
        "source_handles": "Kaynak tutamakları",
        "neighbor": "Arapça komşu",
        "shared_zone": "Ortak alan",
        "distinction": "Ayırıcı eksen",
        "evidence": "Kanıt",
        "rendering": "Karşılık",
        "role": "Rol",
        "preserves": "Koruduğu",
        "loses": "Eksilttiği",
        "adds": "Eklediği",
        "fit": "Uyum",
        "collision": "Çakışma",
        "reference": "Başvuru",
        "dictionary": "Sözlük",
        "route_status": "Yönlendirme durumu",
        "relationship": "İlişki",
        "selected_quote": "Seçilmiş Arapça alıntı",
        "contribution": "Katkı",
        "explanation": "Açıklama",
        "source_analysis": "Kaynak çözümlemesi",
        "morphemes": "Köklü biçimbirimler",
        "words": "Kelimeler",
        "ayah_count": "Ayetler",
        "surahs": "Sureler",
        "ordinal": "Sıra",
        "lemma_surface": "Madde / yüzey",
        "pos": "Sözcük türü",
        "morphology": "Biçimbilim",
        "count": "Sayı",
        "qac_refs": "Konumlar",
        "qac_ref": "Konum",
        "surface": "Arapça yüzey",
        "lemma": "Madde",
        "measure": "Kalıp",
        "ayah": "Ayet",
        "attachment_handles": "Sözdizimsel kanıt",
        "verb_frames": "Toplu fiil istem çerçeveleri",
        "noun_patterns": "Toplu isim yönetim örüntüleri",
        "frame": "Çerçeve",
        "instances": "Örnek sayısı",
        "samples": "Örnek konumlar",
        "profile": "Görünüm",
        "source_id": "Kaynak",
        "source_note": "Kaynak notu",
        "accessed_on": "Erişim tarihi",
        "source_language": "Kaynak dili",
        "locator": "Kaynaktaki konum",
        "verified_excerpt": "İncelenen alıntı",
        "none": "Yok.",
    },
}


class ContractError(ValueError):
    """Raised when packet or authored input violates the contract."""


def fail(message: str) -> None:
    raise ContractError(message)


def duplicate_safe_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=duplicate_safe_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON {path}: {exc}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        fail(f"cannot read JSONL {path}: {exc}")
    records = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line, object_pairs_hook=duplicate_safe_object)
        except (json.JSONDecodeError, ContractError) as exc:
            fail(f"{path}:{line_number}: {exc}")
        if not isinstance(record, dict):
            fail(f"{path}:{line_number}: each JSONL line must be an object")
        if "__line__" in record:
            fail(f"{path}:{line_number}: reserved field '__line__'")
        record["__line__"] = line_number
        records.append(record)
    if not records:
        fail("authored JSONL is empty")
    return records


def require_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{context} must be an object")
    return value


def require_list(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{context} must be an array")
    return value


def require_text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{context} must be a non-empty string")
    return value.strip()


def require_substantive_text(value: Any, context: str) -> str:
    text = require_text(value, context)
    if text.casefold().rstrip(".!") in GENERIC_FILLER:
        fail(f"{context} contains generic filler {text!r}")
    return text


def require_verification_text(
    value: Any,
    context: str,
    *,
    minimum: int,
    maximum: int,
    reject_status: bool = True,
    preserve: bool = False,
) -> str:
    if preserve:
        if not isinstance(value, str) or not value.strip():
            fail(f"{context} must be a non-empty string")
        if value != value.strip():
            fail(f"{context} must not have leading or trailing whitespace")
        text = value
        if text.casefold().rstrip(".!") in GENERIC_FILLER:
            fail(f"{context} contains generic filler {text!r}")
    else:
        text = require_substantive_text(value, context)
    if not minimum <= len(text) <= maximum:
        fail(f"{context} must be {minimum}-{maximum} characters")
    if any(unicodedata.category(character).startswith("C") for character in text):
        fail(f"{context} must not contain control or format characters")
    normalized = text.casefold().strip(" .,:;_-()[]{}")
    if reject_status and (
        normalized in VERIFICATION_PLACEHOLDERS
        or VERIFICATION_STATUS_RE.fullmatch(normalized)
    ):
        fail(f"{context} must identify inspected source content, not a status placeholder")
    return text


def bounded_bilingual_text(
    value: Any,
    context: str,
    *,
    minimum: int,
    maximum: int,
    reject_status: bool = False,
) -> dict[str, str]:
    obj = require_object(value, context)
    if set(obj) != set(LANGUAGES):
        fail(f"{context} must contain exactly en and tr")
    return {
        lang: require_verification_text(
            obj[lang],
            f"{context}.{lang}",
            minimum=minimum,
            maximum=maximum,
            reject_status=reject_status,
        )
        for lang in LANGUAGES
    }


def validate_verification(value: Any, context: str) -> dict[str, Any]:
    verification = require_object(value, context)
    required = {"accessed_on", "source_language", "locator", "excerpt"}
    missing_required = sorted(required - set(verification))
    if missing_required:
        fail(f"{context}: missing " + ", ".join(missing_required))
    source_language = require_text(
        verification["source_language"], context + ".source_language"
    )
    if source_language not in SOURCE_LANGUAGE_VALUES:
        fail(f"{context}.source_language must be one of ar, en, tr")
    expected = required | (
        {"excerpt_transliteration"} if source_language == "ar" else set()
    )
    missing = sorted(expected - set(verification))
    extra = sorted(set(verification) - expected)
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra/forbidden " + ", ".join(extra))
        fail(f"{context}: " + "; ".join(details))
    accessed_on = require_text(verification["accessed_on"], context + ".accessed_on")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", accessed_on):
        fail(f"{context}.accessed_on must be a YYYY-MM-DD calendar date")
    try:
        date.fromisoformat(accessed_on)
    except ValueError:
        fail(f"{context}.accessed_on must be a valid calendar date")
    excerpt = require_verification_text(
        verification["excerpt"],
        context + ".excerpt",
        minimum=1,
        maximum=500,
        preserve=True,
    )
    if source_language == "ar" and not ARABIC_RE.search(excerpt):
        fail(f"{context}.excerpt must contain Arabic script for an Arabic source")
    result = {
        "accessed_on": accessed_on,
        "source_language": source_language,
        "locator": bounded_bilingual_text(
            verification["locator"],
            context + ".locator",
            minimum=3,
            maximum=300,
            reject_status=True,
        ),
        "excerpt": excerpt,
    }
    if source_language == "ar":
        result["excerpt_transliteration"] = bounded_bilingual_text(
            verification["excerpt_transliteration"],
            context + ".excerpt_transliteration",
            minimum=1,
            maximum=500,
        )
    return result


def require_int(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(f"{context} must be an integer")
    return value


def exact_fields(record: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(record) - {"__line__"}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra/forbidden " + ", ".join(extra))
        fail(f"{context}: " + "; ".join(details))


def fields_with_optional(
    record: dict[str, Any], required: set[str], optional: set[str], context: str
) -> None:
    actual = set(record) - {"__line__"}
    missing = sorted(required - actual)
    extra = sorted(actual - required - optional)
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra/forbidden " + ", ".join(extra))
        fail(f"{context}: " + "; ".join(details))


def bilingual_text(
    value: Any, context: str, *, substantive: bool = True
) -> dict[str, str]:
    obj = require_object(value, context)
    if set(obj) != set(LANGUAGES):
        fail(f"{context} must contain exactly en and tr")
    validator = require_substantive_text if substantive else require_text
    return {lang: validator(obj[lang], f"{context}.{lang}") for lang in LANGUAGES}


def bilingual_list(
    value: Any, context: str, *, allow_empty: bool = False
) -> dict[str, list[str]]:
    obj = require_object(value, context)
    if set(obj) != set(LANGUAGES):
        fail(f"{context} must contain exactly en and tr")
    result = {}
    for lang in LANGUAGES:
        items = require_list(obj[lang], f"{context}.{lang}")
        if not items and not allow_empty:
            fail(f"{context}.{lang} must not be empty")
        result[lang] = [
            require_substantive_text(item, f"{context}.{lang} item") for item in items
        ]
    return result


def branch_ref(row: dict[str, Any]) -> str:
    return f"{row['root_id']}/{row['branch_id']}"


def branch_source_handles(branch: dict[str, Any]) -> list[str]:
    """Split only the packet-defined semicolon roster; source refs stay opaque."""
    raw = branch.get("source_refs") or ""
    handles = [handle for handle in raw.split(";") if handle]
    if len(handles) != len(set(handles)):
        fail(f"packet branch {branch_ref(branch)} has duplicate source handles")
    return handles


def validate_packet(packet: Any) -> dict[str, Any]:
    packet = require_object(packet, "packet")
    required = {
        "root_envelope_id",
        "root_join_key",
        "root_norm",
        "v4_roots",
        "branches",
        "dictionary_sources",
        "lexical_senses",
        "branch_lexical_links",
        "qac",
        "attachments",
    }
    missing = sorted(required - set(packet))
    if missing:
        fail("packet missing " + ", ".join(missing))
    envelope_id = require_text(packet["root_envelope_id"], "packet.root_envelope_id")
    if not ROOT_ID_RE.fullmatch(envelope_id):
        fail(f"invalid packet root_envelope_id {envelope_id!r}")
    roots = require_list(packet["v4_roots"], "packet.v4_roots")
    root_ids = []
    for number, row in enumerate(roots, start=1):
        row = require_object(row, f"packet V4 root {number}")
        root_ids.append(require_text(row.get("root_id"), f"packet V4 root {number} ID"))
    if not root_ids or len(root_ids) != len(set(root_ids)):
        fail("packet V4 root roster is empty or duplicated")
    if envelope_id != "--".join(root_ids):
        fail("packet root envelope does not match ordered V4 root IDs")

    branches = require_list(packet["branches"], "packet.branches")
    branch_keys = []
    for number, row in enumerate(branches, start=1):
        row = require_object(row, f"packet branch {number}")
        key = (
            require_text(row.get("root_id"), f"packet branch {number} root_id"),
            require_text(row.get("branch_id"), f"packet branch {number} branch_id"),
        )
        if key[0] not in root_ids:
            fail(f"packet branch has unknown root {key[0]!r}")
        branch_source_handles(row)
        branch_keys.append(key)
    if not branch_keys or len(branch_keys) != len(set(branch_keys)):
        fail("packet branch roster is empty or duplicated")

    sources = require_list(packet["dictionary_sources"], "packet.dictionary_sources")
    for number, row in enumerate(sources, start=1):
        row = require_object(row, f"packet dictionary source {number}")
        if row.get("root_id") not in root_ids:
            fail(f"packet source {number} has unknown root")
        require_text(row.get("source_id"), f"packet source {number} source_id")
        require_text(row.get("source_ref"), f"packet source {number} source_ref")

    lexical = require_list(packet["lexical_senses"], "packet.lexical_senses")
    lexical_keys = []
    for number, row in enumerate(lexical, start=1):
        row = require_object(row, f"packet lexical sense {number}")
        key = (
            require_text(row.get("root_id"), f"packet lexical sense {number} root_id"),
            require_text(
                row.get("lexical_unit_id"),
                f"packet lexical sense {number} lexical_unit_id",
            ),
        )
        if key[0] not in root_ids:
            fail(f"packet lexical sense has unknown root {key[0]!r}")
        lexical_keys.append(key)
    if len(lexical_keys) != len(set(lexical_keys)):
        fail("packet lexical keys are duplicated")

    branch_set = set(branch_keys)
    lexical_set = set(lexical_keys)
    links = require_list(packet["branch_lexical_links"], "packet.branch_lexical_links")
    link_keys = []
    for number, row in enumerate(links, start=1):
        row = require_object(row, f"packet branch lexical link {number}")
        branch_key = (row.get("root_id"), row.get("branch_id"))
        lexical_key = (row.get("root_id"), row.get("lexical_unit_id"))
        if branch_key not in branch_set or lexical_key not in lexical_set:
            fail(f"packet branch lexical link {number} has an unknown key")
        link_keys.append(branch_key + (row["lexical_unit_id"],))
    if len(link_keys) != len(set(link_keys)):
        fail("packet branch lexical links are duplicated")

    qac = require_object(packet["qac"], "packet.qac")
    require_object(qac.get("summary"), "packet.qac.summary")
    occurrences = require_list(qac.get("occurrences"), "packet.qac.occurrences")
    occurrence_refs = []
    for number, row in enumerate(occurrences, start=1):
        row = require_object(row, f"packet occurrence {number}")
        occurrence_refs.append(
            require_text(row.get("qac_ref"), f"packet occurrence {number} qac_ref")
        )
    if len(occurrence_refs) != len(set(occurrence_refs)):
        fail("packet QAC occurrence references are duplicated")
    ayahs = require_list(qac.get("ayah_contexts"), "packet.qac.ayah_contexts")
    ayah_refs = []
    for number, row in enumerate(ayahs, start=1):
        row = require_object(row, f"packet ayah {number}")
        ayah_refs.append(require_text(row.get("ref"), f"packet ayah {number} ref"))
    if len(ayah_refs) != len(set(ayah_refs)):
        fail("packet ayah references are duplicated")
    occurrence_ayahs = {f"{row.get('surah')}:{row.get('ayah')}" for row in occurrences}
    if occurrence_ayahs != set(ayah_refs):
        fail("packet occurrence ayah handles do not match ayah contexts")

    attachments = require_object(packet["attachments"], "packet.attachments")
    for name, rows in attachments.items():
        rows = require_list(rows, f"packet.attachments.{name}")
        for number, row in enumerate(rows, start=1):
            require_object(row, f"packet.attachments.{name}[{number}]")
    return packet


def form_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for occurrence in packet["qac"]["occurrences"]:
        key = (
            occurrence.get("lemma_ar", ""),
            occurrence.get("surface_ar", ""),
            occurrence.get("pos", ""),
            occurrence.get("morph_features", ""),
        )
        grouped.setdefault(key, []).append(occurrence)
    rows = []
    for ordinal, (key, occurrences) in enumerate(grouped.items(), start=1):
        lemma, surface, pos, morphology = key
        rows.append(
            {
                "ordinal": ordinal,
                "lemma_ar": lemma,
                "surface_ar": surface,
                "pos": pos,
                "morphology": morphology,
                "count": len(occurrences),
                "qac_refs": [row["qac_ref"] for row in occurrences],
                "representative": occurrences[0],
            }
        )
    return rows


def occurrence_form_ordinals(packet: dict[str, Any]) -> dict[str, int]:
    result = {}
    for form in form_rows(packet):
        for qac_ref in form["qac_refs"]:
            result[qac_ref] = form["ordinal"]
    return result


def validate_glosses(value: Any, context: str) -> dict[str, list[dict[str, str]]]:
    obj = require_object(value, context)
    if set(obj) != set(LANGUAGES):
        fail(f"{context} must contain exactly en and tr")
    fields = {"text", "role", "preserves", "loses", "adds", "fit", "collision"}
    result = {}
    for lang in LANGUAGES:
        rows = require_list(obj[lang], f"{context}.{lang}")
        if not 1 <= len(rows) <= 3:
            fail(f"{context}.{lang} must contain 1-3 glosses")
        parsed = []
        for number, row in enumerate(rows, start=1):
            row = require_object(row, f"{context}.{lang}[{number}]")
            exact_fields(row, fields, f"{context}.{lang}[{number}]")
            parsed_row = {
                key: require_substantive_text(
                    row[key], f"{context}.{lang}[{number}].{key}"
                )
                for key in fields
            }
            if parsed_row["role"] not in ROLE_VALUES:
                fail(f"{context}.{lang}[{number}].role is not allowed")
            if parsed_row["fit"] not in FIT_VALUES:
                fail(f"{context}.{lang}[{number}].fit is not allowed")
            parsed.append(parsed_row)
        if sum(row["role"] == "primary" for row in parsed) != 1:
            fail(f"{context}.{lang} must contain exactly one primary gloss")
        if parsed[0]["role"] != "primary":
            fail(f"{context}.{lang} primary gloss must be first")
        result[lang] = parsed
    return result


def validate_distinctions(
    value: Any, context: str, allowed_evidence: set[str]
) -> list[dict[str, Any]]:
    rows = require_list(value, context)
    if not rows:
        fail(f"{context} must contain at least one structured contrast")
    fields = {"neighbor_ar", "transliteration", "shared_zone", "distinction", "evidence"}
    result = []
    for number, row in enumerate(rows, start=1):
        row = require_object(row, f"{context}[{number}]")
        exact_fields(row, fields, f"{context}[{number}]")
        evidence = require_list(row["evidence"], f"{context}[{number}].evidence")
        if not evidence:
            fail(f"{context}[{number}].evidence must not be empty")
        evidence = [
            require_text(ref, f"{context}[{number}].evidence item") for ref in evidence
        ]
        unknown = [ref for ref in evidence if ref not in allowed_evidence]
        if unknown:
            fail(f"{context}[{number}] has unknown evidence refs {unknown!r}")
        neighbor_ar = require_text(
            row["neighbor_ar"], f"{context}[{number}].neighbor_ar"
        )
        if not ARABIC_RE.search(neighbor_ar):
            fail(f"{context}[{number}].neighbor_ar must contain Arabic script")
        result.append(
            {
                "neighbor_ar": neighbor_ar,
                "transliteration": bilingual_text(
                    row["transliteration"],
                    f"{context}[{number}].transliteration",
                    substantive=False,
                ),
                "shared_zone": bilingual_text(
                    row["shared_zone"], f"{context}[{number}].shared_zone"
                ),
                "distinction": bilingual_text(
                    row["distinction"], f"{context}[{number}].distinction"
                ),
                "evidence": evidence,
            }
        )
    return result


def assert_exact_roster(label: str, actual: list[Any], expected: list[Any]) -> None:
    actual_set = set(actual)
    expected_set = set(expected)
    missing = [key for key in expected if key not in actual_set]
    extra = [key for key in actual if key not in expected_set]
    if missing or extra or len(actual) != len(expected):
        fail(f"{label} roster mismatch; missing={missing!r}; extra={extra!r}")


def record_key_text(record: dict[str, Any], field: str, context: str) -> str:
    return require_text(record.get(field), f"{context}.{field}")


def source_matches(
    packet: dict[str, Any], root_id: str, source_ref: str
) -> list[dict[str, Any]]:
    return [
        row
        for row in packet["dictionary_sources"]
        if row.get("root_id") == root_id and row.get("source_ref") == source_ref
    ]


def transliteration_pairs(
    packet: dict[str, Any], authored: dict[str, Any]
) -> list[tuple[str, str, dict[str, str], bool]]:
    """Return exact Arabic/overlay pairs; the boolean enables article checks."""
    pairs = [
        (
            "root.transliteration",
            str(packet.get("root_join_key") or packet.get("root_norm") or ""),
            authored["root"]["transliteration"],
            False,
        )
    ]
    packet_branches = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    for key, editorial in authored["branches"].items():
        branch = packet_branches[key]
        pairs.extend(
            (
                f"branch {key!r}.{overlay_field}",
                str(branch.get(arabic_field) or ""),
                editorial[overlay_field],
                True,
            )
            for arabic_field, overlay_field in (
                ("branch_image_ar", "image_transliteration"),
                ("what_is_ar", "what_is_ar_transliteration"),
                ("what_is_not_ar", "what_is_not_ar_transliteration"),
            )
        )
        for number, distinction in enumerate(editorial["distinctions"], start=1):
            pairs.append(
                (
                    f"branch {key!r}.distinctions[{number}].transliteration",
                    distinction["neighbor_ar"],
                    distinction["transliteration"],
                    True,
                )
            )

    packet_lexical = {
        (row["root_id"], row["lexical_unit_id"]): row
        for row in packet["lexical_senses"]
    }
    for key, editorial in authored["lexical"].items():
        sense = packet_lexical[key]
        pairs.extend(
            (
                f"lexical {key!r}.{overlay_field}",
                str(sense.get(arabic_field) or ""),
                editorial[overlay_field],
                True,
            )
            for arabic_field, overlay_field in (
                ("expression_ar", "expression_transliteration"),
                ("sense_ar", "sense_ar_transliteration"),
                ("source_phrase_ar", "source_phrase_transliteration"),
            )
        )
    for key, editorial in authored["branch_sources"].items():
        pairs.append(
            (
                f"branch_source {key!r}.quote_transliteration",
                editorial["selected_quote_ar"],
                editorial["quote_transliteration"],
                True,
            )
        )
    forms = {row["ordinal"]: row for row in form_rows(packet)}
    for ordinal, editorial in authored["quran_form"].items():
        form = forms[ordinal]
        pairs.extend(
            (
                f"quran_form {ordinal}.{overlay_field}",
                str(form[arabic_field]),
                editorial[overlay_field],
                True,
            )
            for arabic_field, overlay_field in (
                ("lemma_ar", "lemma_transliteration"),
                ("surface_ar", "surface_transliteration"),
            )
        )
    ayahs = {row["ref"]: row for row in packet["qac"]["ayah_contexts"]}
    for ref, editorial in authored["quran_ayah"].items():
        pairs.append(
            (
                f"quran_ayah {ref}.transliteration",
                str(ayahs[ref].get("surface_ar") or ""),
                editorial["transliteration"],
                False,
            )
        )
    for source_id, source in authored["external_sources"].items():
        verification = source["verification"]
        if verification["source_language"] == "ar":
            pairs.append(
                (
                    f"external_source {source_id!r}.verification.excerpt_transliteration",
                    verification["excerpt"],
                    verification["excerpt_transliteration"],
                    True,
                )
            )
    return [pair for pair in pairs if pair[1]]


def substantive_prose_fields(
    authored: dict[str, Any]
) -> Iterable[tuple[str, str, str]]:
    root = authored["root"]
    for field in ("overview", "quran_note"):
        for lang in LANGUAGES:
            yield f"root.{field}.{lang}", lang, root[field][lang]
    for lang in LANGUAGES:
        for number, text in enumerate(root["quran_observations"][lang], start=1):
            yield f"root.quran_observations.{lang}[{number}]", lang, text
    for key, branch in authored["branches"].items():
        for field in ("concept", "target_language_note"):
            for lang in LANGUAGES:
                yield f"branch {key!r}.{field}.{lang}", lang, branch[field][lang]
        for field in ("scope_in", "scope_out"):
            for lang in LANGUAGES:
                for number, text in enumerate(branch[field][lang], start=1):
                    yield f"branch {key!r}.{field}.{lang}[{number}]", lang, text
        for number, distinction in enumerate(branch["distinctions"], start=1):
            for field in ("shared_zone", "distinction"):
                for lang in LANGUAGES:
                    yield (
                        f"branch {key!r}.distinctions[{number}].{field}.{lang}",
                        lang,
                        distinction[field][lang],
                    )
        for lang in LANGUAGES:
            for number, gloss in enumerate(branch["glosses"][lang], start=1):
                for field in ("text", "preserves", "loses", "adds", "collision"):
                    yield (
                        f"branch {key!r}.glosses.{lang}[{number}].{field}",
                        lang,
                        gloss[field],
                    )
    for key, source in authored["branch_sources"].items():
        for field in ("contribution", "explanation", "analysis"):
            for lang in LANGUAGES:
                yield f"branch_source {key!r}.{field}.{lang}", lang, source[field][lang]
    for key, lexical in authored["branch_lexical"].items():
        for field in ("meaning", "analysis"):
            for lang in LANGUAGES:
                yield f"branch_lexical {key!r}.{field}.{lang}", lang, lexical[field][lang]
    for source_id, source in authored["external_sources"].items():
        for lang in LANGUAGES:
            yield f"external_source {source_id!r}.note.{lang}", lang, source["note"][lang]


UNMISTAKABLE_TRANSLITERATION_MARKS = set(
    "āīūâîûḥḫṣḍṭẓḳẕġṯʿʾ"
)


def validate_prose_transliteration_anchors(
    authored: dict[str, Any], pairs: list[tuple[str, str, dict[str, str], bool]]
) -> None:
    inventory: dict[str, dict[str, set[str]]] = {lang: {} for lang in LANGUAGES}
    for _context, arabic, overlays, _article_checked in pairs:
        for lang in LANGUAGES:
            transliteration = unicodedata.normalize("NFC", overlays[lang]).strip()
            if len(transliteration) < 3 or not any(
                character.casefold() in UNMISTAKABLE_TRANSLITERATION_MARKS
                for character in transliteration
            ):
                continue
            inventory[lang].setdefault(transliteration, set()).add(
                unicodedata.normalize("NFC", arabic)
            )

    for context, lang, text in substantive_prose_fields(authored):
        normalized_text = unicodedata.normalize("NFC", text)
        candidates = []
        for transliteration, arabic_values in inventory[lang].items():
            pattern = re.compile(
                rf"(?<!\w){re.escape(transliteration)}(?!\w)"
            )
            candidates.extend(
                (match.start(), match.end(), transliteration, arabic_values)
                for match in pattern.finditer(normalized_text)
            )
        selected = []
        occupied_until = -1
        for candidate in sorted(candidates, key=lambda row: (row[0], -(row[1] - row[0]))):
            if candidate[0] < occupied_until:
                continue
            selected.append(candidate)
            occupied_until = candidate[1]
        for start, end, transliteration, arabic_values in selected:
            if any(
                normalized_text[:start].endswith(arabic + " (")
                and normalized_text[end:].startswith(")")
                for arabic in arabic_values
            ):
                continue
            fail(
                f"{context} reuses known transliteration {transliteration!r} without "
                "its exact Arabic anchor in Arabic (transliteration) form"
            )


SUN_LETTER_TURKISH = {
    "ت": "t",
    "ث": "s",
    "د": "d",
    "ذ": "ẕ",
    "ر": "r",
    "ز": "z",
    "س": "s",
    "ش": "ş",
    "ص": "ṣ",
    "ض": "ḍ",
    "ط": "ṭ",
    "ظ": "ẓ",
    "ل": "l",
    "ن": "n",
}
MOON_LETTERS = set("ءاأإآبجحخعغفقكمهوي")


def initial_arabic_article_letter(value: str) -> Optional[str]:
    letters = []
    started = False
    for character in unicodedata.normalize("NFC", value):
        category = unicodedata.category(character)
        if not started and (character.isspace() or category.startswith("P")):
            continue
        started = True
        if category.startswith("M") or character == "ـ":
            continue
        if ARABIC_RE.fullmatch(character):
            letters.append(character)
            if len(letters) == 3:
                break
        elif letters:
            break
        else:
            return None
    if len(letters) == 3 and letters[0] in {"ا", "ٱ"} and letters[1] == "ل":
        return letters[2]
    return None


def transliteration_without_leading_punctuation(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).strip()
    index = 0
    while index < len(normalized) and (
        normalized[index].isspace()
        or unicodedata.category(normalized[index]).startswith("P")
    ):
        index += 1
    return normalized[index:].casefold()


def validate_turkish_definite_articles(
    pairs: list[tuple[str, str, dict[str, str], bool]]
) -> None:
    for context, arabic, overlays, article_checked in pairs:
        if not article_checked:
            continue
        article_letter = initial_arabic_article_letter(arabic)
        if article_letter is None:
            continue
        transliteration = transliteration_without_leading_punctuation(overlays["tr"])
        if article_letter in SUN_LETTER_TURKISH:
            consonant = SUN_LETTER_TURKISH[article_letter]
            expected = f"e{consonant}-{consonant}".casefold()
            description = f"assimilated Turkish article prefix {expected!r}"
        elif article_letter in MOON_LETTERS:
            expected = "el-"
            description = "Turkish moon-letter article prefix 'el-'"
        else:
            continue
        if not transliteration.startswith(expected):
            fail(f"{context}.tr must begin with {description} for Arabic {arabic!r}")


def validate_authored(
    records: list[dict[str, Any]], packet: dict[str, Any]
) -> dict[str, Any]:
    by_type: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        line = record["__line__"]
        if record.get("schema_version") != SCHEMA_VERSION:
            fail(f"line {line}: schema_version must be 1")
        record_type = record.get("type")
        if record_type not in RECORD_TYPES:
            fail(f"line {line}: unknown record type {record_type!r}")
        by_type.setdefault(record_type, []).append(record)

    external_fields = {
        "schema_version",
        "type",
        "external_source_id",
        "title",
        "url",
        "note",
        "verification",
    }
    external_sources = {}
    for record in by_type.get("external_source", []):
        context = f"external_source record on line {record['__line__']}"
        exact_fields(record, external_fields, context)
        source_id = record_key_text(record, "external_source_id", context)
        if not EXTERNAL_ID_RE.fullmatch(source_id):
            fail(f"{context}.external_source_id is not a stable authored ID")
        if source_id in external_sources:
            fail(f"duplicate external source ID {source_id!r}")
        record["title"] = bounded_bilingual_text(
            record["title"], context + ".title", minimum=2, maximum=200
        )
        record["url"] = require_text(record["url"], context + ".url")
        if any(
            character.isspace()
            or unicodedata.category(character).startswith("C")
            or character in "<>\\"
            for character in record["url"]
        ):
            fail(f"{context}.url contains unsafe Markdown URL characters")
        parsed_url = None
        try:
            parsed_url = urlparse(record["url"])
            hostname = parsed_url.hostname
        except ValueError:
            hostname = None
        if (
            parsed_url is None
            or parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
            or not hostname
        ):
            fail(f"{context}.url must be an absolute HTTP(S) URL")
        record["note"] = bilingual_text(record["note"], context + ".note")
        record["verification"] = validate_verification(
            record["verification"], context + ".verification"
        )
        external_sources[source_id] = record

    roots = by_type.get("root", [])
    if len(roots) != 1:
        fail(f"expected one root envelope record, found {len(roots)}")
    root = roots[0]
    root_required = {
        "schema_version",
        "type",
        "root_envelope_id",
        "transliteration",
        "overview",
        "quran_note",
    }
    fields_with_optional(root, root_required, {"quran_observations"}, "root record")
    if root.get("root_envelope_id") != packet["root_envelope_id"]:
        fail("root record does not match packet root_envelope_id")
    root["transliteration"] = bilingual_text(
        root["transliteration"], "root.transliteration", substantive=False
    )
    root["overview"] = bilingual_text(root["overview"], "root.overview")
    root["quran_note"] = bilingual_text(root["quran_note"], "root.quran_note")
    root["quran_observations"] = bilingual_list(
        root.get("quran_observations", {"en": [], "tr": []}),
        "root.quran_observations",
        allow_empty=True,
    )

    packet_source_refs = {
        row.get("source_ref")
        for row in packet["dictionary_sources"]
        if isinstance(row.get("source_ref"), str) and row.get("source_ref") != "-"
    }
    for branch in packet["branches"]:
        packet_source_refs.update(branch_source_handles(branch))
    branch_refs = {branch_ref(row) for row in packet["branches"]}
    allowed_evidence = packet_source_refs | branch_refs | set(external_sources)

    branch_fields = {
        "schema_version",
        "type",
        "root_id",
        "branch_id",
        "image_transliteration",
        "what_is_ar_transliteration",
        "what_is_not_ar_transliteration",
        "concept",
        "scope_in",
        "scope_out",
        "distinctions",
        "glosses",
        "target_language_note",
    }
    branches = {}
    for record in by_type.get("branch", []):
        context = f"branch record on line {record['__line__']}"
        exact_fields(record, branch_fields, context)
        key = (
            record_key_text(record, "root_id", context),
            record_key_text(record, "branch_id", context),
        )
        if key in branches:
            fail(f"duplicate branch record {key!r}")
        record["image_transliteration"] = bilingual_text(
            record["image_transliteration"],
            context + ".image_transliteration",
            substantive=False,
        )
        for field in (
            "what_is_ar_transliteration",
            "what_is_not_ar_transliteration",
        ):
            record[field] = bilingual_text(
                record[field], context + "." + field, substantive=False
            )
        record["concept"] = bilingual_text(record["concept"], context + ".concept")
        record["scope_in"] = bilingual_list(record["scope_in"], context + ".scope_in")
        record["scope_out"] = bilingual_list(record["scope_out"], context + ".scope_out")
        record["distinctions"] = validate_distinctions(
            record["distinctions"], context + ".distinctions", allowed_evidence
        )
        record["glosses"] = validate_glosses(record["glosses"], context + ".glosses")
        record["target_language_note"] = bilingual_text(
            record["target_language_note"], context + ".target_language_note"
        )
        branches[key] = record
    expected_branches = [(row["root_id"], row["branch_id"]) for row in packet["branches"]]
    assert_exact_roster("branch", list(branches), expected_branches)

    branch_source_fields = {
        "schema_version",
        "type",
        "root_id",
        "branch_id",
        "source_ref",
        "selected_quote_ar",
        "quote_transliteration",
        "relationship",
        "contribution",
        "explanation",
        "analysis",
    }
    branch_sources = {}
    packet_branches = {
        (row["root_id"], row["branch_id"]): row for row in packet["branches"]
    }
    for record in by_type.get("branch_source", []):
        context = f"branch_source record on line {record['__line__']}"
        exact_fields(record, branch_source_fields, context)
        key = (
            record_key_text(record, "root_id", context),
            record_key_text(record, "branch_id", context),
            record_key_text(record, "source_ref", context),
        )
        if key in branch_sources:
            fail(f"duplicate branch_source record {key!r}")
        branch = packet_branches.get(key[:2])
        if branch is None or key[2] not in branch_source_handles(branch):
            fail(f"{context} has a source key outside the packet branch roster")
        quote = require_text(record["selected_quote_ar"], context + ".selected_quote_ar")
        if not ARABIC_RE.search(quote):
            fail(f"{context}.selected_quote_ar must contain Arabic script")
        source_texts = [
            row.get("entry_text_clean") or ""
            for row in source_matches(packet, key[0], key[2])
        ]
        source_texts.append(branch.get("source_phrase_ar") or "")
        if not any(quote in text for text in source_texts):
            fail(f"{context}.selected_quote_ar is not an exact packet substring")
        record["selected_quote_ar"] = quote
        record["quote_transliteration"] = bilingual_text(
            record["quote_transliteration"],
            context + ".quote_transliteration",
            substantive=False,
        )
        if record.get("relationship") not in RELATIONSHIP_VALUES:
            fail(f"{context}.relationship is not allowed")
        for field in ("contribution", "explanation", "analysis"):
            record[field] = bilingual_text(record[field], context + "." + field)
        branch_sources[key] = record
    expected_branch_sources = [
        (branch["root_id"], branch["branch_id"], source_ref)
        for branch in packet["branches"]
        for source_ref in branch_source_handles(branch)
    ]
    assert_exact_roster(
        "branch_source", list(branch_sources), expected_branch_sources
    )

    lexical_fields = {
        "schema_version",
        "type",
        "root_id",
        "lexical_unit_id",
        "expression_transliteration",
        "sense_ar_transliteration",
        "source_phrase_transliteration",
    }
    lexical = {}
    for record in by_type.get("lexical", []):
        context = f"lexical record on line {record['__line__']}"
        exact_fields(record, lexical_fields, context)
        key = (
            record_key_text(record, "root_id", context),
            record_key_text(record, "lexical_unit_id", context),
        )
        if key in lexical:
            fail(f"duplicate lexical record {key!r}")
        for field in (
            "expression_transliteration",
            "sense_ar_transliteration",
            "source_phrase_transliteration",
        ):
            record[field] = bilingual_text(
                record[field], context + "." + field, substantive=False
            )
        lexical[key] = record
    expected_lexical = [
        (row["root_id"], row["lexical_unit_id"])
        for row in packet["lexical_senses"]
    ]
    assert_exact_roster("lexical", list(lexical), expected_lexical)

    branch_lexical_fields = {
        "schema_version",
        "type",
        "root_id",
        "branch_id",
        "lexical_unit_id",
        "meaning",
        "analysis",
    }
    branch_lexical = {}
    for record in by_type.get("branch_lexical", []):
        context = f"branch_lexical record on line {record['__line__']}"
        exact_fields(record, branch_lexical_fields, context)
        key = (
            record_key_text(record, "root_id", context),
            record_key_text(record, "branch_id", context),
            record_key_text(record, "lexical_unit_id", context),
        )
        if key in branch_lexical:
            fail(f"duplicate branch_lexical record {key!r}")
        record["meaning"] = bilingual_text(record["meaning"], context + ".meaning")
        record["analysis"] = bilingual_text(record["analysis"], context + ".analysis")
        branch_lexical[key] = record
    expected_branch_lexical = [
        (row["root_id"], row["branch_id"], row["lexical_unit_id"])
        for row in packet["branch_lexical_links"]
    ]
    assert_exact_roster(
        "branch_lexical", list(branch_lexical), expected_branch_lexical
    )

    quran_specs = {
        "quran_form": (
            "form_ordinal",
            [row["ordinal"] for row in form_rows(packet)],
            {"lemma_transliteration", "surface_transliteration"},
        ),
        "quran_ayah": (
            "ref",
            [row["ref"] for row in packet["qac"]["ayah_contexts"]],
            {"transliteration"},
        ),
    }
    quran_records = {}
    for record_type, (key_field, expected, overlay_fields) in quran_specs.items():
        found = {}
        allowed = {"schema_version", "type", key_field, *overlay_fields}
        for record in by_type.get(record_type, []):
            context = f"{record_type} record on line {record['__line__']}"
            exact_fields(record, allowed, context)
            if key_field == "form_ordinal":
                key = require_int(record.get(key_field), context + ".form_ordinal")
            else:
                key = record_key_text(record, key_field, context)
            if key in found:
                fail(f"duplicate {record_type} key {key!r}")
            for field in overlay_fields:
                record[field] = bilingual_text(
                    record[field], context + "." + field, substantive=False
                )
            found[key] = record
        assert_exact_roster(record_type, list(found), expected)
        quran_records[record_type] = found

    authored = {
        "root": root,
        "branches": branches,
        "branch_sources": branch_sources,
        "lexical": lexical,
        "branch_lexical": branch_lexical,
        "external_sources": external_sources,
        **quran_records,
    }
    pairs = transliteration_pairs(packet, authored)
    validate_turkish_definite_articles(pairs)
    validate_prose_transliteration_anchors(authored, pairs)
    return authored


def cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\r", " ").replace("\n", "<br>").replace("|", "\\|")


def prose(value: str) -> str:
    return " ".join(value.replace("\r", "\n").splitlines())


def display_code(
    code: Any, mapping: dict[str, dict[str, str]], lang: str, category: str
) -> str:
    value = str(code or "").strip()
    if not value:
        return "-"
    label = mapping.get(lang, {}).get(value)
    if label:
        return label
    return f"Other {category.lower()}" if lang == "en" else f"Diğer {category.lower()}"


def display_pos(code: Any, lang: str) -> str:
    category = "Part-of-speech" if lang == "en" else "Sözcük türü"
    return display_code(code, POS_DISPLAY, lang, category)


def display_measure(code: Any, lang: str) -> str:
    value = str(code or "").strip()
    if not value:
        return "-"
    return f"Form {value}" if lang == "en" else f"{value}. kalıp"


def morphology_summary(row: dict[str, Any], lang: str) -> str:
    codes = []
    for field in ("morpheme_role", "aspect", "mood", "voice"):
        value = str(row.get(field) or "").strip()
        if value:
            codes.append(value)
    raw = str(row.get("morph_features") or "")
    for token in raw.split("|"):
        token = token.strip()
        if not token or token.startswith(("LEM:", "ROOT:", "POS:")):
            continue
        if token in FEATURE_DISPLAY[lang]:
            codes.append(token)
    labels = []
    for code in codes:
        label = FEATURE_DISPLAY[lang].get(code)
        if label and label not in labels:
            labels.append(label)
    return ", ".join(labels) or ("No additional features" if lang == "en" else "Ek özellik yok")


def construction_summary(signature: Any, lang: str) -> str:
    key_labels = {
        "en": {"obj": "object", "prep": "preposition", "clause": "clause", "cognate": "cognate accusative"},
        "tr": {"obj": "nesne", "prep": "ilgeç", "clause": "tümce", "cognate": "meful-i mutlak"},
    }
    value_labels = {
        "en": {"explicit": "explicit", "clitic": "clitic", "none": "none", "none_passive": "none (passive)", "yes": "present", "no": "absent", "-": "none"},
        "tr": {"explicit": "açık", "clitic": "bitişik zamir", "none": "yok", "none_passive": "yok (edilgen)", "yes": "var", "no": "yok", "-": "yok"},
    }
    parts = []
    for item in str(signature or "").split("|"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key_label = key_labels[lang].get(key)
        if not key_label:
            continue
        if key == "prep" and value not in value_labels[lang]:
            value_label = "present" if lang == "en" else "var"
        else:
            value_label = value_labels[lang].get(
                value, "other" if lang == "en" else "diğer"
            )
        parts.append(f"{key_label}: {value_label}")
    return "; ".join(parts) or ("No summarized frame" if lang == "en" else "Özetlenmiş çerçeve yok")


def governing_summary(profile: Any, lang: str) -> str:
    relation_labels = {
        "en": {
            "direct_object": "direct object", "subject": "subject", "idafa": "genitive construction",
            "modifier": "modifier", "prep_complement": "prepositional complement", "adjective": "adjective",
            "predication": "predication", "circumstantial": "circumstantial expression", "apposition": "apposition",
            "adverbial": "adverbial", "particle_complement": "particle complement", "conjoined": "conjoined expression",
        },
        "tr": {
            "direct_object": "belirtili nesne", "subject": "özne", "idafa": "isim tamlaması",
            "modifier": "niteleyici", "prep_complement": "ilgeç tümleci", "adjective": "sıfat",
            "predication": "yüklemleme", "circumstantial": "hâl ifadesi", "apposition": "açıklayıcı öge",
            "adverbial": "zarf tümleci", "particle_complement": "edat tümleci", "conjoined": "bağlanmış ifade",
        },
    }
    parts = []
    for item in str(profile or "").split(";"):
        key, separator, count = item.partition(":")
        label = relation_labels[lang].get(key)
        if label:
            parts.append(f"{label}: {count}" if separator else label)
    return "; ".join(parts) or ("No summarized pattern" if lang == "en" else "Özetlenmiş örüntü yok")


def escape_link_label(value: str) -> str:
    escaped = prose(value).replace("\\", "\\\\")
    for character in ("`", "*", "_", "[", "]", "<", ">"):
        escaped = escaped.replace(character, "\\" + character)
    return escaped


def escape_markdown_inline(value: str) -> str:
    escaped = prose(value).replace("\\", "\\\\")
    for character in ("`", "*", "_", "[", "]", "<", ">"):
        escaped = escaped.replace(character, "\\" + character)
    return escaped


def markdown_url(value: str) -> str:
    return f"<{value}>"


def quoted(text: str) -> list[str]:
    return [f"> {line}" if line else ">" for line in text.splitlines() or [""]]


def render_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> list[str]:
    result = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    result.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return result


def skeleton_marker(kind: str, ordinal: int) -> str:
    return f"<!-- SKELETON {kind} {ordinal} -->"


def lexical_by_key(packet: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (row["root_id"], row["lexical_unit_id"]): row
        for row in packet["lexical_senses"]
    }


def dictionary_name(source_id: Any, lang: str) -> str:
    value = str(source_id or "").strip()
    if value in DICTIONARY_DISPLAY:
        return DICTIONARY_DISPLAY[value]
    return "Classical dictionary" if lang == "en" else "Klasik sözlük"


def source_names(
    packet: dict[str, Any], root_id: str, source_refs: Iterable[str], lang: str
) -> list[str]:
    names = []
    for source_ref in source_refs:
        for source in source_matches(packet, root_id, source_ref):
            name = dictionary_name(source.get("source_id"), lang)
            if name not in names:
                names.append(name)
    return names or ["Classical lexical evidence" if lang == "en" else "Klasik sözlük kanıtı"]


def lexical_source_names(
    packet: dict[str, Any], sense: dict[str, Any], lang: str
) -> str:
    refs = [ref for ref in str(sense.get("source_refs") or "").split(";") if ref]
    return ", ".join(source_names(packet, sense["root_id"], refs, lang))


def evidence_names(
    packet: dict[str, Any], authored: dict[str, Any], refs: Iterable[str], lang: str
) -> str:
    packet_branches = {branch_ref(branch): branch for branch in packet["branches"]}
    names = []
    for ref in refs:
        if ref in authored["external_sources"]:
            name = escape_markdown_inline(
                authored["external_sources"][ref]["title"][lang]
            )
        elif ref in packet_branches:
            branch = packet_branches[ref]
            editorial = authored["branches"][(branch["root_id"], branch["branch_id"])]
            name = (
                f"{branch.get('branch_image_ar', '')} "
                f"({editorial['image_transliteration'][lang]}): "
                f"{editorial['glosses'][lang][0]['text']}"
            )
        else:
            matches = [
                source
                for source in packet["dictionary_sources"]
                if source.get("source_ref") == ref
            ]
            name = (
                dictionary_name(matches[0].get("source_id"), lang)
                if matches
                else ("Classical source evidence" if lang == "en" else "Klasik kaynak kanıtı")
            )
        if name not in names:
            names.append(name)
    return "; ".join(names)


def publication_prose(
    value: str, packet: dict[str, Any], authored: dict[str, Any], lang: str
) -> str:
    """Replace canonical editorial keys and workflow terms for publication."""
    text = prose(value)
    for branch in packet["branches"]:
        key = (branch["root_id"], branch["branch_id"])
        editorial = authored["branches"][key]
        descriptor = (
            f"“{branch.get('branch_image_ar', '')} "
            f"({editorial['image_transliteration'][lang]})”"
        )
        for token in (branch_ref(branch), branch["branch_id"]):
            suffix_pattern = (
                r"(?P<suffix>'(?:deki|daki|teki|taki|ye|ya|e|a|de|da|te|ta|nin|nın|in|ın))?"
                if lang == "tr"
                else r"(?P<suffix>'s)?"
            )

            def replace_branch(match: re.Match[str]) -> str:
                if lang == "en":
                    return descriptor + ("’s" if match.group("suffix") else "")
                suffix = match.groupdict().get("suffix") or ""
                ending = {
                    "'ye": "na",
                    "'ya": "na",
                    "'e": "na",
                    "'a": "na",
                    "'deki": "ndaki",
                    "'daki": "ndaki",
                    "'teki": "ndaki",
                    "'taki": "ndaki",
                    "'de": "nda",
                    "'da": "nda",
                    "'te": "nda",
                    "'ta": "nda",
                    "'nin": "nın",
                    "'nın": "nın",
                    "'in": "nın",
                    "'ın": "nın",
                }.get(suffix, "")
                return descriptor + (" dalı" + ending if suffix else "")

            text = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(token)}{suffix_pattern}(?![A-Za-z0-9_])",
                replace_branch,
                text,
            )
    for sense in packet["lexical_senses"]:
        key = (sense["root_id"], sense["lexical_unit_id"])
        overlay = authored["lexical"][key]
        replacement = (
            f"{sense.get('expression_ar', '')} "
            f"({overlay['expression_transliteration'][lang]})"
        )
        text = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(sense['lexical_unit_id'])}(?![A-Za-z0-9_])",
            replacement,
            text,
        )
    for source in packet["dictionary_sources"]:
        source_ref = str(source.get("source_ref") or "")
        if source_ref and source_ref != "-":
            text = text.replace(
                source_ref, dictionary_name(source.get("source_id"), lang)
            )
    for root_id in {row["root_id"] for row in packet["v4_roots"]}:
        replacement = (
            f"the {packet['root_norm']} root"
            if lang == "en"
            else f"{packet['root_norm']} kökü"
        )
        text = text.replace(root_id, replacement)
    substitutions = {
        "en": (
            (r"\broot envelope\b", "root entry"),
            (r"\bsource roster\b", "source evidence"),
            (r"\bsource record\b", "lexicographic evidence"),
            (r"\bsource[- ]audited\b", "source-supported"),
            (r"\baudit(?:ed|ing)?\b", "source review"),
            (r"\brouted source(?: phrase)?s?\b", "matched source evidence"),
            (r"\brouted\b", "matched"),
            (r"\bfrozen\b", "established"),
            (r"\bpacket's\b", "sources'"),
            (r"\bpacket\b", "sources"),
        ),
        "tr": (
            (r"\bkök zarfındaki\b", "kök maddesindeki"),
            (r"\bkök zarfı\b", "kök maddesi"),
            (r"\bkaynak döküm(?:ü|üdür)?\b", "sözlük kanıtları"),
            (r"\bkaynak denetimi\b", "kaynak incelemesi"),
            (r"\bdenetim\b", "kaynak incelemesi"),
            (r"\byönlendirilmiş kaynak(?: sözleri| ifadeleri)?\b", "eşleşen kaynak kanıtı"),
            (r"\byönlendirilmiş\b", "eşleşen"),
            (r"\bdondurulmuş\b", "yerleşik"),
            (r"\bdonmuş\b", "kalıplaşmış"),
            (r"\bpaketler\b", "birleştirir"),
            (r"\bpaketteki\b", "kaynaklardaki"),
            (r"\bpakette\b", "kaynaklarda"),
            (r"\bpaketin\b", "kaynak derleminin"),
            (r"\bpaket\b", "kaynak derlemi"),
        ),
    }
    for pattern, replacement in substitutions[lang]:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    if lang == "tr":
        text = text.replace(". kaynaklarda", ". Kaynaklarda")
        text = text.replace("- kaynaklarda", "- Kaynaklarda")
    return text


def attachment_evidence(
    packet: dict[str, Any], occurrence: dict[str, Any], lang: str
) -> str:
    word_unit_id = (
        f"q:{occurrence.get('surah')}:{occurrence.get('ayah')}:"
        f"{occurrence.get('word_index')}"
    )
    instance_labels = {
        "en": {"verb_instances": "Verb construction", "noun_instances": "Noun construction"},
        "tr": {"verb_instances": "Fiil yapısı", "noun_instances": "İsim yapısı"},
    }
    relation_labels = {
        "en": {
            "direct_object": "direct object",
            "subject": "subject",
            "idafa": "genitive construction",
            "modifier": "modifier",
            "prep_complement": "prepositional complement",
        },
        "tr": {
            "direct_object": "belirtili nesne",
            "subject": "özne",
            "idafa": "isim tamlaması",
            "modifier": "niteleyici",
            "prep_complement": "ilgeç tümleci",
        },
    }
    attachment_rows = {
        str(row.get("unit_id")): row
        for row in packet["attachments"].get("attachments", [])
        if row.get("unit_id")
    }
    labels = []
    for category in ("verb_instances", "noun_instances"):
        for instance in packet["attachments"].get(category, []):
            if instance.get("word_unit_id") != word_unit_id:
                continue
            if instance_labels[lang][category] not in labels:
                labels.append(instance_labels[lang][category])
            for key, value in instance.items():
                if (key.endswith("attachment_id") or key.endswith("attachment_ids")) and value:
                    for attachment_id in re.split(r"[;,]", str(value)):
                        attachment = attachment_rows.get(attachment_id.strip())
                        relation = relation_labels[lang].get(
                            str((attachment or {}).get("relation") or "")
                        )
                        if relation and relation not in labels:
                            labels.append(relation)
    if labels:
        return "; ".join(labels)
    return "No linked construction" if lang == "en" else "Bağlı yapı yok"


def readable_qac_ref(value: Any, lang: str) -> str:
    parts = str(value or "").split(":")
    if len(parts) == 4 and all(part.isdigit() for part in parts):
        surah, ayah, word, segment = parts
        if lang == "en":
            return f"{surah}:{ayah}, word {word}, segment {segment}"
        return f"{surah}:{ayah}, {word}. kelime, {segment}. parça"
    return "Corpus location" if lang == "en" else "Derlem konumu"


def readable_sample_refs(value: Any, lang: str) -> str:
    result = []
    for ref in str(value or "").split(";"):
        parts = ref.split(":")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            surah, ayah, word = parts
            result.append(
                f"{surah}:{ayah}, word {word}"
                if lang == "en"
                else f"{surah}:{ayah}, {word}. kelime"
            )
    return "; ".join(result) or ("No sample" if lang == "en" else "Örnek yok")


def aggregate_rows(
    rows: list[dict[str, Any]], kind: str, lang: str
) -> list[tuple[Any, ...]]:
    if kind == "verb":
        return [
            (
                display_code(row.get("form_tag"), FORM_TAG_DISPLAY, lang, "Form" if lang == "en" else "Biçim"),
                construction_summary(row.get("frame_signature"), lang),
                row.get("instance_count", ""),
                readable_sample_refs(row.get("sample_refs"), lang),
            )
            for row in rows
        ]
    return [
        (
            display_code(row.get("form_tag"), FORM_TAG_DISPLAY, lang, "Form" if lang == "en" else "Biçim"),
            governing_summary(row.get("governing_relation_profile"), lang),
            row.get("instance_count", ""),
            readable_sample_refs(row.get("sample_refs"), lang),
        )
        for row in rows
    ]


def render_entry(packet: dict[str, Any], authored: dict[str, Any], lang: str) -> str:
    labels = LABELS[lang]
    root = authored["root"]
    publish = lambda value: publication_prose(value, packet, authored, lang)
    lines = [
        GENERATED_MARKER,
        f"<!-- authored-entry-schema: {SCHEMA_VERSION}; language: {lang}; root: {packet['root_envelope_id']} -->",
        f"# {labels['title']} {packet['root_norm']} ({root['transliteration'][lang]})",
        "",
        publish(root["overview"][lang]),
        "",
        f"## {labels['overview']}",
        "",
    ]
    overview_rows = []
    for branch in packet["branches"]:
        key = (branch["root_id"], branch["branch_id"])
        editorial = authored["branches"][key]
        overview_rows.append(
            (
                f"{branch.get('branch_image_ar', '')} ({editorial['image_transliteration'][lang]})",
                publish(editorial["glosses"][lang][0]["text"]),
            )
        )
    lines += render_table(
        [labels["arabic_image"], labels["primary"]],
        overview_rows,
    )

    senses = lexical_by_key(packet)
    source_ordinal = 0
    link_ordinal = 0
    for branch_ordinal, branch in enumerate(packet["branches"], start=1):
        lines += ["", skeleton_marker("BRANCH", branch_ordinal)]
        key = (branch["root_id"], branch["branch_id"])
        editorial = authored["branches"][key]
        primary = publish(editorial["glosses"][lang][0]["text"])
        lines += [
            f"## {branch.get('branch_image_ar', '')} "
            f"({editorial['image_transliteration'][lang]}): {primary}",
            "",
            f"**{labels['primary']}: {primary}**",
            "",
            f"### {labels['concept']}",
            "",
            publish(editorial["concept"][lang]),
            "",
            f"### {labels['scope']}",
            "",
            f"**{labels['includes']}**",
            "",
        ]
        lines += [f"- {publish(item)}" for item in editorial["scope_in"][lang]]
        lines += ["", f"**{labels['excludes']}**", ""]
        lines += [f"- {publish(item)}" for item in editorial["scope_out"][lang]]
        lines += [
            "",
            f"#### {labels['boundaries']}",
            "",
            f"- {branch.get('what_is_ar', '')} "
            f"({editorial['what_is_ar_transliteration'][lang]})",
            f"- {branch.get('what_is_not_ar', '')} "
            f"({editorial['what_is_not_ar_transliteration'][lang]})",
            "",
            f"### {labels['lexical']}",
            "",
        ]
        for link in packet["branch_lexical_links"]:
            if (link["root_id"], link["branch_id"]) != key:
                continue
            link_ordinal += 1
            lines.append(skeleton_marker("BRANCH_LEXICAL", link_ordinal))
            lexical_key = (link["root_id"], link["lexical_unit_id"])
            sense = senses[lexical_key]
            lexical_editorial = authored["lexical"][lexical_key]
            link_key = key + (link["lexical_unit_id"],)
            link_editorial = authored["branch_lexical"][link_key]
            lines += [
                f"#### {sense.get('expression_ar', '')} "
                f"({lexical_editorial['expression_transliteration'][lang]})",
                "",
                f"- **{labels['kind']}:** "
                f"{display_code(sense.get('unit_kind'), UNIT_KIND_DISPLAY, lang, 'unit' if lang == 'en' else 'birim')}",
                f"- **{labels['v4_sense']}:** {sense.get('sense_ar', '')} "
                f"({lexical_editorial['sense_ar_transliteration'][lang]})",
                f"- **{labels['meaning']}:** {publish(link_editorial['meaning'][lang])}",
                f"- **{labels['analysis']}:** {publish(link_editorial['analysis'][lang])}",
                f"- **{labels['source_phrase']}:** {sense.get('source_phrase_ar', '')} "
                f"({lexical_editorial['source_phrase_transliteration'][lang]})",
                f"- **{labels['source_id']}:** {lexical_source_names(packet, sense, lang)}",
                "",
            ]
        lines += ["", f"### {labels['distinctions']}", ""]
        for row in editorial["distinctions"]:
            lines += [
                f"#### {row['neighbor_ar']} ({row['transliteration'][lang]})",
                "",
                f"- **{labels['shared_zone']}:** {publish(row['shared_zone'][lang])}",
                f"- **{labels['distinction']}:** {publish(row['distinction'][lang])}",
                f"- **{labels['evidence']}:** "
                f"{evidence_names(packet, authored, row['evidence'], lang)}",
                "",
            ]
        lines += ["", f"### {labels['glosses']}", ""]
        for row in editorial["glosses"][lang]:
            lines += [
                f"#### {publish(row['text'])}",
                "",
                f"- **{labels['role']}:** {ROLE_DISPLAY[lang][row['role']]}",
                f"- **{labels['preserves']}:** {publish(row['preserves'])}",
                f"- **{labels['loses']}:** {publish(row['loses'])}",
                f"- **{labels['adds']}:** {publish(row['adds'])}",
                f"- **{labels['fit']}:** {FIT_DISPLAY[lang][row['fit']]}",
                f"- **{labels['collision']}:** {publish(row['collision'])}",
                "",
            ]
        lines += ["", f"### {labels['audits']}", ""]
        for source_ref in branch_source_handles(branch):
            source_ordinal += 1
            lines.append(skeleton_marker("BRANCH_SOURCE", source_ordinal))
            source_key = key + (source_ref,)
            source_editorial = authored["branch_sources"][source_key]
            matches = source_matches(packet, branch["root_id"], source_ref)
            source_title = dictionary_name(
                matches[0].get("source_id") if matches else "", lang
            )
            lines += [
                f"#### {source_title}",
                "",
                f"- {labels['relationship']}: "
                f"{RELATIONSHIP_DISPLAY[lang][source_editorial['relationship']]}",
                "",
                f"**{labels['selected_quote']}**",
                "",
            ]
            lines += quoted(source_editorial["selected_quote_ar"])
            lines += [
                "",
                f"{labels['transliteration']}: "
                f"{source_editorial['quote_transliteration'][lang]}",
                "",
                f"**{labels['contribution']}:** "
                f"{publish(source_editorial['contribution'][lang])}",
                "",
                f"**{labels['explanation']}:** "
                f"{publish(source_editorial['explanation'][lang])}",
                "",
                f"**{labels['source_analysis']}:** "
                f"{publish(source_editorial['analysis'][lang])}",
                "",
            ]
        lines += [
            f"### {labels['note']}",
            "",
            publish(editorial["target_language_note"][lang]),
        ]

    summary = packet["qac"]["summary"]
    lines += [
        "",
        f"## {labels['quran']}",
        "",
        publish(root["quran_note"][lang]),
        "",
        f"### {labels['census']}",
        "",
        f"- {labels['morphemes']}: {summary.get('morpheme_count', len(packet['qac']['occurrences']))}",
        f"- {labels['words']}: {summary.get('word_count', '')}",
        f"- {labels['ayah_count']}: {summary.get('ayah_count', len(packet['qac']['ayah_contexts']))}",
        f"- {labels['surahs']}: {summary.get('surah_count', '')}",
        "",
        f"### {labels['forms']}",
        "",
    ]
    form_table = []
    for form in form_rows(packet):
        lines.append(skeleton_marker("QURAN_FORM", form["ordinal"]))
        overlay = authored["quran_form"][form["ordinal"]]
        form_table.append(
            (
                f"{form['lemma_ar']} ({overlay['lemma_transliteration'][lang]}) / "
                f"{form['surface_ar']} ({overlay['surface_transliteration'][lang]})",
                display_pos(form["pos"], lang),
                morphology_summary(form["representative"], lang),
                form["count"],
                "; ".join(readable_qac_ref(ref, lang) for ref in form["qac_refs"]),
            )
        )
    lines += render_table(
        [
            labels["lemma_surface"],
            labels["pos"],
            labels["morphology"],
            labels["count"],
            labels["qac_refs"],
        ],
        form_table,
    )
    lines += ["", f"### {labels['occurrences']}", ""]
    occurrence_table = []
    form_ordinals = occurrence_form_ordinals(packet)
    for ordinal, occurrence in enumerate(packet["qac"]["occurrences"], start=1):
        lines.append(skeleton_marker("QURAN_OCCURRENCE", ordinal))
        form_ordinal = form_ordinals[occurrence["qac_ref"]]
        overlay = authored["quran_form"][form_ordinal]
        occurrence_table.append(
            (
                readable_qac_ref(occurrence["qac_ref"], lang),
                f"{occurrence.get('surface_ar', '')} "
                f"({overlay['surface_transliteration'][lang]})",
                display_pos(occurrence.get("pos"), lang),
                display_measure(occurrence.get("measure"), lang),
                morphology_summary(occurrence, lang),
                f"{occurrence.get('surah')}:{occurrence.get('ayah')}",
                attachment_evidence(packet, occurrence, lang),
            )
        )
    lines += render_table(
        [
            labels["qac_ref"],
            labels["surface"],
            labels["pos"],
            labels["measure"],
            labels["morphology"],
            labels["ayah"],
            labels["attachment_handles"],
        ],
        occurrence_table,
    )
    lines += ["", f"### {labels['constructions']}", ""]
    verb_frames = packet["attachments"].get("verb_valency_frames", [])
    noun_patterns = packet["attachments"].get("noun_governing_patterns", [])
    lines += [f"#### {labels['verb_frames']}", ""]
    lines += render_table(
        [labels["kind"], labels["frame"], labels["instances"], labels["samples"]],
        aggregate_rows(verb_frames, "verb", lang),
    ) if verb_frames else [f"- {labels['none']}"]
    lines += ["", f"#### {labels['noun_patterns']}", ""]
    lines += render_table(
        [labels["kind"], labels["frame"], labels["instances"], labels["samples"]],
        aggregate_rows(noun_patterns, "noun", lang),
    ) if noun_patterns else [f"- {labels['none']}"]
    observations = root["quran_observations"][lang]
    if any(root["quran_observations"][item] for item in LANGUAGES):
        lines += ["", f"### {labels['quran_observations']}", ""]
        lines += (
            [f"- {publish(item)}" for item in observations]
            if observations
            else [f"- {labels['none']}"]
        )
    lines += ["", f"### {labels['ayahs']}", ""]
    for ordinal, ayah in enumerate(packet["qac"]["ayah_contexts"], start=1):
        lines += [skeleton_marker("QURAN_AYAH", ordinal), f"#### {ayah['ref']}", ""]
        lines += quoted(str(ayah.get("surface_ar", "")))
        lines += [
            "",
            f"{labels['transliteration']}: "
            f"{authored['quran_ayah'][ayah['ref']]['transliteration'][lang]}",
            "",
        ]

    lines += [f"## {labels['bibliography']}", "", f"### {labels['external']}", ""]
    for ordinal, source_id in enumerate(sorted(authored["external_sources"]), start=1):
        source = authored["external_sources"][source_id]
        verification = source["verification"]
        lines += [
            skeleton_marker("EXTERNAL_SOURCE", ordinal),
            f"- [{escape_link_label(source['title'][lang])}]({markdown_url(source['url'])}) - "
            f"{escape_markdown_inline(publish(source['note'][lang]))}",
            f"  - **{labels['accessed_on']}:** {verification['accessed_on']}",
            f"  - **{labels['source_language']}:** "
            f"{SOURCE_LANGUAGE_DISPLAY[lang][verification['source_language']]}",
            f"  - **{labels['locator']}:** "
            f"{escape_markdown_inline(verification['locator'][lang])}",
            f"  - **{labels['verified_excerpt']}:** "
            f"{escape_markdown_inline(verification['excerpt'])}",
        ]
        if verification["source_language"] == "ar":
            lines.append(
                f"  - **{labels['transliteration']}:** "
                f"{escape_markdown_inline(verification['excerpt_transliteration'][lang])}"
            )
    if not authored["external_sources"]:
        lines.append(f"- {labels['none']}")
    return "\n".join(lines).rstrip() + "\n"


def output_paths(output_dir: Path, root_id: str) -> dict[str, Path]:
    return {lang: output_dir / lang / f"{root_id}.md" for lang in LANGUAGES}


def has_marker(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return GENERATED_MARKER in "".join(handle.readline() for _ in range(4))
    except (OSError, UnicodeError):
        return False


def reject_output_symlinks(output_dir: Path, paths: dict[str, Path]) -> None:
    candidates = [output_dir]
    candidates.extend(path.parent for path in paths.values())
    candidates.extend(paths.values())
    for path in candidates:
        if path.is_symlink():
            fail(f"refusing symlinked output path {path}")


def stage_file(path: Path, content: str) -> Path:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.stage-", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return temporary_path


def unused_backup_path(path: Path) -> Path:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.backup-", dir=path.parent)
    os.close(descriptor)
    temporary_path = Path(temporary)
    temporary_path.unlink()
    return temporary_path


def write_pair(paths: dict[str, Path], rendered: dict[str, str]) -> None:
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    reject_output_symlinks(next(iter(paths.values())).parent.parent, paths)

    stages: dict[str, Path] = {}
    backups: dict[str, Path] = {}
    installed: list[str] = []
    success = False
    try:
        for lang in LANGUAGES:
            stages[lang] = stage_file(paths[lang], rendered[lang])
        for lang in LANGUAGES:
            path = paths[lang]
            if path.exists():
                backup = unused_backup_path(path)
                os.replace(path, backup)
                backups[lang] = backup
        for lang in LANGUAGES:
            os.replace(stages[lang], paths[lang])
            installed.append(lang)
        success = True
    except BaseException as exc:
        rollback_errors = []
        for lang in reversed(installed):
            try:
                paths[lang].unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        for lang in LANGUAGES:
            backup = backups.get(lang)
            if backup is not None and backup.exists():
                try:
                    os.replace(backup, paths[lang])
                except OSError as rollback_exc:
                    rollback_errors.append(str(rollback_exc))
        detail = f"pair write failed: {exc}"
        if rollback_errors:
            detail += "; rollback errors: " + "; ".join(rollback_errors)
        fail(detail)
    finally:
        for temporary in stages.values():
            temporary.unlink(missing_ok=True)
        if success:
            for backup in backups.values():
                backup.unlink(missing_ok=True)


def execute(
    source: Path,
    packet_path: Path,
    output_dir: Path,
    check: bool = False,
    force: bool = False,
) -> dict[str, Path]:
    if check and force:
        fail("--check and --force cannot be combined")
    packet = validate_packet(load_json(packet_path))
    authored = validate_authored(load_jsonl(source), packet)
    paths = output_paths(output_dir, packet["root_envelope_id"])
    rendered = {lang: render_entry(packet, authored, lang) for lang in LANGUAGES}
    reject_output_symlinks(output_dir, paths)

    if check:
        problems = []
        for lang in LANGUAGES:
            path = paths[lang]
            if not path.is_file():
                problems.append(f"missing output {path}")
                continue
            try:
                current = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                problems.append(f"cannot read output {path}: {exc}")
                continue
            if current != rendered[lang]:
                problems.append(f"stale output {path}")
        if problems:
            fail("; ".join(problems))
        return paths

    existing = [path for path in paths.values() if path.exists()]
    if existing and not force:
        fail(
            "output exists; use --force only for renderer-owned files: "
            + ", ".join(map(str, existing))
        )
    unowned = [path for path in existing if not path.is_file() or not has_marker(path)]
    if unowned:
        fail("refusing to replace unmarked output: " + ", ".join(map(str, unowned)))
    write_pair(paths, rendered)
    return paths


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, metavar="SOURCE.jsonl")
    parser.add_argument("--packet", required=True, type=Path, metavar="PACKET.json")
    parser.add_argument("--output-dir", required=True, type=Path, metavar="entries")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        paths = execute(args.source, args.packet, args.output_dir, args.check, args.force)
    except ContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    action = "checked" if args.check else "wrote"
    for lang in LANGUAGES:
        print(f"{action} {paths[lang]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
