# Root Entry Orchestrator Contract

This contract is followed by the top-level coordinating agent. Do not delegate
this role to a worker. Editorial agents produce content; they do not spawn,
manage, stop, or direct other agents.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
PACKET_JSON={{PACKET_JSON}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
BRANCH_BUNDLE_DIR={{BRANCH_BUNDLE_DIR}}
CANDIDATE_DIR={{CANDIDATE_DIR}}
AUTHORED_JSONL={{AUTHORED_JSONL}}
OUTPUT_DIR={{OUTPUT_DIR}}
```

Read `spec.md`, `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`,
`schema/authored-entry.schema.md`, the packet, the root bundle, and every branch
bundle before assigning editorial work.

## Ownership

The top-level orchestrator:

- records the exact root and branch roster;
- starts requested editorial agents with distinct candidate paths;
- actively monitors agent status without steering a running agent;
- keeps script implementation, code review, and editorial production separate;
- updates reusable prompts when a completed run exposes a general workflow
  defect, then starts a fresh run against the revised prompt snapshot;
- sends code-review findings back to the same script implementer only after
  that implementer's current run has completed;
- sends linguistic corrections back to the agent that authored the candidate
  only as a new run after the producer's current run has completed;
- runs validation and rendering scripts itself;
- deeply reads both rendered entries before declaring success;
- never manually fixes authored or rendered output;
- never delegates orchestration;
- never stops or closes an agent without explicit user authorization.

## Procedure

1. Generate or verify the packet, bundle tree, and scaffold reading aids.
2. Record exact packet-owned identities and Quran keys.
3. If renderer/schema code changes are needed, assign them to one implementer,
   obtain review from a persistent code-review agent, and return findings to the
   implementer until focused tests pass.
4. Start every requested independent editorial run from the same reviewed
   schema and immutable prompt snapshot. Each run writes a complete candidate
   JSONL in its own directory. Never inject clarifications, corrections, or
   redirects into a running editorial agent.
5. Validate each candidate mechanically. Validation failures go to that
   candidate's producer in a fresh run after the current run completes. If a
   failure reveals a reusable workflow defect, fix the prompt before rerunning;
   do not encode a root-specific patch in orchestration chat.
6. Compare candidates for evidence fidelity, lexicographic depth, gloss
   quality, transliteration, and independent English/Turkish prose.
7. Have an editorial agent produce the reviewed canonical JSONL at
   `AUTHORED_JSONL`. Do not splice or patch linguistic content manually.
8. Render `entries/en/<root_envelope_id>.md` and
   `entries/tr/<root_envelope_id>.md` with
   `scripts/render_language_entries.py`.
9. Read both files completely. Check the primary gloss and the deeper concept,
   boundary, contrast, source-audit, lexical-unit, Quran, and bibliography
   sections. Route defects to their owner through a revised prompt and a fresh
   completed-agent run, then rerender.
10. Run focused tests, renderer `--check`, and `git diff --check`.

## Non-negotiable evidence rules

- Preserve every frozen branch exactly once.
- Never assign a Quran occurrence to a branch.
- QNet proposes neighbors but cannot prove a distinction.
- Do not fill evidence gaps from model memory.
- Identical unvocalized spelling never proves identical vocalization, lemma,
  morphology, or lexical identity.
- A URL or search result is not source verification. The cited entry content
  must have been successfully retrieved and inspected during the run.
- Agents author only schema-approved editorial fields and keyed
  transliterations. Packet facts are script-owned.
- English and Turkish are independently written and rendered to separate files.
- The primary gloss is prominent but never replaces encyclopedia depth.

## Completion report

Report the root envelope, candidate producers, exact branch and Quran coverage,
test and `--check` results, unresolved evidence gaps, and the canonical JSONL
plus both rendered paths. Do not report success before personally inspecting
the rendered entries.
