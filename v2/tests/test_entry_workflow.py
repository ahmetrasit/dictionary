import copy
import tempfile
import unittest
from pathlib import Path

from v2.scripts.assemble_entry import (
    canonical_sha256,
    assemble,
    json_content,
    validate_fragment,
)
from v2.scripts.build_branch_evidence import DEFAULT_FURUQ, build_packages
from v2.scripts.create_entry import (
    atomic_write,
    prepare_initial_tasks,
    prepare_inputs,
    prepare_root_task,
    run_workflow,
)
from v2.scripts.render_entry import render
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
        "source_discussion": branch["source_discussion"],
        "dictionary_annotations": [
            {
                "source_id": source["source_id"],
                "roles": source["roles"],
                "contribution": source["contribution"],
            }
            for source in branch["dictionary_basis"]["sources"]
        ],
        "glosses": branch["glosses"],
        "arabic_neighbor_distinctions": branch[
            "arabic_neighbor_distinctions"
        ],
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

    def test_fixture_fragments_match_all_agent_schemas(self):
        for branch in self.fixture["branches"]:
            validate_fragment(
                branch_response(branch),
                "branch_writer",
                FIXTURE,
            )
        occurrence = {
            "root_envelope_id": self.fixture["root_envelope_id"],
            "language": "tr",
            "observations": self.fixture["occurrence_evidence"]["observations"],
        }
        validate_fragment(occurrence, "occurrence_observer", FIXTURE)
        root = {
            "root_envelope_id": self.fixture["root_envelope_id"],
            "language": "tr",
            "root_profile": self.fixture["root_profile"],
        }
        validate_fragment(root, "root_profile_writer", FIXTURE)

    def create_fixture_run(self, directory: Path) -> tuple[Path, Path, Path, dict]:
        evidence_dir = directory / "evidence"
        work_dir = directory / "work"
        _packet_path, _packet, index_path, index = prepare_inputs(
            "root_000858",
            "tr",
            None,
            DEFAULT_FURUQ,
            evidence_dir,
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

        occurrence_task = work_dir / "tasks/occurrence_observations.json"
        write_fragment(
            work_dir / "fragments/occurrence_observations.json",
            occurrence_task,
            {
                "root_envelope_id": self.fixture["root_envelope_id"],
                "language": "tr",
                "observations": self.fixture["occurrence_evidence"]["observations"],
            },
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

    def test_stale_fragment_and_wrong_dictionary_roster_are_rejected(self):
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
            response["dictionary_annotations"].pop()
            write_fragment(fragment_path, task_path, response)
            with self.assertRaisesRegex(ContractError, "roster mismatch"):
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
        "source_discussion": branch["source_discussion"],
        "dictionary_annotations": [
            {
                "source_id": source["source_id"],
                "roles": source["roles"],
                "contribution": source["contribution"],
            }
            for source in branch["dictionary_basis"]["sources"]
        ],
        "glosses": branch["glosses"],
        "arabic_neighbor_distinctions": branch["arabic_neighbor_distinctions"],
    }
elif role == "occurrence_observer":
    response = {
        "root_envelope_id": task["root_envelope_id"],
        "language": task["language"],
        "observations": fixture["occurrence_evidence"]["observations"],
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
            evidence_dir = directory / "evidence"
            work_dir = directory / "work"
            _packet_path, _packet, index_path, index = prepare_inputs(
                "root_000858",
                "tr",
                None,
                DEFAULT_FURUQ,
                evidence_dir,
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
                "<!-- generated-by: v2/scripts/render_entry.py schema=2 -->"
            ))


if __name__ == "__main__":
    unittest.main()
