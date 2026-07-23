import copy
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import v2.scripts.build_branch_evidence as evidence_module
import v2.scripts.render_occurrences as occurrence_module
from v2.scripts.assemble_entry import (
    agent_root_evidence,
    assemble,
    canonical_sha256,
    json_content,
    load_evidence,
    load_task_fragment,
    validate_fragment,
    write_root_writer_splits,
)
from v2.scripts.build_branch_evidence import (
    DEFAULT_FURUQ,
    build_packages,
    dictionary_basis,
    packet_sources,
    write_packages,
)
from v2.scripts.create_entry import (
    PROMPTS,
    atomic_write,
    check_output_targets,
    check_pinned_evidence,
    prepare_initial_tasks,
    prepare_inputs,
    publish_pair,
)
from v2.scripts.accept_root_writer import accept, validate_repair_preservation
from v2.scripts.accept_root_review import (
    accept as accept_root_review,
    check_pass as check_root_review_pass,
    check_review,
    main as accept_root_review_main,
    repair_scope as semantic_repair_scope,
)
from v2.scripts.check_root_review import main as check_root_review_main
from v2.scripts.check_root_writer import check as check_root_writer
from v2.scripts.finalize_entry import finalize
from v2.scripts.repair_scope import classify
from v2.scripts.prepare_root_review import prepare as prepare_root_review
from v2.scripts.stage_root_reviewer import stage as stage_root_reviewer
from v2.scripts.stage_root_writer import stage
from v2.scripts.validate_agent_output import validate as validate_agent_output
from v2.scripts.render_entry import render, render_markdown
from v2.scripts.render_occurrences import load_packet
from v2.scripts.validate_entry import ContractError, load_json, validate_entry


PROJECT = Path(__file__).resolve().parents[2]
SOURCE_ENTRY = PROJECT / "v2/examples/root_000858.tr.entry.json"
ARABIC_RUN_RE = re.compile(r"[\u0600-\u06FF]+")


def plain_target_fixture(value):
    if isinstance(value, str):
        return ARABIC_RUN_RE.sub("Arapça söz", value)
    if isinstance(value, list):
        return [plain_target_fixture(item) for item in value]
    if isinstance(value, dict):
        return {key: plain_target_fixture(item) for key, item in value.items()}
    return value


def write_response(path: Path, task_path: Path, response: dict) -> None:
    task = load_json(task_path)
    atomic_write(
        path,
        json_content({"inputs_sha256": canonical_sha256(task), **response}),
    )


def reduced_root_response(task: dict, evidence: dict) -> dict:
    branches = []
    for index, supplied in enumerate(evidence["branches"], start=1):
        ref = supplied["branch_ref"]
        claim_ids = [row["claim_id"] for row in supplied["source_claims"]]
        neighbor_ref = supplied["neighbor_refs"][0]
        distinction = {
            "neighbor_ref": neighbor_ref,
            "relation_type": "near_neighbor",
            "boundary_match": "partial",
            "focus_only": "Bu dal kendi anlam çekirdeğini ve kullanım sınırını korur.",
            "neighbor_only": None,
            "gloss": "Yakın alandaki başka bir anlam dalıdır.",
            "shared_zone": "İki dal aynı geniş anlam alanında buluşur.",
            "distinction": "Odak dalın çekirdeği komşu dalın çekirdeğiyle aynı değildir.",
        }
        definition = (
            f"Bu dal, {index}. kanıt kümesindeki ortak anlam çekirdeğini ve onun "
            "sınırlarını birlikte açıklar."
        )
        concept_gloss = {
            "text": f"{index}. dalın ortak anlam çekirdeği",
            "applicability": "Dalın genel kavram haritasını açıklamak için kullanılır.",
            "error_profile": {
                "fit": "none",
                "preserves": "Ortak anlam çekirdeğini korur.",
                "loses": None,
                "adds": None,
                "collision": None,
            },
            "facet_ids": ["F001"],
        }

        branches.append(
            {
                "branch_ref": ref,
                "concept_map": {
                    "definition": definition,
                    "facets": [
                        {
                            "facet_id": "F001",
                            "role": "core",
                            "statement": definition,
                            "claim_ids": claim_ids,
                        }
                    ],
                },
                "source_synthesis": {
                    "common_summary": (
                        "Kaynak iddiaları bu dalın ortak anlam çekirdeğini ve "
                        "kullanım sınırını birlikte destekler."
                    ),
                    "common_claim_ids": claim_ids,
                    "source_details": [],
                    "supporting_claim_ids": [],
                    "duplicate_claims": [],
                },
                "concept_gloss": concept_gloss,
                "contextual_glosses": [],
                "lexical_glosses": [
                    {
                        "lexical_unit_id": claim["lexical_unit_id"],
                        "rendering_kind": claim["rendering_policy"],
                        "target_gloss": (
                            None
                            if claim["rendering_policy"] == "proper_name"
                            else plain_target_fixture(claim["sense_ar"])
                        ),
                    }
                    for claim in supplied["source_claims"]
                ],
                "excluded_glosses": [
                    {
                        "text": "genel ve belirsiz yönelim",
                        "category": "confusable",
                        "error_profile": {
                            "fit": "displacement",
                            "preserves": "Yönelme düşüncesinin bir bölümünü korur.",
                            "loses": "Dalın ayırt edici anlam çekirdeğini siler.",
                            "adds": None,
                            "collision": "Başka anlam dallarıyla kolayca karışır.",
                        },
                    }
                ],
                "neighbor_distinctions": [distinction],
                "neighbor_coverage_note": (
                    "Adaylar değerlendirildi ve bu komşu sınırı açıklamak için "
                    "yeterli bulundu."
                ),
            }
        )
    response = {
        "branches": plain_target_fixture(branches),
        "root_profile": {
            "summary": (
                "Beş donmuş dal, kasıtlı yönelme ve ritüel uzmanlaşma ile su, "
                "kuş ve özel ad dallarını karma bir yapı içinde birleştirir."
            ),
            "polysemy": "polysemic",
            "organization": "multi_branch",
        },
    }
    validate_fragment(response, "root_writer", Path("synthetic-root-response.json"))
    self_roster = [row["branch_ref"] for row in branches]
    if self_roster != task["branch_roster"]:
        raise AssertionError((self_roster, task["branch_roster"]))
    return response


def write_approved_transliteration_review(
    path: Path,
    response: dict,
    transliterations: dict,
) -> None:
    values = {"root_profile": "Deneme kökü"}
    required = {"root_profile"}
    for branch_index, branch in enumerate(response["branches"], start=1):
        required.add(f"branch:{branch['branch_ref']}")
        values[f"branch:{branch['branch_ref']}"] = f"Deneme dalı {branch_index}"
        for neighbor_index, neighbor in enumerate(
            branch["neighbor_distinctions"], start=1
        ):
            key = f"neighbor:{neighbor['neighbor_ref']}"
            required.add(key)
            values[key] = f"Deneme komşusu {branch_index}-{neighbor_index}"
    anchors = {row["key"]: row["arabic"] for row in transliterations["gaps"]}
    required -= set(transliterations.get("values", {}))
    review = {
        "format": "dictionary-v2-transliteration-review-v1",
        "root_envelope_id": transliterations["root_envelope_id"],
        "language": transliterations["language"],
        "items": [
            {
                "key": key,
                "arabic": anchors.get(key, "test anchor"),
                "suggested_value": "",
                "status": "approved",
                "value": values[key],
            }
            for key in sorted(required)
        ],
    }
    atomic_write(path, json_content(review))


def write_approved_name_review(path: Path, evidence: dict) -> None:
    items = []
    for branch in evidence["branches"]:
        for claim in branch["source_claims"]:
            if claim["rendering_policy"] != "proper_name":
                continue
            items.append(
                {
                    "key": (
                        f"name:{branch['branch_ref']}:"
                        f"{claim['lexical_unit_id']}"
                    ),
                    "arabic": claim["expression_ar"],
                    "status": "approved",
                    "value": f"Test adı {claim['lexical_unit_id']}",
                }
            )
    atomic_write(
        path,
        json_content(
            {
                "format": "dictionary-v2-name-review-v1",
                "root_envelope_id": "root_001697",
                "language": "tr",
                "items": items,
            }
        ),
    )


def write_pass_review(work_dir: Path, writer_task: Path, writer_response: Path) -> None:
    review_task = work_dir / "tasks/root_reviewer.json"
    prepare_root_review(writer_task, writer_response, review_task)
    raw = work_dir / "review/output/root_review.json"
    atomic_write(
        raw,
        json_content(
            {
                "verdict": "pass",
                "summary": "Yapılandırılmış yanıt kanıtla uyumlu ve yayına hazırdır.",
                "issues": [],
            }
        ),
    )
    accept_root_review(review_task, raw, work_dir / "fragments/root_review.json")


class EntryWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load_json(SOURCE_ENTRY)
        cls.packet_path, cls.packet = load_packet(PROJECT, "root_001697", None)
        _source_path, cls.source_packet = load_packet(PROJECT, "root_000858", None)

    def prepare_run(self, directory: Path):
        work_dir = directory / "work"
        _packet_path, _packet, index_path, index = prepare_inputs(
            "root_001697", "tr", None, DEFAULT_FURUQ, None
        )
        task_path = prepare_initial_tasks(index_path, index, "tr", work_dir)[0]
        task = load_json(task_path)
        evidence = load_json(work_dir / "inputs/root_evidence.json")
        response = reduced_root_response(task, evidence)
        write_response(work_dir / "fragments/root_001697_entry.json", task_path, response)
        write_pass_review(
            work_dir, task_path, work_dir / "fragments/root_001697_entry.json"
        )
        write_approved_transliteration_review(
            work_dir / "inputs/transliteration_review.json",
            response,
            load_json(work_dir / "inputs/transliterations.json"),
        )
        write_approved_name_review(
            work_dir / "inputs/name_review.json",
            evidence,
        )
        write_root_writer_splits(index_path, work_dir, "tr")
        return index_path, index, work_dir, task_path, response

    def test_branch_packages_are_scoped_and_counted(self):
        index, packages = build_packages(self.packet, self.packet_path, DEFAULT_FURUQ)
        self.assertEqual(index["format"], 2)
        self.assertEqual(len(packages), 5)
        for package in packages.values():
            self.assertEqual(package["format"], 2)
            self.assertTrue(package["dictionary_basis"]["dictionary_count"])
            self.assertTrue(package["furuq_candidates"])

    def test_postfix_theme_port_is_used_for_qnet_fallback(self):
        _index, packages = build_packages(self.packet, self.packet_path, DEFAULT_FURUQ)
        package = packages["root_001697--B002.json"]
        coverage = package["qnet_focus_coverage"]
        self.assertFalse(coverage["raw_keyword_exact_port"])
        self.assertTrue(coverage["postfix_exact_port"])
        self.assertEqual(coverage["theme_scope"], "branch")
        self.assertTrue(package["qnet_theme_overlap_candidates"])

    def test_dictionary_basis_rejects_non_exact_routes(self):
        packet = copy.deepcopy(self.packet)
        branch = packet["branches"][0]
        branch["source_refs"] += ";missing:reference"
        with self.assertRaisesRegex(ValueError, "absent from packet dictionary rows"):
            dictionary_basis(branch, packet_sources(packet))

    def test_package_check_rejects_stale_extra_branch_files(self):
        index, packages = build_packages(self.packet, self.packet_path, DEFAULT_FURUQ)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            write_packages(output, index, packages, check=False)
            (output / "branches/stale.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unmarked file"):
                write_packages(output, index, packages, check=True)

    def test_prepare_creates_one_deduplicated_root_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            work_dir = directory / "work"
            _p, _packet, index_path, index = prepare_inputs(
                "root_001697", "tr", None, DEFAULT_FURUQ, None
            )
            tasks = prepare_initial_tasks(index_path, index, "tr", work_dir)
            self.assertEqual(set(PROMPTS), {"root_writer", "root_reviewer"})
            self.assertEqual(tasks, [work_dir / "tasks/root_writer.json"])
            task = load_json(tasks[0])
            self.assertEqual(task["role"], "root_writer")
            self.assertNotIn("entry_contract", task)
            evidence = load_json(work_dir / "inputs/root_evidence.json")
            self.assertEqual(len(evidence["branches"]), 5)
            self.assertEqual(evidence["format"], "dictionary-v2-agent-root-evidence-v4")
            self.assertTrue(all(row["source_claims"] for row in evidence["branches"]))
            policies = {
                claim["lexical_unit_id"]: claim["rendering_policy"]
                for branch in evidence["branches"]
                for claim in branch["source_claims"]
            }
            self.assertEqual(policies["lu_014"], "proper_name")
            self.assertEqual(policies["lu_017"], "ordinary")
            self.assertNotIn("transliteration_gaps", evidence)
            self.assertNotIn("transliterations", task["coordinator"])
            total_refs = sum(len(row["neighbor_refs"]) for row in evidence["branches"])
            self.assertLess(len(evidence["neighbor_registry"]), total_refs)

    def test_production_prompts_are_role_bounded_and_root_generic(self):
        writer = PROMPTS["root_writer"].read_text(encoding="utf-8")
        reviewer = PROMPTS["root_reviewer"].read_text(encoding="utf-8")
        orchestrator = (
            PROJECT / "v2/prompts/entry-orchestrator.md"
        ).read_text(encoding="utf-8")

        self.assertNotRegex(writer, r"(?:root|lu)_[0-9]{3,6}")
        self.assertIn("Do not delegate, spawn another agent", writer)
        self.assertIn("Do not delegate, spawn another agent", reviewer)
        self.assertIn("Never spawn a worker merely to run a command", orchestrator)
        self.assertIn("Run every deterministic or operational task yourself", orchestrator)

    def test_regular_writer_input_has_only_bounded_contracts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, _index, work_dir, task_path, _response = self.prepare_run(
                directory
            )
            workspace = work_dir / "input"
            isolated = stage(task_path)
            self.assertNotIn("coordinator", isolated)
            self.assertNotIn("entry_contract", isolated)
            bound_names = {
                Path(item["path"]).name
                for item in (isolated["prompt"], isolated["response_schema"], isolated["evidence"])
            }
            self.assertEqual(len(bound_names), 3)
            for item in (isolated["prompt"], isolated["response_schema"], isolated["evidence"]):
                copied = (workspace / item["path"]).resolve()
                copied.relative_to(workspace.resolve())
                self.assertTrue(copied.is_file())
            self.assertTrue((workspace / "instructions.md").is_file())
            self.assertTrue((work_dir / "output").is_dir())
            self.assertEqual(
                isolated["output"]["path"], "../output/root_001697_entry.json"
            )
            self.assertEqual(
                isolated["validation"]["command"][:2],
                ["python3", "v2/scripts/validate_agent_output.py"],
            )
            self.assertEqual(
                {path.name for path in workspace.iterdir()},
                {
                    "instructions.md",
                    "task.json",
                    "prompt.md",
                    "response.schema.json",
                    "evidence.json",
                },
            )
            self.assertNotIn(
                "# Root writer",
                (workspace / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "do not use `/tmp`",
                (workspace / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "correct it from the exact error",
                (workspace / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Do not delegate, spawn another agent",
                (workspace / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Run no command except the exact argv",
                (workspace / "instructions.md").read_text(encoding="utf-8"),
            )
            write_root_writer_splits(index_path, work_dir, "tr", check=True)

    def test_writer_self_validation_preserves_failed_output_for_in_place_fix(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, task_path, response = self.prepare_run(
                directory
            )
            stage(task_path)
            raw = work_dir / "output/root_001697_entry.json"
            atomic_write(raw, json_content(response))
            role, path, checked = validate_agent_output(work_dir / "input/task.json")
            self.assertEqual(role, "root_writer")
            self.assertEqual(path, raw.resolve())
            self.assertEqual(len(checked["branches"]), 5)

            invalid = copy.deepcopy(response)
            invalid["branches"][4]["concept_map"]["definition"] += " {{lu_017}}"
            atomic_write(raw, json_content(invalid))
            with self.assertRaisesRegex(
                ContractError,
                "placeholders are allowed only for declared proper names.*lu_017",
            ):
                validate_agent_output(work_dir / "input/task.json")
            self.assertTrue(raw.is_file())
            self.assertIn("{{lu_017}}", raw.read_text(encoding="utf-8"))

    def test_semantic_reviewer_uses_bounded_regular_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, _task, _response = self.prepare_run(
                directory
            )
            task_path = work_dir / "tasks/root_reviewer.json"
            staged = stage_root_reviewer(task_path)
            review_input = work_dir / "review/input"
            self.assertEqual(
                {path.name for path in review_input.iterdir()},
                {
                    "instructions.md",
                    "task.json",
                    "prompt.md",
                    "response.schema.json",
                    "evidence.json",
                    "writer_response.json",
                },
            )
            self.assertEqual(staged["output"]["path"], "../output/root_review.json")
            self.assertEqual(
                staged["validation"]["command"][:2],
                ["python3", "v2/scripts/validate_agent_output.py"],
            )
            self.assertNotIn(
                "# Root semantic reviewer",
                (review_input / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Do not use `/tmp`",
                (review_input / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Do not delegate, spawn another agent",
                (review_input / "instructions.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Run no command except the exact argv",
                (review_input / "instructions.md").read_text(encoding="utf-8"),
            )
            raw = work_dir / "review/output/root_review.json"
            atomic_write(
                raw,
                json_content(
                    {
                        "verdict": "pass",
                        "summary": (
                            "Yapılandırılmış yanıt kanıtla uyumlu ve yayına hazırdır."
                        ),
                        "issues": [],
                    }
                ),
            )
            role, path, checked = validate_agent_output(
                work_dir / "review/input/task.json"
            )
            self.assertEqual(role, "root_reviewer")
            self.assertEqual(path, raw.resolve())
            self.assertEqual(checked["verdict"], "pass")

    def test_semantic_repair_scope_is_evidence_grounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, _task, _response = self.prepare_run(
                directory
            )
            review_task = work_dir / "tasks/root_reviewer.json"
            task = load_json(review_task)
            issue = {
                "target_ref": "root_001697/B001",
                "field": "concept_gloss",
                "severity": "major",
                "confidence": "high",
                "claim_ids": ["lu_001"],
                "evidence_conflict": (
                    "Birincil karşılık bilinçli seçme öğesini görünür biçimde taşımıyor."
                ),
                "smallest_correction": (
                    "Karşılığı bilinçli seçme ve yönelmeyi birlikte söyleyecek biçimde düzelt."
                ),
            }
            raw = directory / "repair-review.json"
            raw.write_text(
                json_content(
                    {
                        "verdict": "repair",
                        "summary": "Bir dalda kanıtla desteklenen sınırlı bir düzeltme gerekiyor.",
                        "issues": [issue],
                    }
                ),
                encoding="utf-8",
            )
            accepted_path = directory / "accepted-review.json"
            accepted = accept_root_review(review_task, raw, accepted_path)
            self.assertEqual(check_review(review_task, accepted_path)["verdict"], "repair")
            with self.assertRaisesRegex(ContractError, "semantic_review_repair"):
                check_root_review_pass(review_task, accepted_path)
            self.assertEqual(
                semantic_repair_scope(accepted, task),
                {
                    "repairable_by": "root_writer",
                    "editable_branch_indexes": [0],
                    "root_editable": False,
                },
            )

            canonical_review = work_dir / "fragments/root_review.json"
            review_output = work_dir / "review/output/root_review.json"
            review_output.parent.mkdir(parents=True, exist_ok=True)
            review_output.write_text(raw.read_text(encoding="utf-8"), encoding="utf-8")
            with mock.patch("builtins.print"):
                self.assertEqual(
                    accept_root_review_main(
                        [
                            str(review_task),
                            str(review_output),
                            "--output",
                            str(canonical_review),
                        ]
                    ),
                    0,
                )
            sidecars = (
                work_dir / "review/output/semantic_review_error.txt",
                work_dir / "review/output/repair_scope.json",
            )
            for path in sidecars:
                self.assertTrue(path.is_file())
                path.unlink()
            with mock.patch("builtins.print"):
                self.assertEqual(
                    accept_root_review_main(
                        [
                            str(review_task),
                            str(canonical_review),
                            "--output",
                            str(canonical_review),
                        ]
                    ),
                    0,
                )
            for path in sidecars:
                self.assertTrue(path.is_file())
            with mock.patch("builtins.print"):
                self.assertEqual(
                    check_root_review_main(
                        [
                            str(review_task),
                            str(canonical_review),
                            "--any-verdict",
                        ]
                    ),
                    0,
                )

            issue["confidence"] = "low"
            raw.write_text(
                json_content(
                    {
                        "verdict": "repair",
                        "summary": "Belirsiz bir değerlendirme doğrudan onarıma gönderilmemelidir.",
                        "issues": [issue],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "editorial_review"):
                accept_root_review(review_task, raw, directory / "rejected-review.json")

    def test_proper_name_queue_is_writer_completed_and_substituted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, _index, work_dir, task_path, response = self.prepare_run(
                directory
            )
            branch = response["branches"][4]
            lexical = branch["lexical_glosses"][0]
            self.assertEqual(lexical["lexical_unit_id"], "lu_014")
            self.assertEqual(lexical["rendering_kind"], "proper_name")
            self.assertIsNone(lexical["target_gloss"])
            branch["concept_map"]["definition"] = (
                "Bu dal, {{lu_014}} adı çevresindeki kişi ve yer kullanımlarını anlatır."
            )
            branch["concept_map"]["facets"][0]["statement"] = (
                "{{lu_014}} kişi ve yer adı olarak kullanılır."
            )
            raw = directory / "proper-name-response.json"
            raw.write_text(json_content(response), encoding="utf-8")
            accept(task_path, raw, work_dir / "fragments/root_001697_entry.json")
            (work_dir / "inputs/name_review.json").unlink()
            with self.assertRaisesRegex(ContractError, "needs_name_review"):
                write_root_writer_splits(index_path, work_dir, "tr")
            review_path = work_dir / "inputs/name_review.json"
            review = load_json(review_path)
            self.assertIn("Root writer completion queue", review["instructions"])
            self.assertEqual(len(review["items"]), 4)
            self.assertTrue(all(item["value"] == "" for item in review["items"]))
            values = {
                "lu_014": "Yemame",
                "lu_015": "Yemame",
                "lu_016": "Yime",
                "lu_018": "Yemame Ovası",
            }
            for item in review["items"]:
                lexical_id = item["key"].rsplit(":", 1)[-1]
                item["status"] = "approved"
                item["value"] = values[lexical_id]
            atomic_write(review_path, json_content(review))
            write_root_writer_splits(index_path, work_dir, "tr")
            fragment = load_json(
                work_dir / "fragments/branches/root_001697--B005.json"
            )
            self.assertIn("Yemame adı", fragment["concept_map"]["definition"])
            self.assertEqual(fragment["lexical_glosses"][0]["target_gloss"], "Yemame")

    def test_source_claim_ids_prevent_cross_source_attribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, _index, work_dir, task_path, response = self.prepare_run(
                directory
            )
            synthesis = response["branches"][4]["source_synthesis"]
            synthesis["common_claim_ids"].remove("lu_017")
            synthesis["source_details"] = [
                {
                    "claim_ids": ["lu_017"],
                    "kind": "derivation",
                    "summary": (
                        "Bu kaynak, yer adına bağlı kişi veya şeyi anlatan ayrı bir biçim verir."
                    ),
                }
            ]
            fragment_path = work_dir / "fragments/root_001697_entry.json"
            write_response(fragment_path, task_path, response)
            accepted = accept(task_path, fragment_path, fragment_path)
            self.assertEqual(
                accepted["branches"][4]["source_note"],
                {
                    "SI": (
                        "Bu kaynak, yer adına bağlı kişi veya şeyi anlatan ayrı "
                        "bir biçim verir."
                    )
                },
            )
            write_pass_review(
                work_dir, task_path, fragment_path
            )
            entry = assemble(index_path, work_dir, "tr", directory / "entry.json")
            detail = entry["branches"][4]["source_discussion"]["details"][0]
            self.assertEqual(detail["source_ids"], ["sihah"])
            self.assertTrue(
                all(source_ref.startswith("sihah:") for source_ref in detail["source_refs"])
            )

    def test_repair_is_restaged_through_regular_input_and_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, task_path, _response = self.prepare_run(
                directory
            )
            output_dir = work_dir / "output"
            output_dir.mkdir()
            error_path = output_dir / "finalize_error.txt"
            error_path.write_text("$.branches[0].glosses: invalid\n", encoding="utf-8")
            scope_path = output_dir / "repair_scope.json"
            scope_path.write_text(
                json_content(
                    {
                        "repairable_by": "root_writer",
                        "editable_branch_indexes": [0],
                        "root_editable": False,
                    }
                ),
                encoding="utf-8",
            )
            fragment_path = work_dir / "fragments/root_001697_entry.json"
            staged = stage(
                task_path,
                previous_path=fragment_path,
                repair_error_path=error_path,
                repair_scope_path=scope_path,
            )
            self.assertEqual(staged["repair"]["error"], "repair_error.txt")
            previous = load_json(work_dir / "input/previous_response.json")
            self.assertNotIn("inputs_sha256", previous)
            self.assertIn(
                "change only fields allowed",
                (work_dir / "input/instructions.md").read_text(encoding="utf-8"),
            )

    def test_complete_root_response_assembles_and_renders(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, _index, work_dir, _task, _response = self.prepare_run(directory)
            entry_path = directory / "entry.json"
            markdown_path = directory / "entry.md"
            entry = assemble(index_path, work_dir, "tr", entry_path)
            validate_entry(entry_path)
            rendered = render(entry_path, markdown_path)
            self.assertEqual(len(entry["branches"]), 5)
            self.assertEqual(entry["root_profile"]["collocation_weight"], "unknown")
            for branch in entry["branches"]:
                self.assertEqual(branch["summary"], branch["glosses"]["semantic_definition"])
                self.assertTrue(
                    all(
                        neighbor["relation_type"] == "near_neighbor"
                        for neighbor in branch["arabic_neighbor_distinctions"]
                    )
                )
                self.assertEqual(
                    [row["rank"] for row in branch["glosses"]["selected"]],
                    list(range(1, len(branch["glosses"]["selected"]) + 1)),
                )
            self.assertIn("Oluşum biçimi özeti", rendered)

    def test_zero_useful_neighbors_assembles_and_renders(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, _index, work_dir, task_path, response = self.prepare_run(directory)
            response["branches"][0]["neighbor_distinctions"] = []
            response["branches"][0]["neighbor_coverage_note"] = (
                "Adayların tümü değerlendirildi; hiçbiri kavram sınırını yararlı "
                "biçimde belirginleştirmedi."
            )
            write_response(work_dir / "fragments/root_001697_entry.json", task_path, response)
            entry_path = directory / "zero.json"
            entry = assemble(index_path, work_dir, "tr", entry_path)
            self.assertEqual(entry["branches"][0]["arabic_neighbor_distinctions"], [])
            self.assertEqual(
                entry["branches"][0]["neighbor_coverage"]["assessment"],
                "none_useful",
            )
            rendered = render(entry_path, directory / "zero.md")
            self.assertIn("yararlı bir komşu ayrımı seçilmedi", rendered)

    def test_stale_and_extra_root_response_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, _index, work_dir, task_path, response = self.prepare_run(directory)
            response_path = work_dir / "fragments/root_001697_entry.json"
            stored = load_json(response_path)
            stored["inputs_sha256"] = "0" * 64
            atomic_write(response_path, json_content(stored))
            with self.assertRaisesRegex(ContractError, "stale task hash"):
                assemble(index_path, work_dir, "tr", directory / "stale.json")
            invalid = copy.deepcopy(response)
            invalid["dictionary_annotations"] = []
            write_response(response_path, task_path, invalid)
            with self.assertRaisesRegex(ContractError, "unknown property"):
                assemble(index_path, work_dir, "tr", directory / "extra.json")

    def test_used_transliterations_are_a_resumable_writer_completion_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            work_dir = directory / "work"
            _packet, _data, index_path, index = prepare_inputs(
                "root_001697", "tr", None, DEFAULT_FURUQ, None
            )
            task_path = prepare_initial_tasks(index_path, index, "tr", work_dir)[0]
            task = load_json(task_path)
            evidence = load_json(work_dir / "inputs/root_evidence.json")
            self.assertNotIn("transliteration_gaps", evidence)
            self.assertNotIn("transliterations", task["coordinator"])
            response = reduced_root_response(task, evidence)
            self.assertNotIn("transliteration_resolutions", response)
            write_response(work_dir / "fragments/root_001697_entry.json", task_path, response)
            with self.assertRaisesRegex(ContractError, "needs_transliteration_review"):
                write_root_writer_splits(index_path, work_dir, "tr")
            review = load_json(work_dir / "inputs/transliteration_review.json")
            self.assertIn("Root writer completion queue", review["instructions"])
            self.assertTrue(review["items"])
            self.assertTrue(all(item["status"] == "pending" for item in review["items"]))
            selected_count = sum(
                len(branch["neighbor_distinctions"]) for branch in response["branches"]
            )
            self.assertLessEqual(len(review["items"]), 1 + len(response["branches"]) + selected_count)

    def test_root_writer_rejects_arabic_prose_and_selected_loanwords(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, task_path, response = self.prepare_run(
                directory
            )
            response["branches"][0]["concept_map"]["definition"] = "هذا تعريف عربي كامل."
            write_response(work_dir / "fragments/root_001697_entry.json", task_path, response)
            with self.assertRaisesRegex(ContractError, "does not match"):
                load_task_fragment(
                    task_path,
                    work_dir / "fragments/root_001697_entry.json",
                    "root_writer",
                )

            response = reduced_root_response(
                load_json(task_path),
                load_json(work_dir / "inputs/root_evidence.json"),
            )
            response["branches"][0]["concept_gloss"]["loanword_status"] = "common"
            write_response(work_dir / "fragments/root_001697_entry.json", task_path, response)
            with self.assertRaisesRegex(ContractError, "unknown property 'loanword_status'"):
                load_task_fragment(
                    task_path,
                    work_dir / "fragments/root_001697_entry.json",
                    "root_writer",
                )

    def test_orchestrator_handoff_accepts_and_finalizes_without_agent_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            work_dir = directory / "work"
            _p, _packet, index_path, index = prepare_inputs(
                "root_001697", "tr", None, DEFAULT_FURUQ, None
            )
            tasks = prepare_initial_tasks(index_path, index, "tr", work_dir)
            task = load_json(tasks[0])
            evidence = load_json(work_dir / "inputs/root_evidence.json")
            response = reduced_root_response(task, evidence)
            write_approved_transliteration_review(
                work_dir / "inputs/transliteration_review.json",
                response,
                load_json(work_dir / "inputs/transliterations.json"),
            )
            write_approved_name_review(
                work_dir / "inputs/name_review.json",
                evidence,
            )
            response_file = work_dir / "output/root_001697_entry.json"
            response_file.parent.mkdir(parents=True, exist_ok=True)
            response_file.write_text(json_content(response), encoding="utf-8")
            fragment_path = work_dir / "fragments/root_001697_entry.json"
            accepted = accept(tasks[0], response_file, fragment_path)
            self.assertEqual(load_json(response_file), accepted)
            self.assertEqual(
                accepted["artifact_format"], "dictionary-v2-root-entry-draft-v1"
            )
            branch = accepted["branches"][0]
            self.assertEqual(branch["branch_image_ar"], "قصد الشيء وتعمده")
            self.assertTrue(branch["what_is_ar"])
            self.assertTrue(branch["source_phrase_ar"])
            self.assertEqual(branch["sources"], ["MQ", "JA", "SI"])
            self.assertEqual(branch["source_note"], {})
            self.assertNotIn("dictionary_basis", branch)
            self.assertNotIn("source_refs", json.dumps(branch, ensure_ascii=False))
            self.assertNotIn("artifact_path", accepted["occurrence_evidence"])
            self.assertEqual(len(accepted["occurrence_evidence"]["occurrences"]), 11)
            self.assertEqual(
                sum(
                    len(row["alignment"]["attachments"])
                    for row in accepted["occurrence_evidence"]["occurrences"]
                ),
                11,
            )
            tampered_path = directory / "tampered-entry.json"
            tampered = copy.deepcopy(accepted)
            tampered["branches"][0]["branch_image_ar"] = "مبدل"
            atomic_write(tampered_path, json_content(tampered))
            with self.assertRaisesRegex(ContractError, "stale or modified"):
                check_root_writer(tasks[0], tampered_path)
            self.assertEqual(len(check_root_writer(tasks[0], fragment_path)["branches"]), 5)
            write_pass_review(work_dir, tasks[0], fragment_path)
            entry_path = directory / "entry.json"
            markdown_path = directory / "entry.md"
            finalize(
                "root_001697",
                "tr",
                evidence_index=index_path,
                work_dir=work_dir,
                entry_path=entry_path,
                markdown_path=markdown_path,
            )
            validate_entry(entry_path)

    def test_accept_rejects_wrong_branch_roster(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, task_path, response = self.prepare_run(
                directory
            )
            response["branches"] = list(reversed(response["branches"]))
            raw = directory / "response.json"
            raw.write_text(json_content(response), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "roster/order mismatch"):
                accept(task_path, raw, work_dir / "fragments/rejected.json")

    def test_coordinator_rendering_policy_and_exact_boundary_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            _index_path, _index, work_dir, task_path, response = self.prepare_run(
                directory
            )
            raw = directory / "response.json"

            response["branches"][4]["lexical_glosses"][3][
                "rendering_kind"
            ] = "proper_name"
            response["branches"][4]["lexical_glosses"][3]["target_gloss"] = None
            raw.write_text(json_content(response), encoding="utf-8")
            with self.assertRaisesRegex(
                ContractError,
                "lu_017 must use coordinator rendering policy 'ordinary'",
            ):
                accept(task_path, raw, directory / "misclassified.json")

            response = reduced_root_response(
                load_json(task_path),
                load_json(work_dir / "inputs/root_evidence.json"),
            )
            relation = response["branches"][0]["neighbor_distinctions"][0]
            relation["relation_type"] = "near_neighbor"
            relation["boundary_match"] = "exact"
            relation["focus_only"] = "Odak dalında ek bir koşul vardır."
            raw.write_text(json_content(response), encoding="utf-8")
            with self.assertRaisesRegex(
                ContractError,
                "exact boundary requires synonym and no asymmetry",
            ):
                accept(task_path, raw, directory / "bad-exact.json")

            response = reduced_root_response(
                load_json(task_path),
                load_json(work_dir / "inputs/root_evidence.json"),
            )
            response["branches"][4]["lexical_glosses"][3][
                "target_gloss"
            ] = "{{lu_015}} ile ilişkili veya o yerden olan"
            raw.write_text(json_content(response), encoding="utf-8")
            accepted = accept(task_path, raw, directory / "protected-reference.json")
            self.assertIn(
                "{{lu_015}}",
                accepted["branches"][4]["lexical_glosses"][3]["target_gloss"],
            )

    def test_output_protection_and_atomic_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            entry_path = directory / "entry.json"
            markdown_path = directory / "entry.md"
            reviewed = copy.deepcopy(self.source)
            reviewed["status"] = "reviewed"
            entry_path.write_text(json_content(reviewed), encoding="utf-8")
            markdown_path.write_text("authored\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "reviewed"):
                check_output_targets(entry_path, markdown_path, force_entry=False)
            check_output_targets(entry_path, markdown_path, force_entry=True)

            candidate_entry = directory / "candidate.json"
            candidate_markdown = directory / "candidate.md"
            candidate_entry.write_text('{"new":true}\n', encoding="utf-8")
            candidate_markdown.write_text("new\n", encoding="utf-8")
            publish_pair(
                candidate_entry,
                candidate_markdown,
                entry_path,
                markdown_path,
                force_entry=True,
            )
            self.assertEqual(entry_path.read_text(encoding="utf-8"), '{"new":true}\n')

    def test_repair_routing_separates_deterministic_failures(self):
        task = {"branch_roster": ["root_000001/B001", "root_000001/B002"]}
        self.assertEqual(
            classify("$.provenance: digest mismatch", task),
            {
                "repairable_by": "deterministic_pipeline",
                "editable_branch_indexes": [],
                "root_editable": False,
            },
        )
        self.assertEqual(
            classify("$.branches[1].glosses: invalid", task),
            {
                "repairable_by": "root_writer",
                "editable_branch_indexes": [1],
                "root_editable": False,
            },
        )
        self.assertEqual(
            classify("needs_transliteration_review: pending", task)["repairable_by"],
            "root_writer",
        )
        self.assertEqual(
            classify("needs_name_review: pending", task)["repairable_by"],
            "root_writer",
        )

    def test_repair_preserves_unaffected_branches(self):
        previous = {
            "branches": [{"branch_ref": "root_000001/B001", "value": "a"},
                         {"branch_ref": "root_000001/B002", "value": "b"}],
            "root_profile": {"summary": "root"},
        }
        candidate = copy.deepcopy(previous)
        candidate["branches"][0]["value"] = "fixed"
        validate_repair_preservation(
            previous,
            candidate,
            editable_branch_indexes={0},
            root_editable=False,
        )
        candidate["branches"][1]["value"] = "changed"
        with self.assertRaisesRegex(ContractError, "protected branch index 1"):
            validate_repair_preservation(
                previous,
                candidate,
                editable_branch_indexes={0},
                root_editable=False,
            )

    def test_render_escapes_agent_authored_markdown(self):
        entry = copy.deepcopy(self.source)
        entry["root_profile"]["summary"] = (
            "<script>alert(1)</script> [unsafe](https://example.invalid) # heading"
        )
        rendered = render_markdown(entry, self.source_packet)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("[unsafe](https://example.invalid)", rendered)

    def test_standalone_generators_guard_canonical_evidence(self):
        with mock.patch(
            "v2.scripts.render_occurrences.protect_pinned_entries",
            side_effect=ValueError("pinned occurrence evidence"),
        ):
            with self.assertRaisesRegex(SystemExit, "pinned occurrence evidence"):
                occurrence_module.main(["root_001697", "--language", "tr"])
        with mock.patch(
            "v2.scripts.build_branch_evidence.protect_pinned_entries",
            side_effect=ValueError("pinned branch evidence"),
        ):
            with self.assertRaisesRegex(SystemExit, "pinned branch evidence"):
                evidence_module.main(["root_001697"])


if __name__ == "__main__":
    unittest.main()
