# Complete Root Page Editor Prompt

Assemble and edit one complete bilingual concept-dictionary root page. This is
a root-wide linguistic consistency pass, not another branch-generation pass.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
ROOT_PACKET={{ROOT_PACKET}}
BRANCH_FRAGMENT_DIR={{BRANCH_FRAGMENT_DIR}}
OBSERVATORY_FRAGMENT={{OBSERVATORY_FRAGMENT}}
FINAL_ENTRY={{FINAL_ENTRY}}
```

Read:

- `ENTRY_GENERATION_PLAN.md`;
- `TRANSLITERATION_POLICY.md`;
- `spec.md`;
- `schema/entry.schema.md`;
- the frozen branch roster in the packet;
- every reviewed branch fragment;
- and the Quran observatory fragment.

## Assembly

Create the final root page in this order:

1. schema marker and root title;
2. root identity;
3. complete branch index;
4. branch blocks in frozen `(root_id, branch_id)` order;
5. one root-level Quran occurrence observatory;
6. bibliography and evidence handles.

Write the result to `FINAL_ENTRY`.

## Required checks

### Frozen coverage

- Compare the packet roster with branch begin/end markers.
- Every frozen identity must appear exactly once.
- Do not merge overlapping V4 records.
- Do not omit a branch because it is rare, source-specific, or absent from
  obvious Quranic usage.

### Source audit

- Every material source claim has a reference and Arabic phrase or excerpt.
- Agreement, nuance, explicit disagreement, sole attestation, and absence are
  distinguished accurately.
- Silence is never rewritten as disagreement.
- Source examples stay attributed to their source.

### Boundary consistency

- English and Turkish accounts preserve the same Arabic boundary.
- Sibling entries do not accidentally collapse into identical definitions.
- Cross-references explain overlap without silently merging identities.
- QNet-only comparisons are removed or marked as unverified draft material.

### Rendering quality

- Each language has one to three renderings for every branch.
- The most faithful rendering is first and may be multi-word or multi-clause.
- Mainstream translations and loanwords are secondary and their problems are
  explicit.
- Every fit label names the actual lost or added dimensions.
- Material target-language collisions are explained in both directions across
  affected entries where possible.
- A long rendering has not added unsupported sequence, causality, purpose,
  intensity, agent, or doctrinal content.

### Quran observatory neutrality

- It occurs once, outside branch blocks.
- It contains the complete QAC occurrence list.
- Groupings are morphological or constructional, never semantic activation
  groups.
- No occurrence is assigned, ranked, scored, or colored by branch.
- Focus words in any target-language context line remain neutral or masked.

### Reader clarity

- A reader with no Arabic can understand every essential distinction.
- Arabic phrases remain available as evidence.
- Every Arabic unit in English prose has English transliteration; every Arabic
  unit in Turkish prose has Turkish transliteration.
- No transliterated Arabic term appears without its Arabic-script anchor.
- Exact Arabic quotations and full ayah contexts have complete English and
  Turkish transliteration lines.
- Jargon is translated or briefly explained.
- Repetition across sibling entries is reduced with cross-references, without
  making an entry dependent on hidden knowledge.

## Editing limits

You may improve organization, clarity, consistency, citation presentation,
cross-references, and target-language naturalness. You may not:

- change the V4 inventory or Arabic boundary;
- add evidence from memory;
- resolve an evidence gap silently;
- assign Quran occurrences to branches;
- or promote a conventional gloss because it is shorter or more familiar.

If a substantive problem cannot be fixed from supplied evidence, preserve a
clear editorial note and list it in the completion report.

## Output

Return the complete final Markdown root page, followed by a short separate
completion report containing only:

- expected/authored branch count;
- unresolved evidence gaps;
- unresolved target-language research gaps;
- and any schema violation still present.
