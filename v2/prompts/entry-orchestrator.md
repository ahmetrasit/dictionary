# V2 entry orchestrator

Follow `v2/orchestration/entry-creation.spec.md`.
Run every deterministic or operational task yourself. Never spawn a worker merely to run a command.

The workflow is intentionally limited to one writer role and one
reviewer-editor role:

1. Agent A writes a missing entry output.
2. Agent B independently reviews that output, records findings, and makes only
   the surgical corrections supported by those findings.

Agent A is never used for repair. Agent B's corrected output is not sent to a
second reviewer.

## Start

Resolve the requested root envelopes from existing
`data/output/root_packets/root_*.json` packet files. For Quranic scope, include
packets with at least one branch whose `origin_corpus` is `quranic`. Reuse the
already prepared bundles under:

```text
v2/work/entry_creation/<root>/<language>/
```

Do not regenerate a bundle solely because its writer or review output is
missing. Do not use a ledger, state machine, hash comparison, acceptance
fragment, published entry, or Markdown file to decide whether the two agent
turns are complete.

## Agent A

For a root without:

```text
output/<root>_entry.json
```

delegate exactly one writer using the prepared `input/` instructions and output
path. Tell the writer to:

- perform the work itself and use no subagents;
- read only its prepared bundle;
- write only its declared writer output;
- run structural/schema validation after writing;
- correct schema errors in the same file before returning.

When the writer output already exists, reuse it and do not launch Agent A.

## Agent B

After writer output exists, delegate exactly one reviewer-editor using the
prepared `review/input/` bundle. The review bundle's
`writer_response.json` is the immutable pre-fix snapshot. Agent B's live
correction target is:

```text
v2/work/entry_creation/<root>/<language>/output/<root>_entry.json
```

Give Agent B the current `v2/prompts/root-reviewer.md` role contract. A copied
prompt inside an older prepared bundle may say that the reviewer cannot edit;
that instruction belongs to the former workflow and is superseded. Reuse the
bundle's evidence, response schema, and writer snapshot without repreparing
them.

Tell Agent B to:

1. review the snapshot against only the supplied evidence;
2. write and schema-validate `review/output/root_review.json` before editing the
   writer output;
3. make no writer edit for `pass`;
4. for `repair`, change only the bounded fields named in its findings;
5. schema-validate the corrected writer output;
6. use `editorial_review` without editing when a correction would require a
   broad rewrite, unsupported judgment, branch restructuring, or evidence
   reassignment;
7. return only after the review and any surgical correction are complete.

Agent B must not contact Agent A, delegate, broadly rewrite sound material, run
downstream publication work, or request another review.

## Existing artifacts

Use artifacts directly:

- missing writer output: Agent A, then Agent B;
- writer output with no review: Agent B;
- former-workflow `pass` review: no agent work remains;
- former-workflow `repair` review: Agent B must review the current output and
  perform the correction under the new contract;
- `editorial_review`: report it for human judgment.

The verdict in a newly completed Agent B turn has these semantics:

- `pass`: reviewed, no edit required;
- `repair`: findings recorded, all listed surgical edits applied, corrected
  writer output schema-valid;
- `editorial_review`: reviewed, unresolved, no edit applied.

If Agent B is interrupted between recording findings and completing repair,
rerun Agent B for that root. Do not reconstruct or retain Agent A.

## Concurrency and reporting

Run different roots concurrently within the explicit worker cap. Never overlap
Agent A and Agent B on the same root or allow two agents to edit one root.

Report:

- roots completed with `pass`;
- roots completed after Agent B's surgical `repair`;
- roots awaiting `editorial_review`;
- roots still missing Agent A output;
- roots still awaiting Agent B.

Do not report assembly, rendering, projection, publication, state labels, or
hash status as part of this workflow's completion.
