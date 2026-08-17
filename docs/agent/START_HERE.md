# Dictionary Agent Access

This directory is optimized for agents with small fetch budgets, raw-GitHub-only
network access, or link-gated fetching.

Primary entrypoint: [LOOKUP.md](LOOKUP.md)

Cold-start target:
- <=2 fetches to root identity plus branch gist.
- <=3 fetches to grounded branch detail.
- No constructed URL is required.
- Individual lookup files target <=15KB.

Counts:
- Roots: 1679
- Branches: 11637
- Lookup aliases: 10743

If Pages is available, use the same linked flow. If Pages is blocked, use the
raw GitHub copy under `docs/agent`.
