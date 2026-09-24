"""The reviewer validator keeps its pre-fix snapshot after a live repair."""

import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from v2.scripts.assemble_entry import ROOT_ENTRY_ARTIFACT_FORMAT, json_content, sha256_file
from v2.scripts.create_entry import GENERATOR
from v2.scripts.stage_root_reviewer import stage as stage_reviewer
from v2.scripts.validate_agent_output import _validate_reviewer_writer_state
from v2.scripts.validate_entry import ContractError
import v2.scripts.validate_agent_output as validator


class StagedReviewerRepairTest(unittest.TestCase):
    def test_regular_root_staging_keeps_original_writer_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            inputs = work / "source"
            inputs.mkdir()
            bindings = {}
            for key, name in (("prompt", "prompt.md"),
                              ("response_schema", "schema.json"),
                              ("evidence", "evidence.json")):
                path = inputs / name
                path.write_text(key + "\n", encoding="utf-8")
                bindings[key] = {"path": str(path), "sha256": sha256_file(path)}
            writer_path = work / "output/root_900001_entry.json"
            writer_path.parent.mkdir()
            writer_path.write_text(json_content({
                "inputs_sha256": "a" * 64,
                "artifact_format": ROOT_ENTRY_ARTIFACT_FORMAT,
                "generated_by": "v2/scripts/accept_root_writer.py",
                "root_envelope_id": "root_900001",
                "language": "tr",
                "branches": [{"branch_ref": "root_900001/B001"}],
                "root_profile": {"summary": "Written"},
            }), encoding="utf-8")
            task = {"format": 4, "generated_by": GENERATOR,
                    "role": "root_reviewer", "root_envelope_id": "root_900001",
                    "language": "tr", "branch_roster": ["root_900001/B001"],
                    **bindings,
                    "writer_response": {"path": str(writer_path),
                                        "sha256": sha256_file(writer_path)}}
            task_path = work / "tasks/root_reviewer.json"
            task_path.parent.mkdir()
            task_path.write_text(json_content(task), encoding="utf-8")
            staged = stage_reviewer(task_path)
            snapshot = work / "review/input/writer_response.json"
            self.assertEqual(snapshot.read_bytes(), writer_path.read_bytes())
            self.assertEqual(staged["writer_response"]["sha256"],
                             task["writer_response"]["sha256"])

    def test_immutable_snapshot_and_only_recorded_live_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            review_input = work / "review/input"
            review_input.mkdir(parents=True)
            output = work / "output/root_900001_entry.json"
            output.parent.mkdir()
            snapshot_path = review_input / "writer_response.json"
            original = {
                "branches": [{"branch_ref": "root_900001/B001",
                              "concept_gloss": {"text": "Before"}}],
                "root_profile": {"summary": "Protected"},
            }
            snapshot_path.write_text(json_content(original), encoding="utf-8")
            repaired = copy.deepcopy(original)
            repaired["branches"][0]["concept_gloss"]["text"] = "After"
            output.write_text(json_content(repaired), encoding="utf-8")
            staged = {"root_envelope_id": "root_900001",
                      "branch_roster": ["root_900001/B001"],
                      "evidence": {"path": "evidence.json"},
                      "writer_response": {"path": "writer_response.json",
                                          "sha256": sha256_file(snapshot_path)}}
            canonical = {"branch_roster": staged["branch_roster"],
                         "writer_response": {"path": str(output),
                                             "sha256": sha256_file(snapshot_path)}}
            review = {"verdict": "repair", "issues": [
                {"target_ref": "root_900001/B001", "field": "concept_gloss"}
            ]}
            task_path = review_input / "task.json"
            with (mock.patch.object(validator, "validate_fragment"),
                  mock.patch.object(validator, "validate_semantic_contract")):
                _validate_reviewer_writer_state(task_path, "root_reviewer",
                                                staged, canonical, review)
                changed = copy.deepcopy(repaired)
                changed["root_profile"]["summary"] = "Unauthorized"
                output.write_text(json_content(changed), encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "protected root profile"):
                    _validate_reviewer_writer_state(task_path, "root_reviewer",
                                                    staged, canonical, review)
                output.write_text(json_content(repaired), encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "Only a recorded repair"):
                    _validate_reviewer_writer_state(task_path, "root_reviewer",
                                                    staged, canonical,
                                                    {"verdict": "pass", "issues": []})
                snapshot_path.write_text("{}\n", encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "immutable binding"):
                    _validate_reviewer_writer_state(task_path, "root_reviewer",
                                                    staged, canonical, review)
                staged["writer_response"]["sha256"] = sha256_file(snapshot_path)
                with self.assertRaisesRegex(ContractError, "lacks a snapshot bound"):
                    _validate_reviewer_writer_state(task_path, "root_reviewer",
                                                    staged, canonical, review)


if __name__ == "__main__":
    unittest.main()
