# QAC v0 Schema

Status: draft implementation contract.

This schema describes source-derived QAC artifacts. It is not an activation
schema and not a dictionary schema.

## Tables

### `qac_morphemes`

One row per QAC morpheme.

Required fields:

- `qac_ref` primary key, `surah:ayah:word:morpheme`;
- `qac_word_ref`, `surah:ayah:word`;
- `surah`;
- `ayah`;
- `word_index`;
- `morpheme_index`;
- `surface_ar`;
- `stem_ar`;
- `lemma_ar`;
- `root_raw`;
- `root_join_key`;
- `pos`;
- `morph_features`;
- `aspect`;
- `mood`;
- `voice`;
- `measure`;
- `source_line_no`;
- `source_file_sha256`;
- `parser_version`;

### `qac_words`

One row per positioned word, derived from `qac_morphemes`.

Required fields:

- `qac_word_ref` primary key;
- `surah`;
- `ayah`;
- `word_index`;
- `surface_ar`;
- `morpheme_refs`;
- `root_join_keys`;
- `lemmas_ar`;
- `pos_tags`;
- `measures`;
- `has_multiple_roots`;
- `parser_version`.

### `qac_occurrence_counts`

Mechanical occurrence counts.

Required fields:

- `count_id` primary key;
- `count_scope`: `root`, `lemma`, `root_measure`, `root_pos`, `surah_root`,
  `ayah_root`;
- `root_join_key`;
- `lemma_ar`;
- `pos`;
- `measure`;
- `surah`;
- `ayah`;
- `occurrence_count`;
- `sample_qac_refs`;
- `source_run_id`.

### `qac_cooccurrence_windows`

Window definitions used for mechanical co-occurrence.

Required fields:

- `window_id` primary key;
- `center_surah`;
- `center_ayah`;
- `window_type`: `intra_ayah`, `previous_next_ayah`, `centered_5`,
  `centered_7`, `pericope`, `custom`;
- `start_surah`;
- `start_ayah`;
- `end_surah`;
- `end_ayah`;
- `qac_refs`;
- `source_run_id`.

### `qac_cooccurrence_pairs`

Mechanical pair counts inside declared windows.

Required fields:

- `pair_id` primary key;
- `window_id`;
- `left_key_type`: `root`, `lemma`, `form`, `pos`;
- `left_key`;
- `right_key_type`;
- `right_key`;
- `pair_count`;
- `distance_min`;
- `distance_max`;
- `sample_window_refs`;
- `source_run_id`;

The first implementation emits root/root pairs. Other key types are reserved
for later graph-candidate indexes. Distances are token-order distances among
rooted QAC morphemes inside the declared window.

## Constraints

- QAC indexes must be reproducible from QAC source files.
- No row may contain V4 sense handles except optional lookup cache columns in a
  separate derived table.
- No row may claim activation, dominance, or semantic coactivation.
- Every generated artifact must record source file checksums and parser version.

## Derived Bridge

The current derived V4 lookup table is not stored inside `qac.sqlite`. It lives
under:

```text
_corpus/qac_v4/
```

That bridge may cache V4 form handles for QAC positions, but only as derived
lookup output with explicit unique/ambiguous/unmatched status.
