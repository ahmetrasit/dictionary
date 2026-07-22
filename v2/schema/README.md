# V2 Encyclopedia Entry Contract

`encyclopedia-entry.schema.json` defines one authored entry for one root
envelope in one target language. English and Turkish are separate documents;
an agent never fills both languages in the same record.

The root packet owns Arabic branch identity, branch boundaries, dictionary
passages, lexical units, Quran occurrences, grammar, attachments, and QNet
discovery data. Agents own target-language concept-map synthesis, source
discussion, gloss judgments, error profiles, verified neighbor-relation types,
and Arabic-neighbor comparison prose. The coordinator attaches all stable IDs,
references, QAC data, ayahs, and attachment data.

The provenance block binds the entry to the canonical packet, branch-evidence
index, and Furuq database with paths and SHA-256 digests. Occurrence evidence
also carries the digest of its generated Markdown artifact. Validation rejects
drift in any of these inputs.

`generated_by: v2/scripts/assemble_entry.py` marks coordinator-produced entry
JSON. Automatic regeneration replaces only marked drafts; other JSON requires
an explicit force operation.

## Master Entry and Consumer Projections

The validated schema-v4 JSON is the single comprehensive master entry. This
README is its normative human contract, and `encyclopedia-entry.schema.json` is
its machine shape. Consumer payloads are deterministic projections; they never
become independent authored records and each carries a SHA-256 binding to its
master entry.

`v2/scripts/project_entry.py` exposes three projections:

- `translation_agent`: branch identity and Arabic boundaries, the target-language
  definition, selected and excluded gloss candidates, and each candidate's
  preservation, loss, addition, fit, applicability, and collision notes. It omits
  dictionary sources, Arabic-neighbor evidence, morphology, occurrences, and
  attachments.
- `user_dictionary`: the concept-map definition, one faithful concept gloss,
  separate contextual gloss text, and one key Arabic distinction per branch. It omits source apparatus,
  error profiles, morphology, occurrences, and attachments.
- `scholar_view`: the complete validated entry, including full sources, neighbors,
  lexical realizations, morphology, occurrences, and aligned attachments.

When `arabic_neighbor_distinctions` is nonempty, its first row is the key
distinction used by the compact user projection. Writers order the array by reader-facing importance;
the remaining rows preserve the fuller comparison set for scholars. Entries
authored before this ordering rule can be projected mechanically, but their first
choice remains an editorial review target.

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
6. A concept-complete semantic definition plus one to five usable target-language glosses with
   usage roles, applicability notes, and error profiles, followed by one to
   three genuinely rejected or confusable alternatives.
7. Zero to five Furuq-verified Arabic-neighbor distinctions carrying a primary
   semantic `relation_type` and explicit `neighbor_root_id` and
   `neighbor_branch_id` fields.
8. A reference to the deterministic occurrence artifact plus structured QAC
   forms, morphology, ayahs, occurrences, and aligned attachment detail.
9. Packet-backed lexical realizations and source-aware discussion prose that
   preserves explicitly attributed examples, disputes, restrictions, and
   implications.
10. Optional structured notes only when their source ownership is supplied
    upstream; the root writer does not invent a second note roster from the
    already synthesized source phrase.

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

New root-writer entries store a structured `concept_map`. Its facets distinguish
core meaning, specialization, extension, associated use, example, and source
variant; `semantic_definition` remains the reader-facing rendering of that map.
For a guidance branch that includes showing a path, bringing someone onto it,
and enabling progress along it, the core must retain all three rather than
collapse them to “lead to the right path.” The concept gloss is separate from
contextual running-text glosses. Compatibility ranks are derived only for legacy
consumers. A common loanword
may remain in legacy entries, but the current root-writer contract accepts only
`loanword_status: none`. A gloss may be a word or a word group.
Contextually valid natural translations remain selected candidates; their
narrowing or additions belong in the error profile rather than exclusion.
Internal conditions remain explicit: an offered indication is not identical to
its acceptance or realized result, and a human guide's capacity need not equal
an evidence-supported divine or causative use. Applicability and error profiles
state which part of that conditioned map each gloss can carry.

All authored definitions, source discussions, glosses, root summaries, and
neighbor prose use clear ordinary target-language wording. Arabic script,
transliterated Arabic, and borrowed Arabic technical labels cannot substitute
for explanation. This is a clarity rule, not an attempt to purge historically
naturalized vocabulary from the target language: it rejects terms used as
unexplained source-language shorthand, such as Turkish `tevfik` or `hidayet` in
place of describing what is enabled or how guidance operates. A rejected
loanword may remain in the scholar-facing excluded-gloss apparatus solely to
document why it is unsuitable; it is never a selected gloss or a substitute for
the concept explanation.

Every selected and excluded gloss carries the same error-profile fields. Loss,
addition, and collision are null when absent instead of forcing boilerplate.
Per-lexical-unit target renderings are stored separately from branch concept and
contextual glosses.

## Arabic Neighbors

QNet, Neo, and other network layers may nominate a neighbor, but the published
relation and distinction must be verified against the supplied Furuq branch
concepts. The primary `relation_type` is one of `synonym`, `near_synonym`,
`antonym`, `polarity_pair`, `near_neighbor`, `same_field`, `thematic`, or
`other`. The visible downstream link is derived as:

```text
(neighbor_root_id/neighbor_branch_id)
```

The focus branch and neighbor branch may share a root, but they cannot be the
same branch. Evidence references remain opaque strings.

The writer assesses the complete packaged candidate roster and includes every
materially useful distinction, up to five. If none sharpens the branch boundary,
the distinction array is empty and coverage is `none_useful`. A single selected
neighbor requires an explicit `single_sufficient` rationale; migrated legacy
minimum selections remain visibly marked until that coverage is reviewed.

The candidate roster is built deterministically. It combines packet-carried QNet
neighbors, raw core overlap, raw bridge overlap, branch-theme overlap, and every
sibling branch in the same root envelope. The four cross-root lanes are sampled
round-robin into at most eight unique stable `(root_id, branch_id)` candidates;
siblings are then appended, and duplicate identities and discovery bases are
merged. Keyword rows are ranked by overlap count and replicate consensus; theme
rows are ranked by shared-theme count and two-replicate support. A candidate is
exposed to the writer only when its Furūq branch exists and is both `accepted`
and `contaminated: no`. The writer—not the discovery query—decides which
candidates are materially useful, authors the actual contrast, selects at most
five, and puts the key reader distinction first.

### Deferred Quran-SLM enrichment (2026-07-21)

Quran-SLM is an optional semantic candidate-nomination lane. Its absence is not
a failure of the master-entry contract, and it never replaces Furūq verification
of a published branch distinction. The current corpus-only and combined global
baseline/Neo catalogs omit `root_000086/B011`, `root_000086/B012`,
`root_000086/B014`, and `root_001697/B002`. These are missing branch cards in
already represented QAC-attested roots, not missing roots.

Initial entry work proceeds without rebuilding those networks. QNet may nominate
fallback candidates, but the fallback level must be understood correctly:

- B011 and B012 have exact branch ports in the frozen QNet snapshot;
- B002 has an exact thematic assignment in the frozen copy of Latent
  Activation's comprehensive `v11` post-fix record;
- B014 has no exact QNet port, so only root/theme-level indirect nomination is
  available.

An indirect QNet candidate is not evidence about the focus branch and a QNet
score is never relabeled as Quran-SLM/Neo similarity. Every published contrast
still resolves to an accepted, uncontaminated Furūq neighbor and uses Furūq
branch evidence. `neighbor_coverage.assessment` describes the complete roster
actually packaged for that authoring run; it does not claim that every optional
future discovery network has been consulted.

After the Quran-SLM rebuild, the four affected entries receive a reviewed manual
enrichment pass. Merge candidates by stable `(root_id, branch_id)`, discard
duplicates, retain only materially useful Furūq-verified distinctions, keep at
most five, and reassess the authorial order because item 0 feeds the compact
user-dictionary projection. Then revalidate the master JSON, rerender it, and
regenerate all projections. Do not silently overwrite a reviewed or published
entry.

## Occurrence Boundary

The occurrence artifact and the entry's occurrence arrays are deterministic
root-level evidence. Agents do not read or author them. Neither the artifact nor
this entry contract assigns a Quran occurrence to a dictionary branch or sense.

Attachment source IDs are never treated as QAC IDs. A deterministic alignment
artifact maps attachment instances onto canonical `qac_word_ref` values using
root/form compatibility and monotonic ayah order. Ambiguous or unmatched rows
remain explicit.

## Agent Fragments

`fragments/` contains the strict authored-fragment schemas used by the
coordinator:

- `root-writer.schema.json` for the reduced one-call production response;
- `root-reviewer.schema.json` for evidence-grounded semantic issues or pass;
- `branch-writer.schema.json` for one target-language branch-shaped fragment;
- `root-profile.schema.json` for the final short root profile.

Production authoring uses one root-level writer invocation per root envelope and
target language, but the authored content remains branch-shaped. For each focus
branch, the writer receives the branch identity and boundary plus a compact
claim roster projected from accepted lexical units. Each neighbor is projected to `root_id`,
`branch_id`, `branch_image_ar`, and `what_is_ar`. The root response is a thin
transport envelope containing branch fragments and the root profile; it is not a
new master data schema.

The response carries stable claim and lexical-unit IDs but omits numeric ranks, branch
counts, duplicated branch summaries, coverage enums, collocation defaults,
known transliterations, and excluded-gloss display reasons. The coordinator
derives these, splits the accepted response into strict branch/root-profile
fragments, and restores evidence-owned fields by stable key. Claim IDs expand to
precise source names and references. The writer receives no transliteration or
approved name values. Missing used anchors and protected proper names enter
separate resumable review files.

Agent responses do not contain deterministic names, source rosters, QAC data,
ayahs, attachments, or the coordinator's `inputs_sha256`. The master entry
schema, full transliteration policy, and orchestration spec are coordinator-only
contracts and are not part of the model-facing package.
