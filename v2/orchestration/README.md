# V2 entry orchestration

This directory defines the current authored-entry workflow.

Read these files in order:

1. [`entry-creation.spec.md`](entry-creation.spec.md), the normative contract;
2. [`../prompts/entry-orchestrator.md`](../prompts/entry-orchestrator.md), the
   controller instructions;
3. [`../prompts/root-writer.md`](../prompts/root-writer.md), Agent A's role;
4. [`../prompts/root-reviewer.md`](../prompts/root-reviewer.md), Agent B's
   reviewer-editor role.

The workflow is:

```text
missing writer output -> Agent A writes
writer output         -> Agent B reviews
bounded findings      -> Agent B surgically fixes and validates
```

Agent A is not called for repair. Agent B records findings before changing the
writer output, changes only fields named in those findings, and performs no
broad rewrite. There is no second review.

Prepared input bundles under `v2/work/entry_creation/` are reused as-is. The
workflow does not require packet regeneration, state transitions, content-hash
gates, acceptance copies, publication, rendering, or projection.

## Start one root

Give one top-level controller an instruction such as:

```text
Read v2/orchestration/README.md and complete the current entry workflow for
root_000858 in tr. Reuse its prepared bundles. Use Agent A only if writer output
is missing; then have Agent B review and surgically fix only its recorded
findings.
```

## Start a campaign

```text
Read v2/orchestration/README.md and complete the current entry workflow for all
Quranic packet envelopes in tr. Reuse prepared bundles. Run Agent A only for
missing writer outputs. Run Agent B for every output that still needs review;
Agent B records findings first and applies only surgical fixes.
```

The controller may parallelize different roots within the supplied worker cap.
For one root, Agent A finishes before Agent B begins. Workers do not spawn
subagents or operate the campaign.

## Completion

A root has completed this agent workflow when its writer output is schema-valid,
Agent B's review exists and validates, and Agent B has applied any recorded
surgical correction before returning. `editorial_review` is reviewed but
unresolved and must be reported separately.

Downstream assembly and publication are separate from this completion
definition.
