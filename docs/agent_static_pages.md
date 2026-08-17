# Static Agent Access Layer

The root packets are the source of truth, but they are too large for mobile
chat agents to search directly. The static agent access layer publishes small,
deterministic files that can be served by GitHub Pages or any static host.

## Build

```sh
python3 scripts/build_agent_pages.py
```

Default output:

```text
public/agent/
  START_HERE.md
  index.html
  manifest.min.json
  roots.min.json
  aliases.min.json
  branches.min.jsonl
  occurrences.min.jsonl
  concepts.min.json
  root/<root_id>/card.md
  root/<root_id>/branches.json
  root/<root_id>/occurrences.compact.json
  root/<root_id>/full.json
```

In the default compact build, `full.json` is a small metadata file containing
the exact repository source path and raw GitHub URL for the full packet. Use
`--include-full` only if you intentionally want the Pages artifact to duplicate
all full packet JSON files.

## Retrieval Ladder

Agents should climb this ladder only as needed:

1. `START_HERE.md`
2. `aliases.min.json`
3. `root/<root_id>/card.md`
4. `root/<root_id>/branches.json`
5. `root/<root_id>/occurrences.compact.json`
6. `root/<root_id>/full.json`, then the exact raw packet URL if necessary

## Identity Policy

The canonical identity is the opaque root envelope ID plus the Arabic root fields
from the packet:

```json
{
  "root_id": "root_000001",
  "root_norm": "ح م م",
  "root_join_key": "حمم"
}
```

Aliases are not identity. They are lookup aids with status labels:

- `exact`: exact root ID or exact Arabic packet field.
- `strong`: reversible machine alias, such as Buckwalter root letters.
- `candidate`: normalized Arabic recall alias; compare all returned cards.

Loose ASCII aliases should be added only when they are intentionally reviewed.
They must remain candidate-level because they can erase hamza, weak-letter, and
doubling distinctions.

## GitHub Pages

The included Pages workflow builds the compact `public/agent/` surface from
`main` and uploads it as the Pages artifact. After the branch is merged and
Pages is configured to use GitHub Actions, the mobile-agent entry point will be:

```text
https://<owner>.github.io/<repo>/agent/START_HERE.md
```
