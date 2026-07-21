import json
import tempfile
import unittest
from pathlib import Path

from v2.scripts.export_jsonl import render_jsonl, write_output


PROJECT = Path(__file__).resolve().parents[2]
FIXTURE = PROJECT / "v2/examples/root_000858.tr.entry.json"


class ExportJsonlTest(unittest.TestCase):
    def test_export_is_one_valid_entry_per_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            entries_dir = Path(temporary) / "entries"
            entries_dir.mkdir()
            (entries_dir / "root_000858.json").write_text(
                FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
            )

            content, count = render_jsonl(entries_dir)

            self.assertEqual(count, 1)
            self.assertEqual(len(content.splitlines()), 1)
            self.assertEqual(json.loads(content)["entry_id"], "root_000858/tr")

    def test_check_detects_stale_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "entries.jsonl"
            write_output(output, "{}\n", check=False)
            write_output(output, "{}\n", check=True)
            with self.assertRaisesRegex(Exception, "Stale JSONL export"):
                write_output(output, '{"changed":true}\n', check=True)


if __name__ == "__main__":
    unittest.main()
