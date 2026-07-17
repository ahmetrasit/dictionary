# QAC Source Layer

QAC owns positioned Quranic morphology and mechanical occurrence indexing.

It supplies:

- stable positional references;
- root lookup seeds;
- lemma and POS;
- aspect, mood, voice, and measure/form where available;
- mechanical occurrence and co-occurrence indexes for search and graph
  candidate discovery.

It does not own:

- dictionary senses;
- Furūq claims;
- reviewed semantic activation;
- commentary;
- target-language rendering.

## Current Resources

The raw QAC file is currently parked under V4:

```text
_corpus/v4/quranic-corpus-morphology-0.4.txt
```

Do not use `_corpus/v4/qac-morphology-arabic.tsv` as a current input. That
generated TSV name is deprecated/absent in this repo. The first QAC importer
should read `quranic-corpus-morphology-0.4.txt` directly and write source-owned
QAC tables/indexes under `_corpus/qac/` or `_corpus/sources/qac/`.

Future source-owned location:

```text
_corpus/qac/
```

or:

```text
_corpus/sources/qac/
```

The storage location is still open. The contract is not open: occurrence and
mechanical co-occurrence indexes must be QAC-derived, not V4-derived.

## Core Key

Every positioned QAC unit must expose:

```text
qac_ref = surah:ayah:word:morpheme
```

For word-level consumers, a word reference may be derived:

```text
qac_word_ref = surah:ayah:word
```

Use `qac_ref` for morpheme-level activation and morphology. Use `qac_word_ref`
only when a product explicitly needs word-level grouping.

## Root Join Key

QAC root strings should be normalized into an unspaced join key:

```text
root_join_key = strip_spaces(fold_hamza(root_norm))
```

Generated QAC tables may also carry `root_ar`, the spaced Arabic display form
of the root. Use `root_join_key` for equality joins and `root_ar` for display
or audit.

Hamza fold:

```text
أ، إ، آ، ٱ، ء -> ء
```

Do not fold bare alef `ا` into hamza. Bare alef can represent weak-radical
behavior and must not be merged with radical hamza.

## Occurrence And Co-Occurrence

QAC-derived indexes are mechanical source artifacts:

- occurrence counts by root, lemma, POS, measure/form, ayah, and surah;
- root/form/lemma occurrence lists by `qac_ref`;
- window-local root/root co-occurrence pairs in the first implementation;
- root/form/lemma neighborhood lookup tables for graph candidate discovery in
  later QAC-derived indexes.

In `qac_cooccurrence_pairs`, `distance_min` and `distance_max` are token-order
distances among rooted QAC morphemes inside the declared window. They are not
semantic distance and do not mean coactivation.

These indexes do not mean a sense is activated. Reviewed semantic activation
and coactivation belong to `_corpus/activation/` and `_corpus/graph/`.

## V4 Form Bridge

QAC root lookup can seed V4 directly through `root_join_key`, but form-level
lookup must use the derived bridge:

```text
_corpus/qac_v4/
```

The bridge records one row per rooted QAC stem morpheme and says whether it
maps to a unique V4 form handle, several possible handles, or no V4 form. QAC
does not store those V4 handles as source truth.

## First Implementation

1. Parse QAC into normalized row tables defined in `SCHEMA.md`.
2. Build deterministic occurrence counts from parsed rows.
3. Build deterministic co-occurrence windows with configurable window sizes.
4. Validate counts against QAC row totals and spot-check root normalization.
5. Build and audit the QAC-to-V4 bridge before form-level activation.
6. Expose read-only artifacts to V4 lookup, graph candidate generation, and
   activation pilots.
