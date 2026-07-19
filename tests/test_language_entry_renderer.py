import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.render_language_entries import ContractError, execute, form_rows


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts/render_language_entries.py"
BRANCH_STEMS = {"B001": "FIRST", "B002": "SECOND"}
LEXICAL_STEMS = {"lu_001": "LEXICAL_ONE", "lu_002": "LEXICAL_TWO"}


def bilingual(stem):
    return {"en": f"EN_SENTINEL_{stem}", "tr": f"TR_SENTINEL_{stem}"}


def packet_fixture():
    occurrences = [
        {
            "qac_ref": "1:1:1:1",
            "qac_word_ref": "1:1:1",
            "surah": 1,
            "ayah": 1,
            "word_index": 1,
            "morpheme_index": 1,
            "surface_ar": "كَتَبَ",
            "lemma_ar": "كَتَبَ",
            "pos": "V",
            "measure": "I",
            "morpheme_role": "STEM",
            "aspect": "PERF",
            "mood": "",
            "voice": "ACT",
            "morph_features": "STEM|POS:V|LEM:PACKET_BUCKWALTER_LEM|ROOT:PACKET_BUCKWALTER_ROOT|M|S",
        },
        {
            "qac_ref": "1:2:2:1",
            "qac_word_ref": "1:2:2",
            "surah": 1,
            "ayah": 2,
            "word_index": 2,
            "morpheme_index": 1,
            "surface_ar": "كَتَبَ",
            "lemma_ar": "كَتَبَ",
            "pos": "V",
            "measure": "I",
            "morpheme_role": "STEM",
            "aspect": "PERF",
            "mood": "",
            "voice": "ACT",
            "morph_features": "STEM|POS:V|LEM:PACKET_BUCKWALTER_LEM|ROOT:PACKET_BUCKWALTER_ROOT|M|S",
        },
        {
            "qac_ref": "1:2:3:1",
            "qac_word_ref": "1:2:3",
            "surah": 1,
            "ayah": 2,
            "word_index": 3,
            "morpheme_index": 1,
            "surface_ar": "كِتَابٌ",
            "lemma_ar": "كِتَاب",
            "pos": "N",
            "measure": "",
            "morpheme_role": "STEM",
            "aspect": "",
            "mood": "",
            "voice": "",
            "morph_features": "STEM|POS:N|LEM:PACKET_BUCKWALTER_NOUN|ROOT:PACKET_BUCKWALTER_ROOT|NOM|S",
        },
    ]
    return {
        "root_envelope_id": "root_000001",
        "root_join_key": "كتب",
        "root_norm": "ك ت ب",
        "v4_roots": [{"root_id": "root_000001", "source_root_norm": "ك ت ب"}],
        "branches": [
            {
                "root_id": "root_000001",
                "branch_id": "B001",
                "branch_image_ar": "جمع الحروف",
                "branch_image_en": "PACKET_ENGLISH_BRANCH_IMAGE",
                "what_is_ar": "يدخل فيه نقش الحروف",
                "what_is_not_ar": "لا يدخل فيه الجمع المطلق",
                "source_refs": "source:file=x:section=one;source:file=x:section=shared",
                "source_phrase_ar": "كتب الكتاب",
                "review_note": "PACKET_ENGLISH_BRANCH_REVIEW",
            },
            {
                "root_id": "root_000001",
                "branch_id": "B002",
                "branch_image_ar": "فرض الشيء",
                "branch_image_en": "PACKET_ENGLISH_SECOND_IMAGE",
                "what_is_ar": "يدخل فيه الفرض",
                "what_is_not_ar": "لا يدخل فيه الخط وحده",
                "source_refs": "source:file=x:section=two",
                "source_phrase_ar": "كتب عليه",
                "review_note": "PACKET_ENGLISH_SECOND_REVIEW",
            },
        ],
        "dictionary_sources": [
            {
                "root_id": "root_000001",
                "source_id": "source",
                "source_ref": "source:file=x:section=one",
                "headword": "كتب",
                "entry_text_clean": "مقدمة كتب الكتاب خاتمة",
                "route_status": "exact",
                "route_note": "PACKET_ENGLISH_ROUTE_ONE",
            },
            {
                "root_id": "root_000001",
                "source_id": "source",
                "source_ref": "source:file=x:section=shared",
                "headword": "كتب",
                "entry_text_clean": "بداية كتب نهاية",
                "route_status": "variant",
                "route_note": "PACKET_ENGLISH_ROUTE_SHARED",
            },
            {
                "root_id": "root_000001",
                "source_id": "source",
                "source_ref": "source:file=x:section=two",
                "headword": "كتب",
                "entry_text_clean": "مقدمة كتب عليه خاتمة",
                "route_status": "exact",
                "route_note": "PACKET_ENGLISH_ROUTE_TWO",
            },
            {
                "root_id": "root_000001",
                "source_id": "ayn",
                "source_ref": "-",
                "headword": "كتب",
                "entry_text_clean": "مرجع غير موجّه",
                "route_status": "no_match",
                "route_note": "PACKET_ENGLISH_UNROUTED",
            },
        ],
        "lexical_senses": [
            {
                "root_id": "root_000001",
                "lexical_unit_id": "lu_001",
                "expression_ar": "كَتَبَ",
                "unit_kind": "form",
                "sense_ar": "نقش الحروف",
                "sense_en": "PACKET_ENGLISH_LEXICAL_SENSE",
                "source_refs": "source:file=x:section=one",
                "source_phrase_ar": "كتب الكتاب",
            },
            {
                "root_id": "root_000001",
                "lexical_unit_id": "lu_002",
                "expression_ar": "كُتِبَ عَلَيْهِ",
                "unit_kind": "construction",
                "sense_ar": "فرض عليه",
                "sense_en": "PACKET_ENGLISH_SECOND_SENSE",
                "source_refs": "source:file=x:section=two",
                "source_phrase_ar": "كتب عليه",
            },
        ],
        "branch_lexical_links": [
            {"root_id": "root_000001", "branch_id": "B001", "lexical_unit_id": "lu_001"},
            {"root_id": "root_000001", "branch_id": "B002", "lexical_unit_id": "lu_001"},
            {"root_id": "root_000001", "branch_id": "B002", "lexical_unit_id": "lu_002"},
        ],
        "qac": {
            "summary": {
                "morpheme_count": 3,
                "word_count": 3,
                "ayah_count": 2,
                "surah_count": 1,
            },
            "occurrences": occurrences,
            "ayah_contexts": [
                {"ref": "1:1", "surah": 1, "ayah": 1, "surface_ar": "كَتَبَ", "words": []},
                {"ref": "1:2", "surah": 1, "ayah": 2, "surface_ar": "هُوَ كَتَبَ كِتَابٌ", "words": []},
            ],
        },
        "attachments": {
            "verb_instances": [
                {
                    "unit_id": "verb:1:2:2",
                    "word_unit_id": "q:1:2:2",
                    "object_attachment_ids": "attachment:1",
                    "grammar": "PACKET_ENGLISH_VERB_GRAMMAR",
                }
            ],
            "noun_instances": [
                {
                    "unit_id": "noun:1:2:3",
                    "word_unit_id": "q:1:2:3",
                    "grammar": "PACKET_ENGLISH_NOUN_GRAMMAR",
                }
            ],
            "attachments": [
                {
                    "unit_id": "attachment:1",
                    "relation": "direct_object",
                    "reason": "PACKET_ENGLISH_ATTACHMENT_REASON",
                }
            ],
            "verb_valency_frames": [
                {
                    "stem": "كتب",
                    "form_tag": "PV",
                    "frame_signature": "obj=explicit",
                    "instance_count": "1",
                    "sample_refs": "1:2:2",
                    "object_status_profile": "explicit:1",
                    "notes": "PACKET_ENGLISH_FRAME_NOTE",
                }
            ],
            "noun_governing_patterns": [
                {
                    "stem": "كتاب",
                    "form_tag": "NOUN",
                    "governing_relation_profile": "idafa:1",
                    "instance_count": "1",
                    "sample_refs": "1:2:3",
                    "notes": "PACKET_ENGLISH_NOUN_NOTE",
                }
            ],
        },
    }


def gloss_rows(stem):
    result = {}
    for lang, prefix in (("en", "EN_SENTINEL"), ("tr", "TR_SENTINEL")):
        result[lang] = [
            {
                "text": f"{prefix}_{stem}_PRIMARY",
                "role": "primary",
                "preserves": f"{prefix}_{stem}_PRESERVES",
                "loses": f"{prefix}_{stem}_LOSES",
                "adds": f"{prefix}_{stem}_ADDS",
                "fit": "none",
                "collision": f"{prefix}_{stem}_COLLISION",
            },
            {
                "text": f"{prefix}_{stem}_ALTERNATIVE",
                "role": "alternative",
                "preserves": f"{prefix}_{stem}_ALT_PRESERVES",
                "loses": f"{prefix}_{stem}_ALT_LOSES",
                "adds": f"{prefix}_{stem}_ALT_ADDS",
                "fit": "narrowing",
                "collision": f"{prefix}_{stem}_ALT_COLLISION",
            },
        ]
    return result


def authored_fixture(packet):
    records = [
        {
            "schema_version": 1,
            "type": "root",
            "root_envelope_id": packet["root_envelope_id"],
            "transliteration": bilingual("ROOT_TRANSLIT"),
            "overview": {
                "en": "EN_SENTINEL_ROOT_OVERVIEW for a root envelope packet source roster.",
                "tr": "TR_SENTINEL_ROOT_OVERVIEW bir kök zarfı ve paket kaynak dökümüdür.",
            },
            "quran_note": bilingual("QURAN_NOTE"),
            "quran_observations": {
                "en": ["EN_SENTINEL_QURAN_OBSERVATION"],
                "tr": ["TR_SENTINEL_QURAN_OBSERVATION"],
            },
        },
        {
            "schema_version": 1,
            "type": "external_source",
            "external_source_id": "usage.dictionary",
            "title": {
                "en": "EN_SENTINEL_USAGE_DICTIONARY",
                "tr": "TR_SENTINEL_KULLANIM_SOZLUGU",
            },
            "url": "https://example.org/usage",
            "note": bilingual("EXTERNAL_NOTE"),
            "verification": {
                "accessed_on": "2026-07-17",
                "source_language": "en",
                "locator": {
                    "en": "EN_SENTINEL_HEADWORD_WRITE",
                    "tr": "TR_SENTINEL_YAZMA_MADDESI",
                },
                "excerpt": "to form letters or words on a surface",
            },
        },
    ]
    for branch in packet["branches"]:
        stem = BRANCH_STEMS[branch["branch_id"]]
        records.append(
            {
                "schema_version": 1,
                "type": "branch",
                "root_id": branch["root_id"],
                "branch_id": branch["branch_id"],
                "image_transliteration": bilingual(stem + "_IMAGE"),
                "what_is_ar_transliteration": bilingual(stem + "_WHAT_IS"),
                "what_is_not_ar_transliteration": bilingual(stem + "_WHAT_IS_NOT"),
                "concept": {
                    "en": (
                        f"EN_SENTINEL_{stem}_CONCEPT compares B001 with "
                        "root_000001/B002 and lu_001 using "
                        "source:file=x:section=one in a source-audited packet "
                        "with routed source phrases."
                    ),
                    "tr": (
                        f"TR_SENTINEL_{stem}_CONCEPT B001 ile "
                        "root_000001/B002 ve lu_001 öğelerini "
                        "source:file=x:section=one için paketteki "
                        "yönlendirilmiş kaynak sözleriyle karşılaştırır."
                    ),
                },
                "scope_in": {"en": [f"EN_SENTINEL_{stem}_IN"], "tr": [f"TR_SENTINEL_{stem}_IN"]},
                "scope_out": {"en": [f"EN_SENTINEL_{stem}_OUT"], "tr": [f"TR_SENTINEL_{stem}_OUT"]},
                "distinctions": [
                    {
                        "neighbor_ar": "جَمَعَ",
                        "transliteration": bilingual(stem + "_NEIGHBOR"),
                        "shared_zone": bilingual(stem + "_SHARED"),
                        "distinction": bilingual(stem + "_DISTINCTION"),
                        "evidence": [branch["source_refs"].split(";")[0], "usage.dictionary"],
                    }
                ],
                "glosses": gloss_rows(stem),
                "target_language_note": bilingual(stem + "_NOTE"),
            }
        )
        quote_by_ref = {
            "source:file=x:section=one": "كتب الكتاب",
            "source:file=x:section=shared": "كتب",
            "source:file=x:section=two": "كتب عليه",
        }
        for source_ref in branch["source_refs"].split(";"):
            source_stem = source_ref.rsplit("=", 1)[-1].upper()
            records.append(
                {
                    "schema_version": 1,
                    "type": "branch_source",
                    "root_id": branch["root_id"],
                    "branch_id": branch["branch_id"],
                    "source_ref": source_ref,
                    "selected_quote_ar": quote_by_ref[source_ref],
                    "quote_transliteration": bilingual(f"SOURCE_{source_stem}_QUOTE"),
                    "relationship": "explicit_support",
                    "contribution": bilingual(f"SOURCE_{source_stem}_CONTRIBUTION"),
                    "explanation": bilingual(f"SOURCE_{source_stem}_EXPLANATION"),
                    "analysis": bilingual(f"SOURCE_{source_stem}_ANALYSIS"),
                }
            )
    for lexical in packet["lexical_senses"]:
        stem = LEXICAL_STEMS[lexical["lexical_unit_id"]]
        records.append(
            {
                "schema_version": 1,
                "type": "lexical",
                "root_id": lexical["root_id"],
                "lexical_unit_id": lexical["lexical_unit_id"],
                "expression_transliteration": bilingual(stem + "_EXPRESSION"),
                "sense_ar_transliteration": bilingual(stem + "_SENSE"),
                "source_phrase_transliteration": bilingual(stem + "_SOURCE_PHRASE"),
            }
        )
    for link in packet["branch_lexical_links"]:
        stem = (
            f"{BRANCH_STEMS[link['branch_id']]}_"
            f"{LEXICAL_STEMS[link['lexical_unit_id']]}"
        )
        records.append(
            {
                "schema_version": 1,
                "type": "branch_lexical",
                "root_id": link["root_id"],
                "branch_id": link["branch_id"],
                "lexical_unit_id": link["lexical_unit_id"],
                "meaning": bilingual(stem + "_MEANING"),
                "analysis": bilingual(stem + "_ANALYSIS"),
            }
        )
    for form in form_rows(packet):
        records.append(
            {
                "schema_version": 1,
                "type": "quran_form",
                "form_ordinal": form["ordinal"],
                "lemma_transliteration": bilingual(
                    f"FORM_{form['ordinal']}_LEMMA"
                ),
                "surface_transliteration": bilingual(
                    f"FORM_{form['ordinal']}_SURFACE"
                ),
            }
        )
    for ayah in packet["qac"]["ayah_contexts"]:
        stem = ayah["ref"].replace(":", "_")
        records.append(
            {
                "schema_version": 1,
                "type": "quran_ayah",
                "ref": ayah["ref"],
                "transliteration": bilingual(stem + "_AYAH"),
            }
        )
    return records


class LanguageEntryRendererTest(unittest.TestCase):
    def setUp(self):
        self.packet = packet_fixture()
        self.records = authored_fixture(self.packet)

    def write_fixture(self, directory, records=None, packet=None):
        root = Path(directory)
        packet_path = root / "packet.json"
        source_path = root / "authored.jsonl"
        packet_path.write_text(json.dumps(packet or self.packet, ensure_ascii=False), encoding="utf-8")
        source_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in (records if records is not None else self.records)) + "\n",
            encoding="utf-8",
        )
        return source_path, packet_path

    def render(self, directory, records=None, packet=None, **kwargs):
        source, packet_path = self.write_fixture(directory, records, packet)
        paths = execute(source, packet_path, Path(directory) / "entries", **kwargs)
        return paths, {lang: path.read_text(encoding="utf-8") for lang, path in paths.items()}

    @staticmethod
    def skeleton(document):
        return re.findall(r"^<!-- SKELETON .+ -->$", document, flags=re.MULTILINE)

    @staticmethod
    def visible(document):
        return re.sub(r"<!--.*?-->", "", document, flags=re.DOTALL)

    def mutate_first(self, records, record_type, **changes):
        copied = copy.deepcopy(records)
        row = next(record for record in copied if record["type"] == record_type)
        row.update(changes)
        return copied

    def assert_contract_error(self, records, pattern=None, packet=None):
        with tempfile.TemporaryDirectory() as directory:
            source, packet_path = self.write_fixture(directory, records, packet)
            manager = self.assertRaisesRegex(ContractError, pattern) if pattern else self.assertRaises(ContractError)
            with manager:
                execute(source, packet_path, Path(directory) / "entries")

    def test_deterministic_pair_skeleton_and_language_isolation(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            paths, text = self.render(first)
            _, reordered = self.render(second, list(reversed(self.records)))
            self.assertEqual(text, reordered)
            self.assertEqual(self.skeleton(text["en"]), self.skeleton(text["tr"]))
            normalized = {
                lang: document.replace("\\", "") for lang, document in text.items()
            }
            self.assertIn("EN_SENTINEL", normalized["en"])
            self.assertNotIn("TR_SENTINEL", normalized["en"])
            self.assertIn("TR_SENTINEL", normalized["tr"])
            self.assertNotIn("EN_SENTINEL", normalized["tr"])
            self.assertEqual(paths["en"].name, "root_000001.md")

    def test_branch_cross_references_are_compact_and_grammatical(self):
        records = copy.deepcopy(self.records)
        branch = next(
            row
            for row in records
            if row["type"] == "branch" and row["branch_id"] == "B001"
        )
        branch["concept"] = {
            "en": (
                "B002 is sentence-initial evidence. "
                "The comparison belongs to B001."
            ),
            "tr": (
                "B002 cümle başındaki kanıttır. "
                "Karşılaştırma B001'e aittir."
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory, records)

        english = self.visible(text["en"])
        turkish = self.visible(text["tr"])
        english_concept = english.split("### Concept and Meaning", 1)[1].split(
            "### Scope", 1
        )[0]
        turkish_concept = turkish.split("### Kavram ve Anlam", 1)[1].split(
            "### Kapsam", 1
        )[0]

        self.assertIn(
            "“فرض الشيء (EN_SENTINEL_SECOND_IMAGE)” is sentence-initial evidence.",
            english_concept,
        )
        self.assertIn(
            "belongs to “جمع الحروف (EN_SENTINEL_FIRST_IMAGE)”.",
            english_concept,
        )
        self.assertIn(
            "“فرض الشيء (TR_SENTINEL_SECOND_IMAGE)” cümle başındaki kanıttır.",
            turkish_concept,
        )
        self.assertIn(
            "Karşılaştırma “جمع الحروف (TR_SENTINEL_FIRST_IMAGE)” dalına aittir.",
            turkish_concept,
        )
        self.assertNotIn("EN_SENTINEL_FIRST_PRIMARY", english_concept)
        self.assertNotIn("EN_SENTINEL_SECOND_PRIMARY", english_concept)
        self.assertNotIn("TR_SENTINEL_FIRST_PRIMARY", turkish_concept)
        self.assertNotIn("TR_SENTINEL_SECOND_PRIMARY", turkish_concept)
        for document in (english, turkish):
            self.assertNotRegex(document, r"root_[0-9]|\bB[0-9]{3}\b")
        self.assertEqual(self.skeleton(text["en"]), self.skeleton(text["tr"]))

    def test_reader_facing_encyclopedia_shape_without_packet_dumps(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            expected_terms = {
                "en": ("Concept", "Scope", "Lexical", "Distinction", "Gloss", "Source", "Quran"),
                "tr": ("Kavram", "Kapsam", "Sözlük", "Ayrım", "Karşılık", "Kaynak", "Kur'an"),
            }
            for language, document in text.items():
                document = self.visible(document)
                for heading in expected_terms[language]:
                    self.assertIn(heading.lower(), document.lower())
                self.assertNotIn("Complete packet", document)
                self.assertNotIn("Packet field", document)
                self.assertNotIn("خاتمة", document)
                self.assertNotIn("مقدمة", document)
                for forbidden in (
                    "root_000001",
                    "B001",
                    "B002",
                    "lu_001",
                    "lu_002",
                    "source:file=",
                    "route status",
                    "yönlendirme durumu",
                    "frozen",
                    "dondurulmuş",
                    "V4",
                    "audit",
                    "denetim",
                    "explicit_support",
                    "schema_version",
                    "root envelope",
                    "source roster",
                    "kök zarfı",
                    "kaynak dökümü",
                ):
                    self.assertNotIn(forbidden.casefold(), document.casefold())
            self.assertIn("كتب الكتاب", text["en"])
            self.assertIn("### Source Evidence", text["en"])
            self.assertIn("### Kaynak Kanıtları", text["tr"])

    def test_primary_gloss_is_immediately_below_heading_and_in_overview(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            primary = "EN_SENTINEL_FIRST_PRIMARY"
            self.assertGreaterEqual(text["en"].count(primary), 2)
            start = text["en"].index(
                f"## جمع الحروف (EN_SENTINEL_FIRST_IMAGE): {primary}"
            )
            self.assertEqual(
                text["en"][start:].splitlines()[2], f"**Primary gloss: {primary}**"
            )

    def test_branch_source_exact_roster_and_opaque_handles(self):
        source_rows = [row for row in self.records if row["type"] == "branch_source"]
        missing = [row for row in self.records if row is not source_rows[0]]
        self.assert_contract_error(missing, "branch_source roster mismatch")
        duplicate = copy.deepcopy(self.records) + [copy.deepcopy(source_rows[0])]
        self.assert_contract_error(duplicate, "duplicate branch_source")
        extra = copy.deepcopy(self.records)
        row = copy.deepcopy(source_rows[0])
        row["source_ref"] = "source:file=x:section=unknown:with:colons"
        extra.append(row)
        self.assert_contract_error(extra, "outside the packet branch roster")
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            visible = self.visible(text["en"])
            self.assertNotIn("source:file=x:section=one", visible)
            self.assertIn("EN_SENTINEL_SOURCE_ONE_CONTRIBUTION", visible)
            self.assertIn("كتب الكتاب", visible)

    def test_selected_quote_must_be_exact_packet_substring(self):
        records = self.mutate_first(
            self.records, "branch_source", selected_quote_ar="عبارة غير موجودة"
        )
        self.assert_contract_error(records, "not an exact packet substring")

    def test_structured_contrasts_require_valid_evidence(self):
        records = copy.deepcopy(self.records)
        branch = next(row for row in records if row["type"] == "branch")
        branch["distinctions"][0]["evidence"] = []
        self.assert_contract_error(records, "evidence must not be empty")
        records = copy.deepcopy(self.records)
        branch = next(row for row in records if row["type"] == "branch")
        branch["distinctions"][0]["evidence"] = ["free-form citation"]
        self.assert_contract_error(records, "unknown evidence refs")
        records = [row for row in copy.deepcopy(self.records) if row["type"] != "external_source"]
        branch = next(row for row in records if row["type"] == "branch")
        branch["distinctions"][0]["evidence"] = ["usage.dictionary"]
        self.assert_contract_error(records, "unknown evidence refs")

    def test_multi_branch_lexical_links_have_distinct_editorial_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            self.assertIn("EN_SENTINEL_FIRST_LEXICAL_ONE_MEANING", text["en"])
            self.assertIn("EN_SENTINEL_SECOND_LEXICAL_ONE_MEANING", text["en"])
            self.assertEqual(
                len(
                    re.findall(
                        r"^#### كَتَبَ \(EN_SENTINEL_LEXICAL_ONE_EXPRESSION\)$",
                        text["en"],
                        flags=re.MULTILINE,
                    )
                ),
                2,
            )
        records = [
            row
            for row in self.records
            if not (row["type"] == "branch_lexical" and row["branch_id"] == "B002" and row["lexical_unit_id"] == "lu_001")
        ]
        self.assert_contract_error(records, "branch_lexical roster mismatch")

    def test_quran_form_and_ayah_records_are_transliteration_only_and_exact(self):
        records = copy.deepcopy(self.records)
        records.append(
            {
                "schema_version": 1,
                "type": "quran_occurrence",
                "qac_ref": "1:1:1:1",
                "transliteration": bilingual("FORBIDDEN_OCCURRENCE"),
            }
        )
        self.assert_contract_error(records, "unknown record type 'quran_occurrence'")
        records = copy.deepcopy(self.records)
        form = next(row for row in records if row["type"] == "quran_form")
        form["count"] = 9
        self.assert_contract_error(records, "extra/forbidden count")
        records = copy.deepcopy(self.records)
        ayah = next(row for row in records if row["type"] == "quran_ayah")
        ayah["note"] = bilingual("FORBIDDEN")
        self.assert_contract_error(records, "extra/forbidden note")
        missing = copy.deepcopy(self.records)
        missing.remove(next(row for row in missing if row["type"] == "quran_form"))
        self.assert_contract_error(missing, "quran_form roster mismatch")
        duplicate = copy.deepcopy(self.records)
        duplicate.append(
            copy.deepcopy(next(row for row in duplicate if row["type"] == "quran_form"))
        )
        self.assert_contract_error(duplicate, "duplicate quran_form")
        wrong_form = self.mutate_first(self.records, "quran_form", form_ordinal=99)
        self.assert_contract_error(wrong_form, "quran_form roster mismatch")

    def test_quran_and_ayah_coverage_uses_curated_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            for language in ("en", "tr"):
                document = text[language]
                self.assertEqual(len(re.findall(r"SKELETON QURAN_FORM", document)), 2)
                self.assertEqual(len(re.findall(r"SKELETON QURAN_OCCURRENCE", document)), 3)
                self.assertEqual(len(re.findall(r"SKELETON QURAN_AYAH", document)), 2)
                expected_locations = (
                    ("1:1, word 1, segment 1", "1:2, word 2, segment 1", "1:2, word 3, segment 1")
                    if language == "en"
                    else ("1:1, 1. kelime, 1. parça", "1:2, 2. kelime, 1. parça", "1:2, 3. kelime, 1. parça")
                )
                for location in expected_locations:
                    self.assertIn(location, document)
                for ayah in self.packet["qac"]["ayah_contexts"]:
                    self.assertIn(f"#### {ayah['ref']}", document)
                self.assertNotIn("verb:1:2:2", document)
                self.assertNotIn("attachment:1", document)
                self.assertNotIn("word_index", document)
                self.assertNotIn("quran_occurrence", document)
            occurrence_section = text["en"].split(
                "SKELETON QURAN_OCCURRENCE 1", 1
            )[1].split("###", 1)[0]
            self.assertEqual(
                occurrence_section.count("EN_SENTINEL_FORM_1_SURFACE"), 2
            )
            self.assertEqual(
                occurrence_section.count("EN_SENTINEL_FORM_2_SURFACE"), 1
            )
            self.assertIn(
                "كَتَبَ (EN_SENTINEL_FORM_1_LEMMA) / "
                "كَتَبَ (EN_SENTINEL_FORM_1_SURFACE)",
                text["en"],
            )

    def test_turkish_omits_packet_authored_english_prose(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            self.assertNotIn("PACKET_ENGLISH", text["tr"])
            self.assertNotIn("PACKET_ENGLISH", text["en"])
            self.assertIn("Fiil yapısı; belirtili nesne", text["tr"])

    def test_arabic_overlays_hide_buckwalter_and_localize_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            for language, prefix in (("en", "EN_SENTINEL"), ("tr", "TR_SENTINEL")):
                document = text[language]
                self.assertIn(
                    f"يدخل فيه نقش الحروف ({prefix}_FIRST_WHAT_IS)", document
                )
                self.assertIn(
                    f"لا يدخل فيه الجمع المطلق ({prefix}_FIRST_WHAT_IS_NOT)",
                    document,
                )
                self.assertIn(
                    f"نقش الحروف ({prefix}_LEXICAL_ONE_SENSE)", document
                )
                self.assertNotIn("LEM:", document)
                self.assertNotIn("ROOT:", document)
                self.assertNotIn("PACKET_BUCKWALTER", document)
                occurrence_section = document.split(
                    "SKELETON QURAN_OCCURRENCE 1", 1
                )[1].split("###", 1)[0]
                self.assertNotIn("| كِتَاب |", occurrence_section)
            turkish = text["tr"]
            self.assertIn("**Rol:** Birincil", turkish)
            self.assertIn("**Uyum:** Daraltma", turkish)
            self.assertIn("Açık destek", turkish)
            self.assertNotIn("Tam yönlendirme", turkish)
            self.assertIn("**Tür:** Biçim", turkish)
            self.assertIn("| Fiil |", turkish)
            self.assertNotIn("primary", turkish)
            self.assertNotIn("narrowing", turkish)
            self.assertNotIn("(`form`)", turkish)
            self.assertNotIn("(`V`)", turkish)
            self.assertNotIn("`explicit_support`", turkish)

        records = copy.deepcopy(self.records)
        branch = next(row for row in records if row["type"] == "branch")
        del branch["what_is_ar_transliteration"]
        self.assert_contract_error(records, "missing what_is_ar_transliteration")
        records = copy.deepcopy(self.records)
        lexical = next(row for row in records if row["type"] == "lexical")
        del lexical["sense_ar_transliteration"]
        self.assert_contract_error(records, "missing sense_ar_transliteration")

    def test_known_marked_transliterations_require_exact_arabic_anchors(self):
        records = copy.deepcopy(self.records)
        lexical = next(
            row
            for row in records
            if row["type"] == "lexical" and row["lexical_unit_id"] == "lu_001"
        )
        lexical["expression_transliteration"] = {
            "en": "kātaba",
            "tr": "kâtebe",
        }
        branch = next(
            row
            for row in records
            if row["type"] == "branch" and row["branch_id"] == "B001"
        )
        branch["concept"] = {
            "en": "The forms كَتَبَ (kātaba), then [كَتَبَ (ka\u0304taba)], recur.",
            "tr": "كَتَبَ (kâtebe), ardından [كَتَبَ (ka\u0302tebe)], yinelenir.",
        }
        with tempfile.TemporaryDirectory() as directory:
            self.render(directory, records)

        for language, decomposed in (
            ("en", "ka\u0304taba"),
            ("tr", "ka\u0302tebe"),
        ):
            broken = copy.deepcopy(records)
            broken_branch = next(
                row
                for row in broken
                if row["type"] == "branch" and row["branch_id"] == "B001"
            )
            anchored = "كَتَبَ (" + decomposed + ")"
            broken_branch["concept"][language] = (
                f"{anchored}, but {decomposed}; is bare after punctuation."
            )
            self.assert_contract_error(
                broken,
                rf"concept\.{language} reuses known transliteration .* without its exact Arabic anchor",
            )

    def test_plain_ascii_overlay_reuse_is_outside_anchor_validation_boundary(self):
        records = copy.deepcopy(self.records)
        lexical = next(
            row
            for row in records
            if row["type"] == "lexical" and row["lexical_unit_id"] == "lu_001"
        )
        lexical["expression_transliteration"] = {"en": "kataba", "tr": "ketebe"}
        branch = next(row for row in records if row["type"] == "branch")
        branch["concept"] = {
            "en": "The plain ASCII token kataba is mechanically ambiguous.",
            "tr": "Düz ASCII ketebe dizisi mekanik olarak belirsizdir.",
        }
        with tempfile.TemporaryDirectory() as directory:
            self.render(directory, records)

    def test_turkish_definite_article_policy_is_derived_from_arabic_initials(self):
        sun_cases = (
            ("التَّمْر", "et-temr"),
            ("الثَّوْب", "es-sevb"),
            ("الدِّين", "ed-dîn"),
            ("الذِّكْر", "eẕ-ẕikr"),
            ("الرَّحْمَة", "er-raḥme"),
            ("الزَّكَاة", "ez-zekât"),
            ("السَّلَام", "es-selâm"),
            ("«الشَّمْس»", "“eş-şems”"),
            ("الصِّدْق", "eṣ-ṣıdḳ"),
            ("الضَّوْء", "eḍ-ḍavʾ"),
            ("الطَّرِيق", "eṭ-ṭarîḳ"),
            ("الظُّلْم", "eẓ-ẓulm"),
            ("اللَّيْل", "el-leyl"),
            ("النُّور", "en-nûr"),
        )
        for arabic, turkish in sun_cases:
            with self.subTest(arabic=arabic, turkish=turkish):
                packet = copy.deepcopy(self.packet)
                records = copy.deepcopy(self.records)
                packet["branches"][0]["branch_image_ar"] = arabic
                next(
                    row
                    for row in records
                    if row["type"] == "branch" and row["branch_id"] == "B001"
                )["image_transliteration"]["tr"] = turkish
                with tempfile.TemporaryDirectory() as directory:
                    self.render(directory, records, packet)

        packet = copy.deepcopy(self.packet)
        records = copy.deepcopy(self.records)
        packet["branches"][0]["branch_image_ar"] = "«الْكِتَاب»"
        branch = next(
            row
            for row in records
            if row["type"] == "branch" and row["branch_id"] == "B001"
        )
        branch["image_transliteration"]["tr"] = "“el-kitâb”"
        packet["branches"][0]["what_is_not_ar"] = "شَمْس"
        branch["what_is_not_ar_transliteration"]["tr"] = "şems"
        with tempfile.TemporaryDirectory() as directory:
            self.render(directory, records, packet)

        branch["image_transliteration"]["tr"] = "eş-şems"
        self.assert_contract_error(records, "moon-letter article prefix", packet)

    def test_turkish_article_validation_covers_each_exact_overlay_category(self):
        packet = copy.deepcopy(self.packet)
        records = copy.deepcopy(self.records)
        packet_branch = packet["branches"][0]
        branch = next(
            row
            for row in records
            if row["type"] == "branch" and row["branch_id"] == "B001"
        )
        packet_branch["what_is_ar"] = "الشَّمْس"
        branch["what_is_ar_transliteration"]["tr"] = "eş-şems"
        branch["distinctions"][0]["neighbor_ar"] = "الرَّحْمَة"
        branch["distinctions"][0]["transliteration"]["tr"] = "er-raḥme"

        packet_lexical = packet["lexical_senses"][0]
        lexical = next(
            row
            for row in records
            if row["type"] == "lexical" and row["lexical_unit_id"] == "lu_001"
        )
        packet_lexical["expression_ar"] = "النُّور"
        lexical["expression_transliteration"]["tr"] = "en-nûr"
        packet_lexical["sense_ar"] = "الْقَمَر"
        lexical["sense_ar_transliteration"]["tr"] = "el-ḳamer"
        packet_lexical["source_phrase_ar"] = "الطَّرِيق"
        lexical["source_phrase_transliteration"]["tr"] = "eṭ-ṭarîḳ"

        packet["dictionary_sources"][0]["entry_text_clean"] = "مقدمة الشَّمْس خاتمة"
        source = next(
            row
            for row in records
            if row["type"] == "branch_source"
            and row["source_ref"] == "source:file=x:section=one"
        )
        source["selected_quote_ar"] = "الشَّمْس"
        source["quote_transliteration"]["tr"] = "“eş-şems”"

        for occurrence in packet["qac"]["occurrences"][:2]:
            occurrence["lemma_ar"] = "الشَّمْس"
            occurrence["surface_ar"] = "الشَّمْسُ"
        quran_form = next(
            row
            for row in records
            if row["type"] == "quran_form" and row["form_ordinal"] == 1
        )
        quran_form["lemma_transliteration"]["tr"] = "eş-şems"
        quran_form["surface_transliteration"]["tr"] = "eş-şemsü"

        with tempfile.TemporaryDirectory() as directory:
            self.render(directory, records, packet)

        invalid_cases = (
            ("branch boundary", lambda rows: next(row for row in rows if row["type"] == "branch")["what_is_ar_transliteration"].__setitem__("tr", "el-şems")),
            ("distinction", lambda rows: next(row for row in rows if row["type"] == "branch")["distinctions"][0]["transliteration"].__setitem__("tr", "el-raḥme")),
            ("lexical expression", lambda rows: next(row for row in rows if row["type"] == "lexical" and row["lexical_unit_id"] == "lu_001")["expression_transliteration"].__setitem__("tr", "el-nûr")),
            ("source quote", lambda rows: next(row for row in rows if row["type"] == "branch_source" and row["source_ref"] == "source:file=x:section=one")["quote_transliteration"].__setitem__("tr", "el-şems")),
            ("Quran lemma", lambda rows: next(row for row in rows if row["type"] == "quran_form" and row["form_ordinal"] == 1)["lemma_transliteration"].__setitem__("tr", "el-şems")),
            ("Quran surface", lambda rows: next(row for row in rows if row["type"] == "quran_form" and row["form_ordinal"] == 1)["surface_transliteration"].__setitem__("tr", "el-şemsü")),
        )
        for label, mutate in invalid_cases:
            with self.subTest(label=label):
                broken = copy.deepcopy(records)
                mutate(broken)
                self.assert_contract_error(
                    broken, "assimilated Turkish article prefix", packet
                )

    def test_external_sources_are_structured_and_drive_bibliography(self):
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory)
            self.assertNotIn("usage.dictionary", self.visible(text["en"]))
            self.assertIn("EN\\_SENTINEL\\_USAGE\\_DICTIONARY", text["en"])
            self.assertNotIn("TR_SENTINEL_KULLANIM_SOZLUGU", text["en"])
            self.assertIn("TR\\_SENTINEL\\_KULLANIM\\_SOZLUGU", text["tr"])
            self.assertNotIn("EN_SENTINEL_USAGE_DICTIONARY", text["tr"])
            self.assertIn("https://example.org/usage", text["tr"])
            self.assertIn("TR\\_SENTINEL\\_EXTERNAL\\_NOTE", text["tr"])
            self.assertIn("**Accessed:** 2026-07-17", text["en"])
            self.assertIn("**Source language:** English", text["en"])
            self.assertIn(
                "**Location in source:** EN\\_SENTINEL\\_HEADWORD\\_WRITE",
                text["en"],
            )
            self.assertNotIn("TR_SENTINEL_YAZMA_MADDESI", text["en"])
            self.assertIn(
                "**Inspected excerpt:** to form letters or words on a surface",
                text["en"],
            )
            self.assertIn("**Erişim tarihi:** 2026-07-17", text["tr"])
            self.assertIn("**Kaynak dili:** İngilizce", text["tr"])
            self.assertIn(
                "**Kaynaktaki konum:** TR\\_SENTINEL\\_YAZMA\\_MADDESI",
                text["tr"],
            )
            self.assertNotIn("EN_SENTINEL_HEADWORD_WRITE", text["tr"])
            self.assertIn("## Kur'an Eki", text["tr"])
        records = self.mutate_first(self.records, "external_source", url="not-a-url")
        self.assert_contract_error(records, "absolute HTTP")
        records = self.mutate_first(self.records, "external_source", external_source_id="bad id")
        self.assert_contract_error(records, "stable authored ID")

    def test_external_source_title_and_locator_are_strict_bilingual_objects(self):
        cases = (
            ("title string", "title", "Single title", "must be an object"),
            ("title missing", "title", {"en": "English title"}, "exactly en and tr"),
            (
                "title extra",
                "title",
                {"en": "English title", "tr": "Türkçe başlık", "ar": "عنوان"},
                "exactly en and tr",
            ),
            (
                "title wrong value",
                "title",
                {"en": ["English title"], "tr": "Türkçe başlık"},
                "non-empty string",
            ),
            ("locator string", "locator", "Headword", "must be an object"),
            (
                "locator missing",
                "locator",
                {"en": "Headword entry"},
                "exactly en and tr",
            ),
            (
                "locator extra",
                "locator",
                {"en": "Headword entry", "tr": "Madde başı", "ar": "المدخل"},
                "exactly en and tr",
            ),
            (
                "locator wrong value",
                "locator",
                {"en": "Headword entry", "tr": 7},
                "non-empty string",
            ),
        )
        for label, field, value, pattern in cases:
            with self.subTest(label=label):
                records = copy.deepcopy(self.records)
                source = next(
                    row for row in records if row["type"] == "external_source"
                )
                if field == "title":
                    source[field] = value
                else:
                    source["verification"][field] = value
                self.assert_contract_error(records, pattern)

        for field, value, pattern in (
            ("title", {"en": "x", "tr": "Geçerli başlık"}, "2-200 characters"),
            (
                "title",
                {"en": "English\u200btitle", "tr": "Geçerli başlık"},
                "control or format",
            ),
            (
                "locator",
                {"en": "Headword\u200blabel", "tr": "Geçerli konum"},
                "control or format",
            ),
        ):
            with self.subTest(field=field, value=value):
                records = copy.deepcopy(self.records)
                source = next(
                    row for row in records if row["type"] == "external_source"
                )
                if field == "title":
                    source[field] = value
                else:
                    source["verification"][field] = value
                self.assert_contract_error(records, pattern)

    def test_arabic_verification_excerpt_requires_and_isolates_transliterations(self):
        records = copy.deepcopy(self.records)
        source = next(row for row in records if row["type"] == "external_source")
        source["verification"].update(
            {
                "source_language": "ar",
                "excerpt": "نَصٌّ مُعَايَن",
                "excerpt_transliteration": {
                    "en": "naṣṣun [EN] <inspected>",
                    "tr": "naṣṣün [TR] <incelenen>",
                },
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory, records)

        for document in text.values():
            self.assertIn("**Inspected excerpt:** نَصٌّ مُعَايَن", text["en"])
            self.assertIn("**İncelenen alıntı:** نَصٌّ مُعَايَن", text["tr"])
        self.assertIn(
            r"**English transliteration:** naṣṣun \[EN\] \<inspected\>",
            text["en"],
        )
        self.assertNotIn("naṣṣün", text["en"])
        self.assertIn(
            r"**Türkçe çevriyazı:** naṣṣün \[TR\] \<incelenen\>",
            text["tr"],
        )
        self.assertNotIn("naṣṣun", text["tr"])

        invalid_cases = (
            ("missing overlay", lambda verification: verification.pop("excerpt_transliteration"), "missing excerpt_transliteration"),
            ("non-Arabic excerpt", lambda verification: verification.__setitem__("excerpt", "inspected text"), "must contain Arabic script"),
            ("wrong overlay type", lambda verification: verification.__setitem__("excerpt_transliteration", "naṣṣ"), "must be an object"),
            ("missing language", lambda verification: verification.__setitem__("excerpt_transliteration", {"en": "naṣṣ"}), "exactly en and tr"),
            ("extra language", lambda verification: verification.__setitem__("excerpt_transliteration", {"en": "naṣṣ", "tr": "naṣṣ", "ar": "نص"}), "exactly en and tr"),
            ("wrong value type", lambda verification: verification.__setitem__("excerpt_transliteration", {"en": 3, "tr": "naṣṣ"}), "non-empty string"),
        )
        for label, mutate, pattern in invalid_cases:
            with self.subTest(label=label):
                broken = copy.deepcopy(records)
                verification = next(
                    row for row in broken if row["type"] == "external_source"
                )["verification"]
                mutate(verification)
                self.assert_contract_error(broken, pattern)

        non_arabic = copy.deepcopy(self.records)
        next(row for row in non_arabic if row["type"] == "external_source")[
            "verification"
        ]["excerpt_transliteration"] = {"en": "text", "tr": "metin"}
        self.assert_contract_error(
            non_arabic, "extra/forbidden excerpt_transliteration"
        )

    def test_arabic_verification_overlay_joins_known_anchor_inventory(self):
        records = copy.deepcopy(self.records)
        source = next(row for row in records if row["type"] == "external_source")
        source["verification"].update(
            {
                "source_language": "ar",
                "excerpt": "نَصّ",
                "excerpt_transliteration": {"en": "naṣṣ", "tr": "naṣṣ"},
            }
        )
        source["note"] = {
            "en": "The inspected term نَصّ (naṣṣ) supports this contrast.",
            "tr": "İncelenen نَصّ (naṣṣ) terimi bu ayrımı destekler.",
        }
        with tempfile.TemporaryDirectory() as directory:
            self.render(directory, records)

        broken = copy.deepcopy(records)
        next(row for row in broken if row["type"] == "external_source")["note"][
            "en"
        ] = "The bare transliteration naṣṣ lacks its Arabic anchor."
        self.assert_contract_error(broken, "without its exact Arabic anchor")

    def test_external_source_verification_is_exact_bounded_and_substantive(self):
        source = next(
            row for row in self.records if row["type"] == "external_source"
        )
        missing = copy.deepcopy(self.records)
        del next(row for row in missing if row["type"] == "external_source")[
            "verification"
        ]
        self.assert_contract_error(missing, "missing verification")

        cases = (
            ({"accessed_on": "2026-02-30"}, "valid calendar date"),
            ({"accessed_on": "2026-2-03"}, "YYYY-MM-DD"),
            ({"accessed_on": 20260717}, "non-empty string"),
            ({"source_language": "de"}, "one of ar, en, tr"),
            ({"locator": {"en": "maintenance status: pending", "tr": "Geçerli konum"}}, "status placeholder"),
            ({"locator": {"en": "to be checked", "tr": "Geçerli konum"}}, "status placeholder"),
            ({"locator": {"en": "unchecked", "tr": "Geçerli konum"}}, "status placeholder"),
            ({"locator": {"en": "placeholder entry", "tr": "Geçerli konum"}}, "status placeholder"),
            ({"locator": {"en": "ab", "tr": "Geçerli konum"}}, "3-300 characters"),
            ({"locator": {"en": "x" * 301, "tr": "Geçerli konum"}}, "3-300 characters"),
            ({"excerpt": "query pending"}, "status placeholder"),
            ({"excerpt": "not yet checked"}, "status placeholder"),
            ({"excerpt": "TBD after access"}, "status placeholder"),
            ({"excerpt": ""}, "non-empty string"),
            ({"excerpt": "x" * 501}, "1-500 characters"),
            ({"excerpt": "line\nfeed"}, "control or format"),
        )
        for changes, pattern in cases:
            with self.subTest(changes=changes):
                records = copy.deepcopy(self.records)
                verification = next(
                    row for row in records if row["type"] == "external_source"
                )["verification"]
                verification.update(changes)
                self.assert_contract_error(records, pattern)

        extra = copy.deepcopy(self.records)
        next(row for row in extra if row["type"] == "external_source")[
            "verification"
        ]["status"] = "checked"
        self.assert_contract_error(extra, "extra/forbidden status")

        incidental = copy.deepcopy(self.records)
        next(row for row in incidental if row["type"] == "external_source")[
            "verification"
        ]["excerpt"] = "The entry remained unchecked by later editors."
        with tempfile.TemporaryDirectory() as directory:
            self.render(directory, incidental)
        self.assertEqual(source["verification"]["source_language"], "en")

    def test_external_source_markdown_and_url_are_hardened(self):
        records = copy.deepcopy(self.records)
        source = next(row for row in records if row["type"] == "external_source")
        source["title"] = {
            "en": "Hostile \\ [title] ]( <script>",
            "tr": "Saldırgan \\ [başlık] ]( <betik>",
        }
        source["url"] = "https://example.org/a_(b)?x=(y)"
        source["note"] = {
            "en": "note [bad](javascript:x) <script> *bold*\n## heading",
            "tr": "not [bad](javascript:x) <script> *kalın*\n## başlık",
        }
        source["verification"]["locator"] = {
            "en": "Section [one] <locator>",
            "tr": "Bölüm [bir] <konum>",
        }
        source["verification"]["excerpt"] = "exact [text] <excerpt>"
        with tempfile.TemporaryDirectory() as directory:
            _, text = self.render(directory, records)
            self.assertIn(r"\[title\]", text["en"])
            self.assertNotIn("başlık", text["en"])
            self.assertIn(r"\[başlık\]", text["tr"])
            self.assertNotIn("title", text["tr"])
            for language, document in text.items():
                self.assertIn(
                    "(<https://example.org/a_(b)?x=(y)>)", document
                )
                self.assertNotIn("[bad](javascript:x)", document)
                self.assertNotIn("<script>", document)
                self.assertIn(r"exact \[text\] \<excerpt\>", document)
                self.assertNotRegex(document, r"(?m)^## (title|heading|başlık)$")
            self.assertIn(r"Section \[one\] \<locator\>", text["en"])
            self.assertNotIn("Bölüm", text["en"])
            self.assertIn(r"Bölüm \[bir\] \<konum\>", text["tr"])
            self.assertNotIn("Section", text["tr"])

        for unsafe_url in (
            "https://example.org/white space",
            "https://example.org/control\x01",
            "https://example.org/<angle>",
            "https://example.org/back\\slash",
        ):
            with self.subTest(url=unsafe_url):
                records = self.mutate_first(
                    self.records, "external_source", url=unsafe_url
                )
                self.assert_contract_error(records, "unsafe Markdown URL")

    def test_overwrite_marker_symlink_and_pair_rollback_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            paths, original = self.render(directory)
            source, packet = self.write_fixture(directory)
            with self.assertRaisesRegex(ContractError, "output exists"):
                execute(source, packet, Path(directory) / "entries")
            paths["en"].write_text("user file\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "unmarked"):
                execute(source, packet, Path(directory) / "entries", force=True)
            self.assertEqual(paths["tr"].read_text(encoding="utf-8"), original["tr"])
            paths["en"].write_text(original["en"], encoding="utf-8")

            changed = copy.deepcopy(self.records)
            next(row for row in changed if row["type"] == "root")["overview"] = bilingual("CHANGED_OVERVIEW")
            source, packet = self.write_fixture(directory, changed)
            real_replace = os.replace

            def fail_second_install(src, dst):
                if ".stage-" in Path(src).name and Path(dst) == paths["tr"]:
                    raise OSError("simulated second replace failure")
                return real_replace(src, dst)

            with mock.patch("scripts.render_language_entries.os.replace", side_effect=fail_second_install):
                with self.assertRaisesRegex(ContractError, "pair write failed"):
                    execute(source, packet, Path(directory) / "entries", force=True)
            self.assertEqual(paths["en"].read_text(encoding="utf-8"), original["en"])
            self.assertEqual(paths["tr"].read_text(encoding="utf-8"), original["tr"])

            target = Path(directory) / "symlink-target.md"
            target.write_text(original["en"], encoding="utf-8")
            paths["en"].unlink()
            os.symlink(target, paths["en"])
            with self.assertRaisesRegex(ContractError, "symlinked output"):
                execute(source, packet, Path(directory) / "entries", force=True)

    def test_check_and_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            paths, _ = self.render(directory)
            source, packet = self.write_fixture(directory)
            execute(source, packet, Path(directory) / "entries", check=True)
            paths["tr"].unlink()
            with self.assertRaisesRegex(ContractError, "missing output"):
                execute(source, packet, Path(directory) / "entries", check=True)
            paths["tr"].write_text("stale\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "stale output"):
                execute(source, packet, Path(directory) / "entries", check=True)
        with tempfile.TemporaryDirectory() as directory:
            source, packet = self.write_fixture(directory)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--packet", str(packet), "--output-dir", str(Path(directory) / "entries")],
                cwd=PROJECT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("wrote", result.stdout)

    def test_root_packet_mismatch_and_generic_filler_are_rejected(self):
        records = self.mutate_first(
            self.records, "root", root_envelope_id="root_999999"
        )
        self.assert_contract_error(records, "does not match packet")
        records = copy.deepcopy(self.records)
        root = next(row for row in records if row["type"] == "root")
        root["overview"]["en"] = "resolved"
        self.assert_contract_error(records, "generic filler")


if __name__ == "__main__":
    unittest.main()
