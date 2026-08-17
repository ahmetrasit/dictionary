# Agent Navigation Guide

This repository contains large root packets. Do not begin by searching or
opening every file in `data/output/root_packets/`.

For root lookup, use the static agent access layer:

1. Open `docs/agent/LOOKUP.md` from raw GitHub or a local checkout. On Pages,
   open `/agent/LOOKUP.md`.
2. Follow only literal links that appeared in fetched Markdown if your fetch
   tool blocks constructed URLs.
3. Use the lookup bucket entry for root identity plus branch gist.
4. Follow the visible `card.md` or `branches.md` link for grounded detail.
5. Open the raw source packet only after the compact linked layer is
   insufficient.

Arabic-script root identity and opaque `root_...` IDs are authoritative. ASCII
or Latin aliases are candidate lookup aids only. If an alias is marked
`ambiguous`, there is no primary root; compare Arabic evidence before analysis.

Build the static access layer with:

```sh
python3 scripts/build_agent_access.py
python3 scripts/smoke_agent_access.py
```
