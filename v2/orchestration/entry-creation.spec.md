# V2 Entry Creation Orchestration

Status: normative orchestration contract for entry schema version 4.

This workflow creates one encyclopedia entry for one root envelope and one
target language. Agents author small lexical fragments. The coordinator owns
all evidence routing, occurrence data, assembly, validation, and rendering.
No agent edits a shared entry document.

## Scope

The workflow covers:

- one branch-writer task per accepted branch;
- one root-profile task after all branch fragments are complete;
- selected and excluded target-language glosses with error profiles;
- Furuq-verified Arabic-neighbor distinctions;
- deterministic dictionary-source routing and lexical realizations;
- deterministic QAC morphology, ayahs, attachment alignment, and occurrences;
- deterministic assembly, validation, Markdown rendering, and JSONL export.

Occurrence-to-branch assignment is outside this contract. An occurrence layer
may later choose a branch; the dictionary entry must give it enough material to
choose a natural gloss after that branch has been selected.

## Required Inputs

Canonical production inputs are:

```text
data/output/root_packets/<root-envelope>.json
data/working/furuq_v4.sqlite
data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite
v2/output/occurrences/<root-envelope>.<language>.md
v2/output/alignments/<root-envelope>.json
v2/schema/encyclopedia-entry.schema.json
TRANSLITERATION_POLICY.md
```

The coordinator validates and hash-binds these inputs. Agents do not receive
the packet, occurrence Markdown, alignment file, Quran ayahs, QAC morphology,
attachment records, dictionary source metadata, or full branch packages.

## Artifact Layout

```text
v2/output/branch_evidence/<root-envelope>/index.json
v2/output/branch_evidence/<root-envelope>/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/inputs/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/tasks/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/tasks/root_profile.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/root_profile.json
v2/entries/<language>/<root-envelope>.json
v2/entries/<language>/<root-envelope>.md
v2/output/dictionary.<language>.jsonl
```

The full branch-evidence package is coordinator-only. Before a branch task is
created, the coordinator writes a minimal projection under `inputs/branches/`
and binds only that projection to the agent task.

## Agent Evidence Projection

The focus branch contains exactly:

```json
{
  "branch_id": "B001",
  "branch_image_ar": "...",
  "what_is_ar": "...",
  "source_phrase_ar": "..."
}
```

Each neighbor contains exactly:

```json
{
  "root_id": "root_000672",
  "branch_id": "B001",
  "branch_image_ar": "...",
  "what_is_ar": "..."
}
```

The task manifest carries the focus `root_id`, `branch_id`, language, prompt,
response schema, and policy bindings. Those are control metadata, not lexical
evidence. The agent cannot browse the repository and receives no other root or
occurrence data.

## Agent Roles

### Branch Writer

Run once per branch. Branch tasks may run in parallel.

The writer authors:

- image transliteration and a concise branch summary;
- a synthesis of the supplied Arabic source phrase;
- source-grounded register, constraint, or technical notes;
- disputed, rare, or technical qualifiers;
- selected and excluded natural glosses with error profiles;
- distinctions for the supplied neighbor roster;
- neighbor-coverage assessment.

The fragment intentionally contains no source references, source IDs,
dictionary annotations, lexical units, ayahs, morphology, attachments, or
occurrence claims. The coordinator reconstructs evidence-owned fields by stable
IDs after accepting the fragment.

### Root Profile Writer

Run once after all branch fragments are complete. It receives only immutable
root identity, branch count, and the completed branch fragments. It receives no
ayahs, QAC morphology, attachment data, or occurrence artifact.

The writer summarizes root-level semantic organization. Occurrence-dependent
collocation fields remain `unknown`; deterministic occurrence data is attached
later by the coordinator.

## Field Ownership

| Final field | Owner |
|---|---|
| Schema version, IDs, language, status, provenance | coordinator |
| Root profile prose and semantic organization | root profile writer |
| Frozen Arabic branch fields | packet / coordinator |
| Image transliteration, summary, source synthesis | branch writer |
| Glosses, error profiles, qualifiers, permitted usage notes | branch writer |
| Neighbor prose and coverage assessment | branch writer |
| Neighbor Arabic image, basis, references, candidate count | Furuq package / coordinator |
| Dictionary counts, names, source roster, references | packet / coordinator |
| Lexical realizations | packet / coordinator |
| QAC forms, morphology, ayahs, and occurrence rows | coordinator |
| Attachment-to-QAC alignment and linked attachment detail | coordinator |
| Markdown and JSONL | deterministic renderers |

An agent response containing fields outside its schema is rejected. The
coordinator adds `inputs_sha256` after validation; agents do not author it.

## Execution Order

```text
1. Validate packet and deterministic occurrence/alignment artifacts
2. Build full coordinator-side branch evidence
3. Project and hash-bind minimal branch evidence
4. Run one branch writer per branch in parallel
5. Run the root profile writer from completed branch fragments
6. Add packet, QAC, ayah, morphology, and aligned-attachment data mechanically
7. Assemble and validate schema-v4 JSON
8. Render Markdown and verify it with --check
9. Export validated entries as one-entry-per-line JSONL
```

Roots with more than 100 occurrences follow the same process. Their occurrence
arrays are built deterministically after agent work, so occurrence count does
not increase branch-writer or root-profile context.

## Isolation and Resumption

Each agent runs in a new read-only temporary workspace containing only files
named by its hash-bound task. Repository reads are denied with `sandbox-exec`
on macOS or bubblewrap on Linux. A run stops if neither confinement mechanism
is available.

A valid fragment is reused only when its `inputs_sha256` matches the canonical
task. Missing or stale fragments are rerun. Timeouts and nonzero process exits
are operational failures and are not retried as editorial repairs. A fatal
parallel task terminates active peers.

## Assembly and Validation

`assemble_entry.py` performs a keyed merge:

- branch fragments are keyed by `(root_id, branch_id)`;
- the packet determines branch and lexical-unit order;
- the evidence package determines source and neighbor identity;
- gloss order is the explicit numeric `rank`;
- source references are attached to authored claims mechanically;
- QAC and attachment structures are recomputed and compared exactly;
- missing, duplicate, extra, stale, or wrong-language fragments are rejected.

Only branch-writer or root-profile fields are eligible for agent repair.
Dictionary routing, provenance, morphology, alignment, ayahs, and occurrence
errors are deterministic pipeline failures and are never sent to an agent.

Draft generated JSON and Markdown are staged, validated, and published as a
pair. Reviewed or published outputs and their pinned evidence require explicit
force flags before replacement.

## Acceptance Criteria

A run is complete only when:

1. Every expected branch has one hash-matching fragment.
2. The root-profile fragment depends on exactly those branch fragments.
3. Minimal evidence projections match their coordinator-side packages.
4. Schema and packet-aware validation pass.
5. Markdown is reproducible under `--check`.
6. JSONL export validates every entry and preserves one common schema.

## Script Boundary

```text
build_branch_evidence.py   full deterministic coordinator evidence
create_entry.py            projection, scheduling, isolation, and agent calls
assemble_entry.py          keyed merge and deterministic evidence attachment
validate_entry.py          schema and evidence validation
render_occurrences.py      QAC, ayah, morphology, and attachment structures
render_entry.py            reader-facing Markdown
export_jsonl.py            one complete validated entry per line
```
