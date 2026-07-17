# Target-Language Gloss And Collision Reviewer Prompt

Review one completed branch block for faithful English and Turkish rendering.
Your responsibility is target-language fit and contrast preservation. The
frozen V4 branch and its Arabic/source audit are inputs, not claims to reopen.

## Inputs

```text
BRANCH_FRAGMENT={{BRANCH_FRAGMENT}}
FOCUS_BUNDLE={{FOCUS_BUNDLE}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
TARGET_LANGUAGE_SOURCES={{TARGET_LANGUAGE_SOURCES}}
OUTPUT_FRAGMENT={{OUTPUT_FRAGMENT}}
```

Read `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`,
`schema/entry.schema.md`, the complete branch fragment, the sibling roster, and
verified neighbor evidence.

## Task

Return the complete revised branch block. Preserve source quotations,
references, V4 identity, and evidence-grounded Arabic boundaries. Improve the
English/Turkish concept accounts only when needed to make them faithful or
clear.

## Review each language independently

Do not assume that an English solution works in Turkish or that a Turkish
solution can be translated into English. For each language:

1. Restate the branch's indispensable dimensions.
2. Test the primary rendering against every dimension.
3. Prefer a multi-word or multi-clause rendering when one word would drop or
   shift a dimension.
4. Test shorter conventional candidates separately.
5. Check actual modern-language usage when criticizing a familiar word.
6. Give one to three final candidates.

Whenever the prose names an Arabic focus, neighbor, form, root, phrase, or
letter, retain the Arabic script and follow it with that language's
transliteration. Do this on every mention and on both sides of every
comparison.

The gloss is not a simplification. It is the most faithful compact rendering
the target language can provide.

## Fit analysis

For every candidate state exactly:

- what it preserves;
- what it loses;
- what it adds;
- and the appropriate fit label:

```text
none
narrowing
broadening
displacement
drifted_loanword
```

Do not use a label without naming the affected facets. A candidate can be
natural and still be conceptually misleading.

Test multi-clause renderings too. They must not introduce an unsupported
sequence, causality, purpose, intensity, agent, doctrinal association, or
register.

## Collision analysis

Check whether a candidate is also conventionally used for:

- another branch of the same root;
- a verified neighboring root;
- an opposite or adjacent Arabic concept;
- or a culturally loaded loanword category.

If so, explain:

1. the shared target-language label;
2. the verified Arabic shared zone;
3. the Arabic distinguishing axis;
4. and the misleading concept a reader may form.

Collision is separate from fit error and may coexist with it. A gloss that is
reasonable in isolation can still erase an important Arabic distinction.

For cases like Turkish `yol` applied to both `صِرَاط (ṣirâṭ)` and `سَبِيل
(sebîl)`, do not invent the distinction from memory. Use the supplied
V4/Furūq and dictionary evidence to say why the two concepts differ, then
explain how `yol` hides that boundary.

## Mainstream translations and loanwords

They may be included for recognition, but:

- never place them first as the primary faithful rendering;
- label them `recognition` or a secondary `alternative`;
- say why they are familiar;
- identify what they lose, add, institutionalize, moralize, or confuse;
- and cite target-language usage evidence when the critique depends on actual
  contemporary meaning.

Do not preserve a misleading loanword merely because readers expect it.

## Research discipline

Use reputable monolingual dictionaries, corpora, and documented translation
practice for target-language claims. Target-language evidence diagnoses the
rendering; it cannot establish or alter the Arabic branch.

If appropriate sources are unavailable, write a visible target-language
evidence note rather than relying on intuition.

## Output

Return only the complete revised Markdown branch block with:

- one to three English candidates;
- one to three Turkish candidates;
- faithful rendering first in both languages;
- complete preserves/loses/adds/error cells;
- and prose distinction notes for every material collision.

Reject the result if it contains bare Arabic lexical material or a bare Latin
transliteration with no Arabic anchor.
