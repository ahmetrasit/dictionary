# V2 Entry Creation Orchestration

Status: normative orchestration contract for schema version 2.

This workflow creates one encyclopedia entry for one root envelope and one
target language. It uses small agent-owned fragments and deterministic assembly.
No agent edits a shared entry document.

## Scope

The workflow covers:

- root profile prose;
- branch summaries and source discussion;
- per-branch dictionary roles and contribution notes;
- selected and excluded target-language glosses with error profiles;
- Furuq-verified Arabic-neighbor distinctions;
- root-level occurrence observations; and
- deterministic assembly, validation, and rendering.

Co-occurrence and branch-resonance analysis are out of scope for this version.

English and Turkish are separate runs. They share evidence packages but never
share authored prose fields.

## Required Inputs

For `<root-envelope>` and `<language>` the run requires:

```text
data/output/root_packets/<root-envelope>.json
v2/output/occurrences/<root-envelope>.<language>.md
v2/schema/encyclopedia-entry.schema.json
data/working/furuq_v4.sqlite
data/upstream/qnet/incidence_full/raw_keyword_incidence.sqlite
TRANSLITERATION_POLICY.md
```

The packet and occurrence artifact must validate before any agent task starts.
Their hashes are frozen into the run inputs. A changed input invalidates every
downstream fragment from that run.

## Artifact Layout

Generated evidence:

```text
v2/output/branch_evidence/<root-envelope>/index.json
v2/output/branch_evidence/<root-envelope>/branches/<root-id>--<branch-id>.json
```

Resumable tasks and agent fragments:

```text
v2/work/entry_creation/<root-envelope>/<language>/tasks/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/tasks/occurrence_observations.json
v2/work/entry_creation/<root-envelope>/<language>/tasks/root_profile.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/branches/<root-id>--<branch-id>.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/occurrence_observations.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/root_profile.json
```

Canonical outputs:

```text
v2/entries/<language>/<root-envelope>.json
v2/entries/<language>/<root-envelope>.md
```

`v2/output` is deterministic and replaceable. `v2/work` is resumable staging.
`v2/entries` contains the validated authored artifact and its rendered form.

## Branch Evidence Package

`build_branch_evidence.py` creates one language-neutral package per frozen
branch. The package contains evidence, not editorial conclusions.

Minimal shape:

```json
{
  "format": 1,
  "root_envelope_id": "root_000858",
  "packet_path": "data/output/root_packets/root_000858.json",
  "packet_sha256": "...",
  "branch": {
    "root_id": "root_000858",
    "branch_id": "B001",
    "branch_image_ar": "...",
    "what_is_ar": "...",
    "what_is_not_ar": "...",
    "source_phrase_ar": "..."
  },
  "dictionary_basis": {
    "dictionary_count": 3,
    "passage_count": 4,
    "sources": [
      {
        "source_id": "maqayis",
        "dictionary_name": "Maqāyīs al-Lugha",
        "source_refs": ["..."],
        "passages": [
          {
            "source_ref": "...",
            "entry_text_clean": "...",
            "route_status": "exact"
          }
        ]
      }
    ]
  },
  "lexical_units": [],
  "qnet_candidates": [],
  "qnet_core_overlap_candidates": [],
  "furuq_candidates": []
}
```

The packager derives dictionary and passage counts. It includes only dictionary
rows whose exact source handles occur in the frozen branch roster. Both `exact`
and `variant` routes may therefore be included; root-level `no_match` rows are
excluded.
QNet candidates are discovery prompts; Furuq candidate cards contain stable
`root_id/branch_id`, branch boundaries, and source references. When the packet
shortlist is too narrow, the packager adds at most eight direct core-keyword
overlap candidates from the frozen QNet incidence database. It orders them by
shared-core count, then two-replicate overlap, then stable branch ID. This is a
bounded discovery expansion, not an unbounded semantic search.

## Agent Roles

There are three roles. A role may run several tasks, but no additional voting or
debate agents are part of the baseline workflow.

### 1. Branch Writer

Run once for every branch in the selected target language. Branch tasks may run
in parallel.

Inputs:

- one branch evidence package;
- target language;
- the branch portion of the v2 entry schema; and
- target-language gloss and transliteration policies.

Output fragment:

```json
{
  "inputs_sha256": "...",
  "root_id": "root_000858",
  "branch_id": "B001",
  "language": "tr",
  "image_transliteration": "...",
  "summary": "...",
  "source_discussion": {},
  "dictionary_annotations": [
    {
      "source_id": "maqayis",
      "roles": ["base_definition"],
      "contribution": "..."
    }
  ],
  "glosses": {},
  "arabic_neighbor_distinctions": []
}
```

The branch writer cannot change dictionary counts, source names, source
references, root IDs, or branch IDs. `dictionary_annotations` must contain one
row for every prefilled dictionary and no others. The assembler merges roles and
contributions into the deterministic dictionary basis.

The writer may return several possible glosses or distinctions only inside the
schema's allowed arrays; it does not emit alternative whole branch drafts.

### 2. Occurrence Observer

Run once per root envelope and target language. It can run in parallel with the
branch writers.

Inputs:

- the generated occurrence artifact;
- the packet QAC and attachment reference inventory; and
- the occurrence-observation portion of the schema.

Output fragment:

```json
{
  "inputs_sha256": "...",
  "root_envelope_id": "root_000858",
  "language": "tr",
  "observations": [
    {
      "category": "recurrent_pattern",
      "statement": "...",
      "evidence_refs": ["1:6:2:2"]
    }
  ]
}
```

Observations are sparse. The agent records recurrent grammar, exceptions, and
translation risks that are useful to a translator. It cannot assign an
occurrence to a dictionary branch or sense.

### 3. Root Profile Writer

Run after every branch fragment and the occurrence fragment are present.

Inputs:

- immutable root identity and branch count;
- all completed branch fragments;
- the occurrence observations; and
- the root-profile portion of the schema.

Output fragment:

```json
{
  "inputs_sha256": "...",
  "root_envelope_id": "root_000858",
  "language": "tr",
  "root_profile": {
    "transliteration": "...",
    "summary": "...",
    "polysemy": "polysemic",
    "organization": "mixed",
    "branch_count": 3,
    "collocation_weight": "low",
    "collocation_note": "..."
  }
}
```

The root profile writer summarizes completed branch work. It does not rewrite a
branch fragment or occurrence observation.

## Field Ownership

| Final field | Owner |
|---|---|
| Schema version, entry ID, language, status | assembler |
| Root envelope, root IDs, packet path and hash | evidence packager / assembler |
| Root profile | root profile writer |
| Branch root ID and branch ID | evidence packager / assembler |
| Branch image transliteration and summary | branch writer |
| Source discussion and disagreement | branch writer |
| Dictionary count, passage count, names and references | evidence packager |
| Dictionary roles and contribution notes | branch writer |
| Selected and excluded glosses | branch writer |
| Arabic-neighbor distinctions | branch writer |
| Occurrence artifact path and generator | assembler |
| Occurrence observations | occurrence observer |

An agent response containing fields outside its ownership is rejected rather
than merged. The coordinator adds `inputs_sha256` after accepting the response;
the agent does not author this field. It is the SHA-256 of the exact canonical
task input, including target language and frozen evidence.

## Execution Order

```text
1. Preflight packet and occurrence artifact
2. Build branch evidence packages
3. Run all branch writers ─────────────┐
4. Run occurrence observer ────────────┤ in parallel
5. Run root profile writer after 3–4 ──┘
6. Assemble one target-language entry JSON
7. Validate against schema, packet, occurrence artifact, and Furuq
8. Render Markdown
9. Run renderer --check
```

The orchestrator infers the task roster from the packet branch order. A mutable
run manifest is not required. An existing valid fragment is reused only when
its `inputs_sha256` matches the current canonical task input; missing or stale
fragments are rerun.

## Assembly Rules

`assemble_entry.py` performs a keyed merge; array position from agent output is
never used as identity.

- Branch fragments are keyed by `(root_id, branch_id)`.
- Dictionary annotations are keyed by `source_id`.
- The packet determines final branch order.
- The packager determines source order and immutable source fields.
- Selected gloss order is the explicit numeric `rank`.
- The assembler refuses missing, duplicate, extra, or wrong-language fragments.
- Assembly writes atomically and never overwrites an unmarked authored file.

The assembler produces exactly the shape defined by
`v2/schema/encyclopedia-entry.schema.json`.

## Validation and Repair

Run `v2/scripts/validate_entry.py` after assembly. Errors are routed to the
field owner:

| Error path | Repair owner |
|---|---|
| `root_profile` | root profile writer |
| `branches[i].summary`, source discussion, glosses, distinctions | matching branch writer |
| dictionary counts, source roster, provenance, branch roster | deterministic pipeline failure |
| `occurrence_evidence.observations` | occurrence observer |

Only the failing fragment and the validator message are sent for repair. A
repair task receives the same frozen evidence as the original task. After two
failed repair attempts, the run stops with the fragment and errors preserved.
Deterministic pipeline failures are never sent to an agent.

## Agent Failure States

Agents must not invent evidence to make the schema pass.

- No actual disagreement: write `disagreement: null`.
- No verified neighbor: deterministic task preparation reports `needs_evidence`
  and stops before calling the branch writer.
- Missing dictionary passage: fail preflight; do not ask an agent to reconstruct it.
- Ambiguous gloss: retain the uncertainty in the error profile.
- QNet-only neighbor: it remains a candidate until Furuq evidence is attached.
- Unsupported occurrence claim: omit it.

`needs_evidence` is a preflight result, not an entry fragment, and therefore
cannot be assembled into a final entry.

## Acceptance Criteria

A run is complete only when:

1. Every expected branch has one fragment in packet order.
2. The occurrence and root-profile fragments are present.
3. All fragment input hashes match the current evidence and target language.
4. `validate_entry.py` passes without warnings or placeholders.
5. The rendered Markdown is reproducible under `--check`.

## Script Boundary

The orchestration implementation should remain a thin coordinator:

```text
build_branch_evidence.py   deterministic evidence packaging
create_entry.py            task scheduling and agent adapter calls
assemble_entry.py          deterministic fragment merge
validate_entry.py          schema and evidence validation
render_entry.py            deterministic reader-facing rendering
```

Agent prompts remain separate files for the three roles. Scripts do not contain
agent-authored encyclopedia prose or branch decisions.
