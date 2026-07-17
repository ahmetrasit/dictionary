# Gloss And Collision JSON Reviewer Prompt

Review one complete authored `branch` JSON object for faithful English and
Turkish rendering. The frozen Arabic branch and source audit are inputs, not
claims to reopen.

## Inputs

```text
BRANCH_RECORD={{BRANCH_RECORD}}
BRANCH_SOURCE_RECORDS={{BRANCH_SOURCE_RECORDS}}
FOCUS_BUNDLE={{FOCUS_BUNDLE}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
ROOT_PACKET={{ROOT_PACKET}}
TARGET_LANGUAGE_SOURCES={{TARGET_LANGUAGE_SOURCES}}
OUTPUT_RECORD={{OUTPUT_RECORD}}
```

Read `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`,
`schema/authored-entry.schema.md`, the full branch record, sibling roster, and
verified neighbor and target-language evidence.

## Review

For each language independently:

1. State the branch's indispensable dimensions.
2. Test the primary gloss against every dimension.
3. Prefer a phrase or coordinated clauses when one word drops or shifts a
   dimension.
4. Test conventional shorter candidates separately.
5. Check actual modern-language usage before criticizing a familiar term.
6. Retain one to three candidates and exactly one `primary`.
7. State precisely what each candidate preserves, loses, adds, and confuses.

Fit values are `none`, `narrowing`, `broadening`, `displacement`, and
`drifted_loanword`. Collision is separate from fit and may coexist with it.
Test multi-clause glosses for invented sequence, causality, purpose, intensity,
agent, register, or doctrinal content.

Use target-language evidence to diagnose a gloss, never to establish or alter
the Arabic branch. Use V4 or dictionary evidence for every Arabic distinction;
QNet alone is insufficient. If usage evidence is unavailable, preserve a clear
research note instead of asserting intuition.

An external dictionary or corpus counts as checked only when the specific
entry content was successfully retrieved and read during the run. A query URL,
search snippet, maintenance page, blocked response, or client-side shell with
no entry text cannot support a usage claim. Remove unsupported attribution or
retain an explicit research gap instead of reconstructing the entry from
memory.

## Preservation

Return the complete revised `branch` record. Preserve stable keys, structured
contrast evidence references, and evidence-grounded boundaries. Treat the
separate `branch_source`, `lexical`, and `branch_lexical` records as evidence;
do not copy their quotations or fields into the branch record. Do not add
packet facts or Markdown. Improve concept prose only where needed for faithful
gloss analysis or reader clarity.

In free English prose, pair every Arabic mention with English
transliteration. In free Turkish prose, pair every Arabic mention with Turkish
transliteration.

Before returning, re-audit every gloss and collision note after any concept or
transliteration change. Confirm that same-spelling Arabic forms have not been
silently treated as the same vocalized lexical item.

## Output

Write one valid JSON object on one physical line to `OUTPUT_RECORD`. Return no
review memo or code fence.
