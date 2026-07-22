# V2 Entry Creation Orchestration

Status: normative orchestration contract for entry schema version 4.

This workflow creates one encyclopedia entry for one root envelope and one
target language. One writing invocation receives the minimal evidence for all
accepted branches in that root and returns branch-shaped fragments plus the
short root profile. If finalization discovers missing used transliterations or
protected proper-name target forms, the same writer completes only the generated
surface-form queues and finalization resumes without human review. A top-level
orchestration agent owns the run: it starts and monitors the writer, controls
the global repair budget, and resumes the workflow. Deterministic scripts own
evidence routing, response acceptance, occurrence data, assembly, validation,
and rendering. No agent edits a shared entry document.

No Python script invokes an agent or decides whether to retry one. The
orchestrator follows `v2/prompts/entry-orchestrator.md` and invokes the scripts
only for bounded mechanical operations.

All agent-readable packages and all agent-produced artifacts live in the
repository work tree under
`v2/work/entry_creation/<root-envelope>/<language>/`. Agents never read from or
write to `/tmp`, `/private/tmp`, another operating-system temporary directory,
or a runtime-managed scratch workspace. Agent output is durable and resumable at
the declared repository-local path before any acceptance or publication step.

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
v2/policy/protected_names/<root-envelope>.json
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
v2/policy/protected_names/<root-envelope>.json
v2/work/entry_creation/<root-envelope>/<language>/inputs/root_evidence.json
v2/work/entry_creation/<root-envelope>/<language>/inputs/transliterations.json
v2/work/entry_creation/<root-envelope>/<language>/inputs/transliteration_review.json
v2/work/entry_creation/<root-envelope>/<language>/inputs/name_review.json
v2/work/entry_creation/<root-envelope>/<language>/tasks/root_writer.json
v2/work/entry_creation/<root-envelope>/<language>/input/instructions.md
v2/work/entry_creation/<root-envelope>/<language>/input/task.json
v2/work/entry_creation/<root-envelope>/<language>/input/prompt.md
v2/work/entry_creation/<root-envelope>/<language>/input/response.schema.json
v2/work/entry_creation/<root-envelope>/<language>/input/evidence.json
v2/work/entry_creation/<root-envelope>/<language>/output/<root-envelope>_entry.json
v2/work/entry_creation/<root-envelope>/<language>/output/validation_error.txt
v2/work/entry_creation/<root-envelope>/<language>/output/finalize_error.txt
v2/work/entry_creation/<root-envelope>/<language>/output/repair_scope.json
v2/work/entry_creation/<root-envelope>/<language>/review/input/instructions.md
v2/work/entry_creation/<root-envelope>/<language>/review/input/task.json
v2/work/entry_creation/<root-envelope>/<language>/review/input/prompt.md
v2/work/entry_creation/<root-envelope>/<language>/review/input/response.schema.json
v2/work/entry_creation/<root-envelope>/<language>/review/input/evidence.json
v2/work/entry_creation/<root-envelope>/<language>/review/input/writer_response.json
v2/work/entry_creation/<root-envelope>/<language>/review/output/root_review.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/<root-envelope>_entry.json
v2/work/entry_creation/<root-envelope>/<language>/fragments/root_review.json
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
only that projection to the agent task. `input/` is the complete writer package;
the neighboring plural `inputs/` directory is coordinator state and is not given
to the writer. The root response is only a transport envelope; the authoritative
authored units remain branch fragments.

## Agent Evidence Projection

Each focus branch contains:

```json
{
  "branch_ref": "root_001697/B001",
  "branch_image_ar": "...",
  "what_is_ar": "...",
  "source_claims": [
    {
      "claim_id": "lu_001",
      "lexical_unit_id": "lu_001",
      "unit_kind": "form",
      "expression_ar": "...",
      "sense_ar": "...",
      "source_phrase_ar": "...",
      "source_ids": ["maqayis", "sihah"],
      "rendering_policy": "ordinary"
    }
  ],
  "neighbor_refs": ["root_000672/B001"]
}
```

Repeated neighbor cards are stored once in `neighbor_registry`:

```json
{
  "neighbor_ref": "root_000672/B001",
  "branch_image_ar": "...",
  "what_is_ar": "..."
}
```

The compact source-claim roster is projected deterministically from accepted
lexical units. It supplies complete claim coverage without raw passages. Every
claim also carries a reviewed, coordinator-owned `rendering_policy` of
`ordinary` or `proper_name`; policy coverage must match the lexical roster
exactly before a writer task can be created. The writer dispositions every claim
and copies that rendering policy; acceptance checks both exact rosters.

Transliteration values, draft suggestions, and unresolved anchors remain outside
the initial root-writer evidence. After the writer has selected neighbors, the
coordinator computes the exact used-anchor set. Missing values produce a small
resumable `transliteration_review.json` queue. The same writer completes only
the generated queue rows, and rerunning assembly reuses the unchanged
root-writer response.

The task manifest carries the root envelope, language, prompt, response schema,
and compact policy bindings. Those are control metadata, not lexical evidence.
The writer is explicitly instructed to read only the named files in `input/`,
write only `output/<root-envelope>_entry.json`, and avoid every other path. It receives no
occurrence data.

## Agent Roles

### Root Writer

Run once per root envelope and target language. The response contains one
branch-shaped fragment per accepted branch and one short root profile.

The writer authors:

- a claim-ID-bound synthesis that separates common material from distinctive
  examples, disagreements, restrictions, extensions, implications, derivations,
  and sole attestations;
- a structured concept map that distinguishes core, specialization, extension,
  associated use, example, and source variant;
- one concept gloss, separate contextual glosses, per-lexical-unit target
  renderings, and excluded glosses with error profiles; selected
  glosses never use an Arabic/source-language loanword as conceptual shorthand;
- semantically verified relation types, boundary matches, asymmetries, and distinctions for the supplied
  neighbor roster;
- a neighbor-coverage explanation;
- root-level semantic organization.

In its initial entry response, the writer does not supply or repeat
transliterations or proper-name spellings. It follows the coordinator's
protected-name classifications and uses stable placeholders only for those IDs;
target-language forms are substituted mechanically after the same writer
completes the generated surface-form queues.

The writer orders published neighbor distinctions by reader-facing importance.
When the selection is nonempty, its first distinction is the key contrast used
by the compact user dictionary projection. With no useful neighbor, that compact
field is `null`. This ordering is authored judgment; the projection does not
summarize or rerank neighbor prose.

QNet, Neo, and other network layers nominate candidate branches; they do not
establish synonymy, antonymy, or any other publishable lexical relation. The
writer assigns the primary relation type only after comparing the supplied
focus and neighbor concept cards. Root and branch IDs remain the durable link
targets for later web presentation.

The fragment contains stable claim and lexical-unit IDs but no source references,
dictionary annotations, Arabic lexical records, ayahs, morphology, attachments,
or occurrence claims. The coordinator reconstructs evidence-owned fields by
stable IDs after accepting the fragment.

The writer summarizes root-level semantic organization. Occurrence-dependent
collocation fields remain `unknown`; deterministic occurrence data is attached
later by the coordinator.

### Semantic Reviewer

Runs after structural acceptance and before publication. It receives the same
minimal evidence and the exact accepted writer response, then returns `pass`,
bounded evidence-grounded repair issues, or `editorial_review`. It never rewrites
the entry. Low-confidence or genuinely ambiguous judgments require editorial
review instead of automatic repair.

## Field Ownership

| Final field | Owner |
|---|---|
| Schema version, IDs, language, status, provenance | coordinator |
| Root profile prose and semantic organization | root writer |
| Frozen Arabic branch fields | packet / coordinator |
| Concept-map facets, definitions, and claim-bound source synthesis | root writer, per branch |
| Concept, contextual, lexical, and excluded gloss text and risk | root writer, per branch |
| Neighbor selection, verified relation type, asymmetry, prose, and coverage explanation | root writer, per branch |
| Semantic publication verdict and bounded issue scope | semantic reviewer |
| Proper-name classification | reviewed coordinator policy |
| Proper-name target forms | root writer, through generated surface-form queue |
| Transliteration catalog and used-anchor queue generation | coordinator |
| Used transliteration values | root writer, through generated surface-form queue |
| Proper-name and transliteration restoration | coordinator |
| Branch summary copied from definition; ranks; counts; coverage enum; collocation defaults | coordinator |
| Neighbor Arabic image, basis, references, candidate count | Furuq package / coordinator |
| Dictionary counts, names, source roster, references | packet / coordinator |
| Lexical realizations | packet / coordinator |
| QAC forms, morphology, ayahs, and occurrence rows | coordinator |
| Attachment-to-QAC alignment and linked attachment detail | coordinator |
| Markdown and JSONL | deterministic renderers |
| Consumer projection selection and master hash binding | deterministic projector |

An agent's raw response containing fields outside its schema is rejected. After
validation, the coordinator adds `inputs_sha256` and the deterministic evidence
layer; agents do not author either.
Arabic script in an authored target-language field is rejected by the response
schema. The schema also restricts every selected gloss to
`loanword_status: none`; plain-language quality beyond those mechanical checks
remains part of semantic review.

## Execution Order

```text
1. Validate packet and deterministic occurrence/alignment artifacts
2. Build full coordinator-side branch evidence
3. Deduplicate neighbor cards and hash-bind one minimal semantic root evidence package
4. Orchestrator invokes one root writer for the target language
5. Writer validates and corrects its actual output in place; coordinator rechecks, enriches, and hash-binds it
6. Orchestrator invokes one semantic reviewer on an authored-only view bound to that exact enriched response
7. Route bounded repair or editorial review; review every repaired response again
8. Resolve catalogued transliterations and protected proper names through separate gates
9. Split branch fragments and resolve reviewed names and transliterations mechanically
10. Assemble and validate schema-v4 JSON
11. Render Markdown and verify it with --check
12. Derive bounded consumer projections from the validated master entry
13. Export master or projected entries as one-entry-per-line JSONL
```

Roots with more than 100 occurrences follow the same process. Their occurrence
arrays are built deterministically after writer work and omitted from the
reviewer's authored-only view, so occurrence count does not increase either
agent's context.

The internal validated master retains exact dictionary references for
verification. The accepted and downstream entry artifacts expose only
`branch_image_ar`, `what_is_ar`, `source_phrase_ar`, compact `sources`, and
dictionary-keyed `source_note`. These fields are restored from frozen
packet/evidence data, never rewritten by an agent. Occurrences remain root-level because this workflow does not infer an
occurrence-to-branch assignment. Each occurrence carries its QAC morphology and
mechanically aligned attachment details; downstream projections may expose the
full layer or a compact summary without relocating it into a branch.

The accepted `<root-envelope>_entry.json` also exposes `sources` and
`source_note` on every branch. `sources` is the coordinator-mapped short-code
roster of dictionaries supporting the concept map. `source_note` maps only a
dictionary code to concise prose for its distinctive addition, variant, or
dispute and is `{}` when no such note exists. Exact references, paths, source
detail categories, and claim IDs remain internal validation data.

## Input, Output, and Resumption

Each writer uses the regular resumable `input/` and `output/` folders in its
root/language work directory. `input/` contains only the staged prompt, thin
schema, compact evidence, task, and instructions. The instructions prohibit
reading any other file or directory. The raw response is written only to
`output/<root-envelope>_entry.json`; deterministic acceptance validates it,
injects the coordinator-owned Arabic/source and occurrence/attachment layer
into that same file, and stores the enriched hash-bound canonical fragment.
The reviewer receives a compact authored-only view, so the mechanically added
layer does not increase reviewer context. The reviewer follows the same rule with
`review/input/` and `review/output/root_review.json`. Neither agent may use an
operating-system or runtime temporary directory, including as an intermediate
output location. Repair errors and their mechanically classified scope remain
in `output/`; a repair restage copies only the exact error, previous response,
and scope into `input/`.

Deterministic scripts may use hidden atomic staging files or directories only
beside their repository-local destination. If some other short-lived mechanical
artifact is necessary, it belongs under the current root/language work directory
(for example `temporary/`) and must be removed after use. Such mechanical
staging is never an agent package and never an agent output target.

The staging commands derive `input/`, `output/`, `review/input/`, and
`review/output/` from the canonical task location. They do not accept an
alternate input-directory or output-directory override.

Every staged task carries an exact `validation.command`. The writer and reviewer
run that read-only command from the repository root after writing their declared
output. On failure, the agent keeps the complete response at the same path,
corrects it from the exact validator error, and reruns validation until it
passes. Validation never deletes, moves, truncates, or accepts the response. The
orchestrator runs the same command once more before canonical acceptance.

A valid root-writer response is reused only when its `inputs_sha256` matches the
canonical task. The orchestrator reruns missing or stale responses. A validation
failure is returned first to the same active agent, which repairs the same raw
output; it is not grounds for discarding the response or spawning a competing
candidate. Timeouts and nonzero process exits are operational failures and are
not retried as editorial repairs. One run permits one initial writer turn plus
two orchestrator-mediated repair continuations with that writer. Self-validation
iterations within a turn do not consume the repair budget. A semantic repair
receives the previous accepted response, and deterministic acceptance rejects
any change to branches or root fields outside the routed repair ownership.
A semantic-review pass is reusable only while its task remains bound to that
exact accepted writer response. Any repair invalidates the earlier review.

## Surgical Correction Protocol

Corrections preserve the accepted work already present in a response. They are
owned and routed as follows:

| Failure or finding | Corrector | Required action |
|---|---|---|
| Writer/reviewer schema or semantic-contract error | Same active agent | Keep the actual output; edit only the fields named by the exact error; rerun `validation.command` |
| Evidence-grounded semantic-review issue | Same root writer | Restage the previous response, exact issue, and generated scope; change only permitted fields; validate again |
| Missing or stale protected-name policy | Coordinator | Complete the exact lexical-unit classification roster; do not let a writer infer policy |
| Missing used transliterations or protected-name target forms | Same root writer | Fill only the generated queue rows with approved target-language values; do not change the accepted entry response |
| Stale task/hash or staged-path mismatch | Orchestrator plus deterministic script | Restage canonical files; do not alter authored prose or bless a stale raw response |
| Evidence build, assembly, rendering, or publication failure | Orchestrator plus owning script | Repair or regenerate the deterministic artifact; never route it as a lexical rewrite |
| Scope conflict or evidence ambiguity | Same owning writer or reviewer | Preserve protected artifacts and report the conflict without broadening the correction |

The orchestrator never edits agent-authored JSON. It may invoke validators,
classifiers, staging, acceptance, and deterministic build commands, and it sends
their exact bounded result to the owning agent. A surgical correction must not
regenerate valid branches, reorder unaffected content, rephrase unrelated prose,
or change protected root fields. Validation failures remain at their declared
repository output path until the same agent fixes them or editorial review
explicitly decides otherwise.

## Assembly and Validation

`assemble_entry.py` performs a keyed merge:

- branch fragments are keyed by `(root_id, branch_id)`;
- the packet determines branch and lexical-unit order;
- the evidence package determines source and neighbor identity;
- the concept gloss and contextual glosses stay distinct; compatibility ranks
  are derived mechanically;
- writer-completed proper-name placeholders are substituted mechanically;
- lexical target glosses join by exact lexical-unit ID;
- source claim IDs expand to precise source names and references;
- branch summaries, excluded-gloss display reasons, coverage enums, branch
  counts, and collocation defaults are restored mechanically;
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

1. One root-writer response matches the hash-bound task and exact branch roster.
2. A semantic-review pass is bound to that exact accepted response.
3. Split branch and root-profile fragments reproduce from that response.
4. Minimal semantic evidence matches its coordinator-side packages, every
   lexical unit has reviewed rendering policy, and every used transliteration
   and protected proper-name form has a writer-completed queue value.
5. Schema and packet-aware validation pass.
6. Markdown is reproducible under `--check`.
7. JSONL export validates every entry and preserves one common schema.
8. Every consumer projection is reproducible and hash-bound to its master entry.

## Script Boundary

```text
build_branch_evidence.py   full deterministic coordinator evidence
create_entry.py            prepare evidence projection and canonical task only
stage_root_writer.py       refresh regular input/ and output/ writer folders
check_root_writer.py       verify that a stored response is safely reusable
accept_root_writer.py      validate, scope-check, hash-bind, and store returned JSON
prepare_root_review.py     bind semantic review to accepted evidence and response
check_root_review.py       verify a reusable pass bound to the current response
stage_root_reviewer.py     refresh regular review input/output folders
validate_agent_output.py   read-only staged writer/reviewer output validation
accept_root_review.py      validate verdict/issues and produce bounded repair scope
repair_scope.py            classify deterministic failures and editable writer scope
finalize_entry.py          assemble, render, verify, and atomically publish
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
