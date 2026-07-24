# V2 Orchestration Entry Point

This directory contains the current production orchestration for encyclopedia
entry schema version 4. This README is a discovery and startup guide, not a
second specification.

## Read in this order

1. [`entry-creation.spec.md`](entry-creation.spec.md) is the normative workflow,
   ownership, state, repair, and acceptance contract.
2. [`../prompts/entry-orchestrator.md`](../prompts/entry-orchestrator.md) is the
   instruction set for the sole top-level controller.
3. [`../PRODUCTION_RUNBOOK.md`](../PRODUCTION_RUNBOOK.md) is the exact
   repository-root command sequence and campaign procedure.
4. [`../schema/README.md`](../schema/README.md) is the human contract for the
   authored master entry; the JSON Schema is the machine contract.

If this README conflicts with the normative spec, follow the spec and correct
the README. Do not improvise a hybrid workflow from older manifests or prompts.

## Required run request

Before launching semantic workers, the controller must know:

- the root scope: one existing packet envelope, an explicit envelope list, the
  first `N` packet envelopes, or a through/until boundary;
- the target language (`en` or `tr`);
- the writer model and reasoning profile;
- the reviewer model and reasoning profile;
- any explicit service tier or worker cap requested for the run.

A named campaign configuration may provide those settings. Deterministic
preparation may run while worker configuration is unresolved, but a writer or
reviewer may not be launched until its model and reasoning profile are
explicit. Runtime capacity is the default concurrency ceiling; an explicit cap
can only lower it.

Queue scope is resolved from actual
`data/output/root_packets/root_*.json` files. Do not manufacture missing IDs.
A combined envelope such as `root_000099--root_000100` is one queue item and is
never split.

## Start

Give one top-level controller an instruction like:

```text
Read v2/orchestration/entry-creation.spec.md and
v2/prompts/entry-orchestrator.md, then run the v2 entry orchestration for
root_000858 in tr. Writer workers: <model and reasoning profile>. Reviewer
workers: <model and reasoning profile>. Worker cap: <optional N>.
```

Campaign form:

```text
Read v2/orchestration/entry-creation.spec.md and
v2/prompts/entry-orchestrator.md, then run the v2 entry orchestration for the
first <N> packet envelopes in tr. Writer workers: <model and reasoning profile>.
Reviewer workers: <model and reasoning profile>. Worker cap: <N>.
```

For an interrupted run, use the same scope and configuration and say `resume`.
The controller must prove reuse with the check scripts and task hashes; it must
not infer completion from an existing filename or a worker's status message.

There is no orchestration CLI and intentionally no `--run-agents` option. The
controller begins each eligible root directly, from the repository root:

```sh
python3 v2/scripts/create_entry.py <root-envelope> --language <language>
```

Angle-bracket values in documentation are placeholders. Resolve them before
running a command; never pass the brackets literally.

## Controller rules that prevent common failures

- One top-level controller owns the queue, commands, state transitions, worker
  sessions, repair budgets, publication, and final report.
- The controller runs all deterministic and operational work directly,
  including scripts, file and hash checks, staging, validation, acceptance,
  polling, finalization, rendering, projection, and export.
- Never spawn a script runner, per-root controller, monitor, queue manager,
  validator, publisher, or status-summary agent.
- Delegate only target-language authorship to the staged root writer and
  independent semantic judgment to the staged reviewer. Use native delegation,
  never Python, shell, `codex exec`, or another worker.
- Writers and reviewers cannot spawn subagents. They read only their staged
  package, write only the declared repository-local output, and may run only
  the exact read-only validator recorded in `task.json`.
- Keep same-root work serial. Different roots may use available worker capacity
  concurrently, but a root never has competing writer, review, or repair turns.
- Retain the writer session through review and finalization so bounded repair or
  generated surface-form queues return to the same assignment.
- Treat each branch's staged `source_phrase_ar` as branch authority. Lexical
  units are optional attestations, and their source roster is not the branch
  dictionary basis. The writer must echo the mechanical bare/collocation class
  and may record a supported reframing without altering frozen Arabic evidence.
- Park `structural_review_required` identity judgments before semantic review,
  assembly, or publication.
- Never manually edit or copy worker JSON to bypass a gate. Route structural
  errors to the owning worker and run deterministic fixes in the controller.
- Never use `--force-entry` or another destructive override without explicit
  user authorization.
- A root is terminal only as `published` or `parked`. A parked root does not
  stop an otherwise runnable campaign.

The current writer is [`../prompts/root-writer.md`](../prompts/root-writer.md);
the independent reviewer is
[`../prompts/root-reviewer.md`](../prompts/root-reviewer.md). Do not directly
launch either prompt. `create_entry.py` and the staging scripts generate the
hash-bound instructions and exact output paths that the controller delegates.
`branch-writer.md` and `root-profile-writer.md` are retired compatibility
tombstones, not production roles.

## Durable state and outputs

Resumable controller state and worker artifacts stay under:

```text
v2/work/entry_creation/<root-envelope>/<language>/
```

Published entry pairs are:

```text
v2/entries/<language>/<root-envelope>.json
v2/entries/<language>/<root-envelope>.md
```

Workers must not use `/tmp`, runtime scratch space, another root's work
directory, or published entry paths. The controller reports the published pair
or the exact parked gate for every requested root.
