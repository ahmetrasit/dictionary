import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from v2.gloss_generation.workflow import (
    DEFAULT_LANGUAGES,
    SUPPORTED_LANGUAGES,
    ContractError,
    accept_reviewed_result,
    build_package,
    canonical_sha256,
    load_json,
    parse_languages,
    prepare_entry,
    resolve_path,
    stage_editorial_repair,
    stage_repair,
    stage_review,
    store_result,
    validate_review_response,
    validate_response,
    validate_source_entry,
    verify_task,
)
from v2.scripts.validate_entry import validate_entry


PROJECT = Path(__file__).resolve().parents[3]
FIXTURE = PROJECT / "v2/examples/root_000858.tr.entry.json"


def chosen(text, facet_ids):
    return {
        "text": text,
        "facet_ids": facet_ids,
        "error": {
            "fit": "none",
            "loses_facet_ids": [],
            "adds": None,
            "collision": None,
            "reason": None,
        },
    }


def valid_response(task, package, language):
    branches = []
    for index, branch in enumerate(package["branches"], start=1):
        facet_ids = [row["facet_id"] for row in branch["facets"]]
        branches.append(
            {
                "branch_ref": branch["branch_ref"],
                "concept_gloss": chosen(
                    f"{language} concept gloss {index}", facet_ids
                ),
                "contextual_glosses": [],
                "lexical_glosses": {
                    row["lexical_unit_id"]: chosen(
                        f"{language} lexical gloss {index}-{unit_index}",
                        row["facet_ids"],
                    )
                    for unit_index, row in enumerate(
                        branch["lexical_units"], start=1
                    )
                },
            }
        )
    return {
        "inputs_sha256": task["inputs_sha256"],
        "branches": branches,
    }


def valid_review(task, verdict="pass", issues=None):
    return {
        "inputs_sha256": task["inputs_sha256"],
        "verdict": verdict,
        "summary": "The target-language gloss set was reviewed.",
        "issues": [] if issues is None else issues,
    }


class GlossGenerationWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, _packet = validate_entry(FIXTURE)

    def test_package_is_compact_and_omits_occurrences(self):
        package = build_package(self.entry, FIXTURE, "en")
        branch = package["branches"][0]
        source = self.entry["branches"][0]

        self.assertEqual(branch["source_phrase_ar"], source["source_phrase_ar"])
        self.assertEqual(branch["what_is_ar"], source["what_is_ar"])
        self.assertEqual(branch["what_is_not_ar"], source["what_is_not_ar"])
        self.assertEqual(
            [row["facet_id"] for row in branch["facets"]],
            [
                row["facet_id"]
                for row in source["concept_map"]["facets"]
            ],
        )
        self.assertEqual(
            len(branch["neighbor_distinctions"]),
            len(source["arabic_neighbor_distinctions"]),
        )
        self.assertEqual(
            branch["neighbor_distinctions"][0]["neighbor_ref"],
            "root_000672/B001",
        )
        self.assertIn("distinction_tr", branch["neighbor_distinctions"][0])
        serialized = json.dumps(package, ensure_ascii=False)
        for forbidden in (
            "occurrence_evidence",
            "occurrences",
            "ayahs",
            "attachments",
            "dictionary_basis",
            "arabic_neighbor_distinctions",
            "evidence_refs",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_legacy_review_gate_is_ignored_but_not_projected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = json.loads(FIXTURE.read_text(encoding="utf-8"))
            source["review_gate"] = {
                "semantic_review_verdict": "repair",
                "published_with_unresolved_repair": True,
            }
            source_path = Path(temporary) / FIXTURE.name
            source_path.write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            entry, _packet = validate_source_entry(source_path)
            package = build_package(entry, source_path, "en")
            self.assertIn("review_gate", entry)
            self.assertNotIn(
                "review_gate", json.dumps(package, ensure_ascii=False)
            )

    def test_all_three_locales_stage_validate_and_store(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            task_paths = prepare_entry(
                FIXTURE,
                DEFAULT_LANGUAGES,
                temporary_path / "work",
            )
            self.assertEqual(len(task_paths), 3)
            self.assertEqual(
                {load_json(path)["target_language"] for path in task_paths},
                {"en", "de", "tr"},
            )

            for task_path in task_paths:
                task = load_json(task_path)
                package = load_json(
                    resolve_path(task["inputs"]["package"]["path"])
                )
                response = valid_response(
                    task, package, task["target_language"]
                )
                response_path = resolve_path(task["output"]["path"])
                response_path.parent.mkdir(parents=True, exist_ok=True)
                response_path.write_text(
                    json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                validated_task, validated, _package = validate_response(
                    task_path
                )
                self.assertEqual(
                    validated_task["target_language"],
                    task["target_language"],
                )
                self.assertEqual(
                    len(validated["branches"]),
                    len(package["branches"]),
                )
                result_path = (
                    temporary_path
                    / "results"
                    / task["target_language"]
                    / "root_000858.json"
                )
                store_result(task_path, output_path=result_path)
                result = load_json(result_path)
                self.assertEqual(result["status"], "candidate")
                self.assertEqual(
                    result["target_language"], task["target_language"]
                )

    def test_priority_rollout_has_all_33_locale_prompts(self):
        languages = parse_languages(None, "western-muslim-priority")
        self.assertEqual(len(languages), 33)
        self.assertEqual(len(SUPPORTED_LANGUAGES), 33)
        self.assertEqual(languages[:3], ["en", "de", "fr"])
        self.assertIn("ur", languages)
        self.assertIn("pnb-Arab", languages)
        for language in languages:
            self.assertTrue(
                (
                    PROJECT
                    / "v2/gloss_generation/locales"
                    / f"{language}.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    PROJECT
                    / "v2/gloss_generation/locale_prompts"
                    / f"{language}.md"
                ).is_file()
            )
        with tempfile.TemporaryDirectory() as temporary:
            task_paths = prepare_entry(
                FIXTURE, languages, Path(temporary) / "work"
            )
            self.assertEqual(len(task_paths), 33)
            self.assertEqual(
                [load_json(path)["target_language"] for path in task_paths],
                languages,
            )

    def test_arabic_script_permission_is_locale_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            task_paths = prepare_entry(
                FIXTURE,
                ["en", "ur"],
                Path(temporary) / "work",
            )
            for task_path in task_paths:
                task = load_json(task_path)
                package = load_json(
                    resolve_path(task["inputs"]["package"]["path"])
                )
                response = valid_response(
                    task, package, task["target_language"]
                )
                response["branches"][0]["concept_gloss"]["text"] = (
                    "ݐ target gloss"
                    if task["target_language"] == "en"
                    else "ذمہ داری اور نگہداشت"
                )
                response_path = resolve_path(task["output"]["path"])
                response_path.parent.mkdir(parents=True, exist_ok=True)
                response_path.write_text(
                    json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                if task["target_language"] == "en":
                    with self.assertRaisesRegex(
                        ContractError, "contains Arabic script"
                    ):
                        validate_response(task_path)
                else:
                    validate_response(task_path)

    def test_controller_seal_rejects_a_self_rehashed_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            task_path = prepare_entry(
                FIXTURE, ["en"], Path(temporary) / "work"
            )[0]
            task = load_json(task_path)
            forged_output = str(Path(temporary) / "forged.json")
            task["output"]["path"] = forged_output
            task["inputs"]["contract"]["output_path"] = forged_output
            task["inputs_sha256"] = canonical_sha256(task["inputs"])
            task_path.write_text(
                json.dumps(task, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "Controller task seal mismatch"
            ):
                verify_task(task_path)

    def test_canonical_prompt_change_makes_a_task_stale(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            canonical_prompt = temporary_path / "writer_prompt.md"
            canonical_prompt.write_text(
                "Version one of the canonical prompt.\n",
                encoding="utf-8",
            )
            with patch(
                "v2.gloss_generation.workflow.PROMPT",
                canonical_prompt,
            ):
                task_path = prepare_entry(
                    FIXTURE, ["en"], temporary_path / "work"
                )[0]
                verify_task(task_path)
                canonical_prompt.write_text(
                    "Version two of the canonical prompt.\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    ContractError, "input digest mismatch"
                ):
                    verify_task(task_path)

    def test_lexical_gloss_facets_are_unit_scoped_and_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            task_path = prepare_entry(
                FIXTURE, ["en"], Path(temporary) / "work"
            )[0]
            task = load_json(task_path)
            package = load_json(
                resolve_path(task["inputs"]["package"]["path"])
            )
            response = valid_response(task, package, "en")
            lexical = response["branches"][0]["lexical_glosses"]["lu_003"]
            lexical["facet_ids"].append("F002")
            response_path = resolve_path(task["output"]["path"])
            response_path.parent.mkdir(parents=True, exist_ok=True)
            response_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "unknown represented facet IDs"
            ):
                validate_response(task_path)

            lexical["facet_ids"] = ["F001"]
            response_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "does not disposition facets"
            ):
                validate_response(task_path)

    def test_independent_review_pass_is_required_for_acceptance(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            writer_task_path = prepare_entry(
                FIXTURE, ["en"], temporary_path / "work"
            )[0]
            writer_task = load_json(writer_task_path)
            package = load_json(
                resolve_path(writer_task["inputs"]["package"]["path"])
            )
            writer_response_path = resolve_path(writer_task["output"]["path"])
            writer_response_path.parent.mkdir(parents=True, exist_ok=True)
            writer_response_path.write_text(
                json.dumps(
                    valid_response(writer_task, package, "en"),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            review_task_path = stage_review(writer_task_path)
            review_task = load_json(review_task_path)
            review_path = resolve_path(review_task["output"]["path"])
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                json.dumps(
                    valid_review(review_task),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            validate_review_response(review_task_path)
            result_path = temporary_path / "results/en/root_000858.json"
            accepted = accept_reviewed_result(
                writer_task_path,
                review_task_path,
                output_path=result_path,
            )
            self.assertEqual(load_json(accepted)["status"], "reviewed")
            self.assertEqual(
                accept_reviewed_result(
                    writer_task_path,
                    review_task_path,
                    output_path=result_path,
                ),
                result_path.resolve(),
            )

    def test_repair_is_bounded_and_receives_a_new_task_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            writer_task_path = prepare_entry(
                FIXTURE, ["de"], temporary_path / "work"
            )[0]
            writer_task = load_json(writer_task_path)
            package = load_json(
                resolve_path(writer_task["inputs"]["package"]["path"])
            )
            original = valid_response(writer_task, package, "de")
            writer_response_path = resolve_path(writer_task["output"]["path"])
            writer_response_path.parent.mkdir(parents=True, exist_ok=True)
            writer_response_path.write_text(
                json.dumps(original, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            review_task_path = stage_review(writer_task_path)
            review_task = load_json(review_task_path)
            first_branch = package["branches"][0]
            issue = {
                "branch_ref": first_branch["branch_ref"],
                "field": "concept_gloss",
                "lexical_unit_id": None,
                "facet_ids": [
                    row["facet_id"] for row in first_branch["facets"]
                ],
                "kind": "naturalness",
                "severity": "major",
                "confidence": "high",
                "problem": "Die Begriffsglosse ist im Deutschen unidiomatisch.",
                "smallest_correction": "Nur die Begriffsglosse idiomatisch fassen.",
            }
            contextual_issue = {
                "branch_ref": first_branch["branch_ref"],
                "field": "contextual_glosses",
                "lexical_unit_id": None,
                "facet_ids": [first_branch["facets"][0]["facet_id"]],
                "kind": "semantic_fit",
                "severity": "minor",
                "confidence": "medium",
                "problem": "Eine erforderliche Kontextglosse fehlt.",
                "smallest_correction": "Eine gebundene Kontextglosse ergänzen.",
            }
            review_path = resolve_path(review_task["output"]["path"])
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                json.dumps(
                    valid_review(
                        review_task,
                        "repair",
                        [issue, contextual_issue],
                    ),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            repair_task_path = stage_repair(review_task_path)
            repair_task = load_json(repair_task_path)
            repaired = copy.deepcopy(original)
            repaired["inputs_sha256"] = repair_task["inputs_sha256"]
            repaired["branches"][0]["concept_gloss"][
                "text"
            ] = "idiomatische deutsche Begriffsglosse"
            repair_output = resolve_path(repair_task["output"]["path"])
            repair_output.parent.mkdir(parents=True, exist_ok=True)
            repair_output.write_text(
                json.dumps(repaired, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "leaves review scopes unchanged"
            ):
                validate_response(repair_task_path)

            repaired["branches"][0]["contextual_glosses"].append(
                {
                    "text": "kontextgebundene deutsche Glosse",
                    "facet_ids": [
                        first_branch["facets"][0]["facet_id"]
                    ],
                    "lexical_unit_ids": [],
                    "error": {
                        "fit": "none",
                        "loses_facet_ids": [],
                        "adds": None,
                        "collision": None,
                        "reason": None,
                    },
                }
            )
            repair_output.write_text(
                json.dumps(repaired, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validate_response(repair_task_path)
            self.assertNotEqual(
                repair_task["inputs_sha256"], writer_task["inputs_sha256"]
            )

            lexical_id = next(
                iter(repaired["branches"][0]["lexical_glosses"])
            )
            repaired["branches"][0]["lexical_glosses"][lexical_id][
                "text"
            ] = "unzulässige Nebenänderung"
            repair_output.write_text(
                json.dumps(repaired, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "out-of-scope"):
                validate_response(repair_task_path)

    def test_editorial_repair_can_follow_a_rebound_non_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            writer_task_path = prepare_entry(
                FIXTURE, ["en"], temporary_path / "work"
            )[0]
            writer_task = load_json(writer_task_path)
            package = load_json(
                resolve_path(writer_task["inputs"]["package"]["path"])
            )
            original = valid_response(writer_task, package, "en")
            writer_response_path = resolve_path(writer_task["output"]["path"])
            writer_response_path.parent.mkdir(parents=True, exist_ok=True)
            writer_response_path.write_text(
                json.dumps(original, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            first_branch = package["branches"][0]
            issue = {
                "branch_ref": first_branch["branch_ref"],
                "field": "concept_gloss",
                "lexical_unit_id": None,
                "facet_ids": [
                    row["facet_id"] for row in first_branch["facets"]
                ],
                "kind": "semantic_fit",
                "severity": "major",
                "confidence": "high",
                "problem": "The concept gloss is too broad.",
                "smallest_correction": "Tighten only the concept gloss.",
            }
            review_task_path = stage_review(writer_task_path)
            review_task = load_json(review_task_path)
            review_path = resolve_path(review_task["output"]["path"])
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                json.dumps(
                    valid_review(review_task, "repair", [issue]),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            repair_task_path = stage_repair(review_task_path)
            repair_task = load_json(repair_task_path)
            repaired = copy.deepcopy(original)
            repaired["inputs_sha256"] = repair_task["inputs_sha256"]
            repaired["branches"][0]["concept_gloss"][
                "text"
            ] = "tightened English concept gloss"
            repair_output = resolve_path(repair_task["output"]["path"])
            repair_output.parent.mkdir(parents=True, exist_ok=True)
            repair_output.write_text(
                json.dumps(repaired, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validate_response(repair_task_path)

            rebound_review_task_path = stage_review(repair_task_path)
            rebound_review_task = load_json(rebound_review_task_path)
            rebound_review_path = resolve_path(
                rebound_review_task["output"]["path"]
            )
            rebound_review_path.parent.mkdir(parents=True, exist_ok=True)
            rebound_review_path.write_text(
                json.dumps(
                    valid_review(rebound_review_task, "repair", [issue]),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ContractError, "only one semantic repair"
            ):
                stage_repair(rebound_review_task_path)

            editorial_task_path = stage_editorial_repair(
                rebound_review_task_path
            )
            editorial_task = load_json(editorial_task_path)
            editorial = copy.deepcopy(repaired)
            editorial["inputs_sha256"] = editorial_task["inputs_sha256"]
            editorial["branches"][0]["concept_gloss"][
                "text"
            ] = "editorially tightened English concept gloss"
            editorial_output = resolve_path(editorial_task["output"]["path"])
            editorial_output.parent.mkdir(parents=True, exist_ok=True)
            editorial_output.write_text(
                json.dumps(editorial, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validate_response(editorial_task_path)

    def test_narrowing_requires_a_lost_facet(self):
        with tempfile.TemporaryDirectory() as temporary:
            task_path = prepare_entry(
                FIXTURE, ["en"], Path(temporary) / "work"
            )[0]
            task = load_json(task_path)
            package = load_json(
                resolve_path(task["inputs"]["package"]["path"])
            )
            response = valid_response(task, package, "en")
            response["branches"][0]["concept_gloss"]["error"][
                "fit"
            ] = "narrowing"
            response["branches"][0]["concept_gloss"]["error"][
                "reason"
            ] = "This gloss omits one source facet."
            response_path = resolve_path(task["output"]["path"])
            response_path.parent.mkdir(parents=True, exist_ok=True)
            response_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "narrowing requires a lost facet"
            ):
                validate_response(task_path)

    def test_non_exact_fit_requires_user_facing_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            task_path = prepare_entry(
                FIXTURE, ["en"], Path(temporary) / "work"
            )[0]
            task = load_json(task_path)
            package = load_json(
                resolve_path(task["inputs"]["package"]["path"])
            )
            response = valid_response(task, package, "en")
            error = response["branches"][0]["concept_gloss"]["error"]
            error["fit"] = "narrowing"
            error["loses_facet_ids"] = [
                package["branches"][0]["facets"][-1]["facet_id"]
            ]
            response["branches"][0]["concept_gloss"]["facet_ids"] = [
                facet
                for facet in response["branches"][0]["concept_gloss"]["facet_ids"]
                if facet not in error["loses_facet_ids"]
            ]
            response_path = resolve_path(task["output"]["path"])
            response_path.parent.mkdir(parents=True, exist_ok=True)
            response_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "non-none fit requires a reason"
            ):
                validate_response(task_path)

            error["reason"] = "This gloss omits one source facet."
            response_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validate_response(task_path)

    def test_response_hash_and_lexical_roster_are_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            task_path = prepare_entry(
                FIXTURE, ["de"], Path(temporary) / "work"
            )[0]
            task = load_json(task_path)
            package = load_json(
                resolve_path(task["inputs"]["package"]["path"])
            )
            response = valid_response(task, package, "de")
            stale = copy.deepcopy(response)
            stale["inputs_sha256"] = "0" * 64
            response_path = resolve_path(task["output"]["path"])
            response_path.parent.mkdir(parents=True, exist_ok=True)
            response_path.write_text(
                json.dumps(stale, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "stale task inputs"):
                validate_response(task_path)

            first_lexical = response["branches"][0]["lexical_glosses"]
            first_lexical["lu_999"] = chosen(
                "ungültige zusätzliche Glosse",
                [package["branches"][0]["facets"][0]["facet_id"]],
            )
            response_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "exact lexical-unit roster"
            ):
                validate_response(task_path)


if __name__ == "__main__":
    unittest.main()
