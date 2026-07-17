# Arabic Term And Jargon Policy

This policy controls app-facing English fields in the standardized corpus.

## Rule

App-facing English glosses should be English, not Arabic transliteration or
specialist Arabic grammar labels.

Arabic transliteration belongs in its own layer, not in the English gloss.

For example, a card for زكاة may show:

- Arabic: `زكاة`
- transliteration: `zakah` or `zakat`
- English gloss: `obligatory alms`, `purifying due`, or `almsgiving`

The transliteration helps users recognize the Arabic term. The English gloss
explains what the word means.

Recognition labels are language-specific. Store exact display spelling,
display transliteration, casing, and display policy in:

```text
_corpus/standardized/languages/{lang}/term-labels.tsv
```

The global term registry records term identity and default policy; the
language-specific file records how a user of that language expects to see the
term.

Arabic transliteration remains allowed in:

- transliteration fields
- optional Arabic-term labels
- Arabic-form discussion
- morphology/grammar explanations
- source quotations or variant labels
- proper-name display when the chosen English policy preserves the name

Arabic transliteration is not allowed as the English gloss for an ordinary
lexical item.

## App-Facing Fields

The no-jargon rule applies to:

- language-specific base meaning menus
- preferred glosses
- word-instance selected renders
- translation tokens
- fluent translation spans
- ayah reading text intended as English display
- structure beat English lines

Long interpretive prose may mention Arabic forms when the form itself is being
discussed, but it should not use Arabic transliteration as a replacement for an
English translation.

## Card Layers

Use separate fields for separate jobs:

- `arabic`: Quranic Arabic surface.
- `transliteration`: readable Arabic-form transliteration.
- `english_glosses`: canonical English meaning menu.
- `preferred_display`: default app-facing display for the current language.
- `term_label`: optional recognizable Arabic/Islamic term label.
- `term_display_policy`: where the term label may appear in the app.
- `notes`: linguistic explanation, where Arabic terms may be discussed.

This prevents a word like `zakat` from being forced to do two jobs. It can be
shown as a term label while the actual gloss remains English.

Arabic does not encode uppercase/lowercase, but target languages may require
specific casing. Do not lowercase term labels mechanically. For example,
English and Turkish users expect `Allah` as a display label, and prophet names
such as `Muhammad` or `Muhammed` should preserve language-specific
capitalization.

## Term Registry Status Values

Use these values in the future term registry:

- `term-label`: may appear as an auxiliary label, not as the English gloss.
- `proper-name`: may appear as a name.
- `english-loanword`: accepted as ordinary English only after explicit review.
- `banned-in-gloss`: must not appear in English gloss/display fields.
- `review`: unresolved; do not publish in app-facing gloss fields.

Working default: most Arabic-origin terms are `term-label`, not
`english-loanword`.

## Initial Examples

- `zakah/zakat`: term label only. English gloss should be `obligatory alms`,
  `purifying due`, or another approved English phrase.
- `hajj`: term label by default. English gloss should be `pilgrimage` unless
  the institution name is specifically needed.
- `qiblah`: term label by default. English gloss should be `prayer direction`.
- `jinn`: review. It is common in English, but a beginner-facing card may still
  need `unseen beings`, `spirit beings`, or another explanatory gloss.
- `Quran`: proper name.
- `Allah/Allāh`: term/name layer. Current app-facing English default is `God`.
- `Jahannam`: term label only if needed; English gloss should be `Hell` or an
  approved English menu.
- `zabāniya`: term label only if needed; English gloss should be `the
  enforcers`, `the seizers`, or another approved English phrase.
- `dīn/deen`: term label only if needed; English gloss should be `judgment`,
  `religion`, `way`, `debt-accounting`, etc.
- `taqwā`: term label only if needed; English gloss should be `protective
  awareness`, `God-consciousness`, `self-guarding`, etc.
- `ṣalāh/salah/salat`: term label only if needed; English gloss should be
  `prayer` or `the prayer`.
- `sajdah/sujūd`: term label only if needed; English gloss should be
  `prostration`.
- `shayṭān/shaytan`: term label only if needed; English gloss should be `the
  adversary`, `the devil`, or another approved English phrase.
- Arabic grammar labels such as `wāw al-ʿaṭf`, `lām al-jarr`, `bāʾ
  al-istiʿāna`: use plain English glosses like `and`, `to`, `by`, `with`.

## Publishing Gate

For a surah slice to publish, app-facing English fields should pass a banned
term scan. A banned term may remain only if the field is explicitly marked as
linguistic analysis rather than English display.
