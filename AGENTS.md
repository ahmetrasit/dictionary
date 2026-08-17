# Agent Navigation Guide

This repository contains large root packets. Do not begin by searching or
opening every file in `data/output/root_packets/`.

For root lookup, use the static agent access layer:

If the user says "check my dictionary repo for roots x, y, z", resolve each
requested root separately through this access layer, open each candidate card,
and report every candidate root ID inspected. Do not search full root packets
first.

1. Build or open `public/agent/START_HERE.md`.
2. Resolve root IDs through `public/agent/aliases.index.min.json` shards, or
   `public/agent/aliases.min.json` when whole-file search is available.
   For Arabic surfaces/stems/lemmas or lexical forms, use
   `public/agent/lookup.index.min.json` shards as candidate recall.
   Examples: `ح م` -> `aliases/by-initial/u062d-u0645.min.json`;
   `أ ت` -> also try folded `aliases/by-initial/u0627-u062a.min.json`;
   `ٱتَّقُ` form lookup -> also try folded
   `lookup/by-initial/u0627-u062a-u0642.min.json`.
3. Open `public/agent/root/<root_id>/card.md`.
4. If variant strength, source-root provenance, or composite-root membership
   matters, open `public/agent/root/<root_id>/routes.min.json`.
5. For branch audit, open `public/agent/root/<root_id>/branches.select.min.json`,
   choose the branch by `branch_image_ar`, `what_is_ar`, and `what_is_not_ar`,
   then open only the selected row's `source` path.
6. Open `public/agent/root/<root_id>/branches.json` only when QNet branch evidence is needed.
7. Open `public/agent/root/<root_id>/occurrences.compact.json` when Qur'anic usage is needed.
8. Open the full packet only after the compact card, selected branches, and compact occurrences are insufficient.

Arabic-script root identity and opaque `root_...` IDs are authoritative. ASCII
or Latin aliases are candidate lookup aids only. If an alias resolves to more
than one candidate, inspect every candidate card before analysis.
Bare alif `ا` is never authoritative identity for radical hamza `ء`; hamza/alif
folding is candidate recall only. Use `routes.min.json` to audit exact versus
variant V4 routes.

Build the static access layer with:

```sh
python3 scripts/build_agent_pages.py
```

Copy full packets into the Pages artifact only for an intentional heavy build:

```sh
python3 scripts/build_agent_pages.py --include-full
```
