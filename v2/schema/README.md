# V2 Encyclopedia Entry Contract

`encyclopedia-entry.schema.json` defines one authored entry for one root
envelope in one target language. English and Turkish are separate documents;
an agent never fills both languages in the same record.

The root packet owns Arabic branch identity, branch boundaries, dictionary
passages, lexical units, Quran occurrences, grammar, attachments, and QNet
discovery data. The authored entry owns target-language explanation, source
synthesis, gloss judgments, error profiles, verified Arabic distinctions, and
agent observations. Packet evidence is referenced by stable IDs rather than
copied wholesale.

The provenance block binds the entry to the canonical packet, branch-evidence
index, and Furuq database with paths and SHA-256 digests. Occurrence evidence
also carries the digest of its generated Markdown artifact. Validation rejects
drift in any of these inputs.

`generated_by: v2/scripts/assemble_entry.py` marks coordinator-produced entry
JSON. Automatic regeneration replaces only marked drafts; other JSON requires
an explicit force operation.

## Required Shape

Each entry contains:

1. A one-to-two-sentence root profile plus structured semantic organization,
   frozen branch count, and collocation profile.
2. Every frozen packet branch exactly once and in packet order.
3. One short branch summary.
4. A bounded source discussion containing only selected points and examples,
   with a separate disagreement object when a real disagreement exists.
5. A dictionary basis showing how many distinct dictionaries and passages
   support the branch, which dictionaries they are, their roles, and their
   exact source references.
6. One to three selected target-language glosses with error profiles, followed
   by one to three rejected or confusable alternatives.
7. One to five Furuq-verified Arabic-neighbor distinctions carrying explicit
   `neighbor_root_id` and `neighbor_branch_id` fields.
8. A reference to the deterministic occurrence artifact and a sparse list of
   agent-authored observations.

## Dictionary Basis

The dictionary basis is exhaustive for the frozen branch source roster. A
dictionary counts only when at least one exact source reference routed to the
branch belongs to that dictionary. Repeating passages does not increase the
dictionary count.

- `dictionary_count` equals the number of unique `source_id` values.
- `passage_count` equals the number of unique exact `source_ref` values.
- Every branch source reference appears exactly once under `sources`.
- Every listed reference resolves to the declared dictionary in the packet.
- Sources present elsewhere in the root packet but not routed to the branch do
  not appear and do not increase either count.
- QNet is discovery data and never counts as a dictionary.

The renderer will use `dictionary_name` for the visible name and will display
the count before the source table.

## Gloss Rules

Selected glosses are ordered explicitly by `rank`, starting at 1 without
gaps. A common loanword can only occupy rank 2; it can never be the primary
gloss or a third selected gloss. A gloss may be a word or a word group.

Every selected and excluded gloss carries the same error-profile fields:
what it preserves, loses, and adds; its fit category; and its collision risk
in the target language. An excluded row additionally explains why it was not
selected.

## Arabic Neighbors

QNet may nominate a neighbor, but the published distinction must be verified
against Furuq branch boundaries. The visible downstream link is derived as:

```text
(neighbor_root_id/neighbor_branch_id)
```

The focus branch and neighbor branch may share a root, but they cannot be the
same branch. Evidence references remain opaque strings.

## Occurrence Boundary

The occurrence artifact is deterministic root-level evidence. Authored
observations may discuss recurrent grammar, exceptions, or translation risks,
but neither the artifact nor this entry contract assigns a Quran occurrence to
a dictionary branch or sense.

## Agent Fragments

`fragments/` contains the three strict response schemas used by the coordinator:

- `branch-writer.schema.json` for one target-language branch;
- `occurrence-observer.schema.json` for sparse root-level observations; and
- `root-profile.schema.json` for the final short root profile.

Agent responses do not contain deterministic counts, names, source rosters, or
the coordinator's `inputs_sha256`. The coordinator validates a response, adds
that task hash, and the assembler restores evidence-owned fields by stable key.
