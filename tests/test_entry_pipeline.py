import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_entry_bundles import packet_sha256
from scripts.build_entry_scaffolds import (
    BUNDLE_MANIFEST,
    GENERATED_MANIFEST,
    attachment_links,
    branch_filename,
    instance_attachment_ids,
    render_branch,
    render_quran_observatory,
    recover_interrupted_replacement,
    scaffold_destination,
    split_ids,
    validate_packet,
    write_scaffolds,
)
from scripts.validate_entry import validate_entry


PROJECT = Path(__file__).resolve().parents[1]
PACKET_PATH = PROJECT / "data/output/root_packets/root_000858.json"


class EntryPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))

    def write_bundle_fixture(self, project, packet=None):
        packet = packet or self.packet
        bundle = project / "data/output/entry_bundles/root_000858"
        manifest_path = bundle / BUNDLE_MANIFEST
        if manifest_path.exists():
            return bundle
        branch_dir = bundle / "branches"
        branch_dir.mkdir(parents=True)
        files = {
            "ROOT.md": "# Root evidence bundle\n",
            "INDEX.md": "# Entry bundles\n",
        }
        for branch in packet["branches"]:
            relative = f"branches/{branch_filename(branch)}"
            files[relative] = f"# Branch evidence bundle: {branch['root_id']}/{branch['branch_id']}\n"
        for relative, content in files.items():
            path = bundle / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        manifest = {
            "format": 1,
            "root_envelope_id": "root_000858",
            "packet": str(PACKET_PATH),
            "packet_sha256": packet_sha256(packet),
            "branches": [
                f"{branch['root_id']}/{branch['branch_id']}" for branch in packet["branches"]
            ],
            "files": {
                relative: hashlib.sha256((bundle / relative).read_bytes()).hexdigest()
                for relative in files
            },
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return bundle

    def build_tree(self, project, force=False, packet=None):
        packet = copy.deepcopy(packet or self.packet)
        self.write_bundle_fixture(project, packet)
        output = project / "data/output/entry_scaffolds/root_000858"
        return write_scaffolds(packet, PACKET_PATH, output, project, force=force)

    def assembled_text(self, tree, packet=None):
        packet = packet or self.packet
        parts = [(tree / "ROOT-HEADER.md").read_text(encoding="utf-8")]
        parts.extend(
            (tree / "branches" / branch_filename(branch)).read_text(encoding="utf-8")
            for branch in packet["branches"]
        )
        parts.extend(
            [
                (tree / "QURAN-OBSERVATORY.md").read_text(encoding="utf-8"),
                (tree / "BIBLIOGRAPHY-CANDIDATES.md").read_text(encoding="utf-8"),
            ]
        )
        return "\n".join(parts)

    def test_scaffold_output_is_restricted_to_generated_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            expected = project / "data/output/entry_scaffolds/root_000858"
            _, actual = scaffold_destination(project, "root_000858", expected)
            self.assertEqual(actual, expected.resolve())
            with self.assertRaises(ValueError):
                scaffold_destination(
                    project,
                    "root_000858",
                    project / "data/output/entry_drafts/root_000858",
                )
            with self.assertRaises(ValueError):
                scaffold_destination(project, "root_000858", project / "entries")

    def test_rerun_refuses_by_default_and_force_replaces_complete_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            tree = self.build_tree(project)
            original = (tree / "QURAN-OBSERVATORY.md").read_text(encoding="utf-8")
            stale = tree / "branches/stale.md"
            stale.write_text("stale", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.build_tree(project)
            replaced = self.build_tree(project, force=True)
            self.assertFalse((replaced / "branches/stale.md").exists())
            self.assertEqual(
                (replaced / "QURAN-OBSERVATORY.md").read_text(encoding="utf-8"),
                original,
            )
            self.assertTrue((replaced / GENERATED_MANIFEST).is_file())

    def test_force_refuses_unmarked_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.write_bundle_fixture(project)
            tree = project / "data/output/entry_scaffolds/root_000858"
            tree.mkdir(parents=True)
            (tree / "user-file.md").write_text("authored", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.build_tree(project, force=True)

    def test_missing_or_changed_bundle_preflight_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            output = project / "data/output/entry_scaffolds/root_000858"
            with self.assertRaises(ValueError):
                write_scaffolds(
                    copy.deepcopy(self.packet), PACKET_PATH, output, project
                )
            bundle = self.write_bundle_fixture(project)
            branch = bundle / "branches/root_000858--B001.md"
            branch.write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                write_scaffolds(
                    copy.deepcopy(self.packet), PACKET_PATH, output, project
                )

    def test_symlinked_scaffold_namespace_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            output = project / "data/output"
            target = output / "entry_drafts"
            target.mkdir(parents=True)
            os.symlink(target, output / "entry_scaffolds")
            with self.assertRaises(ValueError):
                scaffold_destination(project, "root_000858")

    def test_interrupted_backup_is_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            tree = self.build_tree(project)
            root = tree.parent
            backup = root / ".root_000858.backup-test"
            tree.rename(backup)
            recover_interrupted_replacement(root, tree, "root_000858")
            self.assertTrue(tree.is_dir())
            self.assertFalse(backup.exists())

    def test_recovery_precedes_bundle_preflight_and_preserves_ambiguous_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            tree = self.build_tree(project)
            root = tree.parent
            backup = root / ".root_000858.backup-test"
            tree.rename(backup)
            (project / "data/output/entry_bundles/root_000858" / BUNDLE_MANIFEST).unlink()
            with self.assertRaises(ValueError):
                write_scaffolds(
                    copy.deepcopy(self.packet), PACKET_PATH, tree, project
                )
            self.assertTrue(tree.is_dir())
            self.assertFalse(backup.exists())

            tree.rename(backup)
            tree.mkdir()
            (tree / "unmarked.md").write_text("authored", encoding="utf-8")
            with self.assertRaises(ValueError):
                recover_interrupted_replacement(root, tree, "root_000858")
            self.assertTrue(backup.is_dir())

    def test_packet_identity_validation(self):
        packet = copy.deepcopy(self.packet)
        packet["root_envelope_id"] = "root_999999"
        with self.assertRaises(ValueError):
            validate_packet(packet)
        packet = copy.deepcopy(self.packet)
        packet["branches"].append(copy.deepcopy(packet["branches"][0]))
        with self.assertRaises(ValueError):
            validate_packet(packet)
        packet = copy.deepcopy(self.packet)
        packet["branch_lexical_links"][0]["branch_id"] = "B999"
        with self.assertRaises(ValueError):
            validate_packet(packet)

    def test_attachment_join_requires_exact_or_corroborated_form(self):
        links = attachment_links(self.packet)
        self.assertEqual(links["q:1:6:2"]["method"], "exact_word_unit")
        self.assertEqual(
            links["q:2:142:20"]["method"], "unique_root_form_in_ayah"
        )

        packet = copy.deepcopy(self.packet)
        instance = next(
            row
            for row in packet["attachments"]["noun_instances"]
            if row["word_unit_id"] == "q:2:142:22"
        )
        instance["surface"] = "مختلف"
        instance["stem"] = "مختلف"
        links = attachment_links(packet)
        self.assertEqual(links["q:2:142:20"]["method"], "unresolved")

    def test_all_verb_attachment_id_fields_are_collected(self):
        instance = {
            "object_attachment_ids": "object-1;object-2",
            "prep_attachment_ids": "prep-1",
            "subject_attachment_id": "subject-1",
            "clausal_attachment_ids": "clause-1;clause-2",
        }
        self.assertEqual(
            instance_attachment_ids(instance),
            ["prep-1", "object-1", "object-2", "subject-1", "clause-1", "clause-2"],
        )
        self.assertEqual(split_ids("a;b, c"), ["a", "b", "c"])

    def test_branch_scaffold_links_full_evidence_and_separates_no_match(self):
        branch = self.packet["branches"][0]
        text = render_branch(
            self.packet,
            branch,
            [
                row
                for row in self.packet["lexical_senses"]
                if row["root_id"] == branch["root_id"]
                and row["lexical_unit_id"] in {"lu_001", "lu_002", "lu_003"}
            ],
            Path("data/output/entry_bundles/root_000858/branches/root_000858--B001.md"),
        )
        self.assertIn("- Required evidence bundle:", text)
        self.assertIn("- V4 source phrase:", text)
        self.assertIn("#### Packet routing gaps", text)
        self.assertNotIn("#### ayn —", text)
        self.assertNotIn("| [REVIEW REQUIRED] | primary |", text)

    def test_quran_scaffold_contains_raw_provenance_not_agent_labels(self):
        text = render_quran_observatory(self.packet)
        self.assertIn("join=exact_word_unit", text)
        self.assertIn("join=unique_root_form_in_ayah", text)
        self.assertIn("prep_profile", text)
        self.assertNotIn("request frame", text.lower())
        self.assertNotIn("active branch", text.lower())

    def test_generated_scaffold_passes_packet_checks_with_review_markers_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            errors = validate_entry(
                copy.deepcopy(self.packet),
                PACKET_PATH,
                self.assembled_text(tree),
                allow_placeholders=True,
            )
            self.assertEqual(errors, [])

    def test_validator_detects_immutable_branch_and_occurrence_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            text = self.assembled_text(tree)
            text = text.replace(
                "- Arabic image: الطريق المستقيم",
                "- Arabic image: changed",
                1,
            )
            text = text.replace("| 1:6:2:2 | صِّرَٰطَ |", "| 1:6:2:2 | changed |", 1)
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, text, allow_placeholders=True
            )
            self.assertTrue(any("Arabic image" in error for error in errors))
            self.assertTrue(any("Quran occurrence packet-backed" in error for error in errors))

    def test_validator_scopes_each_ayah_and_ignores_fenced_headings(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            text = self.assembled_text(tree)
            ayah = self.packet["qac"]["ayah_contexts"][0]["surface_ar"]
            text = text.replace(ayah, "changed ayah", 1)
            text += "\n```text\n### Census\n| not | a | table |\n```\n"
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, text, allow_placeholders=True
            )
            self.assertTrue(any("Arabic ayah context" in error for error in errors))
            self.assertFalse(any("expected one level-3 heading" in error for error in errors))

    def test_unresolved_review_markers_fail_final_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            errors = validate_entry(
                copy.deepcopy(self.packet),
                PACKET_PATH,
                self.assembled_text(tree),
                allow_placeholders=False,
            )
            self.assertTrue(any("unresolved REVIEW REQUIRED" in error for error in errors))

    def test_resolved_scaffold_passes_final_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            text = self.assembled_text(tree)
            text = re.sub(r"\[REVIEW REQUIRED(?:: [^\]]+)?\]", "resolved", text)
            text = text.replace("- Relationship: resolved", "- Relationship: explicit_support")
            placeholder_row = "| resolved | resolved | resolved | resolved | resolved | resolved | resolved |"
            completed_row = "| rendering | primary | preserves | loses | adds | none | collision checked |"
            text = text.replace(placeholder_row, completed_row)
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, text, allow_placeholders=False
            )
            self.assertEqual(errors, [])

    def test_fenced_immutable_lines_do_not_satisfy_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            text = self.assembled_text(tree)
            field = "- Frozen branch records: 3"
            text = text.replace(field, "", 1)
            text = text.replace(
                "## Branch index",
                f"```text\n{field}\n```\n\n## Branch index",
                1,
            )
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, text, allow_placeholders=True
            )
            self.assertTrue(any("Frozen branch records" in error for error in errors))

    def test_validator_checks_all_generated_branch_and_quran_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            original = self.assembled_text(tree)
            mutations = [
                ("- English scaffold fit: `exact`", "- English scaffold fit: `wrong`"),
                ("- V4 review note: ", "- V4 review note: changed "),
                ("joins=exact_word_unit:1", "joins=changed:1"),
                ("إِلَى:16;عَلَى:7", "changed-profile"),
                ("join=exact_word_unit; instance=q:1:6:2", "join=changed; instance=q:1:6:2"),
            ]
            for old, new in mutations:
                with self.subTest(old=old):
                    self.assertIn(old, original)
                    text = original.replace(old, new, 1)
                    errors = validate_entry(
                        copy.deepcopy(self.packet),
                        PACKET_PATH,
                        text,
                        allow_placeholders=True,
                    )
                    self.assertNotEqual(errors, [])

    def test_generator_rejects_explicit_packet_selector_mismatch(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/build_entry_scaffolds.py",
                "root_999999",
                "--packet",
                str(PACKET_PATH),
            ],
            cwd=PROJECT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match explicit packet", result.stderr + result.stdout)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/build_entry_bundles.py",
                "root_999999",
                "--packet",
                str(PACKET_PATH),
            ],
            cwd=PROJECT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match explicit packet", result.stderr + result.stdout)

    def test_validator_json_setup_errors_are_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            entry = directory / "entry.md"
            entry.write_text("# test\n", encoding="utf-8")
            missing = directory / "missing.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_entry.py",
                    str(entry),
                    "--packet",
                    str(missing),
                    "--json",
                ],
                cwd=PROJECT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertIn("setup_error", payload)

            malformed = directory / "malformed.json"
            malformed.write_text("null\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_entry.py",
                    str(entry),
                    "--packet",
                    str(malformed),
                    "--json",
                ],
                cwd=PROJECT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertIn("setup_error", payload)

    def test_empty_linked_sense_branch_uses_zero_row_table(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = copy.deepcopy(self.packet)
            packet["branch_lexical_links"] = [
                link
                for link in packet["branch_lexical_links"]
                if link["branch_id"] != "B003"
            ]
            tree = self.build_tree(Path(directory), packet=packet)
            errors = validate_entry(
                packet,
                PACKET_PATH,
                self.assembled_text(tree, packet),
                allow_placeholders=True,
            )
            self.assertEqual(errors, [])

    def test_wrapped_ayah_paragraph_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            text = self.assembled_text(tree)
            ayah = self.packet["qac"]["ayah_contexts"][1]["surface_ar"]
            words = ayah.split()
            wrapped = " ".join(words[:4]) + "\n" + " ".join(words[4:])
            text = text.replace(ayah, wrapped, 1)
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, text, allow_placeholders=True
            )
            self.assertEqual(errors, [])

    def test_snapshot_contrast_and_bibliography_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            original = self.assembled_text(tree)
            mutations = [
                (
                    f"- Source snapshot: `{PACKET_PATH}`",
                    "- Source snapshot: `wrong/root_000858.json.bak`",
                ),
                (
                    "| Arabic neighbor | English transliteration | Türkçe çevriyazı | Shared zone | Distinguishing axis | Evidence |",
                    "removed contrast table",
                ),
                (
                    "### Target-language usage sources\n\n- [REVIEW REQUIRED: list only English and Turkish sources actually used]",
                    "### Target-language usage sources\n",
                ),
            ]
            for old, new in mutations:
                with self.subTest(old=old):
                    self.assertIn(old, original)
                    errors = validate_entry(
                        copy.deepcopy(self.packet),
                        PACKET_PATH,
                        original.replace(old, new, 1),
                        allow_placeholders=True,
                    )
                    self.assertNotEqual(errors, [])

    def test_conflicting_duplicate_fields_and_empty_contrasts_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            original = self.assembled_text(tree)
            duplicate = original.replace(
                "- Frozen branch records: 3",
                "- Frozen branch records: 3\n- Frozen branch records: 999",
                1,
            )
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, duplicate, True
            )
            self.assertTrue(any("Frozen branch records" in error for error in errors))

            empty_duplicate = original.replace(
                "- English scaffold gap note:",
                "- English scaffold gap note:\n- English scaffold gap note: forged",
                1,
            )
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, empty_duplicate, True
            )
            self.assertTrue(
                any("English scaffold gap note" in error for error in errors)
            )

            contrast_row = (
                "| [REVIEW REQUIRED: verified neighbor or none] | [REVIEW REQUIRED] | "
                "[REVIEW REQUIRED] | [REVIEW REQUIRED] | [REVIEW REQUIRED] | "
                "[REVIEW REQUIRED] |"
            )
            errors = validate_entry(
                copy.deepcopy(self.packet),
                PACKET_PATH,
                original.replace(contrast_row, "", 1),
                True,
            )
            self.assertTrue(any("contrasts requires" in error for error in errors))

    def test_colon_bearing_unmatched_handle_is_validated_as_a_literal(self):
        packet = copy.deepcopy(self.packet)
        packet["branches"][0]["source_refs"] = "sihah:file=missing"
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory), packet=packet)
            text = self.assembled_text(tree, packet)
            self.assertIn("- `sihah:file=missing`", text)
            errors = validate_entry(packet, PACKET_PATH, text, True)
            self.assertEqual(errors, [])

    def test_aggregate_and_bibliography_parent_order_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            original = self.assembled_text(tree)
            aggregate = (
                "#### Aggregate verb frames (packet fields)\n\n"
                "- No packet rows.\n\n"
            )
            moved = original.replace(aggregate, "", 1).replace(
                "### Forms and lemmas", aggregate + "### Forms and lemmas", 1
            )
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, moved, True
            )
            self.assertTrue(any("aggregate" in error.lower() for error in errors))

            errors = validate_entry(
                copy.deepcopy(self.packet),
                PACKET_PATH,
                original + "\n## Extra section\n",
                True,
            )
            self.assertTrue(any("bibliography" in error.lower() for error in errors))

    def test_four_backtick_fence_and_wrapped_source_quote(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = self.build_tree(Path(directory))
            original = self.assembled_text(tree)
            field = "- Frozen branch records: 3"
            fenced = original.replace(field, "", 1).replace(
                "## Branch index",
                f"````text\n{field}\n```\n\n## Branch index",
                1,
            )
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, fenced, True
            )
            self.assertTrue(any("Frozen branch records" in error for error in errors))

            quote = "> [REVIEW REQUIRED: exact relevant Arabic excerpt from the supplied source text]"
            wrapped = original.replace(
                quote,
                "> [REVIEW REQUIRED: exact relevant Arabic excerpt\n"
                "> from the supplied source text]",
                1,
            )
            errors = validate_entry(
                copy.deepcopy(self.packet), PACKET_PATH, wrapped, True
            )
            self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
