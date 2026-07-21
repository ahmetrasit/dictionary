import copy
import unittest
from pathlib import Path

from v2.scripts.project_entry import (
    master_binding,
    project_entry,
    scholar_view_projection,
    translation_agent_projection,
    user_dictionary_projection,
)
from v2.scripts.validate_entry import ContractError, validate_entry


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

    def test_translation_agent_receives_gloss_risk_without_scholar_evidence(self):
        projected = translation_agent_projection(self.entry)
        source = self.entry["branches"][0]
        branch = projected["branches"][0]

        self.assertEqual(projected["projection"], "translation_agent")
        self.assertEqual(branch["what_is_ar"], source["what_is_ar"])
        self.assertEqual(branch["gloss_candidates"], source["glosses"])
        self.assertIn("loses", branch["gloss_candidates"]["selected"][0]["error_profile"])
        keys = set(nested_keys(projected))
        self.assertNotIn("dictionary_basis", keys)
        self.assertNotIn("source_discussion", keys)
        self.assertNotIn("arabic_neighbor_distinctions", keys)
        self.assertNotIn("occurrence_evidence", keys)
        self.assertNotIn("attachments", keys)

    def test_user_dictionary_is_compact_and_uses_first_authored_distinction(self):
        projected = user_dictionary_projection(self.entry)
        source = self.entry["branches"][0]
        branch = projected["branches"][0]
        first_neighbor = source["arabic_neighbor_distinctions"][0]

        self.assertEqual(projected["projection"], "user_dictionary")
        self.assertEqual(branch["definition"], source["glosses"]["semantic_definition"])
        self.assertEqual(
            branch["primary_glosses"],
            [
                {"rank": gloss["rank"], "text": gloss["text"]}
                for gloss in source["glosses"]["selected"]
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
            "occurrence_evidence",
            "evidence_refs",
            "source_refs",
            "attachments",
        ):
            self.assertNotIn(forbidden, keys)

    def test_scholar_view_contains_the_complete_master(self):
        projected = scholar_view_projection(self.entry)
        self.assertEqual(projected["entry"], self.entry)
        self.assertIn("dictionary_basis", projected["entry"]["branches"][0])
        self.assertIn("occurrences", projected["entry"]["occurrence_evidence"])

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
