# V2 Entry Creation Orchestration

Status: normative orchestration contract for entry schema version 4.

This workflow creates one encyclopedia entry for one root envelope and one
target language. One writing invocation receives the minimal evidence for all
accepted branches in that root and returns branch-shaped fragments plus the
short root profile. The coordinator owns all evidence routing, occurrence data,
assembly, validation, and rendering. No agent edits a shared entry document.

## Scope

The workflow covers:

- one root-writer task per root envelope and target language;
- branch-shaped authored fragments for every accepted branch;
- one short root profile authored from the same branch set;
- selected and excluded target-language glosses with error profiles;
- Furuq-verified Arabic-neighbor distinctions;
- deterministic dictionary-source routing and lexical realizations;
- deterministic QAC morphology, ayahs, attachment alignment, and occurrences;
- deterministic assembly, validation, Markdown rendering, and JSONL export;
- deterministic translation-agent, user-dictionary, and scholar projections from
  the validated master entry.

Occurrence-to-branch assignment is outside this contract. An occurrence layer
may later choose a branch; the dictionary entry must give it enough material to
choose a natural gloss after that branch has been selected.

## Required Inputs

Canonical production inputs are:

```text
data/output/root_packets/<root-envelope>.json
data/working/furuq_v4.sqlite
data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite
data/upstream/qnet/bridge_theme_full/bridge_theme_staging.sqlite
data/upstream/qnet/bridge_theme_full/latent_v11_qac_qnet_fix_manifest.json
v2/output/occurrences/<root-envelope>.<language>.md
v2/output/alignments/<root-envelope>.json
v2/schema/encyclopedia-entry.schema.json
TRANSLITERATION_POLICY.md
```

The coordinator validates and hash-binds these inputs. Agents do not receive
the packet, occurrence Markdown, alignment file, Quran ayahs, QAC morphology,
attachment records, dictionary source metadata, full branch packages, the master
entry schema, or this orchestration spec. The model-facing package contains only
the role prompt, a thin root response schema, the minimal root evidence
projection, and any compact policy notes needed for the target language.

The QNet candidate roster is balanced across packet-carried neighbors, raw core
overlap, raw bridge overlap, and branch-theme overlap. At most eight unique
cross-root candidates are retained across those lanes, followed by every sibling
branch in the focus root. If an exact theme port is absent, the builder may use
the represented root's themes as an explicitly labeled indirect fallback.

## Artifact Layout

```text
v2/output/branch_evidence/<root-envelope>/index.json
v2/output/branch_evidence/<root-envelope>/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/inputs/root_evidence.json
v2/work/entry_creation/<root-envelope>/<language>/tasks/root_writer.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/root_writer.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/root_profile.json
v2/entries/<language>/<root-envelope>.json
v2/entries/<language>/<root-envelope>.md
v2/output/dictionary.<language>.jsonl
v2/output/projections/translation-agent.<language>.jsonl
v2/output/projections/user-dictionary.<language>.jsonl
v2/output/projections/scholar-view.<language>.jsonl
```

The full branch-evidence package is coordinator-only. Before a root task is
created, the coordinator writes one minimal projection under `inputs/` and binds
only that projection to the agent task. The root response is only a transport
envelope; the authoritative authored units remain branch fragments.

## Agent Evidence Projection

Each focus branch contains exactly:

```json
{
  "root_id": "root_001697",
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

The root evidence may deduplicate repeated neighbor cards in a shared registry
and let focus branches point to neighbor IDs. That is an input-size optimization
only; it is not a root-centric data model. Semantically, the agent sees only the
focus branch cards and the permitted neighbor branch cards.

The task manifest carries the root envelope, language, prompt, response schema,
and compact policy bindings. Those are control metadata, not lexical evidence.
The agent cannot browse the repository and receives no occurrence data.

## Agent Roles

### Root Writer

Run once per root envelope and target language. The response contains one
branch-shaped fragment per accepted branch and one short root profile.

The writer authors:

- image transliteration and a concise branch summary;
- a synthesis of the supplied Arabic source phrase;
- source-grounded register, constraint, or technical notes;
- disputed, rare, or technical qualifiers;
- selected and excluded natural glosses with error profiles;
- distinctions for the supplied neighbor roster;
- neighbor-coverage assessment;
- root-level semantic organization.

The writer orders published neighbor distinctions by reader-facing importance.
The first selected distinction is the key contrast used by the compact user
dictionary projection. This ordering is authored judgment; the projection does
not summarize or rerank neighbor prose.

The fragment intentionally contains no source references, source IDs,
dictionary annotations, lexical units, ayahs, morphology, attachments, or
occurrence claims. The coordinator reconstructs evidence-owned fields by stable
IDs after accepting the fragment.

The writer summarizes root-level semantic organization. Occurrence-dependent
collocation fields remain `unknown`; deterministic occurrence data is attached
later by the coordinator.

## Field Ownership

| Final field | Owner |
|---|---|
| Schema version, IDs, language, status, provenance | coordinator |
| Root profile prose and semantic organization | root writer |
| Frozen Arabic branch fields | packet / coordinator |
| Image transliteration, summary, source synthesis | root writer, per branch |
| Glosses, error profiles, qualifiers, permitted usage notes | root writer, per branch |
| Neighbor prose and coverage assessment | root writer, per branch |
| Neighbor Arabic image, basis, references, candidate count | Furuq package / coordinator |
| Dictionary counts, names, source roster, references | packet / coordinator |
| Lexical realizations | packet / coordinator |
| QAC forms, morphology, ayahs, and occurrence rows | coordinator |
| Attachment-to-QAC alignment and linked attachment detail | coordinator |
| Markdown and JSONL | deterministic renderers |
| Consumer projection selection and master hash binding | deterministic projector |

An agent response containing fields outside its schema is rejected. The
coordinator adds `inputs_sha256` after validation; agents do not author it.

## Execution Order

```text
1. Validate packet and deterministic occurrence/alignment artifacts
2. Build full coordinator-side branch evidence
3. Project and hash-bind one minimal root evidence package
4. Run one root writer for the target language
5. Split the accepted response into branch fragments and root profile
6. Add packet, QAC, ayah, morphology, and aligned-attachment data mechanically
7. Assemble and validate schema-v4 JSON
8. Render Markdown and verify it with --check
9. Derive bounded consumer projections from the validated master entry
10. Export master or projected entries as one-entry-per-line JSONL
```

Roots with more than 100 occurrences follow the same process. Their occurrence
arrays are built deterministically after agent work, so occurrence count does
not increase root-writer context.

## Isolation and Resumption

Each agent runs in a new read-only temporary workspace containing only files
named by its hash-bound task. Repository reads are denied with `sandbox-exec`
on macOS or bubblewrap on Linux. A run stops if neither confinement mechanism
is available.

A valid root-writer response is reused only when its `inputs_sha256` matches the
canonical task. Missing or stale responses are rerun. Timeouts and nonzero
process exits are operational failures and are not retried as editorial repairs.

## Assembly and Validation

`assemble_entry.py` performs a keyed merge:

- branch fragments are keyed by `(root_id, branch_id)`;
- the packet determines branch and lexical-unit order;
- the evidence package determines source and neighbor identity;
- gloss order is the explicit numeric `rank`;
- source references are attached to authored claims mechanically;
- QAC and attachment structures are recomputed and compared exactly;
- missing, duplicate, extra, stale, or wrong-language fragments are rejected.

Only root-writer fields are eligible for agent repair.
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
7. Every consumer projection is reproducible and hash-bound to its master entry.

## Script Boundary

```text
build_branch_evidence.py   full deterministic coordinator evidence
create_entry.py            projection, scheduling, isolation, and agent calls
assemble_entry.py          keyed merge and deterministic evidence attachment
validate_entry.py          schema and evidence validation
render_occurrences.py      QAC, ayah, morphology, and attachment structures
render_entry.py            reader-facing Markdown
project_entry.py           bounded, master-hash-bound consumer projections
export_jsonl.py            validated master or projection records as JSONL
```

## Target Languages

Packet construction, dictionary routing, Furūq candidate generation, QAC
occurrences, and attachment alignment are language-neutral shared evidence. They
may be reused for every target language and are only revalidated mechanically by
the coordinator.

Root-writer output is language-specific and must be authored independently for
each target language. Gloss fit, loss, addition, collision, applicability, and
natural wording cannot be copied from another language. Shared Arabic evidence
does not need to be rebuilt for each language. Once that language's master entry
validates, all three consumer projections are deterministic and require no
additional agent call.

The current contract supports English (`en`) and Turkish (`tr`). A new language
code requires an explicit schema, transliteration-policy, renderer-label, and CLI
extension; shared Arabic evidence still remains reusable after that extension.
