# Cold-Start Orchestration Runbook

This is the operational entry point for an agent with no prior conversation
context. It explains what this workflow does, why it exists, what must be
checked, and how to run or resume it.

Run every command from the repository root. Values in angle brackets are
placeholders; replace them with concrete paths or identifiers before running a
command.

## 1. Establish the boundary

This workflow produces compact target-language translation glosses from an
existing validated Turkish v2 entry. It does **not**:

- create or review the Turkish encyclopedia entry;
- regenerate the mechanically rendered occurrence section;
- translate the entire dictionary entry;
- rebuild root packets, QAC evidence, Furūq evidence, or neighbor networks;
- publish into `v2/entries/<language>/`.

The durable output is:

```text
v2/gloss_generation/results/<locale>/<root-envelope>.json
```

It contains concept, contextual, and lexical glosses with per-gloss semantic
fit/error profiles. It remains hash-bound to the Turkish source entry, source
packet, semantic package, prompts, locale policy, schemas, and independent
review.

## 2. Read in this order

Before running anything, read:

1. [`README.md`](README.md): architecture, artifacts, and command summary;
2. [`LANGUAGE_ROLLOUT.md`](LANGUAGE_ROLLOUT.md): why these 33 locales were
   selected and how script policy works;
3. [`orchestrator.md`](orchestrator.md): normative controller role, state
   machine, repair budget, and concurrency rules;
4. [`prompt.md`](prompt.md): shared writer contract;
5. [`review_prompt.md`](review_prompt.md): independent reviewer contract.

Read the target's `locales/<locale>.json` and
`locale_prompts/<locale>.md` before launching that locale. Do not read all 33
locale prompts when running only one locale.

If these documents conflict, follow `orchestrator.md` for control flow,
`workflow.py` and the JSON Schemas for machine validation, and record the
documentation discrepancy before continuing.

## 3. Understand what was implemented

The workflow has five layers:

| Layer | Owner | Purpose |
|---|---|---|
| Compact package extraction | `workflow.py` | Projects only translation-relevant Turkish and Arabic fields; excludes occurrences and apparatus |
| Locale policy | `locales/*.json` and `locale_prompts/*.md` | Defines target standard, script, idiom, morphology, loanword risks, proper names, and QA checks |
| Gloss writing | one target-language writer | Authors concept, contextual, and lexical gloss candidates with error profiles |
| Independent review and one repair | fresh reviewer, then retained writer if needed | Produces `pass`, bounded `repair`, or `editorial_review`; prevents self-approval |
| Deterministic acceptance | `workflow.py` | Verifies hashes, freshness, rosters, facets, repair scope, review binding, and stores the reviewed result |

This design reuses Arabic semantic analysis and the Turkish semantic entry while
keeping target-language lexical judgment independent. It avoids the cost and
error surface of asking every locale to recreate a complete encyclopedia entry.

Arabic-script permission is locale-bound. There is deliberately no
`--ignore-arabic` switch: Urdu, Persian, Dari, Pashto, Sorani, and Shahmukhi
Punjabi declare `Arab`; Latin-, Cyrillic-, and Bengali-script locales do not.

## 4. Confirm controller configuration

Do not launch a linguistic worker until all of the following are explicit:

- root scope: one Turkish entry, an explicit root list, or all current Turkish
  entries;
- locale scope: exact locale list or `western-muslim-priority`;
- writer model and reasoning profile;
- reviewer model and reasoning profile;
- maximum concurrent worker turns, if lower than runtime capacity;
- whether this is a new run or a resume.

The safe default locale set is only `en`, `de`, and `tr`. The approved rollout
set contains 33 locales and must be requested explicitly.

## 5. Preflight

Confirm that the command is being run from the repository root:

```sh
test -f v2/gloss_generation/workflow.py
```

Inspect the CLI:

```sh
python3 v2/gloss_generation/workflow.py --help
```

Validate the workflow before a campaign:

```sh
python3 -m unittest v2.gloss_generation.tests.test_workflow
```

After changing workflow code, schemas, prompts, or locale policy, run the full
v2 regression set:

```sh
python3 -m unittest \
  v2.tests.test_branch_lexicalization \
  v2.tests.test_entry_projection \
  v2.tests.test_entry_schema \
  v2.tests.test_entry_workflow \
  v2.tests.test_export_jsonl \
  v2.tests.test_render_occurrences \
  v2.tests.test_root_packet \
  v2.gloss_generation.tests.test_workflow
```

Confirm the requested Turkish source exists:

```sh
test -f v2/entries/tr/<root-envelope>.json
```

List available Turkish entries without manufacturing root IDs:

```sh
find v2/entries/tr -maxdepth 1 -name 'root_*.json' -print | sort
```

Confirm a requested locale is in the rollout and has both required files:

```sh
jq -e '.sets["western-muslim-priority"] | index("<locale>") != null' \
  v2/gloss_generation/rollout.json
test -f v2/gloss_generation/locales/<locale>.json
test -f v2/gloss_generation/locale_prompts/<locale>.md
```

Do not start a writer if source validation or preparation fails.

## 6. Run one root and locale

The following concrete example uses `root_000858/en`.

### 6.1 Prepare

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858 \
  --languages en
```

Expected writer task:

```text
v2/gloss_generation/work/root_000858/en/input/task.json
```

Preparation validates the Turkish entry and packet, extracts the compact
package, copies the canonical prompts/schemas/locale policy, and writes a
controller-owned task seal. It does not call a model.

### 6.2 Reuse or dispatch the writer

If `output/glosses.json` already exists, validate it first:

```sh
python3 v2/gloss_generation/workflow.py validate \
  v2/gloss_generation/work/root_000858/en/input/task.json
```

Reuse only on exit zero. Otherwise delegate exactly:

```text
ROLE: target-language gloss writer
SUBAGENTS: forbidden
INPUT: v2/gloss_generation/work/root_000858/en/input/instructions.md
OUTPUT: the path declared by that task
COMMANDS: only the validation argv declared by that task
```

The controller delegates the staged `instructions.md`, not `prompt.md`
directly. The worker must read only staged files named there, write only the
declared output, and perform the linguistic task itself.

After the worker returns, the controller reruns the validation command. A
worker success message is not evidence of validity.

### 6.3 Prepare independent review

```sh
python3 v2/gloss_generation/workflow.py prepare-review \
  v2/gloss_generation/work/root_000858/en/input/task.json
```

Expected review task:

```text
v2/gloss_generation/work/root_000858/en/review/input/task.json
```

If `review/output/review.json` already exists, validate it first:

```sh
python3 v2/gloss_generation/workflow.py review-validate \
  v2/gloss_generation/work/root_000858/en/review/input/task.json
```

Otherwise delegate exactly:

```text
ROLE: independent target-language gloss reviewer
SUBAGENTS: forbidden
INDEPENDENCE: must not be the writer or a participant in writer repair
INPUT: v2/gloss_generation/work/root_000858/en/review/input/instructions.md
OUTPUT: the path declared by that review task
COMMANDS: only the validation argv declared by that review task
```

After the reviewer returns, rerun `review-validate` and read the validated
verdict from `review/output/review.json`.

### 6.4 Route the verdict

For `pass`, accept:

```sh
python3 v2/gloss_generation/workflow.py accept \
  v2/gloss_generation/work/root_000858/en/input/task.json \
  v2/gloss_generation/work/root_000858/en/review/input/task.json
```

For `repair`, follow section 7.

For `editorial_review`, stop this root/locale pair and report the exact review
artifact. Do not accept, rewrite the verdict, or invent a larger repair scope.

## 7. Run the one permitted repair

Stage the bounded repair from the initial review:

```sh
python3 v2/gloss_generation/workflow.py prepare-repair \
  v2/gloss_generation/work/root_000858/en/review/input/task.json
```

Expected repair task:

```text
v2/gloss_generation/work/root_000858/en/repair/input/task.json
```

Continue the retained writer assignment:

```text
ROLE: same target-language gloss writer
MODE: bounded repair
SUBAGENTS: forbidden
INPUT: v2/gloss_generation/work/root_000858/en/repair/input/instructions.md
OUTPUT: the path declared by that repair task
SCOPE: only task.json repair_scope
```

The response must remain complete, use the new repair-task hash, change every
requested scope, and change nothing outside it. Validate:

```sh
python3 v2/gloss_generation/workflow.py validate \
  v2/gloss_generation/work/root_000858/en/repair/input/task.json
```

Prepare a fresh rebound review:

```sh
python3 v2/gloss_generation/workflow.py prepare-review \
  v2/gloss_generation/work/root_000858/en/repair/input/task.json
```

Delegate:

```text
ROLE: fresh independent target-language gloss reviewer
INPUT: v2/gloss_generation/work/root_000858/en/repair/review/input/instructions.md
```

Validate:

```sh
python3 v2/gloss_generation/workflow.py review-validate \
  v2/gloss_generation/work/root_000858/en/repair/review/input/task.json
```

Accept only a rebound `pass`:

```sh
python3 v2/gloss_generation/workflow.py accept \
  v2/gloss_generation/work/root_000858/en/repair/input/task.json \
  v2/gloss_generation/work/root_000858/en/repair/review/input/task.json
```

If the rebound verdict is `repair` or `editorial_review`, park the pair. There
is no second semantic repair.

## 8. Run multiple locales or a campaign

Stage selected locales for one root:

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858 \
  --languages en de tr ur fa-IR
```

Stage the approved set for one root:

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858 \
  --language-set western-muslim-priority
```

Stage every current Turkish entry:

```sh
python3 v2/gloss_generation/workflow.py prepare-all \
  --language-set western-muslim-priority
```

`prepare-all` stages deterministic tasks only. It does not launch workers.

Track state per `<root-envelope>/<locale>`, not merely per root. Different
pairs may run concurrently within the configured cap. The same pair must never
have a writer and reviewer—or two competing writers—in flight together.

Start with a representative 20-root pilot before a full 33-locale corpus run.
Schema validity alone is not release quality; lower-resource locales require
native or expert sampling.

## 9. Resume safely

Generated `work/` and `results/` are git-ignored but intentionally resumable.
On resume:

1. rerun the same `prepare` command to refresh canonical task inputs;
2. validate any existing writer output before launching a writer;
3. prepare the review only after writer validation;
4. validate any existing review before launching a reviewer;
5. route the stored verdict exactly;
6. rerun `accept` for a passing, matching pair—acceptance is idempotent when
   the existing result is byte-identical.

Canonical changes to `workflow.py`, rollout policy, locale packs, locale
prompts, shared prompts, or schemas intentionally make older tasks stale.
Restaging creates the new task hash. An old output must be corrected or
regenerated against that new task; never edit hashes manually.

Do not infer completion from a filename, worker message, or prior run note.
Only deterministic validation plus `status: reviewed` in the accepted result
is terminal success.

## 10. Failure ownership

| Failure | Owner/action |
|---|---|
| Missing or invalid Turkish entry/packet | Controller parks or repairs the upstream deterministic prerequisite; do not launch a gloss writer |
| Missing locale JSON or locale prompt | Controller fixes rollout/configuration; do not bypass locale validation |
| Canonical digest or task-seal mismatch | Controller restages; worker must not rewrite task files or seals |
| Writer response schema, roster, facet, script, or hash error | Return exact error to the same writer for in-place output correction |
| Review response schema or hash error | Return exact error to that reviewer; do not reinterpret verdict |
| Initial semantic `repair` | Retained writer gets one generated bounded repair task |
| Rebound non-pass | Park; do not create a second repair |
| `editorial_review` | Human decision required; never auto-accept |
| Existing conflicting reviewed result | Stop unless the user explicitly authorizes `--force` for that exact result |

The controller never manually patches worker-authored JSON to make a gate pass.

## 11. Completion checklist

A `<root-envelope>/<locale>` pair is complete only when:

- the current writer task and canonical dependencies validate;
- the writer response matches the exact branch and lexical-unit rosters;
- every concept and lexical gloss accounts for its applicable facets;
- script policy and every fit/error profile pass;
- an independent review bound to the byte-exact final writer response returns
  `pass`;
- any repair stayed within the generated scope and received a fresh review;
- `workflow.py accept` exits zero;
- the stored result has `status: reviewed`.

Report campaign totals for reviewed and parked pairs. For every parked pair,
include the exact failed gate or editorial-review path.

## 12. Copy-paste startup instruction

Give one top-level controller:

```text
Read v2/gloss_generation/RUNBOOK.md,
v2/gloss_generation/orchestrator.md, and
v2/gloss_generation/LANGUAGE_ROLLOUT.md. Run the compact multilingual gloss
workflow for <root scope> and <locale scope>. Writer workers:
<model/reasoning>. Reviewer workers: <model/reasoning>. Worker cap: <N>.
This is a <new/resume> run. Perform every deterministic workflow.py command
yourself; delegate only the staged writer and independent reviewer instructions;
enforce one repair and one rebound review; finish every root/locale pair as
reviewed or parked with exact artifacts.
```
