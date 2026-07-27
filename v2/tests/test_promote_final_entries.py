import json
import tempfile
import unittest
from pathlib import Path

from v2.scripts.promote_final_entries import promote


PROJECT = Path(__file__).resolve().parents[2]
FIXTURE = PROJECT / "v2/examples/root_000858.tr.entry.json"
PACKET_DIR = PROJECT / "data/output/root_packets"


class PromoteFinalEntriesTest(unittest.TestCase):
    def test_promotes_valid_quranic_json_only_with_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "v2_entries" / "tr"
            destination = base / "entries" / "tr"
            source.mkdir(parents=True)
            (source / "root_000858.json").write_text(
                FIXTURE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (source / "root_000858.md").write_text("# ignored\n", encoding="utf-8")

            result = promote(
                language="tr",
                source_dir=source,
                destination_dir=destination,
                packet_dir=PACKET_DIR,
                generated_date="2026-07-27",
                source_commit="test-commit",
                source_tree_has_uncommitted_changes=False,
            )

            self.assertEqual(result["entry_count"], 1)
            self.assertTrue((destination / "root_000858.json").is_file())
            self.assertFalse((destination / "root_000858.md").exists())
            manifest = json.loads(
                (destination / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["format"], "dictionary-final-entry-manifest-v1")
            self.assertEqual(manifest["scope"], "quranic")
            self.assertEqual(manifest["language"], "tr")
            self.assertEqual(manifest["final_entry_count"], 1)
            self.assertEqual(manifest["entries"][0]["path"], "entries/tr/root_000858.json")

    def test_check_detects_stale_final_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "v2_entries" / "tr"
            destination = base / "entries" / "tr"
            source.mkdir(parents=True)
            destination.mkdir(parents=True)
            (source / "root_000858.json").write_text(
                FIXTURE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            promote(
                language="tr",
                source_dir=source,
                destination_dir=destination,
                packet_dir=PACKET_DIR,
                generated_date="2026-07-27",
                source_commit="test-commit",
                source_tree_has_uncommitted_changes=False,
            )
            (destination / "root_000858.json").write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(Exception, "Stale final entry"):
                promote(
                    language="tr",
                    source_dir=source,
                    destination_dir=destination,
                    packet_dir=PACKET_DIR,
                    check=True,
                )

    def test_prunes_stale_root_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "v2_entries" / "tr"
            destination = base / "entries" / "tr"
            source.mkdir(parents=True)
            destination.mkdir(parents=True)
            (source / "root_000858.json").write_text(
                FIXTURE.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (destination / "root_999999.json").write_text("{}\n", encoding="utf-8")

            promote(
                language="tr",
                source_dir=source,
                destination_dir=destination,
                packet_dir=PACKET_DIR,
                generated_date="2026-07-27",
                source_commit="test-commit",
                source_tree_has_uncommitted_changes=False,
            )

            self.assertFalse((destination / "root_999999.json").exists())


if __name__ == "__main__":
    unittest.main()
