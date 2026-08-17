# Static Agent Access Layer

The root packets are the source of truth, but they are too large for mobile chat
agents to search directly. The static access layer is a committed, raw-GitHub
friendly mirror under `docs/agent/` and is also deployed to GitHub Pages.

## Build

```sh
python3 scripts/build_agent_access.py
python3 scripts/smoke_agent_access.py
```

Default output:

```text
docs/
  index.html
  agent/
    LOOKUP.md
    START_HERE.md
    manifest.min.json
    b/<bucket>.md
    root/<root_id>/card.md
    root/<root_id>/branches.md
    roots/<shard>.md
    keyword/<shard>.md
    reports/
```

The Pages workflow uploads `docs/`, so the raw GitHub copy and Pages copy have
the same path shape.

## Retrieval Contract

Use `docs/agent/LOOKUP.md` as the first fetch. It contains literal links to all
terminal lookup buckets so link-gated agents do not need to construct URLs.

Targets:

- <=2 fetches to root identity plus branch gist.
- <=3 fetches to grounded branch detail.
- No constructed URL required.
- Terminal lookup buckets are capped at 15KB.
- `LOOKUP.md` has a separate 20KB entrypoint budget because it must enumerate
  all terminal buckets.

## Identity Policy

Arabic-script roots and opaque `root_...` IDs are authoritative. Latin,
Turkish-informed, and Buckwalter aliases are candidate-only recall aids.

If an alias collides, the bucket marks it as `ambiguous` and sets no primary
root. For example, `kalb` and `kalp` must not silently resolve to `ق ل ب`
because `ك ل ب` is also a real corpus root.

## Validation

`scripts/smoke_agent_access.py` reproduces the failure mode that motivated this
layer:

- Pages is not required.
- Fetching is limited to files linked by the previously fetched Markdown.
- Constructed paths are rejected.

The smoke cases include `قلب`, `ق ل ب`, `qalb`, `qlb`, `q-l-b`, `ḳ-l-b`,
`kalb`, `kalp`, and `root_001248`.
