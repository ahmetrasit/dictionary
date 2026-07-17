# Qnet v2 bridge theme staging

This is the frozen full bridge-theme production substrate for Qnet v2 network
building.

It applies the frozen two-level bridge theme taxonomy to
`incidence_full/raw_keyword_incidence.sqlite`. It is bridge-only; core keywords
remain in the raw incidence DB.

The SQLite file is standalone for production bridge network queries: it embeds
the theme taxonomy, raw bridge keyword -> theme mapping, root/branch nodes,
branch/root evidence, and a compact root-level Quran occurrence layer. Network
builders do not need to read the original replicate files or the separate
mapping TSVs.

Counts:

```text
selected roots:          1,688
branches/nodes:          11,275
raw bridge keywords:     3,522
bridge memberships:      97,758
parent themes:           17
leaf themes:             130
theme-keyword roots:     88,271
root-theme rows:         55,342
branch-theme rows:       73,017
silent bridge nodes:     0
QAC occurrence roots:    1,623
QAC silent roots:        65
QAC root occurrences:    50,560
duplicate root-key groups: 11
ambiguous root IDs:      22
```

Primary files:

- `bridge_theme_staging.sqlite`: queryable staging DB.
- `selected_roots.tsv` and `nodes.tsv`: the full staged root/branch underlay.
- `silent_nodes.tsv`: branches with no bridge-theme evidence in this snapshot.
- `theme_keyword_nodes.tsv`: theme/raw-keyword evidence at branch level.
- `theme_keyword_roots.tsv`: theme/raw-keyword evidence collapsed to roots.
- `theme_inventory.tsv`: theme-level counts for review and network planning.
- `branch_theme_inventory.tsv`: branch activity by theme.
- `root_theme_inventory.tsv`: root-level theme activation summary.

This layer intentionally does not materialize graph edges. The derived
production node/edge DB lives in `../bridge_theme_graph_full/`, built by
`../../scripts/build_bridge_theme_graph.py`.

Use `theme_keyword_roots` for root-level network edges and
`theme_keyword_nodes` / `branch_theme_inventory` as the branch-level underlay
for interpretation, branch activity, and silence checks.

Additional SQLite-only tables:

- `root_index`: root metadata, normalized Arabic root key, branch count, and
  whether the root has QAC occurrences. It also flags duplicate normalized root
  keys via `root_key_is_ambiguous`.
- `quran_root_occurrences`: root-level QAC morpheme occurrences with
  `surah`, `ayah`, word/morpheme position, surface, lemma, POS, and measure.
- `quran_root_key_ambiguity`: duplicate normalized root-key groups. These are
  retained explicitly so no selected root is collapsed or lost.

The Quran occurrence layer is root-level only. It supports surah-filtered
root/theme networks, for example selecting roots occurring in Surah 1 before
joining to `root_theme_inventory`. It does not assert branch-specific Quran
sense activation; that requires a separate occurrence-to-branch assignment
layer. If a query requires strict unambiguous Quran root matching, filter
`root_index.root_key_is_ambiguous = 0`.
