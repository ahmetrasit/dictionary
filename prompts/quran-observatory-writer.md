# Quran Occurrence Observatory Reviewer Prompt

Review the script-generated root-level Quran occurrence observatory. The script
owns packet-backed facts; your job is to resolve explicit review fields and
check linguistic presentation without recreating occurrence data or implying
branch activation.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
ROOT_PACKET={{ROOT_PACKET}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
GENERATED_OBSERVATORY={{GENERATED_OBSERVATORY}}
OUTPUT_FRAGMENT={{OUTPUT_FRAGMENT}}
```

Read `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`,
`schema/entry.schema.md`, the generated observatory, the full QAC section, all
ayah contexts, and every attachment row cited by the generated fragment.

## Required output

Copy the generated section beginning exactly:

```markdown
## Quran occurrence observatory

> These are root-level observations. No occurrence is assigned to a V4 branch.
```

Replace every explicit `REVIEW REQUIRED` field. Return the complete reviewed
section and preserve its required schema order.

## Immutable generated evidence

Do not retype, summarize, reorder, delete, or alter:

- census values;
- form and lemma groupings or counts;
- packet morphology;
- attachment counters and aggregate packet tables;
- QAC references and occurrence order;
- Arabic surfaces, lemmas, frames, attachment IDs, join provenance, or context
  handles;
- Arabic ayah text or ayah order.

If a generated fact is wrong, report a script or packet defect. Do not silently
repair it in prose.

## Review work

1. Supply verified English and Turkish transliterations for every generated
   Arabic form. Follow `TRANSLITERATION_POLICY.md`; raw Buckwalter is not
   reader-facing transliteration.
2. Supply a complete English and Turkish transliteration immediately below each
   complete Arabic ayah.
3. Inspect every `join=unresolved` or `join=unique_root_form_in_ayah` label.
   Preserve the generated label and handles. Add an editorial observation only
   when the supplied packet supports it, and keep the observation separate from
   the immutable occurrence cell.
4. Any optional recurring-pattern prose must cite packet fields or attachment
   units and remain morphological or constructional. Do not create semantic
   occurrence groups.

## Forbidden language and actions

Do not write that an occurrence means, activates, favors, ranks, or probably
belongs to a V4 branch. Do not turn attachment patterns into dictionary senses.
Do not replace generated provenance with freehand labels such as “request
frame.” Do not import a conventional target-language Quran translation to fill
context gaps.

## Output

Return only the complete reviewed observatory section. Do not write branch
entries, activation commentary, or software changes.
