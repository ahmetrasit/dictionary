import copy
import json
import tempfile
import unittest
from pathlib import Path

from v2.scripts.branch_lexicalization import branch_lexicalization_profile
from v2.scripts.validate_entry import (
    ContractError,
    load_json,
    structural_errors,
    validate_entry,
)


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

    def test_schema_allows_a_zero_candidate_neighbor_roster(self):
        schema = load_json(SCHEMA)
        coverage = {
            "candidate_count": 0,
            "assessment": "none_useful",
            "note": "No supplied candidate sharpens this branch boundary.",
        }
        self.assertEqual(
            structural_errors(
                coverage,
                schema["$defs"]["neighborCoverage"],
                schema,
            ),
            [],
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
        def add_unquoted_example(entry):
            discussion = entry["branches"][0]["source_discussion"]
            discussion["examples"].append(
                {
                    "arabic": "عبارة غير موجودة في المصدر",
                    "note": "Bu örnek kaynak pasajında bulunmayan bir ifadedir.",
                    "source_refs": discussion["evidence_refs"][:1],
                }
            )

        self.assert_invalid(add_unquoted_example, "not an exact substring")

    def test_disagreement_requires_a_disputed_qualifier(self):
        def add_unqualified_disagreement(entry):
            branch = entry["branches"][0]
            branch["source_discussion"]["disagreement"] = {
                "summary": "Bu cümle ihtilaf olduğunu ileri sürer ancak niteleyici bunu doğrulamaz.",
                "source_refs": branch["source_discussion"]["evidence_refs"][:1],
            }

        self.assert_invalid(
            add_unqualified_disagreement,
            "disputed qualifier and source disagreement",
        )

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

    def test_lexical_realizations_are_packet_backed(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["lexical_realizations"][0].update(
                {"expression_ar": "عبارة مختلفة"}
            ),
            "packet-backed lexical roster",
        )

    def test_branch_lexicalization_profile_is_mechanically_derived(self):
        def corrupt_profile(entry):
            branch = entry["branches"][0]
            profile = branch_lexicalization_profile(
                branch["lexical_realizations"]
            )
            profile["has_non_bare"] = not profile["has_non_bare"]
            branch["lexicalization_profile"] = profile

        self.assert_invalid(
            corrupt_profile,
            "expected deterministic Furuq unit-kind profile",
        )

    def test_disagreement_and_disputed_qualifier_move_together(self):
        def add_disagreement_without_qualifier(entry):
            branch = entry["branches"][0]
            branch["source_discussion"]["disagreement"] = {
                "summary": "Kaynaklar bu kullanımın açıklanışında birbirinden ayrılan iki açık değerlendirme sunar.",
                "source_refs": branch["source_discussion"]["evidence_refs"][:1],
            }
            branch["evidence_qualifiers"] = []

        self.assert_invalid(
            add_disagreement_without_qualifier,
            "disputed qualifier and source disagreement",
        )

    def test_neighbor_candidate_count_is_evidence_bound(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["neighbor_coverage"].update(
                {"candidate_count": 999}
            ),
            "candidate_count: expected",
        )

    def test_attachment_alignment_is_required_and_hash_bound(self):
        self.assert_invalid(
            lambda entry: entry["occurrence_evidence"].update(
                {"alignment_sha256": "0" * 64}
            ),
            "alignment_sha256: expected",
        )

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

    def test_neighbor_relation_type_uses_the_concept_map_vocabulary(self):
        self.assert_invalid(
            lambda entry: entry["branches"][0]["arabic_neighbor_distinctions"][0].update(
                {"relation_type": "network_similarity"}
            ),
            "relation_type",
        )

    def test_zero_useful_neighbors_requires_explicit_assessment(self):
        entry = copy.deepcopy(self.entry)
        branch = entry["branches"][0]
        branch["arabic_neighbor_distinctions"] = []
        branch["neighbor_coverage"]["assessment"] = "none_useful"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "zero-neighbors.json"
            path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
            validate_entry(path)

        self.assert_invalid(
            lambda candidate: (
                candidate["branches"][0].update(
                    {"arabic_neighbor_distinctions": []}
                ),
                candidate["branches"][0]["neighbor_coverage"].update(
                    {"assessment": "complete"}
                ),
            ),
            "zero selected neighbors require none_useful",
        )

    def test_occurrence_data_is_mechanically_derived(self):
        self.assert_invalid(
            lambda entry: entry["occurrence_evidence"]["occurrences"][0].update(
                {"surface_ar": "لفظ مختلف"}
            ),
            "differs from deterministic QAC data",
        )
        self.assert_invalid(
            lambda entry: entry["occurrence_evidence"]["observations"].append(
                {
                    "category": "grammar",
                    "statement": "Bu gözlem ajan tarafından üretilmemelidir.",
                    "evidence_refs": ["1:6:2:1"],
                }
            ),
            "must be mechanically empty",
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
