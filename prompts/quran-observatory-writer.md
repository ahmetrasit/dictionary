# Quran Transliteration JSON Reviewer Prompt

Supply only the schema-approved linguistic fields needed to render the
packet-generated Quran observatory. The script owns the observatory itself.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
ROOT_PACKET={{ROOT_PACKET}}
OUTPUT_RECORDS={{OUTPUT_RECORDS}}
```

Read `TRANSLITERATION_POLICY.md`, `schema/authored-entry.schema.md`, the packet's
full QAC section, all ayah contexts, and any cited attachment rows.

## Required records

Return the exact keyed `quran_form` and `quran_ayah` records required by the
schema. Each `quran_form` record supplies separate bilingual
`lemma_transliteration` and `surface_transliteration` fields. Each `quran_ayah`
transliteration covers the complete ayah. Raw Buckwalter is not reader-facing
transliteration.

Do not write `quran_occurrence` records. The renderer generates every
occurrence row from the packet and reuses the matching exact form group's
surface transliteration. This is mechanical work, not editorial work.

## Mechanical boundary

Do not copy or alter:

- census values, counts, Arabic forms, lemmas, surfaces, or ayah text;
- POS, morphology, constructions, attachments, join provenance, or ordering;
- QAC and ayah metadata beyond the stable key required by the schema;
- any proposed branch assignment, activation, score, probability, or semantic
  grouping.

The renderer joins each keyed transliteration to the packet. Extra packet-owned
fields are a schema error. If a key or Arabic value is wrong, report a packet
or renderer defect instead of compensating in JSONL.

## Transliteration audit

- Derive each form overlay from its exact vocalized lemma/surface group and
  morphology; do not copy a transliteration from a visually similar group.
- Distinguish the isolated packet morpheme surface from its pronunciation in
  full ayah context, including attached articles, pronouns, and case endings.
- Use one documented article convention consistently within the English ayah
  set and the Turkish guide's article convention throughout the Turkish set.
- Read every complete ayah transliteration against the complete Arabic ayah.
  Check shadda, hamza, long vowels, case/construct boundaries, suffixes, and
  repeated same-spelling forms before returning.
- Run a token-integrity pass for accidental internal spaces, dropped letters,
  inconsistent repeated formulas, and unexplained changes of convention. A
  complete ayah count does not compensate for a malformed token.
- Do not infer a lexical branch from vocalization, syntax, translation, or
  context while performing this audit.
- Do not use forms, contexts, or frequencies to establish, sharpen, rank, or
  label a branch meaning or gloss as dominant.

## Output

Write valid JSONL to `OUTPUT_RECORDS`, one schema-conforming object per physical
line, in packet order. Return no Markdown observatory, prose summary, code
fence, or duplicated occurrence facts.
