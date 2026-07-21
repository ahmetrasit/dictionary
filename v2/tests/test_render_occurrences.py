import copy
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from v2.scripts.render_occurrences import (
    MARKER,
    attachment_rows_by_id,
    build_attachment_crosswalk,
    group_attachment_patterns,
    group_forms,
    link_occurrences,
    local_source_grammar,
    normalize_pattern_surface,
    occurrence_unit_id,
    render_markdown,
    selector_matches,
    validate_packet,
    write_generated,
)


PROJECT = Path(__file__).resolve().parents[2]
SIRAT_PACKET = PROJECT / "data/output/root_packets/root_000858.json"
QARA_PACKET = (
    PROJECT / "data/output/root_packets/root_001210--root_001211.json"
)


def form_index(forms):
    result = {}
    for form in forms:
        for occurrence in form["occurrences"]:
            result.setdefault(occurrence_unit_id(occurrence), set()).add(form["id"])
    return result


def ambiguous_packet():
    occurrences = []
    words = []
    for index in (1, 2):
        occurrences.append(
            {
                "qac_ref": f"1:1:{index}:1",
                "qac_word_ref": f"1:1:{index}",
                "surah": 1,
                "ayah": 1,
                "word_index": index,
                "morpheme_index": 1,
                "surface_ar": "كَتَبَ",
                "stem_ar": "كَتَبَ",
                "lemma_ar": "كَتَبَ",
                "root_ar": "ك ت ب",
                "pos": "V",
                "morph_features": "STEM|POS:V|PERF|3MS",
            }
        )
        words.append({"qac_word_ref": f"1:1:{index}", "surface_ar": "كَتَبَ"})
    instances = [
        {
            "unit_id": f"verb-{index}",
            "word_unit_id": f"q:1:1:{index}",
            "sura": 1,
            "ayah": 1,
            "surface": "كتب",
            "stem": "كتب",
            "root_norm": "ك ت ب",
        }
        for index in (9, 10)
    ]
    return {
        "root_envelope_id": "root_000001",
        "root_join_key": "كتب",
        "root_norm": "ك ت ب",
        "qac": {
            "summary": {
                "morpheme_count": 2,
                "word_count": 2,
                "ayah_count": 1,
                "surah_count": 1,
            },
            "occurrences": occurrences,
            "ayah_contexts": [
                {
                    "ref": "1:1",
                    "surah": 1,
                    "ayah": 1,
                    "surface_ar": "كَتَبَ كَتَبَ",
                    "words": words,
                }
            ],
        },
        "attachments": {
            "noun_instances": [],
            "verb_instances": instances,
            "attachments": [],
        },
    }


class RenderOccurrencesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sirat = json.loads(SIRAT_PACKET.read_text(encoding="utf-8"))
        cls.qara = json.loads(QARA_PACKET.read_text(encoding="utf-8"))

    def test_sirat_forms_join_every_occurrence(self):
        validate_packet(self.sirat)
        forms = group_forms(self.sirat["qac"]["occurrences"])
        self.assertEqual(len(forms), 9)
        self.assertEqual(sum(len(form["occurrences"]) for form in forms), 45)

        links = link_occurrences(self.sirat)
        methods = Counter(link["method"] for link in links.values())
        self.assertEqual(methods, Counter({"qac_crosswalk": 45}))
        self.assertTrue(selector_matches(self.sirat, "root_000858"))
        self.assertTrue(selector_matches(self.sirat, "ص ر ط"))
        self.assertTrue(selector_matches(self.sirat, "صراط"))
        self.assertTrue(selector_matches(self.sirat, "الصراط"))

    def test_sirat_patterns_merge_case_forms_but_preserve_relations(self):
        occurrences = self.sirat["qac"]["occurrences"]
        forms = group_forms(occurrences)
        units = list(dict.fromkeys(occurrence_unit_id(row) for row in occurrences))
        patterns = group_attachment_patterns(
            units,
            link_occurrences(self.sirat),
            attachment_rows_by_id(self.sirat),
            form_index(forms),
        )

        qwm_mustaqim = [
            pattern
            for pattern in patterns
            if pattern["counterpart_key"] == "مستقيم"
            and pattern["detail"]["other_root"] == "ق و م"
        ]
        self.assertEqual(
            {(row["detail"]["relation"], row["count"]) for row in qwm_mustaqim},
            {("adjective", 31), ("circumstantial", 2)},
        )
        self.assertEqual(normalize_pattern_surface("مُسْتَقِيمَاً"), "مستقيم")

    def test_render_lists_every_sirat_occurrence_and_source_grammar(self):
        rendered = render_markdown(self.sirat, SIRAT_PACKET, "tr")
        for occurrence in self.sirat["qac"]["occurrences"]:
            self.assertIn(f"| `{occurrence['qac_ref']}` |", rendered)
        for form_id in range(1, 10):
            self.assertIn(f"### F{form_id:03d}:", rendered)
        self.assertIn("Bağlantı dilbilgisi (kaynak metin)", rendered)
        self.assertIn("NOUN_ABSTRACT accusative, definite (al-), direct object", rendered)
        self.assertIn("güçlü biçimde destekli, yüksek güven", rendered)
        self.assertNotIn("strongly licensed, high confidence", rendered)
        self.assertNotIn("B001", rendered)

    def test_second_root_packet_exercises_nouns_verbs_and_source_gaps(self):
        validate_packet(self.qara)
        self.assertEqual(len(group_forms(self.qara["qac"]["occurrences"])), 19)
        methods = Counter(
            link["method"] for link in link_occurrences(self.qara).values()
        )
        self.assertEqual(
            methods,
            Counter(
                {
                    "qac_crosswalk": 79,
                    "no_attachment_instance": 5,
                    "unresolved_form_mismatch": 4,
                }
            ),
        )
        rendered = render_markdown(self.qara, QARA_PACKET, "en")
        self.assertIn("perfect verb", rendered)
        self.assertIn("Unresolved rows remain visible", rendered)

    def test_repeated_same_form_words_align_by_monotonic_order(self):
        packet = ambiguous_packet()
        validate_packet(packet)
        links = link_occurrences(packet)
        self.assertEqual({link["method"] for link in links.values()}, {"qac_crosswalk"})
        self.assertEqual(
            [links[f"q:1:1:{index}"]["instances"][0]["unit_id"] for index in (1, 2)],
            ["verb-9", "verb-10"],
        )

    def test_attachment_numeric_ids_are_not_used_as_qac_identity(self):
        packet = ambiguous_packet()
        for instance in packet["attachments"]["verb_instances"]:
            instance["word_unit_id"] = "q:1:1:1"
        validate_packet(packet)
        links = link_occurrences(packet)
        self.assertEqual(links["q:1:1:1"]["method"], "qac_crosswalk")
        self.assertEqual(links["q:1:1:2"]["method"], "qac_crosswalk")

    def test_same_root_neighbors_align_to_qac_forms_not_source_ids(self):
        packet = json.loads(
            (PROJECT / "data/output/root_packets/root_000783.json").read_text(
                encoding="utf-8"
            )
        )
        rows = {
            row["qac_word_ref"]: row for row in build_attachment_crosswalk(packet)["rows"]
        }
        self.assertEqual(
            rows["56:55:1"]["attachment_unit_id"], "ae:v3:s056:055:noun:2"
        )
        self.assertEqual(
            rows["56:55:2"]["attachment_unit_id"], "ae:v3:s056:055:noun:3"
        )

    def test_attachment_grammar_drops_global_count_claims(self):
        self.assertEqual(
            local_source_grammar(
                "NOUN_CONCRETE; ACC predicate; COUNT 12 with diverse forms"
            ),
            "NOUN_CONCRETE; ACC predicate",
        )
        self.assertNotIn(
            "62",
            local_source_grammar(
                "noun, nominative. The word appears 62 times in the Quran."
            ),
        )

    def test_generated_output_is_deterministic_and_protected(self):
        rendered = render_markdown(self.sirat, SIRAT_PACKET, "en")
        self.assertEqual(rendered, render_markdown(self.sirat, SIRAT_PACKET, "en"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "occurrences.md"
            write_generated(output, rendered, check=False)
            write_generated(output, rendered, check=True)
            with self.assertRaises(ValueError):
                write_generated(output, rendered + "stale\n", check=True)

            unmarked = Path(directory) / "authored.md"
            unmarked.write_text("authored\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                write_generated(unmarked, f"{MARKER}\nreplacement\n", check=False)

    def test_validation_rejects_duplicate_occurrence_refs(self):
        packet = copy.deepcopy(self.sirat)
        packet["qac"]["occurrences"].append(packet["qac"]["occurrences"][0])
        with self.assertRaises(ValueError):
            validate_packet(packet)

    def test_validation_rejects_dangling_and_duplicate_attachment_rows(self):
        packet = copy.deepcopy(self.sirat)
        instance = packet["attachments"]["noun_instances"][0]
        instance["dependent_attachment_ids"] = "missing:attachment"
        with self.assertRaisesRegex(ValueError, "reference missing rows"):
            validate_packet(packet)

        packet = copy.deepcopy(self.sirat)
        packet["attachments"]["attachments"].append(
            copy.deepcopy(packet["attachments"]["attachments"][0])
        )
        with self.assertRaisesRegex(ValueError, "duplicate attachment unit IDs"):
            validate_packet(packet)

    def test_validation_rejects_incorrect_census_and_unsafe_envelope(self):
        packet = copy.deepcopy(self.sirat)
        packet["qac"]["summary"]["word_count"] += 1
        with self.assertRaisesRegex(ValueError, "summary word_count"):
            validate_packet(packet)

        packet = copy.deepcopy(self.sirat)
        packet["root_envelope_id"] = "../../unsafe"
        with self.assertRaisesRegex(ValueError, "Invalid root envelope"):
            validate_packet(packet)

    def test_valid_empty_occurrence_packet_renders_without_failure(self):
        packet = copy.deepcopy(self.sirat)
        packet["qac"]["occurrences"] = []
        packet["qac"]["ayah_contexts"] = []
        packet["qac"]["summary"] = {
            "morpheme_count": 0,
            "word_count": 0,
            "ayah_count": 0,
            "surah_count": 0,
        }
        validate_packet(packet)
        rendered = render_markdown(packet, SIRAT_PACKET, "tr")
        self.assertIn("- 0 QAC oluşum biçimi", rendered)
        self.assertIn("- Bağlantı eşlemeleri: yok", rendered)


if __name__ == "__main__":
    unittest.main()
