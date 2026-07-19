# Branch Editorial JSON Writer Prompt

Write the editorial JSONL record bundle for one frozen V4 branch. This is an
encyclopedia-content task, not Markdown assembly and not packet transcription.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
FOCUS_BRANCH={{FOCUS_BRANCH}}
FOCUS_BUNDLE={{FOCUS_BUNDLE}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
ROOT_PACKET={{ROOT_PACKET}}
OUTPUT_RECORDS={{OUTPUT_RECORDS}}
```

Read `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`,
`schema/authored-entry.schema.md`, the full focus bundle, relevant packet source
entries, and the complete sibling roster.

## Task

Return the complete branch-owned record bundle conforming to the authored
JSONL schema. Write deep, independently composed English and Turkish editorial
fields. The renderer will create the separate language entries.

The bundle must provide:

- one `branch` record with keyed identity; image, `what_is_ar`, and
  `what_is_not_ar` transliterations; concept and scope prose; structured
  distinctions; glosses; and the target-language note;
- one to three glosses per language with exactly one `primary`;
- complete preserves, loses, adds, fit, and confusion analysis per gloss;
- a full concept account, what belongs, what does not, and target-language
  distinction note in both languages;
- evidence-backed structured Arabic contrasts with a neighbor anchor,
  language-specific transliteration, shared zone, distinguishing axis, and
  validated evidence references;
- one `branch_source` record for every source handle in the packet branch,
  with an exact selected Arabic quotation, relationship, bilingual
  contribution/explanation/analysis, and complete quotation transliteration;
- one `lexical` identity record for every linked lexical unit, including
  expression, Arabic-sense, and source-phrase transliterations;
- one `branch_lexical` record for every packet branch/lexical link, with
  independently written bilingual meaning and analysis.
- one structured `external_source` record for each non-packet source actually
  used by this branch, including bilingual display title and locator, access
  date, source language, and a short exact supporting excerpt; an Arabic
  excerpt also has separate English and Turkish transliterations.

When several branches are assembled, identical `lexical` identity records are
deduplicated by their stable `(root_id, lexical_unit_id)` key. Their
branch-specific `branch_lexical` records remain separate.

## Mechanical boundary

Do not copy packet-owned root data, Arabic branch image, provenance, source
metadata, lexical metadata, Quran counts, morphology, occurrence rows,
attachments, or ayah text into the records. `selected_quote_ar` is the only
intentional selected packet excerpt and must be an exact packet substring.
Use only keys requested by the
schema. If a mechanical fact is wrong or unavailable, report the packet defect;
do not override it in prose or invent a replacement.

## Evidence discipline

- Treat the V4 branch as frozen.
- Derive English and Turkish accounts independently from Arabic evidence.
- Preserve exact Arabic quotations from supplied sources.
- Do not infer disagreement from absence or routing failure.
- QNet may nominate a neighbor; only V4 or dictionary evidence may establish a
  published contrast.
- Do not use Quran occurrence distribution as branch evidence.
- Do not use Quran frequency, context, translation, or occurrence distribution
  to establish, sharpen, rank, or call a branch meaning or gloss dominant.
- Do not import tafsir, theology, or commentary as lexical evidence.
- Do not make source claims from memory.
- Keep collocational meanings at their governed level.
- In free English prose, pair every Arabic mention with English
  transliteration. In free Turkish prose, pair every Arabic mention with
  Turkish transliteration. The keyed transliteration overlays cover renderer-
  inserted Arabic only; they do not excuse bare Arabic typed inside prose.

## Vocalization and form identity

Run a separate vocalization audit before writing prose or transliteration:

1. Inventory every Arabic root, headword, inflected form, quotation, and
   comparison that will be transliterated.
2. Preserve vocalization supplied by the source. When packet text is
   unvocalized, resolve a reading only from an inspectable, authoritative
   vocalized edition or other supplied evidence. If it cannot be resolved,
   use consonantal/root notation where the schema permits or report an evidence
   gap; never manufacture a smooth reading.
3. Treat identical unvocalized spelling as orthographic identity only. It does
   not establish identical vowels, pronunciation, lemma, morphology, lexical
   category, or meaning. Audit same-spelling sibling units independently and
   state orthographic and phonological relationships separately.
4. Verify person, number, gender, voice, case, construct state, suffixes, and
   article behavior across the complete phrase. Do not propagate one unit's
   transliteration to another merely because their consonants match.
5. Recheck every reuse of a corrected form across concepts, scope, contrasts,
   gloss notes, source quotations, lexical records, and branch-specific
   analysis.

If a non-packet edition is needed to resolve a reading, it must be successfully
opened and inspected, and the complete root artifact must include a structured
`external_source` record for it with access date, source language, exact entry
locator in both display languages, and a short exact supporting excerpt. An
Arabic excerpt also requires English and Turkish transliterations. A search
snippet, inaccessible page, generic landing page, or remembered dictionary
form is not evidence.

## Source availability

For every external source used, verify during the run that the URL exposes the
specific entry content supporting the claim. A maintenance notice, application
shell without entry data, blocked response, unrelated search page, or URL that
merely accepts the intended query does not count as inspection. Remove the
claim, use an accessible reputable source, or report a research gap when the
entry content cannot be read. Never say a source was checked when only its URL
or title was available.

## Gloss discipline

The primary gloss is a compact orientation to the whole branch, not a one-word
requirement or a substitute for the concept account. A multi-word or
multi-clause primary is preferred when it avoids loss. Mainstream translations
and loanwords may be `alternative` or `recognition`, never primary merely
because they are familiar. Test the primary against the complete
source-established branch perimeter; do not let Quran frequency or a familiar
context narrow the gloss.

Full-perimeter fidelity does not turn the primary gloss into a branch inventory.
Write a compact, idiomatic dictionary orientation to the central concept. Keep
derivative lists, source caveats, exceptions, and audit explanations in the
concept, lexical, and source fields. Reject target-language calques that do not
stand naturally as glosses.

Allowed roles are `primary`, `alternative`, and `recognition`. Allowed fit
values are `none`, `narrowing`, `broadening`, `displacement`, and
`drifted_loanword`.

## Output

Write valid JSONL to `OUTPUT_RECORDS`, one object per physical line in schema
order: `branch`, its `branch_source` records, linked `lexical` records,
`branch_lexical` records, then any `external_source` records actually used.
Write standard idiomatic English and Turkish; never flatten Turkish letters or
required Turkish transliteration diacritics to ASCII. Return no Markdown, code
fence, planning note, or packet fact outside schema-approved fields.

Before returning, perform three explicit self-passes over the complete branch
bundle: source/quotation fidelity, vocalization/form identity, and independent
English/Turkish anchor consistency. Correct the records before writing the
final JSONL; do not leave these checks for the orchestrator.
