# Gloss Menu Policy

This policy defines how much meaning belongs in the app-facing gloss menu versus
the extended corpus notes.

## Goal

The app-facing gloss menu should show distinct, useful language-specific options
without turning every word into a list of near-synonyms. Standardization should
reduce drift, not erase meaning.

## Menu Size

Use this target for each language-specific lexeme meaning menu:

- default render: one selected gloss per word instance
- menu options: usually two or three distinct glosses
- full gloss: corpus-internal semantic range, not app-facing by default
- extended semantic field: preserve extra nuance, near-synonyms, and rationale

Three menu options is a target, not an absolute law. A lexeme can have fewer
when the meaning is clear. Up to five options are allowed when each option is
genuinely distinct and user-useful. Never force a rich Arabic word into three
options if that distorts its meaning; preserve the wider range in notes, and
expand the menu only when the extra option helps the app-facing choice. More
than five options should be flagged for manual review.

`full_gloss`, when present, is the structured place for the fuller semantic
range that should guide review, commentary, projection, and future language
work. It is not polished user prose and should not be shipped by default. Keep
`notes` for raw curation rationale, warnings, avoided terms, review history, and
TODOs.

## Distinctness Rule

Keep a menu option when it represents a distinct semantic angle. Remove or move
it to notes when it mainly repeats another menu option.

Example for `رَبّ`:

```text
menu: Lord; Nurturer; Sustainer
semantic field: authority, ownership, mastery, nurturing, cultivating,
sustaining, bringing to maturity
```

`Master`, `Owner`, and `Cultivator` are not deleted. They are preserved in the
semantic field because they help explain the Arabic, but they do not all need to
be selectable app-facing glosses.

## Revealing Load-Bearing Images

Prefer natural target-language wording, but do not let naturalness erase a
load-bearing Arabic image. When an idiomatic gloss is correct but hides the root
image or semantic mechanism that makes the word intelligible, a slightly heavier
render is allowed if it remains clear to ordinary users. Record the tradeoff in
`full_gloss` or `notes`.

Example: for `مُسْتَقِيم` (`mustaqīm`), a target-language equivalent of
`straight` may be natural but may hide the `q-w-m` standing/upright force. A
render that makes uprightness visible can be preferred when the path image is
central to the ayah.

## No Added Meaning In Defaults

The preferred/base default and the word-instance `default_render` must not add a
meaning that is not carried by the Arabic word in its local context. If a
target-language word or phrase is broader than the Arabic, imports an extra
action, posture, audience, doctrinal association, or modern technical frame, do
not make it the preferred/default render.

Use the narrowest clear target-language wording that remains honest to the
Arabic. Put explanatory expansions, near-misses, recognition terms, and
secondary interpretive angles in `render_options`, `full_gloss`, `notes`,
term-label fields, or phrase-projection notes. A heavier render is allowed under
the load-bearing-image rule only when it reveals meaning already present in the
Arabic, not when it supplies a new meaning to solve a target-language problem.

## Semantic Flags

English word instances carry app-facing semantic booleans:

- `en_has_polysemy`: the Arabic word has multiple live meanings or semantic
  angles in this context.
- `en_has_conceptual_gap`: English has no compact equivalent for the
  Arabic concept, so the render menu is an honest approximation.

Turkish word instances currently keep a Turkish-specific `semantic_flags` field:

- `none`: no special app-facing semantic signal.
- `polysemic`: the Arabic word has multiple live meanings or semantic angles in
  this context.
- `conceptual_gap`: Turkish has no compact equivalent for the Arabic
  concept, so the render menu is an honest approximation.

Polysemy is about the Arabic word and its context. Conceptual gap is about the
target language. A word can be both, but app display should treat
the language-specific conceptual-gap signal as the stronger signal. Every
`true` English boolean should carry a short `en_flag_note` explaining why it was
assigned; every non-`none` Turkish `semantic_flags` value should carry a
`flag_note`.

The English booleans are the authoritative English app-facing semantic flags.
Turkish `semantic_flags` remain authoritative for Turkish until replaced by an
explicit Turkish boolean schema. Legacy
`translation_json_notes` may contain strings such as `polysemic:` or
`dimension_missing:` as review evidence, but those strings do not automatically
set app flags. A seeded `false` means unflagged pending review, not a permanent
claim that no polysemy or conceptual gap exists.

Use `polysemic` only when multiple distinct meanings are live in the local
context, not merely when a word has a broad dictionary range. Mark it when two
or more semantic angles are simultaneously active, the selected render leaves a
meaningful live dimension behind, or the review evidence explicitly keeps
multiple senses active. Do not mark ordinary near-synonyms, a broad field whose
context clearly selects one sense, or a load-bearing image that is already
handled by the chosen render, `full_gloss`, or notes. If the issue is that the
target language lacks a compact equivalent, use `conceptual_gap`.

## Downstream Precedent

Every accepted app-facing gloss choice is a precedent for downstream surahs
unless the review explicitly marks it as local to a specific surface form,
construction, or discourse context. Reviewers should check repeated lexemes and
closely related forms before approving a default render or menu option, because
short-surah decisions can later constrain larger passages.

When a choice is intentionally contextual, record the reason in notes or review
documentation so future batches know whether to reuse the wording or reopen it.

## Surface Rendering

The lexeme menu should store base meanings. Word-instance render options should
adapt those base meanings to the surface form.

Example:

```text
base menu: Lord; Nurturer; Sustainer
surface: رَبِّكَ
render menu: your Lord; your Nurturer; your Sustainer
```

Do not store surface grammar such as `your` in the base meaning menu.

## Surface Force

Do not store punctuation such as `!` inside base meanings or render options.
Exclamation marks in the source usually signal imperative, vocative, emphatic,
or command force. Preserve the linguistic feature separately in the
word-instance `surface_force` field.

Examples:

```text
base menu: Recite; Read aloud; Proclaim
surface_force: imperative
display decision: Recite or Recite!
```

The corpus should be linguistically honest without making punctuation part of
the gloss. A later app projection can decide whether a force value should affect
display punctuation.

## Loanwords And Technical Terms

Arabic transliterations and technical labels should not be primary app-facing
English glosses unless they are also clear everyday English in the target
language. Store them as term labels, transliteration, or notes.

Example:

```text
avoid menu gloss: zabaniya
possible menu glosses: enforcers; seizers; punishment angels
term label: zabaniya
```

## Multilingual Rule

Apply the same structure in every language, but judge clarity inside the target
language. If a target-language word is too broad and includes irrelevant senses,
lower its priority. If an Arabic loanword is technical or unclear to ordinary
users, do not make it the primary gloss.

For Turkish, `Allah` is an explicit exception for `ٱللَّه`: it is ordinary
Turkish and names the intended referent clearly. Other Arabic-origin religious
words should be handled more cautiously. Terms such as `Rab`, `din`, `namaz`,
and `secde` are familiar, but their inherited associations can keep users inside
loaded defaults instead of helping them explore the Arabic word's meaning range.
Prefer clear Turkish explanatory renders as the primary gloss when a loanword
would smuggle in irrelevant senses or doctrinal/cultural shortcuts; keep the
loanword in notes or term-label fields when useful.
