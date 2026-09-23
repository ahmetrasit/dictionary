"""Source-bound transfer of reviewed furuq writer responses."""

import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from v2.scripts.assemble_entry import agent_root_evidence, json_content, sha256_file
from v2.scripts.create_entry import binding, common_task, write_task
from v2.scripts.enrich_furuq_writer import enrich
import v2.scripts.enrich_furuq_writer as enricher
from v2.scripts.prepare_root_review import prepare
from v2.scripts.stage_root_reviewer import stage as stage_reviewer
from v2.scripts.stage_root_writer import stage as stage_writer
from v2.scripts.validate_entry import ContractError, load_json
from v2.tests.test_entry_workflow import reduced_root_response


PROJECT = Path(__file__).resolve().parents[2]
SOURCE_PACKAGE = (
    PROJECT
    / "v2/output/branch_evidence/root_005406/branches/root_005406--B001.json"
)


class FuruqEnrichmentTest(unittest.TestCase):
    def make_run(self, project: Path, verdict: str = "pass"):
        envelope = "root_005406"
        work = project / "v2/work/entry_creation/furuq" / envelope / "tr"
        package = load_json(SOURCE_PACKAGE)
        occurrence = {
            "qac_ref": "20:111:1:1",
            "qac_word_ref": "20:111:1",
            "surah": 20,
            "ayah": 111,
            "word_index": 1,
            "morpheme_index": 1,
            "surface_ar": "عَنَتِ",
            "stem_ar": "عَنَتِ",
            "lemma_ar": "عَنَتِ",
            "root_ar": "ع ن و",
            "pos": "V",
            "source_pos": "V",
            "morpheme_role": "STEM",
        }
        packet = {
            "root_envelope_id": envelope,
            "root_join_key": "عنو",
            "root_norm": "ع ن و",
            "branches": [package["branch"]],
            "dictionary_sources": [
                {"source_ref": ref, "source_id": source["source_id"]}
                for source in package["dictionary_basis"]["sources"]
                for ref in source["source_refs"]
            ],
            "qac": {
                "summary": {
                    "morpheme_count": 1, "word_count": 1,
                    "ayah_count": 1, "surah_count": 1,
                },
                "occurrences": [occurrence],
                "ayah_contexts": [{
                    "ref": "20:111", "surah": 20, "ayah": 111,
                    "surface_ar": "عَنَتِ",
                    "words": [{"qac_word_ref": "20:111:1", "surface_ar": "عَنَتِ"}],
                }],
            },
            "attachments": {
                "noun_instances": [], "verb_instances": [], "attachments": [],
            },
        }
        packet_path = project / "data/output/furuq/root_packets" / f"{envelope}.json"
        packet_path.parent.mkdir(parents=True)
        packet_path.write_text(json_content(packet), encoding="utf-8")
        package["packet_sha256"] = sha256_file(packet_path)

        index_path = project / "v2/output/branch_evidence" / envelope / "index.json"
        package_path = index_path.parent / "branches/root_005406--B001.json"
        package_path.parent.mkdir(parents=True)
        package_path.write_text(json_content(package), encoding="utf-8")
        index_path.write_text(json_content({
            "root_envelope_id": envelope,
            "packet_sha256": sha256_file(packet_path),
            "branches": [{
                "root_id": envelope, "branch_id": "B001",
                "path": "branches/root_005406--B001.json",
                "sha256": sha256_file(package_path),
            }],
        }), encoding="utf-8")

        evidence_path = work / "inputs/root_evidence.json"
        evidence_path.parent.mkdir(parents=True)
        evidence = agent_root_evidence([package], {})
        evidence_path.write_text(json_content(evidence), encoding="utf-8")
        policy_path = project / "v2/policy/protected_names" / f"{envelope}.json"
        policy_path.parent.mkdir(parents=True)
        policy_path.write_text(json_content({"status": "fallback", "items": []}), encoding="utf-8")

        writer_task = common_task("root_writer", envelope, "tr")
        writer_task.update({
            "branch_roster": ["root_005406/B001"],
            "evidence": binding(evidence_path),
            "coordinator": {
                "evidence_index": binding(index_path),
                "name_policy": binding(policy_path),
            },
        })
        writer_task_path = work / "tasks/root_writer.json"
        write_task(writer_task_path, writer_task)
        stage_writer(writer_task_path)
        writer_path = work / "output/root_005406_entry.json"
        response = reduced_root_response(writer_task, evidence)
        writer_path.write_text(json_content(response), encoding="utf-8")

        review_task_path = work / "tasks/root_reviewer.json"
        prepare(writer_task_path, writer_path, review_task_path)
        stage_reviewer(review_task_path)
        if verdict == "repair":
            review = {
                "verdict": "repair",
                "summary": "The concept gloss needs one bounded correction.",
                "issues": [{
                    "target_ref": "root_005406/B001",
                    "field": "concept_gloss",
                    "severity": "minor",
                    "confidence": "high",
                    "claim_ids": ["bc_001"],
                    "evidence_conflict": "The wording omits the defining captivity sense.",
                    "smallest_correction": "Correct only the concept gloss wording.",
                }],
            }
            response["branches"][0]["concept_gloss"]["text"] = "Esaret çekirdeği"
            writer_path.write_text(json_content(response), encoding="utf-8")
        else:
            review = {
                "verdict": "pass",
                "summary": "The writer response matches the supplied evidence.",
                "issues": [],
            }
        review_path = work / "review/output/root_review.json"
        review_path.write_text(json_content(review), encoding="utf-8")
        return work, packet_path, writer_path

    def test_pass_injects_exact_arabic_sources_and_packet_occurrence(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            work, packet_path, writer_path = self.make_run(project)
            raw_bytes = writer_path.read_bytes()
            output = work / "export/root_005406_entry.json"
            with mock.patch.object(enricher, "PROJECT", project):
                result = enrich(work, output)
            self.assertEqual(result["artifact_format"], "dictionary-v2-root-entry-draft-v1")
            self.assertEqual(result["generated_by"], "v2/scripts/enrich_furuq_writer.py")
            self.assertEqual(result["branches"][0]["branch_image_ar"], load_json(packet_path)["branches"][0]["branch_image_ar"])
            self.assertEqual(result["branches"][0]["sources"], ["AY"])
            self.assertEqual(result["occurrence_evidence"]["summary"]["morpheme_count"], 1)
            self.assertEqual(writer_path.read_bytes(), raw_bytes)
            self.assertEqual(load_json(output), result)

    def test_repair_scope_and_packet_digest_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            work, packet_path, writer_path = self.make_run(project, "repair")
            output = work / "export/root_005406_entry.json"
            with mock.patch.object(enricher, "PROJECT", project):
                result = enrich(work, output)
            self.assertEqual(result["branches"][0]["concept_gloss"]["text"], "Esaret çekirdeği")

            accepted = load_json(writer_path)
            changed = copy.deepcopy(accepted)
            changed["root_profile"]["summary"] += " Extra change."
            writer_path.write_text(json_content(changed), encoding="utf-8")
            with mock.patch.object(enricher, "PROJECT", project):
                with self.assertRaisesRegex(ContractError, "protected root profile"):
                    enrich(work, work / "export/changed.json")

            writer_path.write_text(json_content(accepted), encoding="utf-8")
            packet = load_json(packet_path)
            packet["qac"]["summary"]["morpheme_count"] = 2
            packet_path.write_text(json_content(packet), encoding="utf-8")
            with mock.patch.object(enricher, "PROJECT", project):
                with self.assertRaisesRegex(ContractError, "digest-mismatched furuq packet"):
                    enrich(work, work / "export/changed.json")


if __name__ == "__main__":
    unittest.main()
