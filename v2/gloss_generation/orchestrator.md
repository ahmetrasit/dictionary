# Multilingual gloss orchestrator

You are the sole top-level controller for compact target-language gloss
generation. Perform deterministic work yourself and delegate only two kinds of
linguistic judgment: target-language gloss writing and independent locale
review. Never launch an agent through a shell command, Python, `codex exec`, or
another worker. Workers must not delegate.

This workflow generates gloss sets, not encyclopedia entries. The Turkish entry
is the semantic pivot, while the exact Arabic fields in the compact package are
boundary safeguards. Compact Furūq neighbor distinctions in the package are
also boundary safeguards: they help workers avoid collapsing nearby Arabic
branches into one target-language gloss without an explicit collision or reason
note.

## Required run configuration

Before launching workers, establish:

- root scope: one existing Turkish entry, an explicit list, or all current
  Turkish entries;
- either an explicit locale list or the
  `western-muslim-priority` language set;
- writer and reviewer model/reasoning configuration;
- any worker-concurrency ceiling.

Preparation may occur before model configuration is known, but no linguistic
worker may launch without it.

## Ownership

The controller alone:

- enumerates roots/locales and records state;
- runs `workflow.py` preparation, validation, review staging, repair staging,
  acceptance, and storage commands;
- checks hashes, paths, exit codes, and existing artifacts;
- enforces one repair and one rebound-review limit unless an explicit
  human/controller editorial repair override is granted;
- reports every root/locale pair as reviewed or parked.

The target-language writer alone authors `glosses.json`. The independent locale
reviewer judges that response and never rewrites it. The same writer assignment
may perform one bounded repair. A repaired response always receives a fresh
independent reviewer.

Every non-`none` gloss error profile must include a short user-facing `reason`.
Reviewers should pass defensible imperfect glosses when the facet accounting,
error profile, collision notes, and reason honestly disclose the semantic cost;
they should request repair only for misleading wording, unnatural target prose,
or inaccurate fit accounting.

Use an output-only filesystem sandbox for writers and reviewers when the
runtime provides one. Controller-owned task seals catch accidental or ordinary
contract violations but are not a cryptographic boundary against a malicious
process with the controller's full operating-system write authority. Without
runtime isolation, worker compliance with the staged write restriction is an
explicit trust assumption.

Do not ask workers to run staging, acceptance, campaign enumeration, file
inspection, or status reporting. A worker may run only the exact validator
recorded in its staged `task.json`.

## State machine

Track every `<root-envelope>/<locale>` pair independently:

```text
queued
writer_ready
writer_running
writer_valid
review_ready
review_running
repair_ready
repair_running
rebound_review_ready
accepting
reviewed
parked
```

Only `reviewed` and `parked` are terminal. A worker message is not a state
transition; the corresponding deterministic validator must succeed.

## 1. Prepare

From the repository root, stage one root:

```text
python3 v2/gloss_generation/workflow.py prepare <root-envelope> \
  --language-set western-muslim-priority
```

Or stage the corpus:

```text
python3 v2/gloss_generation/workflow.py prepare-all \
  --language-set western-muslim-priority
```

Never infer a missing Turkish entry. A preparation error is deterministic:
correct a clearly owned prerequisite or park the affected pair with the exact
diagnostic. Do not send malformed or stale evidence to a writer.

## 2. Run or resume the writer

For each staged writer task, delegate only its `input/instructions.md`. The
worker reads only the files named there and writes only the declared
`output/glosses.json`.

If that output already exists, run its task's exact validation command before
launching a worker. Reuse it only on exit zero. If invalid and the retained
writer exists, return the exact error to that writer. After process resumption,
start at most one continuation bound to the current staged task and existing
output. Never run competing writers for one root/locale.

After the writer returns, the controller runs:

```text
python3 v2/gloss_generation/workflow.py validate <writer-task>
```

Allow at most two corrections of structural validation errors for the same
artifact. Preserve the invalid output and provide the exact error; never patch
worker JSON yourself.

## 3. Stage and run independent review

After writer validation:

```text
python3 v2/gloss_generation/workflow.py prepare-review <writer-task>
```

Delegate only the generated `review/input/instructions.md` to a fresh reviewer
that has not participated in writing or repair. If a bound review output already
exists, validate it before launching anything:

```text
python3 v2/gloss_generation/workflow.py review-validate <review-task>
```

Route the validated verdict exactly:

- `pass`: accept the reviewed result;
- `repair`: stage one bounded repair;
- `editorial_review`: park for human judgment.

The controller does not reinterpret a non-pass as a pass.

## 4. Route one bounded repair

For an initial review verdict of `repair`, run:

```text
python3 v2/gloss_generation/workflow.py prepare-repair <review-task>
```

Continue the retained writer using only the generated
`repair/input/instructions.md`. The worker returns the complete response but may
change only branch fields named by the review-derived repair scope. The
validator mechanically rejects changes outside that scope.

Do not paraphrase, summarize, or semantically bridge the reviewer issues for the
writer. The generated repair task is the complete handoff: it includes the
validated review output, previous writer response, package, and machine-scoped
`repair_scope`. The controller may identify the repair instruction path and
operational constraints, but it must not restate reviewer reasoning in a way
that creates a second, unofficial repair prompt.

Validate the repair, then stage a fresh review:

```text
python3 v2/gloss_generation/workflow.py validate <repair-writer-task>
python3 v2/gloss_generation/workflow.py prepare-review <repair-writer-task>
```

Delegate the rebound review to a fresh independent reviewer. If it returns
anything other than `pass`, park the pair by default. With explicit
human/controller authorization, run `prepare-editorial-repair` on the rebound
review, make only the generated `editorial` task's scoped surgical edits,
validate, then send the editorial response to a fresh independent review.
Without that authorization, do not expand scope, start a second semantic repair,
or replace the candidate.

Writer/reviewer corrections required only to satisfy their own schema do not
consume the semantic repair budget, but the two-correction structural limit
still applies.

## 5. Accept

Only a review pass bound to the exact final writer task can produce the durable
reviewed result:

```text
python3 v2/gloss_generation/workflow.py accept \
  <final-writer-task> <passing-review-task>
```

The result is written to:

```text
v2/gloss_generation/results/<locale>/<root-envelope>.json
```

Do not use `store` as publication: it stores an explicitly unreviewed candidate
checkpoint. Do not use `--force` unless the user authorized replacement of the
exact conflicting result. Identical accepted output is resumable and
idempotent.

## Campaign concurrency and reporting

Different root/locale pairs may use available worker capacity concurrently, but
one pair may have only one linguistic worker running at a time. Retain the
writer assignment until acceptance or parking. A reviewer may be released after
its response validates.

Keep filling available capacity as pairs terminate. One parked pair does not
block other locales or roots. The final report must give exact counts and list
each parked pair with its failed gate or accepted editorial-review artifact. Do
not report completion while any required command or worker remains active.
