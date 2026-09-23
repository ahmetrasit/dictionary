"""Review preparation for a validated, unaccepted furuq writer response."""

import tempfile
import unittest
from pathlib import Path

from v2.scripts.assemble_entry import json_content
from v2.scripts.prepare_root_review import prepare
from v2.scripts.stage_root_writer import stage as stage_writer
from v2.scripts.validate_entry import ContractError, load_json
from v2.tests.test_entry_workflow import reduced_root_response


PROJECT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT / "v2/work/entry_creation/furuq/root_005406/tr"


class RawFuruqReviewPreparationTest(unittest.TestCase):
    def test_validated_raw_response_can_be_bound_for_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "furuq/root_005406/tr"
            task_path = work / "tasks/root_writer.json"
            task_path.parent.mkdir(parents=True)
            task_path.write_text(
                (SOURCE / "tasks/root_writer.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            task = load_json(task_path)
            evidence = load_json(SOURCE / "inputs/root_evidence.json")
            stage_writer(task_path)
            response_path = work / "output/root_005406_entry.json"
            response_path.write_text(
                json_content(reduced_root_response(task, evidence)),
                encoding="utf-8",
            )

            review_task_path = work / "tasks/root_reviewer.json"
            review_task = prepare(task_path, response_path, review_task_path)
            self.assertEqual(review_task["branch_roster"], ["root_005406/B001"])
            self.assertEqual(
                review_task["writer_response"]["path"], str(response_path.resolve())
            )
            self.assertTrue(review_task_path.is_file())

            staged = work / "input/task.json"
            staged_task = load_json(staged)
            staged_task["canonical_task_sha256"] = "0" * 64
            staged.write_text(json_content(staged_task), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "stale"):
                prepare(task_path, response_path, review_task_path)


if __name__ == "__main__":
    unittest.main()
