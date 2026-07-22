# V2 Production Runbook

This is the cold-start path for producing one current minimal-input master entry
and its three consumer projections. The production workflow uses one root-level
writer and one evidence-bound semantic reviewer per accepted response. The
reviewer reports bounded issues but never rewrites the entry. Run every command
from the repository root.

## Prerequisites

- Python 3 and an orchestration-agent runtime are available;
- the canonical root packet and the three QNet inputs listed in
  `orchestration/entry-creation.spec.md` exist.

The first production pilot is `root_001697/tr`. Its five branches include B002,
which exercises the Latent v11 post-fix theme overlay without requiring the
Quran-SLM rebuild.

The deterministic preparer writes exactly one root-writer task. Older
branch-per-agent files in a resumable work directory are historical and are not
read by the current workflow.

## 1. Prepare without model calls

```sh
python3 v2/scripts/create_entry.py root_001697 --language tr
```

Expected result: one root-writer task under
`v2/work/entry_creation/root_001697/tr/`, with all five accepted branches in its
minimal evidence package. The orchestrator stages the writer-visible files in
`input/`; the writer writes only `output/root_writer.json`, runs the staged
read-only validator, and corrects that file in place until it passes. Check the
decisive fallback directly:

```sh
jq '.qnet_focus_coverage' \
  v2/output/branch_evidence/root_001697/branches/root_001697--B002.json
```

It must report `postfix_exact_port: true` and `theme_scope: "branch"`.

## 2. Start the resumable orchestration agent

```text
Run the v2 entry orchestrator for root_001697/tr, following
v2/prompts/entry-orchestrator.md.
```

The pilot may use the orchestration runtime's configured model default. Before a
larger production campaign, pin the worker model in the orchestration
configuration and keep it fixed for the run. The orchestrator resumes a
hash-matching response, invokes the writer and reviewer when needed, validates
the master JSON, renders Markdown, and publishes the pair only after semantic
review passes.

A worker validation error does not discard its response. The same writer or
reviewer keeps the actual output file, applies the smallest correction indicated
by the validator, and validates again before the orchestrator accepts it.

If a selected Arabic anchor lacks a reviewed target-language transliteration,
the command stops after preserving the valid writer response and creates:

```text
v2/work/entry_creation/root_001697/tr/inputs/transliteration_review.json
```

Review only the listed used anchors, set each accepted row to
`"status": "approved"`, supply its `value`, and tell the same orchestrator to
resume. The writer is not called again.

Protected person and place names use the parallel queue:

```text
v2/work/entry_creation/root_001697/tr/inputs/name_review.json
```

Approve target-language surface forms there. Writer prose contains stable
placeholders until the coordinator substitutes those approved forms.

## 3. Check the master and projections

```sh
python3 v2/scripts/validate_entry.py v2/entries/tr/root_001697.json
python3 v2/scripts/render_entry.py v2/entries/tr/root_001697.json --check
python3 v2/scripts/project_entry.py v2/entries/tr/root_001697.json \
  --projection translation_agent \
  --output v2/work/entry_creation/root_001697/tr/verification/root_001697.translation.json
python3 v2/scripts/project_entry.py v2/entries/tr/root_001697.json \
  --projection user_dictionary \
  --output v2/work/entry_creation/root_001697/tr/verification/root_001697.user.json
python3 v2/scripts/project_entry.py v2/entries/tr/root_001697.json \
  --projection scholar_view \
  --output v2/work/entry_creation/root_001697/tr/verification/root_001697.scholar.json
```

Review the five structured concept maps rather than treating their definitions
as headword paraphrases. Confirm that core, extension, associated use, example,
and source variant are not collapsed; concept and contextual glosses remain
separate; and reject Arabic script, transliterated
Arabic, or Arabic technical loanwords used instead of plain Turkish explanation.
When distinctions are present, ensure the first is the best compact-reader
choice; when none is useful, verify the explicit empty-selection explanation.
Confirm that QNet/Neo have only
nominated candidates: every published relation type and contrast must be
verified from the retained Furūq branch cards.

## 4. Continue production

Keep the pilot as `draft` until editorial review. Once it is accepted, start the
orchestrator for the next queued root. Do not use `--force-entry` for ordinary
draft production; it is reserved for an intentional replacement of reviewed,
published, invalid, or unmarked outputs.

Quran-SLM remains deferred. When its global catalogs are rebuilt, enrich the
four documented missing focus cards in a separate reviewed pass; do not relabel
current QNet discovery scores as Quran-SLM/Neo scores.
