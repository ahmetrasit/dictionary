"""An unrelated registry append does not invalidate a sealed supplemental task."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from v2.scripts.assemble_entry import json_content, sha256_file
from v2.scripts.create_entry import (
    SUPPLEMENTAL_GENERATOR,
    verify_task_bindings,
)
from v2.scripts.validate_entry import ContractError
import v2.scripts.create_entry as creator


class SupplementalRegistryBindingTest(unittest.TestCase):
    def test_append_keeps_selected_intake_bound_but_selected_change_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            source_dir = project / "data/supplemental"
            entries_dir = source_dir / "entries"
            entries_dir.mkdir(parents=True)
            ident = "root_900001"
            intake = entries_dir / f"{ident}.json"
            intake.write_text('{"id":"root_900001"}\n', encoding="utf-8")
            intake_hash = sha256_file(intake)
            row = {"id": ident, "kind": "lexical_root",
                   "intakePath": f"entries/{ident}.json", "intakeSha256": intake_hash}
            registry = source_dir / "registry.v1.json"
            registry.write_text(json_content({"schemaVersion": "dictionary-supplemental-registry-v1",
                                              "entries": [row]}), encoding="utf-8")
            historical_hash = sha256_file(registry)
            evidence = project / "evidence.json"
            evidence.write_text("{}\n", encoding="utf-8")
            task = {
                "format": 4,
                "generated_by": SUPPLEMENTAL_GENERATOR,
                "role": "root_writer",
                "entryKind": "lexical_root",
                "root_envelope_id": ident,
                "supplementalIntake": {
                    "registryPath": "data/supplemental/registry.v1.json",
                    "registrySha256": historical_hash,
                    "intakePath": f"data/supplemental/entries/{ident}.json",
                    "intakeSha256": intake_hash,
                },
                "coordinator": {
                    "registry": {"path": str(registry), "sha256": historical_hash},
                    "intake": {"path": str(intake), "sha256": intake_hash},
                },
                "evidence": {"path": str(evidence), "sha256": sha256_file(evidence)},
            }
            appended = {"id": "root_900002", "kind": "lexical_root",
                        "intakePath": "entries/root_900002.json", "intakeSha256": "b" * 64}
            with mock.patch.object(creator, "PROJECT", project):
                registry.write_text(json_content({"schemaVersion": "dictionary-supplemental-registry-v1",
                                                  "entries": [row, appended]}), encoding="utf-8")
                verify_task_bindings(task)
                changed = {**row, "intakeSha256": "c" * 64}
                registry.write_text(json_content({"schemaVersion": "dictionary-supplemental-registry-v1",
                                                  "entries": [changed, appended]}), encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "changed selected intake ownership"):
                    verify_task_bindings(task)
                registry.write_text(json_content({"schemaVersion": "dictionary-supplemental-registry-v1",
                                                  "entries": [row, appended]}), encoding="utf-8")
                intake.write_text('{"id":"tampered"}\n', encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "differs from sealed task"):
                    verify_task_bindings(task)


if __name__ == "__main__":
    unittest.main()
