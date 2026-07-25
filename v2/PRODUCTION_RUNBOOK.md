# V2 production runbook

This runbook covers the authored-and-reviewed workflow for Quranic roots. Run
controller commands from the repository root.

The workflow is deliberately small:

```text
Agent A writes a missing output
Agent B reviews it
Agent B applies only its recorded surgical fixes
```

Agent A is not used for repair. There is no second review. Assembly, rendering,
projection, export, and publication are separate downstream work.

## Prerequisites

- Existing packet files are available under `data/output/root_packets/`.
- Prepared Agent A and Agent B bundles are available under
  `v2/work/entry_creation/<root>/<language>/`.
- The controller has the requested writer and reviewer model configuration and
  worker cap.
- Only the top-level controller delegates agents. Both agents have subagents
  forbidden.

Do not reprepare input bundles merely because writer or review output is
missing. Preparation is deterministic coordinator work and consumes no agent
turn.

## Quranic queue

Enumerate `data/output/root_packets/root_*.json`, sort by numeric root envelope,
and retain packets with at least one branch whose `origin_corpus` is `quranic`.
A combined root envelope is one work item. Do not approximate Quranic scope
with a numeric boundary.

## Existing work

For each `<root>/<language>`, inspect:

```text
v2/work/entry_creation/<root>/<language>/output/<root>_entry.json
v2/work/entry_creation/<root>/<language>/review/output/root_review.json
```

Route it as follows:

| Existing artifacts | Work to run |
| --- | --- |
| No writer output | Agent A, then Agent B |
| Writer output, no review | Agent B |
| Former-workflow `pass` review | No agent work |
| Former-workflow `repair` review | Agent B reviews current output and fixes it |
| `editorial_review` | Human decision; no automatic edit |

Old `repair` reviews only reported issues and therefore do not prove the entry
was corrected. They must be handled once by Agent B under the current contract.

## Agent A

Launch Agent A only when the writer output is missing. Bind it to:

```text
INPUT:  v2/work/entry_creation/<root>/<language>/input/
OUTPUT: v2/work/entry_creation/<root>/<language>/output/<root>_entry.json
```

Agent A reads the prepared bundle, writes the schema-shaped response, runs
structural/schema validation, and returns after the output validates. It does
not delegate or run orchestration commands.

Do not retain Agent A for repair. If a previous writer output exists but its
original Agent A session is gone, proceed directly to Agent B.

## Agent B

Launch Agent B after writer output exists. Bind it to:

```text
INPUT:
  v2/work/entry_creation/<root>/<language>/review/input/
PRE-FIX SNAPSHOT:
  v2/work/entry_creation/<root>/<language>/review/input/writer_response.json
REVIEW OUTPUT:
  v2/work/entry_creation/<root>/<language>/review/output/root_review.json
LIVE CORRECTION TARGET:
  v2/work/entry_creation/<root>/<language>/output/<root>_entry.json
```

Agent B must:

1. review the immutable pre-fix snapshot against supplied evidence;
2. write and validate `root_review.json` before editing;
3. leave writer output untouched for `pass`;
4. for `repair`, edit only the bounded fields named in the findings;
5. validate the corrected writer output;
6. use `editorial_review` without editing if the correction is ambiguous,
   structural, unsupported, or broader than a surgical change.

Give Agent B the current `v2/prompts/root-reviewer.md`. If an older prepared
bundle contains a copied prompt that prohibits reviewer edits, that copied role
instruction is obsolete. Reuse its evidence, response schema, and pre-fix
snapshot without repreparing the bundle.

Do not return findings to Agent A. Do not run a rebound review. A successful
Agent B return completes the two-agent workflow for `pass` and `repair`.

## Surgical edit rule

Each issue must identify a branch or `root_profile`, a bounded field, supporting
evidence IDs, and the smallest correction. Agent B may edit only those fields.
It must preserve all other branches and fields, IDs, enum values,
evidence-owned Arabic, and sound prose.

Stylistic cleanup, broad rewriting, branch split/merge, evidence reassignment,
and speculative improvements are forbidden. Route them to `editorial_review`.

## Validation

Validation in this workflow is structural/schema validation of the two agent
artifacts. Workflow ledgers, state names, content hashes, acceptance fragments,
master entries, and rendered Markdown are not completion gates.

The review artifact is validated before repair. The live writer output is
validated again after repair. If a validator reports a schema error caused by
Agent B's listed edit, Agent B corrects that field in place. A semantic change
not supported by the recorded findings is not allowed as a validator fix.

## Concurrency

Different roots may run concurrently within the configured worker cap. For the
same root:

1. Agent A finishes before Agent B starts.
2. Only Agent B writes during review and repair.
3. No second Agent B is launched while the first is active.

An interrupted Agent B turn is rerun against the current writer output. Do not
reconstruct Agent A or create a competing candidate.

## Completion report

Report five counts and root lists:

- completed with `pass`;
- completed after Agent B's surgical `repair`;
- unresolved `editorial_review`;
- missing writer output;
- writer output awaiting Agent B.

A root counts as completed only after its writer output validates, its review
validates, and Agent B has completed any recorded surgical correction. Do not
include downstream publication status in this report.
