# Quran Occurrence Observatory Writer Prompt

Write the root-level Quran occurrence observatory. Its purpose is to help a
reader inspect the root's Quranic deployment and compare it with the complete
branch inventory. It must never perform or imply branch activation.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
ROOT_PACKET={{ROOT_PACKET}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
OUTPUT_FRAGMENT={{OUTPUT_FRAGMENT}}
```

Read `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`,
`schema/entry.schema.md`, the full QAC section, all ayah contexts, and every
relevant attachment-enrichment row.

## Required output

Return one Markdown section beginning exactly:

```markdown
## Quran occurrence observatory

> These are root-level observations. No occurrence is assigned to a V4 branch.
```

Follow the schema through the complete occurrence table.

## Method

### 1. Report the complete census

Give exact morpheme, word, ayah, and surah counts from QAC. Never infer counts
from examples or attachment files.

### 2. Group mechanically

Summarize by observable fields such as:

- surface and lemma;
- part of speech;
- form or measure;
- voice, aspect, and mood;
- governed preposition;
- object/complement type;
- noun relation or modification pattern;
- and recurring attachment frame.

These are morphology and construction groupings, not sense clusters.

### 3. Explain attachments in plain language

Describe what the root word is grammatically connected to and cite attachment
units or sample references. Translate technical grammar into clear English and
Turkish where necessary. Keep exact Arabic forms visible.

### 4. Show the complete occurrences

List all QAC references in Quran order. Include surface, lemma/form,
morphology, observable frame or attachments, and complete Arabic ayah context.
Representative prose examples may highlight constructional variety, but they
do not replace the full list.

Every Arabic surface, lemma, form, root, phrase, or letter in English prose
must carry English transliteration; every one in Turkish prose must carry
Turkish transliteration. Each full Arabic ayah is followed by complete English
and Turkish transliteration lines. Do not expose Buckwalter as reader-facing
transliteration.

### 5. Handle target-language context neutrally

If approved English or Turkish neutral-context lines are supplied, use them
only when focus-root tokens are masked, preserved in Arabic, or otherwise left
without a branch-selecting translation. If no neutral context is supplied,
retain the full Arabic context and do not import a conventional translation to
fill the gap.

## Forbidden language

Do not write:

- “this occurrence means branch ...”;
- “the likely/primary sense here is ...”;
- “this branch is active/inactive in the Quran”;
- occurrence-to-branch probabilities or rankings;
- semantic groups derived from the branch list;
- or target translations of the focus word that pre-decide its branch.

Do not let attachment patterns create a dictionary branch. Do not use
frequency as a reason to emphasize or suppress any V4 branch elsewhere.
Do not leave bare Arabic or bare transliteration in target-language prose.

## Output

Return only the completed root-level observatory section. Do not write branch
entries or an activation commentary.
