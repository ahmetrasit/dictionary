# V2 Production Runbook

This is the cold-start path for producing one current minimal-input master entry
and its three consumer projections. The production workflow uses one root-level
writer invocation per target language; the writer returns branch-shaped
fragments plus the short root profile. Run every command from the repository
root.

## Prerequisites

- Python 3 and the `codex` CLI are available;
- `sandbox-exec` (macOS) or `bwrap` (Linux) is available;
- the canonical root packet and the three QNet inputs listed in
  `orchestration/entry-creation.spec.md` exist.

The first production pilot is `root_001697/tr`. Its five branches include B002,
which exercises the Latent v11 post-fix theme overlay without requiring the
Quran-SLM rebuild.

Implementation status: this runbook describes the production contract. Before
running `--run-agents`, `create_entry.py` must prepare one root-writer task, not
the older branch-per-agent task set.

## 1. Prepare without model calls

```sh
python3 v2/scripts/create_entry.py root_001697 --language tr
```

Expected result: one root-writer task under
`v2/work/entry_creation/root_001697/tr/`, with all five accepted branches in its
minimal evidence package. Check the decisive fallback directly:

```sh
jq '.qnet_focus_coverage' \
  v2/output/branch_evidence/root_001697/branches/root_001697--B002.json
```

It must report `postfix_exact_port: true` and `theme_scope: "branch"`.

## 2. Run the resumable pilot

```sh
python3 v2/scripts/create_entry.py root_001697 --language tr --run-agents
```

The pilot may use the configured Codex default. Before a larger production
campaign, add `--model <pinned-model>` and keep that choice fixed for the run.
The command resumes a hash-matching root-writer response, reruns stale output,
validates the master JSON, renders Markdown, and publishes the pair only after
both succeed.

## 3. Check the master and projections

```sh
python3 v2/scripts/validate_entry.py v2/entries/tr/root_001697.json
python3 v2/scripts/render_entry.py v2/entries/tr/root_001697.json --check
python3 v2/scripts/project_entry.py v2/entries/tr/root_001697.json \
  --projection translation_agent --output /tmp/root_001697.translation.json
python3 v2/scripts/project_entry.py v2/entries/tr/root_001697.json \
  --projection user_dictionary --output /tmp/root_001697.user.json
python3 v2/scripts/project_entry.py v2/entries/tr/root_001697.json \
  --projection scholar_view --output /tmp/root_001697.scholar.json
```

Review the five branch definitions and glosses, ensure the first Arabic
distinction is the best compact-reader distinction, and confirm that QNet has
only nominated candidates: every published contrast must still be grounded in
the retained Furūq branch card.

## 4. Continue production

Keep the pilot as `draft` until editorial review. Once it is accepted, use the
same command for the next queued root. Do not use `--force-entry` for ordinary
draft production; it is reserved for an intentional replacement of reviewed,
published, invalid, or unmarked outputs.

Quran-SLM remains deferred. When its global catalogs are rebuilt, enrich the
four documented missing focus cards in a separate reviewed pass; do not relabel
current QNet discovery scores as Quran-SLM/Neo scores.
