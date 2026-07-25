# Dictionary

## Current production workflow

Current encyclopedia entry development and production use `v2/`. Legacy
root-level workflow files are reference material and are not the current
orchestration.

An agent that will control an entry run must start at the
[v2 orchestration entry point](v2/orchestration/README.md). That README routes
the controller to:

1. the normative orchestration contract;
2. the controller prompt;
3. the production command runbook; and
4. the authored-entry schema contract.

Do not start from a historical work manifest or invoke the retired branch-writer
or root-profile-writer prompts.

## Root packet preparation

Root packet generation is deterministic coordinator work, not agent work. The
current v4 packet preparation script is:

```sh
python3 scripts/prepare_missing_root_packets.py
```

The script enumerates v4 root envelopes from `data/working/furuq_v4.sqlite` as
1,679 Quranic branch-backed envelopes plus 1,770 non-Quranic `furuq`
dictionary-backed envelopes. It calls:

```sh
python3 scripts/root_packet.py <root_id>
```

for each missing representative root. `scripts/root_packet.py` skips an
envelope when its JSON packet already exists, unless `--force` is passed.

The all-v4 completion run using this deterministic script completed with 3,449
total v4 envelopes, 3,449 existing packet JSON files, 0 failed subprocesses,
and 0 remaining missing packet JSON files. Re-running the same command is safe
because existing packet JSONs are skipped.

## Start an orchestration

Start the workflow by instructing one top-level controller agent. There is
intentionally no `--run-agents` command and no script that owns worker
lifecycles.

For one root envelope:

```text
Read v2/orchestration/README.md and run the current v2 entry orchestration
for root_000858 in tr. Writer workers: <model and reasoning profile>.
Reviewer workers: <model and reasoning profile>. Use <optional worker cap>
or the runtime's available capacity.
```

For a campaign:

```text
Read v2/orchestration/README.md and run the current v2 entry orchestration
for the first <N> packet envelopes in tr. Writer workers: <model and reasoning
profile>. Reviewer workers: <model and reasoning profile>. Worker cap: <N>.
```

Replace every placeholder with the intended run configuration. A named,
existing campaign configuration may supply the worker settings instead. The
controller must not invent a model, reasoning profile, service tier, or
concurrency limit.

The controller runs preparation and every other deterministic command itself.
Its first per-root preparation command, run from the repository root, is:

```sh
python3 v2/scripts/create_entry.py root_000858 --language tr
```

That command prepares resumable state; it does not launch agents or complete the
orchestration. Only the controller may use native delegation, and only for the
staged root writer and independent semantic reviewer.

## Quranic Turkish continuation checkpoint

This repository contains an in-progress Turkish entry campaign for the 1,679
Quranic root-packet set. A cold controller agent continuing this campaign should
start from the repository root, read `v2/orchestration/README.md`,
`v2/orchestration/entry-creation.spec.md`, and `v2/prompts/entry-orchestrator.md`,
then reconcile the current state from disk before launching any workers.

Current checkpoint:

- Quranic packet count: 1,679.
- Accepted Turkish fragments: 1,031.
- Staged writer tasks without output: 0.
- Stale output JSONs without accepted fragments: `root_000072`, `root_000089`,
  `root_000124`, `root_000129`, `root_000135`, `root_000136`, `root_000137`,
  `root_000726`, `root_000736`, `root_000741`, `root_000743`, `root_000744`.
- Known parked deterministic-preparation failures: `root_000405`,
  `root_000574`, `root_000618`, `root_000633`, `root_000671`, `root_000719`,
  `root_000752`, `root_000822`, `root_000839`, `root_000889`, `root_000956`,
  `root_000966`, `root_000967`, `root_000984`, `root_001005`, `root_001040`,
  `root_001042`, `root_001046`.
- The next ordinary continuation roots, after accepted fragments, stale outputs,
  and parked prep failures are skipped, begin at `root_001078`.

Operational constraints for continuation:

- Language is Turkish: pass `--language tr`.
- Use one root packet per writer agent.
- Use `5.6 sol` with `xhigh` reasoning for writer agents.
- Do not set a service tier.
- Run in 200-root batch targets with at most 20 active writer agents.
- Do not pre-stage beyond open worker slots.
- Accept and close each worker immediately after its output validates.
- Reconcile from disk at batch boundaries and after any interruption.
- Do not finalize, publish, or review entries during this continuation unless the
  user explicitly changes the scope.
- Do not filter out packet branches because of branch status, review flags, or
  contamination markers. Quranic contamination marks Quranic-root contamination,
  not furuq/non-Quranic branch exclusion.
- Non-bare and collocation branch flags are produced by the deterministic
  attachment/injection workflow; preserve them in the writer task inputs.

For each open worker slot, prepare only that root:

```sh
python3 v2/scripts/create_entry.py <root> --language tr
python3 v2/scripts/stage_root_writer.py v2/work/entry_creation/<root>/tr/tasks/root_writer.json
```

Launch the root writer with this prompt shape:

```text
Turkish v2 root-writer. Repo: /Volumes/OZTURK/_projects/dictionary. Root:
<root>. Read and obey v2/work/entry_creation/<root>/tr/input/instructions.md.
Use v2/work/entry_creation/<root>/tr/input/task.json. Write only the declared
output path. Preserve unrelated changes; no reset/restore/pull/revert. Do not
publish/finalize/review/delegate. Final: output path and validation result only.
```

When a worker completes, validate and accept immediately:

```sh
python3 v2/scripts/validate_agent_output.py v2/work/entry_creation/<root>/tr/input/task.json
mkdir -p v2/work/entry_creation/<root>/tr/fragments
cp -p v2/work/entry_creation/<root>/tr/output/<root>_entry.json v2/work/entry_creation/<root>/tr/fragments/<root>_entry.json
```

A cold-start reconciliation should classify roots mechanically:

- Quranic queue: `data/output/root_packets/root_*.json` files whose branch list
  contains `origin_corpus == "quranic"`.
- Accepted: `v2/work/entry_creation/<root>/tr/fragments/<root>_entry.json`
  exists.
- Stale or unaccepted output: output exists but fragment does not.
- Prepared/no-output: task or input exists but output and fragment do not.
- Unstarted: none of the above.

Use only in-memory bookkeeping during an active 200-root batch. The filesystem
is the source of truth when a new controller starts or a batch ends.
