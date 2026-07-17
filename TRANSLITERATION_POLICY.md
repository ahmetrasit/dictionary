# Arabic Anchor And Transliteration Policy

Every Arabic word, root, form, phrase, or individual letter used in a published
English or Turkish entry must retain its Arabic-script anchor and immediately
show a target-language transliteration.

The transliteration helps a reader pronounce and track the same Arabic unit
throughout an entry. It is an identity aid, not a translation and not a gloss.

## Required inline form

In English prose:

```text
<Arabic> (<English transliteration>)
```

Examples:

- سَبِيل (sabīl)
- صِرَاط (ṣirāṭ)
- اِهْدِنَا (ihdinā)
- ه د ي (h-d-y)
- ع (ʿ)

In Turkish prose:

```text
<Arabic> (<Turkish transliteration>)
```

Examples:

- سَبِيل (sebîl)
- صِرَاط (ṣirâṭ)
- اِهْدِنَا (ihdinâ)
- ه د ي (h-d-y)
- ع (ʿ)

Every mention is paired. Do not introduce the pair once and then use bare
Arabic or bare transliteration later in the same section.

## Arabic remains first

Always place Arabic script before transliteration. Do not write only `sabīl`,
`sebîl`, `ṣirāṭ`, or `ṣirâṭ` when the Arabic unit itself is being discussed.
Do not write Arabic script alone inside target-language prose.

For a comparison, anchor both sides:

```text
English: سَبِيل (sabīl) is not صِرَاط (ṣirāṭ) ...
Turkish: سَبِيل (sebîl), صِرَاط (ṣirâṭ) ile aynı kavram değildir ...
```

This rule applies to:

- prose;
- headings and captions;
- table cells;
- gloss explanations;
- contrast and collision notes;
- morphology and form discussions;
- roots and individual letters;
- lexical units and collocations;
- Quran occurrence examples;
- and cross-references to another entry.

## Bilingual shared sections

When one shared table or heading cannot naturally use a language-specific
parenthesis, give separate transliteration fields:

```markdown
- Arabic: صِرَاط
- English transliteration: ṣirāṭ
- Türkçe çevriyazı: ṣirâṭ
```

Shared lexical-unit tables should use separate columns:

```text
Arabic | English transliteration | Türkçe çevriyazı
```

## Exact Arabic quotations

Never insert Latin characters into an exact Arabic source quotation. Preserve
the quotation unchanged, then place both transliterations immediately below
it:

```markdown
> <exact Arabic quotation>

English transliteration: ...

Türkçe çevriyazı: ...
```

The transliteration must cover the complete quoted phrase, not only the
headword. The subsequent English and Turkish explanations remain separate from
the transliteration.

## Quran ayah context

For a complete Arabic ayah used in the occurrence observatory, retain:

1. the complete Arabic ayah;
2. a complete English-oriented transliteration line;
3. a complete Turkish-oriented transliteration line;
4. and, when approved, neutral English and Turkish context lines in which the
   focus-root token is not given a branch-selecting translation.

Do not treat raw Buckwalter encoding as reader-facing transliteration.

## English transliteration

English uses a readable, distinction-preserving scholarly romanization.

| Arabic | English |
|---|---|
| ء | ʾ |
| ب | b |
| ت | t |
| ث | th |
| ج | j |
| ح | ḥ |
| خ | kh |
| د | d |
| ذ | dh |
| ر | r |
| ز | z |
| س | s |
| ش | sh |
| ص | ṣ |
| ض | ḍ |
| ط | ṭ |
| ظ | ẓ |
| ع | ʿ |
| غ | gh |
| ف | f |
| ق | q |
| ك | k |
| ل | l |
| م | m |
| ن | n |
| ه | h |
| و | w; ū when it marks a long vowel |
| ي | y; ī when it marks a long vowel |
| ا / ى | ā when it marks a long vowel |
| ة | -a or -ah in pause; -at in construct |

Use `a`, `i`, and `u` for short vowels and `ā`, `ī`, and `ū` for long vowels.
Assimilation of the definite article may be shown when pronunciation is the
focus, but spelling-based `al-` is acceptable when it makes cross-entry lookup
clearer. Use one choice consistently within an entry.

## Turkish transliteration

Turkish uses the canonical inherited guide at
`docs/upstream/turkish-transliteration-guide.md`. It is adapted to Turkish
orthographic expectations while retaining distinct Arabic phonemes. In
particular, distinct sounds must not be flattened merely because ordinary
Turkish spelling commonly merges them.

Examples of the distinction-preserving requirement include:

- ح (ḥ), ه (h), and خ (ḫ);
- س (s), ش (ş), and ص (ṣ);
- ت (t) and ط (ṭ);
- د (d) and ض (ḍ);
- ك (k) and ق (ḳ);
- ع (ʿ) and ء (ʾ).

Use `â`, `î`, and `û` for long vowels under the Turkish guide.

## Authoring discipline

- Prefer vocalized Arabic when the source or Quran text supplies it.
- Preserve exact source spelling inside quotations.
- Do not guess an ambiguous vocalization merely to manufacture a smooth
  transliteration.
- Verify transliteration against morphology and the cited lexical form.
- Do not auto-convert with a naive character map: short vowels, shadda,
  hamza, tāʾ marbūṭa, the article, and connected forms require linguistic
  judgment.
- Keep the same transliteration for the same form within a language unless a
  documented pronunciation or grammatical difference requires a change.

## Final check

A target-language entry fails publication review if it contains:

- a bare Arabic lexical unit in English or Turkish prose;
- a bare transliterated Arabic term without its Arabic anchor;
- an Arabic comparison in which only one side is transliterated;
- a source quotation without a full transliteration line;
- or one transliteration reused mechanically for both languages when their
  conventions differ.
