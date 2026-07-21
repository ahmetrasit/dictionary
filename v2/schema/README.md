# V2 Encyclopedia Entry Contract

`encyclopedia-entry.schema.json` defines one authored entry for one root
envelope in one target language. English and Turkish are separate documents;
an agent never fills both languages in the same record.

The root packet owns Arabic branch identity, branch boundaries, dictionary
passages, lexical units, Quran occurrences, grammar, attachments, and QNet
discovery data. Agents own target-language explanation, source synthesis, gloss
judgments, error profiles, and Arabic-neighbor comparison prose. The coordinator
attaches all stable IDs, references, QAC data, ayahs, and attachment data.

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
4. A bounded source synthesis with a separate disagreement object when a real
   disagreement exists.
5. A dictionary basis showing how many distinct dictionaries and passages
   support the branch, which dictionaries they are, and their exact source
   references.
6. A semantic definition plus one to five usable target-language glosses with
   usage roles, applicability notes, and error profiles, followed by one to
   three genuinely rejected or confusable alternatives.
7. One to five Furuq-verified Arabic-neighbor distinctions carrying explicit
   `neighbor_root_id` and `neighbor_branch_id` fields.
8. A reference to the deterministic occurrence artifact plus structured QAC
   forms, morphology, ayahs, occurrences, and aligned attachment detail.
9. Packet-backed lexical realizations and source-grounded structured notes for
   register, constraints, and technical usage.
10. Explicit disputed, rare, or technical evidence qualifiers. The contract
    does not classify a dictionary branch as Quranic or non-Quranic.

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

`semantic_definition` anchors the full branch meaning and is not expected to
serve as natural running prose. Selected glosses are ordered explicitly by
`rank`, starting at 1 without gaps. A common loanword can only occupy rank 2;
it can never be the primary gloss. A gloss may be a word or a word group.
Contextually valid natural translations remain selected candidates; their
narrowing or additions belong in the error profile rather than exclusion.

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

The writer assesses the complete packaged candidate roster and includes every
materially useful distinction, up to five. A single selected neighbor requires
an explicit `single_sufficient` rationale; migrated legacy minimum selections
remain visibly marked until that coverage is reviewed.

## Occurrence Boundary

The occurrence artifact and the entry's occurrence arrays are deterministic
root-level evidence. Agents do not read or author them. Neither the artifact nor
this entry contract assigns a Quran occurrence to a dictionary branch or sense.

Attachment source IDs are never treated as QAC IDs. A deterministic alignment
artifact maps attachment instances onto canonical `qac_word_ref` values using
root/form compatibility and monotonic ayah order. Ambiguous or unmatched rows
remain explicit.

## Agent Fragments

`fragments/` contains the two strict response schemas used by the coordinator:

- `branch-writer.schema.json` for one target-language branch;
- `root-profile.schema.json` for the final short root profile.

Branch agents receive only `branch_id`, `branch_image_ar`, `what_is_ar`, and
`source_phrase_ar` for the focus branch. Each neighbor is projected to
`root_id`, `branch_id`, `branch_image_ar`, and `what_is_ar`. Agent responses do
not contain deterministic counts, names, source rosters, QAC data, ayahs,
attachments, or the coordinator's `inputs_sha256`. The coordinator validates a
response, adds the task hash, and restores evidence-owned fields by stable key.
