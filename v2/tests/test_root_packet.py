import tempfile
import unittest
from pathlib import Path

from scripts.root_packet import (
    prepare_output_paths,
    referenced_attachment_ids,
    root_key,
    tsv_matches,
)


class RootPacketTest(unittest.TestCase):
    def test_existing_packet_outputs_require_force(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            expected = (
                output_dir / "root_000001.json",
                output_dir / "root_000001.md",
            )
            self.assertEqual(
                prepare_output_paths(output_dir, "root_000001", force=False),
                expected,
            )
            expected[0].write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "Rerun with --force"):
                prepare_output_paths(output_dir, "root_000001", force=False)

            self.assertEqual(
                prepare_output_paths(output_dir, "root_000001", force=True),
                expected,
            )

    def test_attachment_selection_closes_over_instance_references(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attachments.tsv"
            path.write_text(
                "unit_id\tdep_root_norm\thead_root_norm\tgrammar\n"
                "direct\tfocus\tother\tlocal grammar\n"
                "referenced\tother\tthird\tCOUNT 9; local grammar\n"
                "unrelated\tother\tthird\tlocal grammar\n",
                encoding="utf-8",
            )
            rows = tsv_matches(
                path,
                root_key("focus"),
                ("dep_root_norm", "head_root_norm"),
                unit_ids={"referenced"},
            )

        self.assertEqual([row["unit_id"] for row in rows], ["direct", "referenced"])
        self.assertEqual(rows[1]["grammar"], "local grammar")

    def test_referenced_attachment_ids_uses_every_instance_field(self):
        instances = [
            {
                "dependent_attachment_ids": "dependent;shared",
                "object_attachment_ids": "object",
                "subject_attachment_id": "subject",
            },
            {
                "prep_attachment_ids": "prep;shared",
                "clausal_attachment_ids": "clause",
            },
        ]
        self.assertEqual(
            referenced_attachment_ids(instances),
            {"dependent", "object", "subject", "prep", "clause", "shared"},
        )


if __name__ == "__main__":
    unittest.main()
