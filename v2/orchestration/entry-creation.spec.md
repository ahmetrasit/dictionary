# V2 Entry Creation Orchestration

Status: normative orchestration contract for entry schema version 4.

This workflow creates one encyclopedia entry for one root envelope and one
target language. One initial writing invocation receives the minimal evidence
for all accepted branches in that root and returns branch-shaped fragments plus
the short root profile. If finalization discovers missing used transliterations
or protected proper-name target forms, the same writer assignment completes
only the generated surface-form queues and finalization resumes without human
review.

One top-level orchestration controller owns the run end to end. It enumerates the
queue, runs every deterministic command directly, launches and resumes the
bounded semantic workers, monitors them, checks every gate, controls the repair
budget, and reports terminal state. There is no separate campaign operator and
no per-root orchestration agent. Deterministic scripts own evidence routing,
response acceptance, occurrence data, assembly, validation, rendering,
publication, and projection. Semantic workers never edit shared or published
entry documents.

## Dispatch Boundary

The controller must use the least expensive capable executor:

| Work | Executor |
|---|---|
| Queue enumeration, path inspection, script execution, polling, staging, validation, acceptance, assembly, rendering, publication, projection, export, and status tracking | Top-level controller, directly |
| Root response authorship, bounded writer repair, and target-language surface-form choices | One root-writer worker per root/language |
| Independent evidence-bound semantic judgment | One semantic-reviewer worker per accepted response |
| Ambiguous editorial decisions and destructive replacement authorization | User/editor |

A deterministic task is never delegated merely because it can be described as a
task. In particular, the controller must not spawn an agent to run
`scripts/root_packet.py`, `v2/scripts/create_entry.py`, a staging or check
script, a validator, an acceptance script, a renderer, a projector, an exporter,
a file operation, a wait loop, or a status check. Long-running controller
commands remain controller commands: the controller waits for or polls the same
process.

Only the top-level controller may launch workers, using the orchestration
runtime's native delegation facility. It must not launch them through Python,
shell, `codex exec`, or a worker. A writer or reviewer may not delegate, spawn,
or manage another agent. The only command a semantic worker may run is the exact
read-only `task.json.validation.command` for its own authored output. The
controller reruns that command before acceptance.

Production campaigns run this same root-level workflow repeatedly. The campaign
queue is built from canonical Quran-corpus root packets under
`data/output/root_packets/`, sorted by numeric root envelope. Missing numeric
IDs are skipped, and combined envelopes such as `root_000099--root_000100` are
treated as one queue item. Each semantic worker owns exactly one root envelope,
one target language, and one declared artifact or explicitly generated
surface-form queue set per turn. "First N roots" counts N sorted packet
envelopes; a combined envelope counts once. "Through root N" includes envelopes
whose first numeric component is at most N and never splits a combined envelope.
The controller may run workers for different roots concurrently up to runtime
capacity, further limited by any explicit lower campaign cap. It must not assume
a fixed slot count, split one root across competing writers, or run a same-root
writer, reviewer, or repair concurrently.

Packet generation is not a production worker workflow. If canonical root
packets are missing or stale, the coordinator runs deterministic packet
preparation outside the worker pool before the campaign queue is built. Do not
spend semantic-worker capacity on packet generation or any other mechanical
operation. No Python script invokes a worker or decides whether to retry one.
The controller follows `v2/prompts/entry-orchestrator.md`.

All semantic-worker-readable packages and worker-produced artifacts live in the
repository work tree under
`v2/work/entry_creation/<root-envelope>/<language>/`. Semantic workers never
read from or write to `/tmp`, `/private/tmp`, another operating-system temporary
directory, or a runtime-managed scratch workspace. Worker output is durable and
resumable at the declared repository-local path before any acceptance or
publication step.

## Worker Session Boundary

Worker authorship uses the controller's native delegation facility, not nested
agent-launching commands. Each worker handoff binds:

```text
ROLE: root writer or independent semantic reviewer
MODEL/REASONING: explicit user or campaign configuration
SESSION: new writer, new reviewer, or continuation of the mapped writer
SUBAGENTS: forbidden
INPUT: exact staged instructions path
OUTPUT: exact staged repository-local output path
```

Model, reasoning level, service tier, and concurrency are run configuration, not
normative lexical policy. The controller must not silently invent or substitute
them. It retains the writer session identity until the root publishes or parks
because review repair or surface-form completion may need a continuation. A
reviewer is always independent of the writer and receives only its staged
review package. The reviewer may be released after validation and acceptance; a
repaired response receives a fresh reviewer. When orchestration resumes without
the original writer handle, the controller may launch one bounded continuation
for a staged repair or exact generated queue; this is not a new full candidate.
If the controller cannot start a required worker continuation, the root parks
with `worker_session_required` and the exact staged input/output paths; it must
not invent an external operator or work around the gate with a nested launch.

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

The coordinator validates and hash-binds these inputs. Semantic workers do not
receive the packet, occurrence Markdown, alignment file, Quran ayahs, QAC
morphology, attachment records, dictionary source metadata, full branch
packages, the master entry schema, or this orchestration spec. The controller
does read this spec. A worker-facing package contains only the role prompt, a
thin root response schema, the minimal root evidence projection, and any compact
policy notes needed for the target language.

`v2/policy/protected_names/<root-envelope>.json` may be a reviewed policy or a
coordinator-generated fallback policy. The fallback classifies every lexical
unit as `ordinary` and is acceptable for orchestration when no protected-name
review exists. A reviewed policy should replace the fallback when proper-name
classification is materially needed, but missing review alone is not a blocker
for running the root workflow.

The QNet candidate roster is balanced across packet-carried neighbors, raw core
overlap, raw bridge overlap, and branch-theme overlap. At most eight unique
cross-root candidates are retained across those lanes, followed by every sibling
branch in the focus root. If an exact theme port is absent, the builder may use
the represented root's themes as an explicitly labeled indirect fallback.
The resulting roster may be empty; in that case the coordinator records
`candidate_count: 0` and the writer assesses the supplied empty roster without
inventing a neighbor.

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
only that projection to the semantic worker task. `input/` is the complete
writer package; the neighboring plural `inputs/` directory is coordinator state
and is not given to the writer. The root response is only a transport envelope;
the authoritative authored units remain branch fragments.

## Semantic Worker Evidence Projection

Each focus branch contains:

```json
{
  "branch_ref": "root_001697/B001",
  "branch_image_ar": "...",
  "what_is_ar": "...",
  "what_is_not_ar": "...",
  "branch_claims": [
    {
      "claim_id": "bc_001",
      "source_phrase_ar": "...",
      "source_ids": ["maqayis", "sihah"]
    }
  ],
  "lexicalization_profile": {
    "branch_kind": "bare",
    "has_non_bare": false,
    "has_collocation": false,
    "unit_kind_counts": {"form": 1},
    "basis": "furuq.lexical_unit_senses.unit_kind"
  },
  "lexical_units": [
    {
      "lexical_unit_id": "lu_001",
      "unit_kind": "form",
      "expression_ar": "...",
      "sense_ar": "...",
      "source_phrase_ar": "...",
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

The exact branch `source_phrase_ar` is projected as one deterministic aggregate
`bc_*` branch claim and is authoritative for branch identity. The compact
`branch_image_ar`, `what_is_ar`, and `what_is_not_ar` fields are provisional
comparison aids. The writer may correct or qualify their framing in authored
entry fields, but never mutates the frozen Arabic evidence or source database.
Concept facets and source synthesis bind only to the branch claim.

Lexical units are a separate, optional attestation roster. A branch with no
accepted lexical units is still writable and receives `lexical_units: []` plus
an `unresolved` lexicalization profile. Lexical source references remain
coordinator-side provenance: they may extend beyond the branch dictionary basis
when they resolve in the packet-wide dictionary roster, and are neither unioned
into branch authority nor silently discarded. Every lexical unit carries a
coordinator-owned `rendering_policy` of `ordinary` or `proper_name`; the policy
status is either `reviewed` or `fallback`. Policy coverage must match the
lexical roster exactly. Acceptance checks the branch-claim roster, lexical
roster, and rendering policy independently.

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

## Semantic Worker Roles

### Root Writer

Run once per root envelope and target language. The response contains one
branch-shaped fragment per accepted branch and one short root profile.

The writer authors:

- an explicit identity judgment grounded in authoritative
  `source_phrase_ar`, including supported qualification or reframing in the
  entry rather than the source data;
- an authored lexicalization-scope note whose `branch_kind` exactly echoes the
  coordinator's mechanical profile and prevents construction-bound senses from
  being generalized into bare meanings;
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
Branch lexicalization status is also coordinator-owned. The coordinator derives
`lexicalization_profile` from Furuq lexical-unit `unit_kind` values already
bound to each branch, so any branch containing collocation or other non-form
units is flagged as non-bare without semantic-worker inference. The writer must
echo its `branch_kind` in `lexicalization_scope` and obey these semantic limits:
`bare` excludes collocation-only readings; `collocation` stays explicitly
construction-bound; `mixed_non_bare` separates bare and non-bare facets;
`non_bare` preserves lexical restriction; and `unresolved` never licenses an
assumption of bare meaning.

The writer also returns `identity_judgment.status` as `accepted`, `qualified`,
`reframed`, or `structural_review_required`. The first three preserve the
prepared branch roster while recording the authored correction. Structural
review means a faithful entry would require a split, merge, deletion, or
reassignment. The coordinator parks that root before semantic review and
refuses assembly or publication.

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
| Branch identity judgment and supported target-language correction | root writer, per branch |
| Mechanical lexicalization class | Furuq / coordinator |
| Authored lexicalization scope note | root writer, constrained by mechanical class |
| Concept-map facets, definitions, and claim-bound source synthesis | root writer, per branch |
| Concept, contextual, lexical, and excluded gloss text and risk | root writer, per branch |
| Neighbor selection, verified relation type, asymmetry, prose, and coverage explanation | root writer, per branch |
| Semantic publication verdict and bounded issue scope | semantic reviewer |
| Proper-name classification | coordinator policy, reviewed or fallback |
| Proper-name target forms | root writer, through generated surface-form queue |
| Transliteration catalog and used-anchor queue generation | coordinator |
| Used transliteration values | root writer, through generated surface-form queue |
| Proper-name and transliteration restoration | coordinator |
| Branch summary copied from definition; ranks; counts; coverage enum; collocation defaults | coordinator |
| Neighbor Arabic image, basis, references, candidate count | Furuq package / coordinator |
| Dictionary counts, names, source roster, references | packet / coordinator |
| Lexical realizations and branch lexicalization profile | packet / Furuq / coordinator |
| QAC forms, morphology, ayahs, and occurrence rows | coordinator |
| Attachment-to-QAC alignment and linked attachment detail | coordinator |
| Markdown and JSONL | deterministic renderers |
| Consumer projection selection and master hash binding | deterministic projector |

Worker raw responses containing fields outside their schema are rejected. After
validation, the coordinator adds `inputs_sha256` and the deterministic evidence
layer; semantic workers do not author either.
Arabic script in an authored target-language field is rejected by the response
schema. The schema also restricts every selected gloss to
`loanword_status: none`; plain-language quality beyond those mechanical checks
remains part of semantic review.

## Execution Order

```text
1. Controller validates packet and deterministic occurrence/alignment artifacts
2. Controller builds full branch evidence and one hash-bound minimal projection
3. Controller reuses a checked writer fragment or launches one root writer
4. Writer authors and self-validates its output; controller revalidates and accepts it
5. Controller parks any `structural_review_required` branch before semantic review
6. Controller reuses a checked review pass or launches one independent reviewer
7. Controller validates and accepts the review, then inspects its explicit verdict
8. Controller routes one bounded writer repair or parks for editorial review
9. Every repaired response receives a fresh independent semantic review
10. Same writer completes generated transliteration/name queues when required
11. Controller finalizes, validates, renders, and atomically publishes JSON/Markdown
12. Controller derives requested projections and exports without another worker
```

Roots with more than 100 occurrences follow the same process. Their occurrence
arrays are built deterministically after writer work and omitted from the
reviewer's authored-only view, so occurrence count does not increase either
semantic worker's context.

The internal validated master retains exact dictionary references for
verification. The accepted and downstream entry artifacts expose only
the frozen Arabic fields `branch_image_ar`, `what_is_ar`, `what_is_not_ar`, and
`source_phrase_ar` plus compact source attribution. These Arabic fields are
restored from frozen packet/evidence data, never rewritten by a semantic worker.
Occurrences remain root-level because this workflow does not infer an
occurrence-to-branch assignment. Each occurrence carries its QAC morphology and
mechanically aligned attachment details; downstream projections may expose the
full layer or a compact summary without relocating it into a branch.

The accepted `<root-envelope>_entry.json` also exposes `identity_judgment`,
`lexicalization_scope`, `sources`, and `source_note` on every branch. `sources`
is the coordinator-mapped short-code roster of dictionaries supporting the
authoritative branch claim. `source_note` maps only a dictionary code to concise
prose for its distinctive addition, variant, or dispute and is `{}` when no
such note exists. Exact references, paths, source detail categories, and claim
IDs remain internal validation data.

### Required State Transitions

The controller tracks one explicit state per root/language:

```text
queued -> preparing -> writer_ready -> writer_running -> writer_accepted
       -> review_ready -> review_running -> pass -> finalizing -> published
                                      -> repair -> writer_repair_ready
                                                -> writer_running
                                                -> review_ready
                                      -> editorial_review -> parked

finalizing -> surface_forms_ready -> writer_running -> finalizing
writer_accepted -> structural_review_required -> parked
```

`parked` is reachable from any failed gate and is terminal for that campaign
unless the user explicitly resumes it. `published` is the only successful
terminal state. The controller may skip `writer_running` or `review_running`
only when the corresponding check script proves a canonical artifact valid and
task-bound. A checked stored non-pass review resumes at its verdict route; it
does not launch another reviewer. The controller may skip `surface_forms_ready`
when finalization requests no queue.

Worker prose such as "done" or "validated" never advances state. A transition
requires the expected artifact plus a zero exit from its check, validation, or
acceptance command. A zero exit from `accept_root_review.py` stores the review
but does not imply `pass`; the controller must read and route the verdict.
Likewise, an existing filename or JSON parse success never proves task-hash,
roster, review-binding, or publication validity.

The controller runs every transition command itself. It may batch independent
controller commands and run semantic workers for different roots concurrently,
but it must preserve same-root order. It never creates a worker whose job is to
operate this state machine.

## Input, Output, and Resumption

Each writer uses the regular resumable `input/` and `output/` folders in its
root/language work directory. `input/` contains only the staged prompt, thin
schema, compact evidence, task, and instructions. During entry and repair, the
instructions prohibit reading any other input. A later surface-form continuation
may authorize only the exact generated queue paths. The raw response is written
only to `output/<root-envelope>_entry.json`; deterministic acceptance validates it,
injects the coordinator-owned Arabic/source, branch lexicalization, and
occurrence/attachment layer into that same file, and stores the enriched
hash-bound canonical fragment.
The reviewer receives a compact authored-only view, so the mechanically added
layer does not increase reviewer context. The reviewer follows the same rule with
`review/input/` and `review/output/root_review.json`. Neither semantic worker may
use an operating-system or runtime temporary directory, including as an
intermediate output location. Validation or review errors and their mechanically
classified scope remain under the owning `output/` or `review/output/`
directory; a repair restage copies only the exact error, previous response, and
scope into `input/`.

Deterministic scripts may use hidden atomic staging files or directories only
beside their repository-local destination. If some other short-lived mechanical
artifact is necessary, it belongs under the current root/language work directory
(for example `temporary/`) and must be removed after use. Such mechanical
staging is never a semantic worker package or output target.

The staging commands derive `input/`, `output/`, `review/input/`, and
`review/output/` from the canonical task location. They do not accept an
alternate input-directory or output-directory override.

Every staged task carries an exact `validation.command`. The writer and reviewer
run that read-only command from the repository root after writing their declared
output. On failure, the worker keeps the complete response at the same path,
corrects it from the exact validator error, and reruns validation until it
passes. Validation never deletes, moves, truncates, or accepts the response. The
controller runs the same command once more before canonical acceptance.

A valid root-writer response is reused only when its `inputs_sha256` matches the
canonical task and `check_root_writer.py` succeeds. A valid semantic-review pass
is reused only when `check_root_review.py` proves that it is bound to that exact
accepted response. For resumption, `check_root_review.py --any-verdict` also
validates bound `repair` and `editorial_review` artifacts so the controller can
route them without launching a duplicate reviewer. Reaccepting a checked
canonical non-pass review as both response and output is an idempotent way to
regenerate missing error/scope sidecars. The controller checks staged raw output
before launching a worker, so a valid resumable artifact does not cause a
duplicate model call.

A validation failure bound to the current task is returned to the same mapped
worker, which repairs the same raw output; it is not grounds for discarding the
response or spawning a competing candidate. The controller never edits or
copies authored JSON to make two artifacts agree. It runs the owning staging,
validation, and acceptance commands and inspects their exit status. A stale
artifact from a different task is never blessed or silently repaired as though
it were current.

Timeouts and nonzero worker exits are operational failures and do not consume a
semantic repair. A run permits one initial writer turn and one semantic-review
repair continuation with that writer. The repaired response
receives a fresh independent review; if that rebound verdict is `repair` or
`editorial_review`, the root parks. Self-validation iterations within a worker
turn and at most two controller-mediated corrections of the same schema-invalid
artifact do not consume the semantic repair budget. Exceeding that structural
correction limit parks the root rather than looping indefinitely.

A semantic repair receives the previous accepted response, exact review issue,
and generated scope. Deterministic acceptance rejects any change to branches or
root fields outside that scope. Any repair invalidates the earlier review.

Finalization may request the transliteration queue and protected-name queue on
separate passes. Each request continues the retained writer session when
available. After process resumption, the controller may launch one bounded
writer continuation authorized only for the exact generated queue paths. This
explicit continuation supersedes the initial input-directory read restriction
only for those named files. The worker must not change the accepted entry
response. A queue receives at most two controller-mediated correction
continuations before the root parks. Other finalization failures are mechanical
and never go to a semantic worker.

## Surgical Correction Protocol

Corrections preserve the accepted work already present in a response. They are
owned and routed as follows:

| Failure or finding | Corrector | Required action |
|---|---|---|
| Writer/reviewer schema or semantic-contract error | Same mapped worker | Keep the actual output; edit only the fields named by the exact error; rerun `validation.command` |
| Evidence-grounded semantic-review issue | Same mapped root writer | Restage the previous response, exact issue, and generated scope; change only permitted fields; validate again |
| Missing or stale protected-name policy | Coordinator | Use the generated all-ordinary fallback policy or replace it with an exact reviewed roster; do not let a writer infer policy |
| Missing used transliterations or protected-name target forms | Same mapped root writer | Fill only the generated queue rows with approved target-language values; do not change the accepted entry response |
| Stale task/hash or staged-path mismatch | Controller, running the owning script directly | Restage canonical files; do not alter authored prose or bless a stale raw response |
| Evidence build, assembly, rendering, or publication failure | Controller, running the owning script directly | Repair or regenerate a clearly owned deterministic prerequisite; never route it as a lexical rewrite |
| Scope conflict or evidence ambiguity | User/editor after worker report | Preserve protected artifacts and park without broadening the correction |

The controller never edits worker-authored JSON. It directly invokes validators,
classifiers, staging, acceptance, and deterministic build commands, then sends
an exact bounded error only to the worker that owns the affected authored field.
A surgical correction must not regenerate valid branches, reorder unaffected
content, rephrase unrelated prose, or change protected root fields. Validation
failures remain at their declared repository output path until the mapped worker
fixes them or editorial review explicitly decides otherwise.

## Assembly and Validation

`assemble_entry.py` performs a keyed merge:

- branch fragments are keyed by `(root_id, branch_id)`;
- the packet determines branch and lexical-unit order;
- the evidence package determines source and neighbor identity;
- the concept gloss and contextual glosses stay distinct; compatibility ranks
  are derived mechanically;
- writer-completed proper-name placeholders are substituted mechanically;
- lexical target glosses join by exact lexical-unit ID;
- branch claim IDs expand to precise branch-basis source names and references;
- branch summaries, excluded-gloss display reasons, coverage enums, branch
  counts, and collocation defaults are restored mechanically;
- source references are attached to authored claims mechanically;
- QAC and attachment structures are recomputed and compared exactly;
- missing, duplicate, extra, stale, or wrong-language fragments are rejected.

Only root-writer fields are eligible for semantic worker repair.
Dictionary routing, provenance, morphology, alignment, ayahs, and occurrence
errors are deterministic pipeline failures and are never sent to a semantic worker.

Draft generated JSON and Markdown are staged, validated, and published as a
pair. Reviewed or published outputs and their pinned evidence require explicit
force flags before replacement.

## Acceptance Criteria

A root workflow is complete only when:

1. One root-writer response matches the hash-bound task and exact branch roster.
2. A semantic-review pass is bound to that exact accepted response.
3. Split branch and root-profile fragments reproduce from that response.
4. Minimal semantic evidence matches its coordinator-side packages, every
   branch has authoritative branch-claim coverage and exact mechanical
   lexicalization scope, every supplied lexical unit has exact reviewed or
   fallback rendering policy, and every used transliteration and protected
   proper-name form has a writer-completed queue value.
5. Schema and packet-aware validation pass.
6. Markdown is reproducible under `--check`.

Only then may the controller mark the root `published`. A campaign export is a
separate deterministic completion gate: when requested, the controller directly
runs JSONL export and required projections after all eligible roots are
terminal. That export is complete only when every record validates, one common
schema is preserved, and every projection is reproducible and hash-bound to its
master entry. Projection or export never requires another semantic worker.

## Script Boundary

```text
build_branch_evidence.py   full deterministic coordinator evidence
create_entry.py            prepare evidence projection and canonical task only
stage_root_writer.py       refresh regular input/ and output/ writer folders
check_root_writer.py       verify that a stored response is safely reusable
accept_root_writer.py      validate, scope-check, hash-bind, and store returned JSON
prepare_root_review.py     bind semantic review to accepted evidence and response
check_root_review.py       verify a bound review; require pass unless --any-verdict
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

The controller runs every script in this table directly and checks its exit
status. The table is not a worker-role roster.

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
additional worker call.

The current contract supports English (`en`) and Turkish (`tr`). A new language
code requires an explicit schema, transliteration-policy, renderer-label, and CLI
extension; shared Arabic evidence still remains reusable after that extension.
