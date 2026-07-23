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
