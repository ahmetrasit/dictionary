"""Focused contract checks for reviewed supplemental export."""

import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from v2.scripts.assemble_entry import canonical_sha256, json_content, sha256_file
from v2.scripts.export_reviewed_supplement import (
    _citation_notes,
    _headword_export,
    _reviewed_response,
    _root_export,
    _staged_task,
)
from v2.scripts.validate_entry import ContractError
import v2.scripts.export_reviewed_supplement as exporter


class SupplementalExportTest(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {"sourceKey": "s1", "sourceId": "lisan", "sourceType": "lexicon",
             "quotationAr": "قول معجمي", "sourceTitle": "Lisān al-ʿArab"},
            {"sourceKey": "s2", "sourceId": "ibn_hisham", "sourceType": "grammar",
             "quotationAr": "قول نحوي", "sourceTitle": "Mughnī al-Labīb"},
        ]
        self.sense = {"senseId": "B001", "imageAr": "صورة", "whatIsAr": "داخل",
                      "whatIsNotAr": "خارج", "sourceKeys": ["s1", "s2"],
                      "claims": [
                          {"claimId": "bc_001", "sourceKeys": ["s1"]},
                          {"claimId": "bc_002", "sourceKeys": ["s2"]},
                      ]}
        self.authored = {
            "branch_ref": "root_900001/B001",
            "identity_judgment": {"rationale": "Reviewed identity.",
                                  "boundary_note": "Reviewed boundary."},
            "concept_map": {"definition": "Reviewed definition."},
            "concept_gloss": {"text": "core gloss", "applicability": "Broad use.",
                              "error_profile": {"fit": "none", "preserves": "Core sense.",
                                                "loses": None, "adds": None, "collision": None}},
            "contextual_glosses": [],
            "excluded_glosses": [],
            "source_synthesis": {"source_details": [
                {"claim_ids": ["bc_001"], "summary": "Sözlük tanıklığı."},
                {"claim_ids": ["bc_002"], "summary": "Nahiv tanıklığı."},
            ], "common_summary": "Reviewed source summary."},
            "lexicalization_scope": {"branch_kind": "bare", "note": "Reviewed bare use."},
        }
        self.meta = {"registryPath": "data/supplemental/registry.v1.json",
                     "registrySha256": "a" * 64,
                     "intakePath": "data/supplemental/entries/root_900001.json",
                     "intakeSha256": "b" * 64}
        self.occurrences = {"summary": {"morpheme_count": 1}, "forms": [],
                            "ayahs": [], "occurrences": []}

    def test_root_preserves_typed_citations_and_badges_only_lexicons(self):
        intake = {"sources": self.sources, "senses": [self.sense]}
        response = {"branches": [self.authored], "root_profile": {"summary": "reviewed"}}
        value = _root_export("root_900001", {"task": "writer"}, response, intake,
                             self.meta, {"lisan": {"badgeCode": "LI"}}, self.occurrences)
        branch = value["branches"][0]
        self.assertEqual(value["artifact_format"], "dictionary-v2-root-entry-draft-v1")
        self.assertEqual(branch["sources"], ["LI"])
        self.assertEqual(branch["citations"], self.sources)
        self.assertEqual(branch["source_note"], {"LI": "Sözlük tanıklığı."})
        self.assertEqual(branch["citationNotes"], [
            {"sourceKey": "s1", "noteTr": "Sözlük tanıklığı."},
            {"sourceKey": "s2", "noteTr": "Nahiv tanıklığı."},
        ])
        self.assertEqual(branch["source_phrase_ar"],
                         "قول معجمي (lisan:s1)؛ قول نحوي (ibn_hisham:s2)")

    def test_headword_has_no_root_envelope_and_keeps_editorial_wrapper(self):
        sense = {**self.sense, "senseId": "S001"}
        authored = {**self.authored, "sense_ref": "headword_000001/S001"}
        authored.pop("branch_ref")
        intake = {"headwordArabic": "كَيْفَ", "binding": {"selector": {}},
                  "sources": self.sources, "senses": [sense]}
        response = {"senses": [authored], "headword_profile": {"summary": "reviewed"}}
        value = _headword_export("headword_000001", {"task": "writer"}, response,
                                 intake, self.meta, self.occurrences)
        self.assertEqual(value["artifact_format"], "dictionary-v2-headword-entry-draft-v1")
        self.assertEqual(value["headwordId"], "headword_000001")
        self.assertEqual(value["citations"], self.sources)
        self.assertEqual(value["senses"][0]["lexicalizationKind"], "bare")
        self.assertEqual(value["senses"][0]["citationKeys"], ["s1", "s2"])
        self.assertEqual(value["senses"][0]["definition"], "Reviewed definition.")
        self.assertEqual(value["senses"][0]["conceptGloss"], "core gloss")
        self.assertEqual(value["senses"][0]["glossAssessments"][0]["text"], "core gloss")
        self.assertIn("Reviewed identity.", value["senses"][0]["usageNote"])
        self.assertIn("Reviewed source summary.", value["senses"][0]["usageNote"])
        self.assertNotIn("root_envelope_id", value)
        self.assertNotIn("root_profile", value)
        self.assertNotIn("occurrence_evidence", value)

    def test_source_detail_note_follows_claim_keys_not_same_work_first_key(self):
        second_lisan = {**self.sources[0], "sourceKey": "s3", "quotationAr": "قول آخر"}
        sources = {row["sourceKey"]: row for row in [*self.sources, second_lisan]}
        sense = {**self.sense, "sourceKeys": ["s1", "s3", "s2"],
                 "claims": [{"claimId": "bc_001", "sourceKeys": ["s3"]}]}
        authored = {"source_synthesis": {"source_details": [
            {"claim_ids": ["bc_001"], "summary": "Only the second passage."}
        ]}}
        self.assertEqual(_citation_notes(authored, sense, sources),
                         [{"sourceKey": "s3", "noteTr": "Only the second passage."}])

    def test_staged_bundle_requires_exact_copied_evidence_and_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            input_dir = work / "input"
            input_dir.mkdir()
            canonical = {"format": 4, "generated_by": "v2/scripts/prepare_supplemental_entry.py",
                         "role": "root_writer", "entryKind": "lexical_root",
                         "language": "tr", "root_envelope_id": "root_900001",
                         "branch_roster": ["root_900001/B001"],
                         "supplementalIntake": self.meta}
            staged = copy.deepcopy(canonical)
            staged["canonical_task_sha256"] = canonical_sha256(canonical)
            for key, name in (("prompt", "prompt.md"), ("response_schema", "response.schema.json"),
                              ("evidence", "evidence.json")):
                path = input_dir / name
                path.write_text(key, encoding="utf-8")
                canonical[key] = {"path": str(path), "sha256": sha256_file(path)}
                staged[key] = {"path": name, "sha256": sha256_file(path)}
            staged["canonical_task_sha256"] = canonical_sha256(canonical)
            output = work / "output/root_900001_entry.json"
            staged["output"] = {"path": "../output/root_900001_entry.json"}
            task_path = input_dir / "task.json"
            task_path.write_text(json_content(staged), encoding="utf-8")
            _staged_task(task_path, canonical, "root_writer", output)
            (input_dir / "evidence.json").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "sealed copy"):
                _staged_task(task_path, canonical, "root_writer", output)

    def test_repair_may_change_only_recorded_field(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "tasks").mkdir()
            (work / "output").mkdir()
            (work / "review/input").mkdir(parents=True)
            (work / "review/output").mkdir()
            writer_task = {"root_envelope_id": "root_900001", "entryKind": "lexical_root",
                           "branch_roster": ["root_900001/B001"], "evidence": {"path": "x", "sha256": "a"}}
            snapshot = {"branches": [{"branch_ref": "root_900001/B001",
                                      "concept_gloss": {"text": "Before"},
                                      "source_synthesis": {"source_details": []}}],
                        "root_profile": {"summary": "Preserve this"}}
            live = copy.deepcopy(snapshot)
            live["branches"][0]["concept_gloss"]["text"] = "After"
            output = work / "output/root_900001_entry.json"
            output.write_text(json_content(live), encoding="utf-8")
            snapshot_path = work / "review/input/writer_response.json"
            snapshot_path.write_text(json_content(snapshot), encoding="utf-8")
            review_task = {"writer_task_sha256": canonical_sha256(writer_task),
                           "branch_roster": writer_task["branch_roster"],
                           "evidence": writer_task["evidence"],
                           "writer_response": {"path": str(output),
                                               "sha256": sha256_file(snapshot_path)}}
            (work / "tasks/root_reviewer.json").write_text(json_content(review_task), encoding="utf-8")
            review = {"verdict": "repair", "issues": [{"target_ref": "root_900001/B001",
                                                       "field": "concept_gloss"}]}
            (work / "review/output/root_review.json").write_text(json_content(review), encoding="utf-8")
            patches = [
                mock.patch.object(exporter, "_task_identity"),
                mock.patch.object(exporter, "_staged_task"),
                mock.patch.object(exporter, "_validate_writer"),
                mock.patch.object(exporter, "validate_fragment"),
                mock.patch.object(exporter, "validate_review"),
            ]
            for patcher in patches:
                patcher.start()
            try:
                result = _reviewed_response(work, writer_task, {}, {}, work,
                                            headword=False)
                self.assertEqual(result, live)
                rebound = copy.deepcopy(snapshot)
                rebound["root_profile"]["summary"] = "Rebound snapshot"
                snapshot_path.write_text(json_content(rebound), encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "lacks a snapshot bound"):
                    _reviewed_response(work, writer_task, {}, {}, work,
                                       headword=False)
                snapshot_path.write_text(json_content(snapshot), encoding="utf-8")
                live["root_profile"]["summary"] = "Unauthorized change"
                output.write_text(json_content(live), encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "protected root profile"):
                    _reviewed_response(work, writer_task, {}, {}, work,
                                       headword=False)
                live["root_profile"]["summary"] = "Preserve this"
                output.write_text(json_content(live), encoding="utf-8")
                review["verdict"] = "editorial_review"
                (work / "review/output/root_review.json").write_text(json_content(review), encoding="utf-8")
                with self.assertRaisesRegex(ContractError, "Unpublishable"):
                    _reviewed_response(work, writer_task, {}, {}, work,
                                       headword=False)
            finally:
                for patcher in reversed(patches):
                    patcher.stop()


if __name__ == "__main__":
    unittest.main()
