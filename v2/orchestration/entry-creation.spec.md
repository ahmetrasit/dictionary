# V2 entry creation workflow

This file is the normative orchestration contract for one root envelope and one
target language.

## Contract

The workflow has two agent turns:

1. Agent A writes the entry when no writer output already exists.
2. Agent B reviews that output and, when necessary, applies only the bounded
   corrections identified in its review.

Agent A is not retained and is never called for repair. Agent B's corrected
writer output is final for this workflow. There is no second review.

Prepared input bundles are reused as they are. Packet preparation, entry
assembly, rendering, projection, and publication are separate deterministic
work and are not completion gates for this authored-and-reviewed workflow.

## Audit boundary

Do not run or use:

```text
python3 v2/scripts/audit_entry_campaign.py ...
```

to determine whether this workflow is complete. That script audits the former
publication pipeline: canonical acceptance fragments, bound reviews, published
entry JSON, rendered Markdown, hashes, and publication validation. Its nonzero
exit and its `state` values do not mean that Agent A or Agent B failed or still
has work.

In particular:

- `publication_stale` describes downstream publication only;
- `writer_missing` may mean that an old canonical fragment is absent even when
  the live `output/<root>_entry.json` needed by this workflow exists;
- `editorial_review` means Agent B reviewed the entry but left a bounded issue
  for human judgment;
- `structural_review_required` means branch-identity curation is needed outside
  Agent B's surgical-edit authority.

Determine Agent A/B completion only from the live writer output, Agent B review,
and completion of any surgical repair as defined below. Never report the old
audit's `published_valid` count as this workflow's completion count.

## Scope

Build a campaign queue from existing packet files under:

```text
data/output/root_packets/root_*.json
```

Sort packet envelopes by their numeric root components. A combined envelope is
one work item. Quranic scope includes every packet with at least one branch
whose `origin_corpus` is `quranic`.

Never infer the queue from a numeric range when packet files can be enumerated.
Do not regenerate prepared input bundles merely because authored or reviewed
output is missing.

## Artifacts

For `<root>` and `<language>`, use:

```text
v2/work/entry_creation/<root>/<language>/
  input/                         prepared Agent A bundle
  output/<root>_entry.json       Agent A output and Agent B's correction target
  review/input/                  prepared Agent B evidence and pre-fix snapshot
  review/output/root_review.json Agent B findings
```

`review/input/writer_response.json` is the exact pre-fix writer response
presented to Agent B. It remains unchanged when Agent B corrects the live writer
output, so the review and original response can be compared later.

The current `v2/prompts/root-reviewer.md` is authoritative for Agent B. A
reviewer prompt copied into an already prepared bundle may describe the former
report-only role; ignore that copied instruction while reusing the bundle's
evidence, response schema, and writer snapshot.

Existing task metadata may be used by scripts internally, but task states,
ledger rows, acceptance copies, and content hashes do not determine completion
under this workflow.

## Roles

### Controller

The controller:

- selects roots and reuses their prepared bundles;
- delegates only Agent A and Agent B turns;
- never creates command-runner or per-root controller agents;
- ensures that only one agent writes a given root at a time;
- records operational failures without converting them into semantic findings;
- reports completion from the two required agent artifacts and the result of
  Agent B's turn;
- never substitutes the legacy publication audit for this workflow's artifact
  count.

The controller may run deterministic schema validation itself. It does not
rewrite authored prose.

### Agent A: writer

Agent A:

- reads only the prepared writer bundle;
- writes exactly `output/<root>_entry.json`;
- follows the writer response schema and supplied evidence;
- does not delegate or orchestrate other work;
- runs structural/schema validation after writing;
- returns after the writer output validates.

If a writer output already exists, do not launch Agent A. That includes outputs
created by an earlier campaign whose Agent A session no longer exists.

### Agent B: reviewer-editor

Agent B:

- independently reviews the exact pre-fix writer output against the prepared
  review evidence;
- writes `review/output/root_review.json` before editing writer output;
- leaves writer output unchanged when the verdict is `pass`;
- for a bounded `repair`, edits only the fields named by its findings;
- runs structural/schema validation after any edit;
- does not delegate, contact Agent A, or launch a second reviewer;
- does not assemble, render, project, or publish the entry.

Agent B is both reviewer and surgical editor. It is not a replacement author.

## Per-root procedure

1. Confirm that the prepared writer and review bundles exist.
2. If `output/<root>_entry.json` is missing, delegate Agent A and require a
   schema-valid writer output.
3. Give Agent B the prepared review bundle, including the exact pre-fix snapshot
   of the writer output.
4. Agent B completes the semantic review and writes
   `review/output/root_review.json`.
5. Route the verdict:
   - `pass`: Agent B makes no writer edit.
   - `repair`: Agent B applies every listed correction, and no unlisted change,
     to `output/<root>_entry.json`, then validates it.
   - `editorial_review`: Agent B does not edit the writer output; report the
     bounded ambiguity for human decision.
6. When Agent B returns successfully, the root's agent workflow is complete.

A stored review from the former workflow with verdict `repair` only reported
issues; it does not prove that Agent B corrected them. Assign Agent B once under
this contract to review the current writer output and make any required
surgical corrections.

## Surgical repair boundary

Every repair finding must name:

- one branch or `root_profile`;
- one bounded field;
- the evidence IDs supporting the finding;
- the smallest concrete correction.

Agent B may change only those named fields. It must preserve:

- every unaffected branch and root-profile field;
- all IDs, rosters, enum values, and evidence-owned Arabic;
- the response shape and ordering required by the schema;
- any sound text outside the reported defect.

Agent B must not perform a broad rewrite, stylistic cleanup, speculative
improvement, branch split or merge, evidence reassignment, or unsupported
lexical decision. When the smallest defensible correction crosses those
boundaries, use `editorial_review` and do not edit.

The review verdict describes Agent B's completed turn:

- `pass` means no issue was found and no edit was made;
- `repair` means the recorded issues were found, surgically corrected by Agent
  B, and the corrected writer output passed schema validation;
- `editorial_review` means a bounded issue remains unresolved because it cannot
  be corrected surgically and confidently.

## Completion

For this workflow, a root is complete when:

- `output/<root>_entry.json` exists and passes structural/schema validation;
- Agent B has reviewed it under this contract;
- `review/output/root_review.json` exists and validates; and
- any `repair` findings were applied by Agent B before its successful return.

There are no workflow states, hash gates, acceptance steps, rebound reviews, or
publication requirements in this definition.

Do not use `audit_entry_campaign.py`, a published entry, a canonical fragment,
or rendered Markdown to add or remove roots from this completion count.

An `editorial_review` result is reviewed but unresolved; list it separately
rather than reporting it as completed content.

## Resumption and concurrency

Different roots may run concurrently. Within one root, Agent A must finish
before Agent B starts, and only Agent B may edit during its turn.

On resumption:

- existing writer output plus no current review: run Agent B;
- no writer output: run Agent A, then Agent B;
- an old-workflow `repair` review: rerun Agent B once under this contract;
- an interrupted Agent B turn: rerun Agent B against the current output and
  require a complete review/fix/validation turn.

Do not reconstruct a missing Agent A session and do not send repair work to a
new writer.

## Downstream work

Assembly, master-entry validation, Markdown rendering, projection, export, and
publication may consume the completed writer output later. They are
deterministic downstream operations and must not be mixed into the definition
of whether Agent A and Agent B completed their work.

The finalized dictionary-entry surface for downstream consumers is root-level
and JSON-only:

```text
entries/<language>/<root_envelope_id>.json
entries/<language>/manifest.json
```

`v2/entries/<language>/` remains the v2 assembly/rendering area and may contain
JSON plus Markdown. It is not the final consumer-facing directory. After a
language's v2 entries are assembled and validated, promote only Quran-corpus
final JSON files with:

```sh
python3 v2/scripts/promote_final_entries.py --language <language>
python3 v2/scripts/promote_final_entries.py --language <language> --check
```

Use `--require-complete` only when the language is expected to have every
Quranic packet envelope finalized. The promoter writes the manifest, refuses
non-Quranic or non-packet roots, and prunes stale `root_*.json` files from the
destination by default. Future languages must use the same
`entries/<language>/` final JSON surface after their language-specific agent
pass and deterministic assembly are complete.

A separate publication-readiness report may use the legacy audit when that
downstream question is explicitly requested. Label such a report
`publication readiness`, never `Agent A/B workflow completion`.
