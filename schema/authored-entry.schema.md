# Authored JSONL Entry Contract

The canonical authored artifact is UTF-8 JSONL containing editorial overlays,
not packet rows. The renderer combines it with one root packet and writes:

```text
entries/en/<root_envelope_id>.md
entries/tr/<root_envelope_id>.md
```

```bash
python3 scripts/render_language_entries.py SOURCE.jsonl \
  --packet PACKET.json --output-dir entries [--check] [--force]
```

Every nonblank line is one JSON object with `"schema_version":1`. Duplicate
JSON keys, unknown fields, unknown record types, duplicate stable keys, missing
packet keys, and extra packet keys are errors. JSONL order never defines a
rendered roster; packet order does.

## Ownership

The packet owns root and branch identity, Arabic branch images and boundaries,
the branch/source and branch/lexical rosters, Arabic lexical expressions and
V4 senses, source routing metadata and handles, Quran forms and counts,
occurrence/ayah order, Arabic Quran text, morphology, construction evidence,
and bibliography handles. The renderer selects reader-facing packet facts and
never publishes wholesale packet dictionaries or untranslated packet prose.

The JSONL owns bilingual prose, gloss judgments, structured contrasts,
selected packet-backed source quotations, external sources, and keyed
English/Turkish transliterations. Bilingual values contain exactly `en` and
`tr`. Required prose must be substantive; bare `resolved`, `todo`, `tbd`,
`fixme`, or `placeholder` is rejected.

### Reuse of keyed transliterations in prose

The renderer builds an inventory from every exact Arabic/transliteration pair
known through the packet and structured authored overlays: root, branch image
and boundaries, distinction neighbor, lexical expression/sense/source phrase,
selected branch-source quote, Quran lemma/surface, full ayah, and an Arabic
external-source verification excerpt. Overlay fields themselves are not prose
and are not scanned for reuse.

In substantive English or Turkish prose, an exact known transliteration with
mechanically unmistakable transliteration notation must appear as
`Arabic (transliteration)`. This applies to every occurrence, including after
punctuation and repeated occurrences. A longer known overlay takes precedence
over an overlapping shorter overlay. Prose, keyed transliterations, and exact
Arabic anchor candidates are normalized to Unicode NFC before matching, so
canonically equivalent combining-mark spellings do not bypass the rule and
all match/anchor locations refer to the same normalized text. The mechanical notation set covers
distinctive scholarly/Turkish transliteration characters such as long-vowel
marks, under-dotted consonants, and `ʿ`/`ʾ`. Plain ASCII strings and strings
distinguishable only through ordinary English or Turkish vocabulary are not
policed: treating those as Arabic terms would require heuristic word lists and
would create unacceptable false positives.

### Turkish definite articles

For each exact structured pair where the Arabic field itself begins with the
definite article, the Turkish overlay must follow the repository Turkish
transliteration policy. Arabic vocalization marks, tatwil, and leading
punctuation are ignored when identifying the initial letters. Before a sun
letter (`ت ث د ذ ر ز س ش ص ض ط ظ ل ن`), the overlay begins with the matching
assimilated form, following the general `eC-C` pattern. Before a moon letter it
begins with `el-`. Leading punctuation in the overlay is allowed. Material
after this mechanically checked prefix may retain context-sensitive case,
construct, or recitation inflection. Fields whose exact Arabic counterpart
does not begin with the article are not subjected to this check.

Colon-bearing source handles are opaque. The packet branch `source_refs` field
defines a semicolon-delimited roster, but each extracted handle is thereafter
compared and rendered byte for byte; it is never split on colons.

## Root

Exactly one root record is required. `quran_observations` is optional; when
present it has bilingual arrays, either of which may be empty.

```json
{"schema_version":1,"type":"root","root_envelope_id":"root_000001","transliteration":{"en":"...","tr":"..."},"overview":{"en":"...","tr":"..."},"quran_note":{"en":"...","tr":"..."},"quran_observations":{"en":["..."],"tr":["..."]}}
```

## Branches and Glosses

There is exactly one branch record for every packet `(root_id, branch_id)`.
Contrasts are one shared structured array so both outputs have the same rows.

```json
{"schema_version":1,"type":"branch","root_id":"root_000001","branch_id":"B001","image_transliteration":{"en":"...","tr":"..."},"what_is_ar_transliteration":{"en":"...","tr":"..."},"what_is_not_ar_transliteration":{"en":"...","tr":"..."},"concept":{"en":"...","tr":"..."},"scope_in":{"en":["..."],"tr":["..."]},"scope_out":{"en":["..."],"tr":["..."]},"distinctions":[{"neighbor_ar":"...","transliteration":{"en":"...","tr":"..."},"shared_zone":{"en":"...","tr":"..."},"distinction":{"en":"...","tr":"..."},"evidence":["opaque-packet-source-ref","root_000001/B002","external.source.id"]}],"glosses":{"en":[{"text":"...","role":"primary","preserves":"...","loses":"...","adds":"...","fit":"none","collision":"..."}],"tr":[{"text":"...","role":"primary","preserves":"...","loses":"...","adds":"...","fit":"none","collision":"..."}]},"target_language_note":{"en":"...","tr":"..."}}
```

Every distinction has at least one evidence reference. Each reference must
equal a packet dictionary/branch source reference, an exact packet branch
reference (`root_id/branch_id`), or a declared `external_source_id`. Arbitrary
citations are rejected.

Each language has one to three gloss rows, exactly one `primary`, and the
primary row comes first. Allowed roles are `primary`, `alternative`, and
`recognition`. Allowed fits are `none`, `narrowing`, `broadening`,
`displacement`, and `drifted_loanword`.

## Branch Source Audits

There is exactly one `branch_source` record for every source handle in every
packet branch, keyed by `(root_id, branch_id, source_ref)`, and no extras.

```json
{"schema_version":1,"type":"branch_source","root_id":"root_000001","branch_id":"B001","source_ref":"source:file=x:section=y","selected_quote_ar":"...","quote_transliteration":{"en":"...","tr":"..."},"relationship":"explicit_support","contribution":{"en":"...","tr":"..."},"explanation":{"en":"...","tr":"..."},"analysis":{"en":"...","tr":"..."}}
```

`selected_quote_ar` must contain Arabic script and be a nonempty exact substring of either the matching
packet dictionary row's `entry_text_clean` or that branch's packet
`source_phrase_ar`. The renderer publishes only this selected quotation inside
the branch. Allowed relationships are:

```text
explicit_support
compatible_support
additional_nuance
explicit_disagreement
sole_attestation
no_located_attestation
```

Packet `no_match` is routing metadata, not proof of source silence or
disagreement.

## Lexical Overlays

Lexical identity/transliteration and branch-specific interpretation are
separate. There is exactly one `lexical` record per packet
`(root_id, lexical_unit_id)`:

```json
{"schema_version":1,"type":"lexical","root_id":"root_000001","lexical_unit_id":"lu_001","expression_transliteration":{"en":"...","tr":"..."},"sense_ar_transliteration":{"en":"...","tr":"..."},"source_phrase_transliteration":{"en":"...","tr":"..."}}
```

There is exactly one `branch_lexical` record per packet branch/lexical link:

```json
{"schema_version":1,"type":"branch_lexical","root_id":"root_000001","branch_id":"B001","lexical_unit_id":"lu_001","meaning":{"en":"...","tr":"..."},"analysis":{"en":"...","tr":"..."}}
```

The renderer takes expression, kind, Arabic V4 sense, source phrase, source
handles, and row order from the packet. A lexical unit linked to multiple
branches has one identity record and one interpretation record per link.
`what_is_ar_transliteration`, `what_is_not_ar_transliteration`, and
`sense_ar_transliteration` are required overlays for the exact corresponding
packet Arabic fields.

## Quran Transliteration Overlays

Quran records contain stable keys and transliterations only. Arabic, counts,
lemmas, morphology, positions, handles, observations, and notes are forbidden.

Forms are grouped in packet occurrence order by the exact tuple
`(lemma_ar, surface_ar, pos, morph_features)`:

```json
{"schema_version":1,"type":"quran_form","form_ordinal":1,"lemma_transliteration":{"en":"...","tr":"..."},"surface_transliteration":{"en":"...","tr":"..."}}
{"schema_version":1,"type":"quran_ayah","ref":"1:2","transliteration":{"en":"...","tr":"..."}}
```

The renderer requires the exact derived form ordinal roster and exact ayah
roster. `quran_occurrence` is not an authored record type and is rejected.
Every packet occurrence is still rendered in packet order: the renderer
mechanically finds its exact form group and reuses that `quran_form` record's
`surface_transliteration`. Context-sensitive full-ayah transliteration belongs
only to `quran_ayah`. The form table renders packet `lemma_ar` with
`lemma_transliteration` and packet `surface_ar` with `surface_transliteration`.
Occurrences publish the grouped surface transliteration, not a second
bare-Arabic lemma column. Raw
`morph_features`, Buckwalter `LEM:`/`ROOT:` values, and unknown feature tokens
are never published. Recognized structured features are rendered as concise
localized morphology labels; canonical POS, measure, and form codes appear
only alongside human-readable English/Turkish labels. It may expose exact
word-unit and attachment handles but does not publish attachment grammar,
reasons, notes, or other untranslated packet prose. Any
`unique_root_form_in_ayah` label is mechanical root/form corroboration within
an ayah, never an exact word-position match.

## External Sources

External and target-language sources are structured authored records. IDs are
ASCII identifiers beginning with a letter; URLs are absolute HTTP(S) URLs.
`title` is an exact bilingual object with substantive `en` and `tr` strings of
2-200 characters. Each output uses only its own title and note values.
URLs containing whitespace, control/format characters, angle brackets, or
backslashes are rejected. Link labels escape backslashes and brackets, and
destinations are rendered as angle-delimited Markdown URLs so valid
parentheses cannot terminate a link early. External notes are escaped as
literal inline Markdown.

```json
{"schema_version":1,"type":"external_source","external_source_id":"en.dictionary.example","title":{"en":"Example Dictionary","tr":"Örnek Sözlük"},"url":"https://example.org/entry","note":{"en":"...","tr":"..."},"verification":{"accessed_on":"2026-07-17","source_language":"en","locator":{"en":"Headword: example","tr":"Madde başı: örnek"},"excerpt":"short exact excerpt inspected by the producer"}}
```

`verification` is required. For an English or Turkish source it contains
exactly the following four fields:

- `accessed_on`: a real calendar date in strict `YYYY-MM-DD` form;
- `source_language`: exactly `ar`, `en`, or `tr`;
- `locator`: an exact bilingual `en`/`tr` object whose values are 3-300
  characters identifying a reader-facing headword, section, page, stable entry
  label, or comparable location within the source;
- `excerpt`: 1-500 characters containing the short exact excerpt the producer
  claims to have inspected.

For an Arabic source, `verification` contains those four fields plus exactly
one `excerpt_transliteration` field. The Arabic excerpt must contain Arabic
script, and `excerpt_transliteration` is an exact bilingual `en`/`tr` object
whose nonempty values are 1-500 characters. It is forbidden when
`source_language` is `en` or `tr`. The renderer publishes the exact Arabic
excerpt unchanged and immediately follows it with only the current output
language's keyed transliteration. The transliteration overlay itself is not
scanned as prose; the exact Arabic/transliteration pair does join the known
overlay inventory used to validate later prose reuse.

Title, locator, excerpt, and excerpt-transliteration values are nonempty,
bounded, and control/format-character-free. Locator and excerpt values
cannot be maintenance, shell, query, pending, unchecked, `to be checked`,
`not yet checked`, `TBD after access`, `placeholder entry`, or similar status
placeholders. Rejection compares the entire case-folded value after trimming
surrounding punctuation; an incidental status word inside a substantive source
sentence is not rejected.
These fields make the authored claim auditable; they do not assert that the
renderer fetched the URL or independently proved the excerpt. Rendering is
deterministic and source-independent. Bibliography entries localize and show
the access date, source language, language-selected locator, and inspected
excerpt while applying the same literal-Markdown escaping used for external
notes and transliterations.

The bibliography is derived from all `external_source` records. Contrast
evidence may cite their IDs. No free-form bibliography or arbitrary evidence
reference can bypass validation.

## Output Shape and Safety

Each branch contains, in order: prominent primary gloss, concept, scope and
frozen Arabic boundary, linked lexical units, structured distinctions, gloss
analysis, branch-specific source audits, and a target-language note. The root
Quran appendix contains the census, every derived form, every occurrence,
curated construction evidence, optional root observations, and every complete
Arabic ayah with the language-specific transliteration.

English reads only `en` editorial values and Turkish reads only `tr` values.
Both outputs carry the same `SKELETON` markers and packet-keyed row order.
Renderer labels are localized. Packet-authored English prose such as route
notes, attachment reasons, and grammar explanations is omitted from Turkish.
Canonical gloss role/fit and source-relationship codes are also localized at
render time; JSONL retains the canonical codes shown above.

By default either existing output blocks the run. `--force` replaces only
regular files bearing this marker in their first four lines:

```html
<!-- generated-by: render_language_entries.py schema=1 -->
```

Output paths and language directories may not be symlinks. Both files are
staged before replacement; existing marked files are moved to backups, and any
failure restores the pair so a run cannot leave mixed old/new outputs.
`--check` validates and byte-compares both files without writing, failing on a
missing or stale member. `--check` and `--force` are mutually exclusive.
