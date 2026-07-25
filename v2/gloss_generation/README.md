# Multilingual Gloss Generation

This workflow generates compact, independently reviewed target-language gloss
sets from a validated Turkish v2 entry. It does not generate another
encyclopedia entry.

Read:

1. [`LANGUAGE_ROLLOUT.md`](LANGUAGE_ROLLOUT.md) for the 33-locale rollout and
   script-policy decision;
2. [`orchestrator.md`](orchestrator.md) for the top-level controller prompt;
3. [`prompt.md`](prompt.md) and [`review_prompt.md`](review_prompt.md) for the
   bounded linguistic roles.

Every worker receives one shared role prompt plus a hash-bound
`locale_prompts/<locale>.md`. Locale-specific prompts cover the target standard,
script, grammar, idiom, loanword and calque risks, proper names, error profiles,
and review checks without duplicating the workflow contract.

## Compact semantic package

Preparation deterministically extracts only:

- Turkish branch definitions and facet statements;
- exact packet-validated `source_phrase_ar`, `what_is_ar`, and
  `what_is_not_ar`;
- mechanical lexicalization class and authored Turkish scope note;
- relevant Arabic lexical units, Turkish glosses, and facet bindings;
- rare, disputed, technical, register, or construction constraints.

Occurrence sections, dictionary apparatus, neighbors, renderer fields, and
unrelated provenance never enter the model package.

Every concept, contextual, and lexical gloss records represented facets and a
compact fit profile: `none`, `narrowing`, `broadening`, `displacement`, or
`drifted_loanword`.

## Prepare writer tasks

The safe default stages the smoke set (`en`, `de`, `tr`):

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858
```

Stage the approved 33-locale set:

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858 \
  --language-set western-muslim-priority
```

Or choose exact locales:

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858 \
  --languages en ur fa-IR
```

Use an explicit validated Turkish entry:

```sh
python3 v2/gloss_generation/workflow.py prepare root_000858 \
  --source-entry v2/examples/root_000858.tr.entry.json
```

Writer tasks are staged under:

```text
work/<root-envelope>/<locale>/
  input/instructions.md
  input/task.json
  input/package.json
  input/locale.json
  input/locale_prompt.md
  input/prompt.md
  input/response.schema.json
  output/glosses.json
```

Delegate only `input/instructions.md`. After the worker returns:

```sh
python3 v2/gloss_generation/workflow.py validate \
  v2/gloss_generation/work/root_000858/en/input/task.json
```

## Independent review and repair

Stage a review bound to the exact valid writer response:

```sh
python3 v2/gloss_generation/workflow.py prepare-review \
  v2/gloss_generation/work/root_000858/en/input/task.json
```

Delegate only the generated `review/input/instructions.md`, then validate:

```sh
python3 v2/gloss_generation/workflow.py review-validate \
  v2/gloss_generation/work/root_000858/en/review/input/task.json
```

Route verdicts exactly:

- `pass`: accept;
- `repair`: stage one bounded repair;
- `editorial_review`: park for human judgment.

For `repair`:

```sh
python3 v2/gloss_generation/workflow.py prepare-repair \
  v2/gloss_generation/work/root_000858/en/review/input/task.json
```

The retained writer handles `repair/input/instructions.md`. Validation rejects
changes outside the review-derived scope. The repaired response must receive a
fresh independent review; a second non-pass verdict is terminal.

## Accept

Only a review pass bound to the exact final writer response can produce the
durable reviewed result:

```sh
python3 v2/gloss_generation/workflow.py accept \
  v2/gloss_generation/work/root_000858/en/input/task.json \
  v2/gloss_generation/work/root_000858/en/review/input/task.json
```

Results are stored under:

```text
results/<locale>/<root-envelope>.json
```

`store` remains available only for an explicitly unreviewed candidate
checkpoint under `results/candidates/<locale>/`. It is not the completion gate
and cannot obstruct the reviewed result path.

## Campaign preparation

Stage the current Turkish corpus for the smoke locales:

```sh
python3 v2/gloss_generation/workflow.py prepare-all
```

Stage the approved priority set:

```sh
python3 v2/gloss_generation/workflow.py prepare-all \
  --language-set western-muslim-priority
```

Preparation validates every source entry and stops on stale or invalid input.
Generated `work/` and `results/` directories are git-ignored.

## Deterministic safeguards

- Branch order and lexical-unit rosters must exactly match the package.
- A `null` concept gloss requires a contextual gloss.
- A concept gloss must disposition every source facet as represented or lost.
- Fit enums have mechanically enforced loss/addition/collision requirements.
- A repair may change only review-named branch fields or lexical units.
- Every writer, reviewer, repair, and locale input is hash-bound.
- Controller-owned task seals detect accidental or ordinary worker-side task
  and path rewriting.
- Canonical prompts, schemas, locale files, rollout configuration, and workflow
  code are freshness-bound; changing any of them makes staged tasks stale.
- Arabic script is permitted only when the locale declares ISO 15924 `Arab`;
  there is no unbound `--ignore-arabic` bypass.
- A passing independent review must bind the final writer task and byte-exact
  response before acceptance.

The seals are integrity checks, not keyed security credentials. A production
runtime should enforce the worker's declared output-only filesystem boundary.
If writer and controller deliberately share unrestricted operating-system write
authority, no local unkeyed file can defend against a malicious worker that
rewrites both the task and its seal; that deployment relies on the worker role
contract.
