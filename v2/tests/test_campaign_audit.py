import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import v2.scripts.audit_entry_campaign as audit_module
import v2.scripts.build_entry_manifest as manifest_module
from v2.scripts.validate_entry import ContractError


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class CampaignAuditTest(unittest.TestCase):
    envelope = "root_000001"
    language = "tr"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.work = (
            self.project
            / "v2/work/entry_creation"
            / self.envelope
            / self.language
        )
        self.writer_task = self.work / "tasks/root_writer.json"
        self.writer_fragment = (
            self.work / "fragments" / f"{self.envelope}_entry.json"
        )
        self.review_task = self.work / "tasks/root_reviewer.json"
        self.review_fragment = self.work / "fragments/root_review.json"
        self.entry = (
            self.project / "v2/entries" / self.language / f"{self.envelope}.json"
        )
        self.markdown = self.entry.with_suffix(".md")

    def prepare_writer(self):
        write_json(self.writer_task, {})
        write_json(self.writer_fragment, {"inputs_sha256": "writer-task-hash"})

    def prepare_review(self):
        write_json(self.review_task, {})
        write_json(self.review_fragment, {"verdict": "pass"})

    def prepare_publication(self):
        write_json(self.entry, {})
        self.markdown.write_text("rendered\n", encoding="utf-8")

    def audit_with_writer(self, review=None):
        writer = {
            "inputs_sha256": "writer-task-hash",
            "branches": [],
        }
        return mock.patch.object(
            audit_module,
            "check_root_writer",
            return_value=writer,
        ), mock.patch.object(
            audit_module,
            "check_review",
            return_value=review or {"verdict": "pass"},
        )

    def test_missing_coordinator_hash_is_writer_invalid(self):
        self.prepare_writer()
        with mock.patch.object(
            audit_module,
            "check_root_writer",
            side_effect=ContractError("missing coordinator inputs_sha256"),
        ):
            result = audit_module.audit_root(
                self.project, self.envelope, self.language
            )
        self.assertEqual(result["state"], "writer_invalid")
        self.assertIn("inputs_sha256", result["detail"])

    def test_stale_review_binding_is_review_invalid(self):
        self.prepare_writer()
        self.prepare_review()
        writer_patch, _review_patch = self.audit_with_writer()
        with writer_patch, mock.patch.object(
            audit_module,
            "check_review",
            side_effect=ContractError("Task input digest mismatch"),
        ):
            result = audit_module.audit_root(
                self.project, self.envelope, self.language
            )
        self.assertEqual(result["state"], "review_invalid")
        self.assertIn("digest mismatch", result["detail"])

    def test_repair_verdict_wins_over_existing_publication(self):
        self.prepare_writer()
        self.prepare_review()
        self.prepare_publication()
        writer_patch, review_patch = self.audit_with_writer(
            {"verdict": "repair"}
        )
        with writer_patch, review_patch, mock.patch.object(
            audit_module, "validate_entry"
        ) as validate:
            result = audit_module.audit_root(
                self.project, self.envelope, self.language
            )
        self.assertEqual(result["state"], "repair_required")
        validate.assert_not_called()

    def test_obsolete_entry_schema_is_publication_stale(self):
        self.prepare_writer()
        self.prepare_review()
        self.prepare_publication()
        writer_patch, review_patch = self.audit_with_writer()
        with writer_patch, review_patch, mock.patch.object(
            audit_module,
            "validate_entry",
            side_effect=ContractError("unknown property 'review_gate'"),
        ):
            result = audit_module.audit_root(
                self.project, self.envelope, self.language
            )
        self.assertEqual(result["state"], "publication_stale")
        self.assertIn("review_gate", result["detail"])

    def test_current_bound_publication_is_successful(self):
        self.prepare_writer()
        self.prepare_review()
        self.prepare_publication()
        writer_patch, review_patch = self.audit_with_writer()
        entry = {"provenance": {"root_task_sha256": "writer-task-hash"}}
        with writer_patch, review_patch, mock.patch.object(
            audit_module,
            "validate_entry",
            return_value=(entry, {}),
        ), mock.patch.object(audit_module, "render") as render:
            result = audit_module.audit_root(
                self.project, self.envelope, self.language
            )
        self.assertEqual(result["state"], "published_valid")
        render.assert_called_once_with(self.entry, self.markdown, check=True)

    def test_quranic_scope_uses_packet_origin_not_numeric_position(self):
        packet_dir = self.project / "data/output/root_packets"
        write_json(
            packet_dir / "root_000001.json",
            {
                "root_envelope_id": "root_000001",
                "branches": [{"origin_corpus": "non_quranic"}],
            },
        )
        write_json(
            packet_dir / "root_005000.json",
            {
                "root_envelope_id": "root_005000",
                "branches": [{"origin_corpus": "quranic"}],
            },
        )
        self.assertEqual(
            audit_module.packet_envelopes(self.project, "quranic"),
            ["root_005000"],
        )


class EntryManifestAuditTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.entry = self.project / "v2/entries/tr/root_000001.json"
        write_json(
            self.entry,
            {
                "schema_version": 4,
                "root_envelope_id": "root_000001",
                "language": "tr",
                "branches": [{}],
                "root_profile": {},
            },
        )
        self.draft = (
            self.project
            / "v2/work/entry_creation/root_000002/tr/output/root_000002_entry.json"
        )
        write_json(
            self.draft,
            {
                "artifact_format": "dictionary-v2-root-entry-draft-v1",
                "root_envelope_id": "root_000002",
                "language": "tr",
                "branches": [{}],
                "root_profile": {},
            },
        )

    def test_default_manifest_excludes_stale_publication_and_drafts(self):
        with mock.patch.object(
            manifest_module,
            "audit_root",
            return_value={"state": "publication_stale"},
        ):
            manifest = manifest_module.build_manifest(project=self.project)
        self.assertEqual(manifest["entries"], [])

    def test_default_manifest_includes_only_audited_publication(self):
        with mock.patch.object(
            manifest_module,
            "audit_root",
            return_value={"state": "published_valid"},
        ):
            manifest = manifest_module.build_manifest(project=self.project)
        self.assertEqual(len(manifest["entries"]), 1)
        self.assertEqual(manifest["entries"][0]["kind"], "entry")

    def test_include_drafts_restores_shape_only_discovery(self):
        manifest = manifest_module.build_manifest(
            project=self.project,
            include_drafts=True,
        )
        self.assertEqual(
            [(row["root_envelope_id"], row["kind"]) for row in manifest["entries"]],
            [("root_000001", "entry"), ("root_000002", "draft")],
        )


if __name__ == "__main__":
    unittest.main()
