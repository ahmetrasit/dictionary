# Language Agent Contract

Language-specific corpus agents must use this contract before reviewing,
generating, or changing language-specific gloss files.

## Required Reading Order

Before proposing language-specific glosses, read:

1. `_corpus/docs/07-app-facing-gloss-review-principles.md`
2. `_corpus/docs/03-loanword-policy.md`
3. `_corpus/docs/05-gloss-menu-policy.md`
4. `_corpus/standardized/lexicon/term-registry.tsv`
5. `_corpus/standardized/languages/{lang}/term-labels.tsv`, if present
6. `_corpus/standardized/languages/{lang}/lexeme-meanings.tsv`
7. `_corpus/standardized/languages/{lang}/word-instances.tsv`

Do not rely on chat history for these rules. Treat the files above as the
repeatable contract.

## Required Decision Flow

For each proposed gloss, answer these questions:

1. What meaning should this word convey in the target language?
2. Is there a recognized Quranic term, name, or title users expect to see?
3. Is that term ordinary and clear in the target language, or is it jargon?
4. Where should the term appear?
5. Does the proposed preferred/default render add any meaning that the Arabic
   word does not carry in this context?

If the answer to question 5 is yes, do not use that render as the preferred
base meaning or word-instance default. Keep it only as a secondary option,
`full_gloss` material, a note, a term label, or a phrase-projection warning if
it is still useful.

Allowed term display policies:

- `none`
- `word-detail-only`
- `inline-secondary`
- `inline-parenthetical`
- `word-detail-or-secondary`
- `primary-render-allowed`

The gloss menu answers: what meaning can this instance display?

The term label answers: what known Quranic term, name, or title anchors user
recognition?

Do not put a recognition term into every gloss option. Store the meaning options
cleanly, then let the app projection display the term label separately.

Preferred/base defaults and word-instance defaults must be meaning-honest before
they are explanatory. A target-language phrase that solves ambiguity by adding a
new action, posture, audience, doctrinal association, or technical frame is not a
valid default, even if it sounds natural. Prefer the narrowest clear
target-language wording that does not add meaning; preserve the extra
explanation in notes or secondary options.

For English word instances, also set the English app-facing semantic booleans:

- `has_polysemy`: `true` when the Arabic word has 2+ meanings from different
  semantic domains that are plausibly active in this context. Different domains
  means different physical/abstract categories, different actor/patient
  relationships, or different registers. Synonyms within one domain (sustain /
  nurture / raise) do NOT count. See decision test and examples in the
  translation pipeline prompt.
- `has_conceptual_gap`: `true` when gap_type is 1 (narrower) or 2 (broader).
  Derived field — always consistent with gap_type.

If either English boolean is `true`, provide a short `en_flag_note`. Conceptual
gap is language-specific and takes visual priority over polysemy in app
projection. Turkish currently uses its Turkish-specific `semantic_flags` and
`flag_note` fields; do not infer English flags from Turkish flags or vice versa.
Treat legacy `translation_json_notes` strings such as `polysemic:` and
`dimension_missing:` as evidence to evaluate, not as authoritative app flags. A
seeded `false` means unflagged pending review unless the row has been explicitly
accepted.

## Concept Gap Types (gap_type)

When a target-language word does not map cleanly to the Arabic concept, the
mismatch has a direction. The `gap_type` field encodes this as an integer:

| Value | Label | Meaning | Decision criteria |
|---|---|---|---|
| 0 | exact | Target word covers exactly the Arabic concept | The common translation preserves the full meaning footprint — no dimensions lost, none added. |
| 1 | narrower (subset) | Target word covers LESS than Arabic | The common translation drops one or more meaning dimensions the Arabic carries. The target word is a proper subset of the Arabic meaning. Fix: expand to multi-word rendering. |
| 2 | broader (superset) | Target word covers MORE than Arabic | The common translation imports meanings the Arabic does NOT carry. The target word is a proper superset of the Arabic meaning. Fix: narrow to a more precise phrase. |
| 3 | not applicable | Function words | Particles, pronouns, conjunctions — gap analysis is irrelevant because these have direct structural mappings. |

When `gap_type` is 1 or 2, `has_conceptual_gap` MUST be `true`.
When `gap_type` is 0 or 3, `has_conceptual_gap` MUST be `false`.

### Loanword traps

Arabic loanwords in target languages (e.g., Turkish ibadet, hidayet, namaz)
are the most common source of gap_type = 1 (narrower). The loanword entered
the target language with a subset of the original Arabic meaning. The agent
must compare the Arabic original's full footprint with the loanword's actual
target-language usage, not assume equivalence.

### When uncertain

When genuinely uncertain about gap_type, set it to the type you think is more
likely. Never default to 0 to avoid work — a false 0 hides a concept gap from
the user and is the most dangerous error in the pipeline.

## Output Requirement

When a language agent proposes or reviews a term-bearing word, it must state:

```text
meaning default:
meaning menu:
en_has_polysemy:
en_has_conceptual_gap:
en_flag_note:
term_key:
term_label:
display_policy:
casing_policy:
notes:
```

If no term label is needed, state `term_key: none`.

## Multilingual Rule

Copy the structure across languages, not the English wording.

Each language owns:

- natural meaning glosses
- term label spelling
- display transliteration
- casing policy
- whether a known term is ordinary enough to be primary

Examples:

```text
ٱللَّه (allah)
English meaning default: God
English term label: Allah
English display policy: word-detail-only

Turkish meaning/default render: Allah
Turkish term label: Allah
Turkish display policy: primary-render-allowed
```

```text
شَيْطَان (shaytan)
English meaning default: the adversary
English term label: Shaytan
English display policy: inline-secondary

Turkish meaning default: reviewed Turkish meaning
Turkish term label: Şeytan
Turkish display policy: inline-secondary
```

## Casing Rule

Arabic source forms do not encode uppercase/lowercase, but target-language term
labels do. Use the exact label from `term-labels.tsv` for app display.

Do not mechanically lowercase names, divine names, prophet names, place names,
or recognized titles during projection. If a language expects `Allah`,
`Muhammad`, `Muhammed`, `Pharaoh`, or `Firavun` with uppercase initial letters,
that casing belongs in the language-specific term-label row.

Technical transliteration fields may remain systematic, but user-facing
recognition labels and display transliterations should follow the
language-specific term-label table.
