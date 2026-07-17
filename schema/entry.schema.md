# Root Entry Schema

This is the required human-readable structure for an authored root page. It is
a content schema, not a database schema. The final file remains ordinary
Markdown so linguists can read and edit it directly.

All Arabic display follows `TRANSLITERATION_POLICY.md`. Arabic script is the
stable anchor; English and Turkish transliterations are language-specific aids.

## File identity

```text
entries/<root_envelope_id>.md
```

Begin every file with:

```markdown
<!-- dictionary-entry-schema: 1 -->
# <Arabic root>

- English transliteration: <...>
- Türkçe çevriyazı: <...>
```

## Root header

Required fields:

```markdown
## Root identity

- Root envelope ID: `<root_envelope_id>`
- Normalized root: `<root_join_key>`
- Arabic root: `<root_norm>`
- English transliteration: `<...>`
- Türkçe çevriyazı: `<...>`
- V4 root records: `<root_id (source_root_norm)>; ...`
- Frozen branch records: `<count>`
- QAC rooted morphemes: `<count>`
- Source snapshot: `<manifest or packet path>`
```

Then include the complete branch roster:

```markdown
## Branch index

| V4 branch | Arabic branch image | English transliteration | Türkçe çevriyazı | Cross-reference note |
|---|---|---|---|---|
| root_000000/B001 | ... | ... | ... | ... |
```

The index must contain every frozen `(root_id, branch_id)` exactly once.

## Branch block

Use stable begin/end markers so a root-wide editor can count and assemble
branches without interpreting prose:

```markdown
<!-- BEGIN BRANCH root_000000/B001 -->
## Branch root_000000/B001 — <branch_image_ar>
...
<!-- END BRANCH root_000000/B001 -->
```

Every branch block requires the following sections.

### V4 identity

```markdown
### V4 identity

- Root record: `root_000000`
- Branch record: `B001`
- Arabic image: ...
- English transliteration: ...
- Türkçe çevriyazı: ...
- English scaffold: ...
- V4 provenance: `origin_corpus=...; status=...; contaminated=...`
```

The provenance line preserves the frozen record. It is not an invitation to
re-adjudicate the branch.

### Hard Arabic-anchor rule

Within English prose, every Arabic word, root, form, phrase, or letter uses:

```text
<Arabic> (<English transliteration>)
```

Within Turkish prose, every Arabic unit uses:

```text
<Arabic> (<Turkish transliteration>)
```

Apply the pairing on every mention, not only the first. Bare Arabic and bare
transliteration are both invalid in target-language prose.

### Concept and boundary

```markdown
### Concept and boundary

#### English

<Complete concept account for a reader with no Arabic.>

#### Türkçe

<Arapça delilden bağımsız olarak yazılmış Türkçe kavram açıklaması.>

#### What belongs to the branch

- ...

#### What does not belong to the branch

- ...
```

The English and Turkish accounts must be independently written from Arabic
evidence. They must preserve the same boundary without copying one another.
Every Arabic unit in each account carries that account language's
transliteration.

### Arabic contrasts

```markdown
### Arabic contrasts

| Arabic neighbor | English transliteration | Türkçe çevriyazı | Shared zone | Distinguishing axis | Evidence |
|---|---|---|---|---|---|
| Arabic unit | ... | ... | ... | ... | V4/source refs |
```

Include sibling, form, collocational, or cross-root contrasts only when they
materially clarify the branch. A QNet suggestion is not evidence.

### Lexical units and examples

```markdown
### Lexical units and examples

| Arabic expression | English transliteration | Türkçe çevriyazı | Kind/form | Meaning in this branch | Source/example |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |
```

Keep collocational units at their governed level. Do not promote a
constructional result into another bare-root branch.

### Source audit

Create one source subsection for each materially relevant dictionary:

```markdown
### Source audit

#### <Dictionary name>

- Relationship: `explicit_support | compatible_support | additional_nuance | explicit_disagreement | sole_attestation | no_located_attestation`
- Reference: `<stable source_ref>`
- Contribution: <what this source supplies>

> <Exact Arabic source phrase or excerpt>

English transliteration: ...

Türkçe çevriyazı: ...

English explanation: ...

Türkçe açıklama: ...

Examples or special analysis: ...
```

Use more than one subsection when a dictionary contributes materially
different passages. Do not manufacture a disagreement from silence or a
different organizational choice.

Never alter the Arabic quotation to insert transliteration. Transliterate the
complete quotation on the two following lines.

### English renderings and confusions

```markdown
### English renderings and confusions

| Rendering | Role | Preserves | Loses | Adds | Fit error | Collision or misleading concept |
|---|---|---|---|---|---|---|
| ... | primary | ... | ... | ... | none | ... |
| ... | alternative | ... | ... | ... | narrowing | ... |
| ... | recognition | ... | ... | ... | drifted_loanword | ... |
```

### Turkish renderings and confusions

```markdown
### Turkish renderings and confusions

| Karşılık | Rol | Koruduğu | Eksilttiği | Eklediği | Uyum hatası | Karıştırdığı kavram veya yanıltıcı sonuç |
|---|---|---|---|---|---|---|
| ... | primary | ... | ... | ... | none | ... |
| ... | alternative | ... | ... | ... | displacement | ... |
| ... | recognition | ... | ... | ... | drifted_loanword | ... |
```

Each table contains one to three rows. A rendering may be one word, a phrase,
or coordinated clauses. Put the most faithful usable rendering first.

Allowed role values:

```text
primary
alternative
recognition
```

Allowed fit-error values:

```text
none
narrowing
broadening
displacement
drifted_loanword
```

Target-language collision is described in the final column and can coexist
with any fit-error value.

Mainstream translations and loanwords may appear only as `recognition` or, when
genuinely useful, a secondary `alternative`. They may never replace the
first-class concept account or primary faithful rendering, and their problem
must never be left blank.

### Target-language distinction notes

After the tables, explain any important collision in prose:

```markdown
### Target-language distinction notes

#### English

<Why a familiar English label collapses or shifts this concept.>

#### Türkçe

<Yaygın Türkçe karşılığın hangi ayrı Arapça kavramları birleştirdiği ve
odaktaki kavramın onlardan neden farklı olduğu.>
```

Every Arabic focus or neighbor named in these notes retains Arabic script and
receives the transliteration appropriate to the note language. For example,
English uses `سَبِيل (sabīl)` and `صِرَاط (ṣirāṭ)`; Turkish uses `سَبِيل
(sebîl)` and `صِرَاط (ṣirâṭ)`.

If there is no material collision, say so briefly rather than inventing one.

## Quran occurrence observatory

This is one root-level section after all branch blocks. It must never appear
inside an individual branch block.

Required shape:

```markdown
## Quran occurrence observatory

> These are root-level observations. No occurrence is assigned to a V4 branch.

### Census

- Rooted morphemes: ...
- Words: ...
- Ayahs: ...
- Surahs: ...

### Forms and lemmas

| Arabic lemma/form | English transliteration | Türkçe çevriyazı | POS/morphology | Count | Observed constructions |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

### Attachment and construction observations

- ...

### Complete occurrences

| QAC ref | Arabic surface | English transliteration | Türkçe çevriyazı | Lemma/form | Morphology | Observable frame/attachments | Ayah context handle |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... |
```

For every full ayah context, show the exact Arabic ayah followed by a complete
English transliteration line and a complete Turkish transliteration line. Raw
Buckwalter encoding is not acceptable reader-facing transliteration.

When English or Turkish context lines become available, mask or preserve the
focus-root word without selecting a branch-specific translation. Never add an
activation, probability, or likely-branch column.

## Bibliography

End with:

```markdown
## Bibliography and evidence handles

### Classical dictionaries

- ...

### Quran morphology and attachment evidence

- QAC packet: ...
- Attachment packet: ...

### Target-language usage sources

- ...
```

Only list sources actually used.

## Structural completion rules

A final root file is structurally complete only when:

1. the branch-index count equals the frozen V4 branch count;
2. every index identity has exactly one matching begin/end branch block;
3. every branch contains both concept accounts, source audit, both rendering
   tables, and target-language distinction notes;
4. each rendering table contains one to three candidates;
5. the Quran observatory occurs once and outside all branches;
6. every Arabic unit in target-language prose is paired with the appropriate
   target-language transliteration;
7. every exact Arabic quotation and ayah context has complete English and
   Turkish transliteration lines;
8. and no unresolved placeholder is hidden or silently deleted.

The schema governs shape. Linguistic truth still comes from the evidence and
the editorial plan.
