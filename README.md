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
