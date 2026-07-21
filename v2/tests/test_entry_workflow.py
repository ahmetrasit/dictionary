import copy
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from v2.scripts.assemble_entry import (
    agent_branch_evidence,
    canonical_sha256,
    assemble,
    json_content,
    load_evidence,
    validate_fragment,
)
import v2.scripts.build_branch_evidence as evidence_module
import v2.scripts.render_occurrences as occurrence_module
from v2.scripts.build_branch_evidence import (
    DEFAULT_FURUQ,
    build_packages,
    dictionary_basis,
    packet_sources,
    write_packages,
)
from v2.scripts.create_entry import (
    atomic_write,
    check_output_targets,
    check_pinned_evidence,
    confined_agent_command,
    materialize_agent_task,
    prepare_initial_tasks,
    prepare_inputs,
    prepare_root_task,
    publish_pair,
    run_agent_task,
    run_initial_tasks,
    run_workflow,
    repair_owners,
)
from v2.scripts.render_entry import render, render_markdown
from v2.scripts.render_occurrences import load_packet
from v2.scripts.validate_entry import ContractError, load_json, validate_entry


PROJECT = Path(__file__).resolve().parents[2]
FIXTURE = PROJECT / "v2/examples/root_000858.tr.entry.json"


def branch_response(branch: dict) -> dict:
    return {
        "root_id": branch["root_id"],
        "branch_id": branch["branch_id"],
        "language": "tr",
        "image_transliteration": branch["image_transliteration"],
        "summary": branch["summary"],
        "source_summary": branch["source_discussion"]["discussion"],
        "usage_notes": [
            {"kind": note["kind"], "statement": note["statement"]}
            for note in branch["usage_notes"]
        ],
        "evidence_qualifiers": [
            {"type": item["type"], "statement": item["statement"]}
            for item in branch["evidence_qualifiers"]
        ],
        "glosses": branch["glosses"],
        "arabic_neighbor_distinctions": [
            {
                key: neighbor[key]
                for key in (
                    "neighbor_root_id",
                    "neighbor_branch_id",
                    "expression_transliteration",
                    "gloss",
                    "shared_zone",
                    "distinction",
                )
            }
            for neighbor in branch["arabic_neighbor_distinctions"]
        ],
        "neighbor_coverage": {
            "assessment": branch["neighbor_coverage"]["assessment"],
            "note": branch["neighbor_coverage"]["note"],
        },
    }


def write_fragment(path: Path, task_path: Path, response: dict) -> None:
    task = load_json(task_path)
    stored = {"inputs_sha256": canonical_sha256(task), **response}
    atomic_write(path, json_content(stored))


class EntryWorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE)
        cls.packet_path, cls.packet = load_packet(PROJECT, "root_000858", None)

    def test_branch_packages_are_scoped_and_counted(self):
        index, packages = build_packages(
            self.packet,
            self.packet_path,
            DEFAULT_FURUQ,
        )
        self.assertEqual(len(index["branches"]), 3)
        self.assertEqual(
            [
                (
                    package["dictionary_basis"]["dictionary_count"],
                    package["dictionary_basis"]["passage_count"],
                )
                for package in packages.values()
            ],
            [(3, 4), (1, 2), (1, 1)],
        )
        first = packages["root_000858--B001.json"]
        self.assertEqual(
            [source["source_id"] for source in first["dictionary_basis"]["sources"]],
            ["sihah", "mufradat", "maqayis"],
        )
        candidate_keys = {
            (row["root_id"], row["branch_id"])
            for row in first["furuq_candidates"]
        }
        self.assertIn(("root_000672", "B001"), candidate_keys)

    def test_dictionary_basis_rejects_non_exact_routes(self):
        packet = copy.deepcopy(self.packet)
        branch = packet["branches"][0]
        routed_ref = branch["source_refs"].split(";", 1)[0]
        source = next(
            row
            for row in packet["dictionary_sources"]
            if row.get("source_ref") == routed_ref
        )
        source["route_status"] = "review"
        with self.assertRaisesRegex(ValueError, "exact or variant"):
            dictionary_basis(branch, packet_sources(packet))

    def test_package_check_rejects_stale_extra_branch_files(self):
        index, packages = build_packages(
            self.packet, self.packet_path, DEFAULT_FURUQ
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            write_packages(output, index, packages, check=False)
            extra = output / "branches/root_999999--B999.json"
            extra.write_text(
                '{"generated_by":"v2/scripts/build_branch_evidence.py"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Stale extra"):
                write_packages(output, index, packages, check=True)
            write_packages(output, index, packages, check=False)
            self.assertFalse(extra.exists())

    def test_package_publication_failure_preserves_existing_tree(self):
        index, packages = build_packages(
            self.packet, self.packet_path, DEFAULT_FURUQ
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            write_packages(output, index, packages, check=False)
            before = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            real_write = evidence_module.write_generated
            calls = 0

            def fail_during_stage(path, content, *, check):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected evidence write failure")
                return real_write(path, content, check=check)

            with mock.patch(
                "v2.scripts.build_branch_evidence.write_generated",
                side_effect=fail_during_stage,
            ):
                with self.assertRaisesRegex(OSError, "injected evidence write failure"):
                    write_packages(output, index, packages, check=False)
            after = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_incomplete_focus_branch_cannot_enter_assembly(self):
        index_path = (
            PROJECT
            / "v2/output/branch_evidence/root_001210--root_001211/index.json"
        )
        with self.assertRaisesRegex(ContractError, "needs_evidence"):
            load_evidence(index_path)

    def test_entry_workflow_rejects_noncanonical_packet_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet_path = Path(temporary) / "root_000858.json"
            packet_path.write_text(
                json_content(self.packet), encoding="utf-8"
            )
            with self.assertRaisesRegex(ContractError, "canonical packet"):
                prepare_inputs(
                    "root_000858", "tr", packet_path, DEFAULT_FURUQ, None
                )

    def test_fixture_fragments_match_all_agent_schemas(self):
        for branch in self.fixture["branches"]:
            validate_fragment(
                branch_response(branch),
                "branch_writer",
                FIXTURE,
            )
        root = {
            "root_envelope_id": self.fixture["root_envelope_id"],
            "language": "tr",
            "root_profile": self.fixture["root_profile"],
        }
        validate_fragment(root, "root_profile_writer", FIXTURE)

    def create_fixture_run(self, directory: Path) -> tuple[Path, Path, Path, dict]:
        work_dir = directory / "work"
        _packet_path, _packet, index_path, index = prepare_inputs(
            "root_000858",
            "tr",
            None,
            DEFAULT_FURUQ,
            None,
        )
        prepare_initial_tasks(index_path, index, "tr", work_dir)
        final_by_key = {
            (branch["root_id"], branch["branch_id"]): branch
            for branch in self.fixture["branches"]
        }
        for row in index["branches"]:
            stem = f"{row['root_id']}--{row['branch_id']}"
            task_path = work_dir / "tasks/branches" / f"{stem}.json"
            fragment_path = work_dir / "fragments/branches" / f"{stem}.json"
            write_fragment(
                fragment_path,
                task_path,
                branch_response(final_by_key[(row["root_id"], row["branch_id"])]),
            )

        root_task = prepare_root_task(index, "tr", work_dir)
        write_fragment(
            work_dir / "fragments/root_profile.json",
            root_task,
            {
                "root_envelope_id": self.fixture["root_envelope_id"],
                "language": "tr",
                "root_profile": self.fixture["root_profile"],
            },
        )
        return index_path, work_dir, root_task, index

    def test_complete_keyed_assembly_and_render(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, work_dir, _root_task, _index = self.create_fixture_run(
                directory
            )
            entry_path = directory / "entries/root_000858.json"
            markdown_path = directory / "entries/root_000858.md"
            assembled = assemble(
                index_path,
                work_dir,
                "tr",
                entry_path,
            )
            self.assertEqual(assembled, self.fixture)
            validate_entry(entry_path)
            content = render(entry_path, markdown_path)
            assemble(
                index_path,
                work_dir,
                "tr",
                entry_path,
                check=True,
            )
            render(entry_path, markdown_path, check=True)
            self.assertIn("3 sözlük, 4 pasaj", content)
            self.assertIn("(`root_000672/B001`)", content)
            self.assertIn("Oluşum biçimi özeti", content)
            self.assertIn("Bağlantılar", content)
            self.assertIn("çok anlamlı / karma", content)
            self.assertNotIn("`polysemic`", content)

    def test_render_escapes_agent_authored_markdown(self):
        entry = copy.deepcopy(self.fixture)
        entry["root_profile"]["summary"] = (
            "<script>alert(1)</script> [unsafe](https://example.invalid) # heading"
        )
        rendered = render_markdown(entry, self.packet)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("[unsafe](https://example.invalid)", rendered)
        self.assertIn("\\<script\\>", rendered)

    def test_reviewed_and_unmarked_outputs_require_explicit_force(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            entry_path = directory / "entry.json"
            markdown_path = directory / "entry.md"
            reviewed = copy.deepcopy(self.fixture)
            reviewed["status"] = "reviewed"
            entry_path.write_text(json_content(reviewed), encoding="utf-8")
            markdown_path.write_text("authored\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "reviewed"):
                check_output_targets(entry_path, markdown_path, force_entry=False)
            check_output_targets(entry_path, markdown_path, force_entry=True)

            entry_path.write_text('{"status":"draft"}\n', encoding="utf-8")
            markdown_path.write_text(
                "<!-- generated-by: v2/scripts/render_entry.py schema=3 -->\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "unmarked entry"):
                check_output_targets(entry_path, markdown_path, force_entry=False)

    def test_reviewed_entry_protects_pinned_evidence_before_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            entry_path = project / "v2/entries/tr/root_000858.json"
            entry_path.parent.mkdir(parents=True)
            reviewed = copy.deepcopy(self.fixture)
            reviewed["status"] = "reviewed"
            entry_path.write_text(json_content(reviewed), encoding="utf-8")
            with mock.patch("v2.scripts.create_entry.PROJECT", project):
                with self.assertRaisesRegex(ContractError, "pinned"):
                    check_pinned_evidence(
                        "root_000858", "tr", force_entry=False
                    )
                check_pinned_evidence("root_000858", "tr", force_entry=True)

    def test_standalone_generators_guard_canonical_evidence(self):
        with mock.patch(
            "v2.scripts.render_occurrences.protect_pinned_entries",
            side_effect=ValueError("pinned occurrence evidence"),
        ) as occurrence_guard:
            with self.assertRaisesRegex(SystemExit, "pinned occurrence evidence"):
                occurrence_module.main(["root_000858", "--language", "tr"])
        occurrence_guard.assert_called_once()

        with mock.patch(
            "v2.scripts.build_branch_evidence.protect_pinned_entries",
            side_effect=ValueError("pinned branch evidence"),
        ) as branch_guard:
            with self.assertRaisesRegex(SystemExit, "pinned branch evidence"):
                evidence_module.main(["root_000858"])
        branch_guard.assert_called_once()

    def test_repository_read_confinement_blocks_project_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            command = confined_agent_command(
                ["/bin/cat", str(PROJECT / "v2/README.md")], workspace
            )
            result = subprocess.run(command, text=True, capture_output=True)
            if "sandbox_apply: Operation not permitted" in result.stderr:
                self.skipTest("nested sandbox-exec is blocked by the test environment")
            self.assertNotEqual(result.returncode, 0)

    def test_packaged_neighbor_errors_route_to_branch_writer(self):
        owners = repair_owners(
            "$.branches[1].arabic_neighbor_distinctions: neighbor is absent "
            "from the branch evidence package",
            {"branches": [{}, {}]},
        )
        self.assertEqual(owners, ({1}, False))

    def test_agent_task_materialization_exposes_only_bound_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            work_dir = directory / "work"
            _packet_path, _packet, index_path, index = prepare_inputs(
                "root_000858", "tr", None, DEFAULT_FURUQ, None
            )
            task_path = prepare_initial_tasks(index_path, index, "tr", work_dir)[0]
            task = load_json(task_path)
            evidence_path = PROJECT / task["evidence"]["path"]
            evidence = load_json(evidence_path)
            self.assertEqual(
                set(evidence["branch"]),
                {"branch_id", "branch_image_ar", "what_is_ar", "source_phrase_ar"},
            )
            self.assertTrue(evidence["neighbors"])
            self.assertEqual(
                set(evidence["neighbors"][0]),
                {"root_id", "branch_id", "branch_image_ar", "what_is_ar"},
            )
            _loaded_index, packages = load_evidence(index_path)
            self.assertEqual(evidence, agent_branch_evidence(packages[0][1]))
            workspace = directory / "isolated"
            isolated = materialize_agent_task(task, workspace)

            def bindings(value):
                if isinstance(value, dict):
                    if {"path", "sha256"}.issubset(value):
                        yield value
                    for child in value.values():
                        yield from bindings(child)
                elif isinstance(value, list):
                    for child in value:
                        yield from bindings(child)

            for item in bindings(isolated):
                copied = (workspace / item["path"]).resolve()
                copied.relative_to(workspace.resolve())
                self.assertTrue(copied.is_file())
            stale = copy.deepcopy(task)
            stale["prompt"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ContractError, "digest mismatch"):
                materialize_agent_task(stale, directory / "stale")
            legacy = copy.deepcopy(task)
            legacy["format"] = 1
            with self.assertRaisesRegex(ContractError, "Stale or unrecognized agent task"):
                materialize_agent_task(legacy, directory / "legacy")

    def test_publication_pair_rolls_back_when_second_install_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            entry_path = directory / "entry.json"
            markdown_path = directory / "entry.md"
            candidate_entry = directory / "candidate-entry.json"
            candidate_markdown = directory / "candidate-entry.md"
            entry_path.write_text(
                '{"generated_by":"v2/scripts/assemble_entry.py",'
                '"status":"draft","old":true}\n',
                encoding="utf-8",
            )
            markdown_path.write_text(
                "<!-- generated-by: v2/scripts/render_entry.py schema=3 -->\nold\n",
                encoding="utf-8",
            )
            candidate_entry.write_text('{"status":"draft","new":true}\n', encoding="utf-8")
            candidate_markdown.write_text("new\n", encoding="utf-8")
            original_entry = entry_path.read_text(encoding="utf-8")
            original_markdown = markdown_path.read_text(encoding="utf-8")
            real_replace = __import__("os").replace

            def failing_replace(source, target):
                if Path(source) == candidate_markdown and Path(target) == markdown_path:
                    raise OSError("injected publication failure")
                return real_replace(source, target)

            with mock.patch(
                "v2.scripts.create_entry.os.replace", side_effect=failing_replace
            ):
                with self.assertRaisesRegex(OSError, "injected publication failure"):
                    publish_pair(
                        candidate_entry,
                        candidate_markdown,
                        entry_path,
                        markdown_path,
                        force_entry=False,
                    )
            self.assertEqual(entry_path.read_text(encoding="utf-8"), original_entry)
            self.assertEqual(
                markdown_path.read_text(encoding="utf-8"), original_markdown
            )

    def test_nonzero_agent_process_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            work_dir = directory / "work"
            _packet_path, _packet, index_path, index = prepare_inputs(
                "root_000858", "tr", None, DEFAULT_FURUQ, None
            )
            task_path = prepare_initial_tasks(index_path, index, "tr", work_dir)[0]
            counter = directory / "calls.txt"
            fake_codex = directory / "fake-codex"
            fake_codex.write_text(
                "#!/usr/bin/env python3\n"
                "from pathlib import Path\n"
                f"path = Path({str(counter)!r})\n"
                "path.write_text(path.read_text() + 'x' if path.exists() else 'x')\n"
                "raise SystemExit(7)\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            with mock.patch(
                "v2.scripts.create_entry.confined_agent_command",
                side_effect=lambda command, _workspace: command,
            ):
                with self.assertRaisesRegex(ContractError, "not retried"):
                    run_agent_task(
                        task_path,
                        work_dir,
                        codex_binary=str(fake_codex),
                        model=None,
                        max_repairs=2,
                    )
            self.assertEqual(counter.read_text(encoding="utf-8"), "x")

    def test_parallel_failure_terminates_active_agent_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            work_dir = directory / "work"
            _packet_path, _packet, index_path, index = prepare_inputs(
                "root_000858", "tr", None, DEFAULT_FURUQ, None
            )
            tasks = prepare_initial_tasks(index_path, index, "tr", work_dir)[:2]
            slow_started = directory / "slow-started"
            fake_codex = directory / "fake-codex"
            fake_codex.write_text(
                "#!/usr/bin/env python3\n"
                "import sys, time\n"
                "from pathlib import Path\n"
                "prompt = sys.stdin.read()\n"
                "if '\"branch_id\": \"B001\"' in prompt:\n"
                "    time.sleep(0.5)\n"
                "    raise SystemExit(9)\n"
                f"Path({str(slow_started)!r}).write_text('started')\n"
                "time.sleep(10)\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            started = time.monotonic()
            with mock.patch(
                "v2.scripts.create_entry.confined_agent_command",
                side_effect=lambda command, _workspace: command,
            ):
                with self.assertRaisesRegex(ContractError, "Agent task failed"):
                    run_initial_tasks(
                        tasks,
                        work_dir,
                        codex_binary=str(fake_codex),
                        model=None,
                        workers=2,
                        max_repairs=0,
                        agent_timeout=30,
                    )
            self.assertTrue(slow_started.is_file())
            self.assertLess(time.monotonic() - started, 4)

    def test_stale_fragment_and_unbound_agent_field_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            index_path, work_dir, _root_task, index = self.create_fixture_run(
                directory
            )
            first = index["branches"][0]
            stem = f"{first['root_id']}--{first['branch_id']}"
            fragment_path = work_dir / "fragments/branches" / f"{stem}.json"
            stored = load_json(fragment_path)
            stored["inputs_sha256"] = "0" * 64
            atomic_write(fragment_path, json_content(stored))
            with self.assertRaisesRegex(ContractError, "stale task hash"):
                assemble(
                    index_path,
                    work_dir,
                    "tr",
                    directory / "stale.json",
                )

            task_path = work_dir / "tasks/branches" / f"{stem}.json"
            response = branch_response(copy.deepcopy(self.fixture["branches"][0]))
            response["dictionary_annotations"] = []
            write_fragment(fragment_path, task_path, response)
            with self.assertRaisesRegex(ContractError, "unknown property"):
                assemble(
                    index_path,
                    work_dir,
                    "tr",
                    directory / "roster.json",
                )

    def test_codex_adapter_runs_and_resumes_complete_workflow(self):
        fake_codex_source = r'''#!/usr/bin/env python3
import json
import pathlib
import sys

prompt = sys.stdin.read()
task_text = prompt.split("```json\n", 1)[1].split("\n```", 1)[0]
task = json.loads(task_text)
fixture = json.loads(
    pathlib.Path("v2/examples/root_000858.tr.entry.json").read_text(encoding="utf-8")
)
role = task["role"]
if role == "branch_writer":
    branch = next(
        row for row in fixture["branches"]
        if row["root_id"] == task["root_id"] and row["branch_id"] == task["branch_id"]
    )
    response = {
        "root_id": branch["root_id"],
        "branch_id": branch["branch_id"],
        "language": task["language"],
        "image_transliteration": branch["image_transliteration"],
        "summary": branch["summary"],
        "source_summary": branch["source_discussion"]["discussion"],
        "usage_notes": [
            {"kind": note["kind"], "statement": note["statement"]}
            for note in branch["usage_notes"]
        ],
        "evidence_qualifiers": [
            {"type": item["type"], "statement": item["statement"]}
            for item in branch["evidence_qualifiers"]
        ],
        "glosses": branch["glosses"],
        "arabic_neighbor_distinctions": [
            {
                key: neighbor[key]
                for key in (
                    "neighbor_root_id",
                    "neighbor_branch_id",
                    "expression_transliteration",
                    "gloss",
                    "shared_zone",
                    "distinction",
                )
            }
            for neighbor in branch["arabic_neighbor_distinctions"]
        ],
        "neighbor_coverage": {
            "assessment": branch["neighbor_coverage"]["assessment"],
            "note": branch["neighbor_coverage"]["note"],
        },
    }
else:
    response = {
        "root_envelope_id": task["root_envelope_id"],
        "language": task["language"],
        "root_profile": fixture["root_profile"],
    }
output = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
output.write_text(json.dumps(response, ensure_ascii=False) + "\n", encoding="utf-8")
'''
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            isolated_fixture = directory / "fixture.json"
            isolated_fixture.write_text(
                json_content(self.fixture), encoding="utf-8"
            )
            fake_codex_source = fake_codex_source.replace(
                'pathlib.Path("v2/examples/root_000858.tr.entry.json")',
                f"pathlib.Path({str(isolated_fixture)!r})",
            )
            work_dir = directory / "work"
            _packet_path, _packet, index_path, index = prepare_inputs(
                "root_000858",
                "tr",
                None,
                DEFAULT_FURUQ,
                None,
            )
            tasks = prepare_initial_tasks(index_path, index, "tr", work_dir)
            fake_codex = directory / "fake-codex"
            fake_codex.write_text(fake_codex_source, encoding="utf-8")
            fake_codex.chmod(0o755)
            entry_path = directory / "entry.json"
            markdown_path = directory / "entry.md"
            arguments = {
                "codex_binary": str(fake_codex),
                "model": None,
                "workers": 4,
                "max_repairs": 2,
            }
            with mock.patch(
                "v2.scripts.create_entry.confined_agent_command",
                side_effect=lambda command, _workspace: command,
            ):
                run_workflow(
                    index_path,
                    index,
                    "tr",
                    work_dir,
                    entry_path,
                    markdown_path,
                    tasks,
                    **arguments,
                )
            first_mtimes = {
                path: path.stat().st_mtime_ns
                for path in (work_dir / "fragments").rglob("*.json")
            }
            with mock.patch(
                "v2.scripts.create_entry.confined_agent_command",
                side_effect=lambda command, _workspace: command,
            ):
                run_workflow(
                    index_path,
                    index,
                    "tr",
                    work_dir,
                    entry_path,
                    markdown_path,
                    tasks,
                    **arguments,
                )
            self.assertEqual(
                first_mtimes,
                {
                    path: path.stat().st_mtime_ns
                    for path in (work_dir / "fragments").rglob("*.json")
                },
            )
            self.assertEqual(load_json(entry_path), self.fixture)
            self.assertTrue(markdown_path.read_text(encoding="utf-8").startswith(
                "<!-- generated-by: v2/scripts/render_entry.py schema=4 -->"
            ))


if __name__ == "__main__":
    unittest.main()
