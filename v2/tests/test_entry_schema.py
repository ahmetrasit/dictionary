import copy
import json
import tempfile
import unittest
from pathlib import Path

from v2.scripts.validate_entry import ContractError, load_json, validate_entry


PROJECT = Path(__file__).resolve().parents[2]
SCHEMA = PROJECT / "v2/schema/encyclopedia-entry.schema.json"
FIXTURE = PROJECT / "v2/examples/root_000858.tr.entry.json"


class EntrySchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = load_json(FIXTURE)

    def assert_invalid(self, mutation, message=None):
        entry = copy.deepcopy(self.entry)
        mutation(entry)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "entry.json"
            path.write_text(
                json.dumps(entry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ContractError) as raised:
                validate_entry(path)
        if message:
            self.assertIn(message, str(raised.exception))

    def test_complete_sirat_fixture_validates(self):
        entry, packet = validate_entry(FIXTURE)
        self.assertEqual(entry["entry_id"], "root_000858/tr")
        self.assertEqual(len(entry["branches"]), len(packet["branches"]))
        self.assertEqual(
            [
                (
                    branch["dictionary_basis"]["dictionary_count"],
                    branch["dictionary_basis"]["passage_count"],
                )
                for branch in entry["branches"]
            ],
            [(3, 4), (1, 2), (1, 1)],
        )

    def test_schema_is_strict_and_language_specific(self):
        schema = load_json(SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["language"]["enum"], ["en", "tr"])
        self.assert_invalid(
            lambda entry: entry.update({"unexpected": "value"}),
            "unknown property 'unexpected'",
        )

    def test_branch_roster_and_counts_are_packet_bound(self):
        self.assert_invalid(
            lambda entry: entry["branches"].reverse(),
            "index roster does not match entry",
        )
        self.assert_invalid(
            lambda entry: entry["root_profile"].update({"branch_count": 4}),
            "branch_count: expected 3",
        )

    def test_dictionary_basis_is_exhaustive_and_counted_by_dictionary(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["dictionary_basis"].update(
                {"dictionary_count": 4}
            ),
            "dictionary_count: expected 3",
        )

        def remove_passage(entry):
            entry["branches"][0]["dictionary_basis"]["sources"][2][
                "source_refs"
            ].pop()
            entry["branches"][0]["dictionary_basis"]["passage_count"] = 3

        self.assert_invalid(remove_passage, "source roster mismatch")

        self.assert_invalid(
            lambda entry: entry["branches"][0]["dictionary_basis"]["sources"][0].update(
                {"source_id": "maqayis"}
            ),
            "belongs to 'sihah', not 'maqayis'",
        )

    def test_source_discussion_cannot_cite_unrouted_material(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["source_discussion"][
                "evidence_refs"
            ].append("unrouted:source"),
            "non-branch source refs",
        )
        self.assert_invalid(
            lambda entry: entry["branches"][0]["source_discussion"]["examples"][
                0
            ].update({"arabic": "عبارة غير موجودة في المصدر"}),
            "not an exact substring",
        )

    def test_disagreement_requires_an_identified_disagreeing_source(self):
        def add_unmarked_disagreement(entry):
            branch = entry["branches"][0]
            branch["source_discussion"]["disagreement"] = {
                "summary": "Bu cümle ihtilaf olduğunu ileri sürer ancak hiçbir kaynak rolü bunu doğrulamaz.",
                "source_refs": branch["source_discussion"]["evidence_refs"][:1],
            }

        self.assert_invalid(add_unmarked_disagreement, "no cited source is marked")

    def test_common_loanword_can_only_be_second_selected_gloss(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["glosses"]["selected"][0].update(
                {"loanword_status": "common"}
            ),
            "common loanword may only be rank 2",
        )

        def move_common_loanword_to_third(entry):
            selected = entry["branches"][0]["glosses"]["selected"]
            selected.append(copy.deepcopy(selected[1]))
            selected[2]["rank"] = 3
            selected[2]["text"] = "sırat"
            selected[2]["loanword_status"] = "common"

        self.assert_invalid(move_common_loanword_to_third, "rank 2")

    def test_neighbor_links_must_exist_and_cite_neighbor_evidence(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["arabic_neighbor_distinctions"][0].update(
                {"neighbor_branch_id": "B999"}
            ),
            "absent from the focus branch evidence package",
        )
        self.assert_invalid(
            lambda entry: entry["branches"][0]["arabic_neighbor_distinctions"][0].update(
                {"evidence_refs": ["unrelated:source"]}
            ),
            "absent from the neighbor's Furuq source roster",
        )

    def test_occurrence_observations_use_real_generated_evidence(self):
        self.assert_invalid(
            lambda entry: entry["occurrence_evidence"]["observations"][0][
                "evidence_refs"
            ].append("999:999:999:999"),
            "unknown references",
        )
        self.assert_invalid(
            lambda entry: entry["occurrence_evidence"].update(
                {"artifact_path": "v2/output/occurrences/root_000858.en.md"}
            ),
            "expected 'v2/output/occurrences/root_000858.tr.md'",
        )

    def test_packet_digest_prevents_evidence_drift(self):
        self.assert_invalid(
            lambda entry: entry["provenance"].update({"packet_sha256": "0" * 64}),
            "Packet digest mismatch",
        )


if __name__ == "__main__":
    unittest.main()
