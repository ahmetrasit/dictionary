# Qnet v2 raw keyword incidence

This is the frozen full raw keyword incidence snapshot for Qnet v2.

It stores raw `union` keyword incidence for 1,688 parse-valid roots and records
12 empty/invalid roots in `rejected_roots.tsv`. It intentionally does not
materialize edge evidence or per-keyword network TSVs.

Use `raw_keyword_incidence.sqlite` as the frozen lower-level source evidence for
both raw `core` and raw `bridge` keywords. Production bridge networks should be
built from `../bridge_theme_full/bridge_theme_staging.sqlite`, which embeds the
reviewed bridge theme mapping.
