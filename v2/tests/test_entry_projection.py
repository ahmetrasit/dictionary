import copy
import unittest
from pathlib import Path

from v2.scripts.branch_lexicalization import branch_lexicalization_profile
from v2.scripts.project_entry import (
    master_binding,
    project_entry,
    scholar_view_projection,
    translation_agent_projection,
    user_dictionary_projection,
)
from v2.scripts.validate_entry import ContractError, DICTIONARY_CODES, validate_entry


PROJECT = Path(__file__).resolve().parents[2]
FIXTURE = PROJECT / "v2/examples/root_000858.tr.entry.json"


def nested_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


class EntryProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, _packet = validate_entry(FIXTURE)

    def test_translation_agent_receives_arabic_sources_and_mechanical_occurrences(self):
        projected = translation_agent_projection(self.entry)
        source = self.entry["branches"][0]
        branch = projected["branches"][0]

        self.assertEqual(projected["projection"], "translation_agent")
        self.assertEqual(branch["what_is_ar"], source["what_is_ar"])
        self.assertEqual(branch["source_phrase_ar"], source["source_phrase_ar"])
        self.assertEqual(
            branch["sources"],
            [
                DICTIONARY_CODES[row["source_id"]]
                for row in source["dictionary_basis"]["sources"]
            ],
        )
        self.assertIn("source_note", branch)
        self.assertEqual(branch["gloss_candidates"], source["glosses"])
        self.assertEqual(
            branch["lexicalization_profile"],
            source.get("lexicalization_profile")
            or branch_lexicalization_profile(source["lexical_realizations"]),
        )
        self.assertIn("loses", branch["gloss_candidates"]["selected"][0]["error_profile"])
        self.assertEqual(
            set(projected["occurrence_evidence"]),
            {"summary", "forms", "ayahs", "occurrences"},
        )
        self.assertNotIn("artifact_path", projected["occurrence_evidence"])
        keys = set(nested_keys(projected))
        self.assertNotIn("dictionary_basis", keys)
        self.assertNotIn("source_discussion", keys)
        self.assertNotIn("arabic_neighbor_distinctions", keys)
        self.assertIn("occurrence_evidence", keys)
        self.assertIn("attachments", keys)

    def test_user_dictionary_is_compact_and_uses_first_authored_distinction(self):
        projected = user_dictionary_projection(self.entry)
        source = self.entry["branches"][0]
        branch = projected["branches"][0]
        first_neighbor = source["arabic_neighbor_distinctions"][0]

        self.assertEqual(projected["projection"], "user_dictionary")
        self.assertEqual(branch["branch_image_ar"], source["branch_image_ar"])
        self.assertEqual(branch["what_is_ar"], source["what_is_ar"])
        self.assertEqual(branch["source_phrase_ar"], source["source_phrase_ar"])
        self.assertTrue(branch["sources"])
        self.assertEqual(
            branch["lexicalization_profile"],
            source.get("lexicalization_profile")
            or branch_lexicalization_profile(source["lexical_realizations"]),
        )
        self.assertEqual(branch["definition"], source["glosses"]["semantic_definition"])
        self.assertEqual(
            branch["concept_gloss"]["text"],
            source["glosses"]["selected"][0]["text"],
        )
        self.assertEqual(
            branch["contextual_glosses"],
            [
                {"text": gloss["text"]}
                for gloss in source["glosses"]["selected"][1:]
            ],
        )
        self.assertEqual(
            (
                branch["key_distinction"]["neighbor_root_id"],
                branch["key_distinction"]["neighbor_branch_id"],
            ),
            (
                first_neighbor["neighbor_root_id"],
                first_neighbor["neighbor_branch_id"],
            ),
        )
        keys = set(nested_keys(projected))
        for forbidden in (
            "dictionary_basis",
            "source_discussion",
            "error_profile",
            "evidence_refs",
            "attachments",
        ):
            self.assertNotIn(forbidden, keys)
        self.assertEqual(
            projected["occurrence_evidence"]["summary"],
            self.entry["occurrence_evidence"]["summary"],
        )

    def test_scholar_view_contains_the_complete_master(self):
        projected = scholar_view_projection(self.entry)
        self.assertEqual(projected["entry"], self.entry)
        self.assertIn("dictionary_basis", projected["entry"]["branches"][0])
        self.assertIn("occurrences", projected["entry"]["occurrence_evidence"])

    def test_user_dictionary_carries_verified_relation_type_when_present(self):
        entry = copy.deepcopy(self.entry)
        entry["branches"][0]["arabic_neighbor_distinctions"][0][
            "relation_type"
        ] = "near_synonym"
        projected = user_dictionary_projection(entry)
        self.assertEqual(
            projected["branches"][0]["key_distinction"]["relation_type"],
            "near_synonym",
        )

    def test_user_dictionary_uses_null_when_no_neighbor_is_useful(self):
        entry = copy.deepcopy(self.entry)
        entry["branches"][0]["arabic_neighbor_distinctions"] = []
        entry["branches"][0]["neighbor_coverage"]["assessment"] = "none_useful"
        projected = user_dictionary_projection(entry)
        self.assertIsNone(projected["branches"][0]["key_distinction"])

    def test_every_projection_is_bound_to_the_same_master(self):
        expected = master_binding(self.entry)
        for name in ("translation_agent", "user_dictionary", "scholar_view"):
            self.assertEqual(project_entry(self.entry, name)["master"], expected)

        changed = copy.deepcopy(self.entry)
        changed["status"] = "reviewed"
        self.assertNotEqual(master_binding(changed)["sha256"], expected["sha256"])

    def test_unknown_projection_is_rejected(self):
        with self.assertRaisesRegex(ContractError, "Unknown entry projection"):
            project_entry(self.entry, "entire_entry_for_everyone")


if __name__ == "__main__":
    unittest.main()
