# Agent Navigation Guide

This repository contains large root packets. Do not begin by searching or
opening every file in `data/output/root_packets/`.

For root lookup, use the static agent access layer:

1. Build or open `public/agent/START_HERE.md`.
2. Resolve exact Arabic forms or root IDs through `public/agent/aliases.min.json`.
3. Open `public/agent/root/<root_id>/card.md`.
4. Open `public/agent/root/<root_id>/branches.json` only when branch evidence is needed.
5. Open `public/agent/root/<root_id>/occurrences.compact.json` when Qur'anic usage is needed.
6. Open the full packet only after the compact card, selected branches, and compact occurrences are insufficient.

Arabic-script root identity and opaque `root_...` IDs are authoritative. ASCII
or Latin aliases are candidate lookup aids only. If an alias resolves to more
than one candidate, inspect every candidate card before analysis.

Build the static access layer with:

```sh
python3 scripts/build_agent_pages.py
```

Copy full packets into the Pages artifact only for an intentional heavy build:

```sh
python3 scripts/build_agent_pages.py --include-full
```
