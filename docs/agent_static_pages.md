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
public/
  index.html
  agent-access.json
  llms.txt
  agent/
    START_HERE.md
    index.html
    manifest.min.json
    roots.min.json
    aliases.min.json
    aliases.index.md
    aliases.index.min.json
    aliases/by-initial/<bucket>.min.json
    lookup.index.min.json
    lookup/by-initial/<bucket>.min.json
    root/<root_id>/card.md
    root/<root_id>/routes.min.json
    root/<root_id>/branches.select.min.json
    root/<root_id>/branches.json
    root/<root_id>/branch/<source_root_id>--<branch_id>.source.json
    root/<root_id>/occurrences.compact.json
    root/<root_id>/full.json
```

The repository root also includes:

```text
AGENT_START.md
agent-access.json
```

These small committed files point generic agents to the public static access
layer before they choose a heavier repository traversal path.

In the default compact build, `full.json` is a small metadata file containing
the exact repository source path and raw GitHub URL for the full packet. Use
`--include-full` only if you intentionally want the Pages artifact to duplicate
all full packet JSON files.

Global `branches.min.jsonl`, `occurrences.min.jsonl`, and `concepts.min.json`
are omitted from the default build because they are bulk analysis files, not the
normal agent lookup path. Add `--include-bulk` only for an intentional heavy
artifact.

## Retrieval Ladder

Agents should climb this ladder only as needed:

1. `START_HERE.md`
2. `aliases.index.min.json` shards, or `aliases.min.json` when whole-file search
   is available
3. `root/<root_id>/card.md`
4. `root/<root_id>/routes.min.json` when variant strength, source-root
   provenance, or composite-root membership matters
5. `root/<root_id>/branches.select.min.json`, then
   the selected row's `source` path for branch audit
6. `root/<root_id>/branches.json` only when QNet branch evidence is needed
7. `root/<root_id>/occurrences.compact.json`
8. `root/<root_id>/full.json`, then the exact raw packet URL if necessary

## Batch Root Requests

If the user says "check my dictionary repo for roots x, y, z", resolve each
requested root independently through the root-alias shard rule, open every
candidate card needed to disambiguate it, and report every candidate root ID
inspected. Do not search or open full root packets first.

## Route Audit Path

Use `routes.min.json` when the question depends on exact versus variant V4
routing, source-root membership inside a composite envelope, or reviewed weak
routes such as `weak_final_variant_candidate` and
`weak_medial_variant_candidate`. Do not decide these questions from a folded
alias alone.

## Branch Audit Path

Agents may already know the broad branch concept from training data or from the
user's working context. In that case they should not read the full packet.

Use `branches.select.min.json` to choose a branch by:

- `branch_image_ar`
- `what_is_ar`
- `what_is_not_ar`

After choosing the branch ID, open only
the selected row's `source` path. That file carries the source phrase and source
references needed for a final audit. The source filename includes the source root
ID because composite envelopes may repeat branch IDs such as `B001`.

## Sharded Lookup

`aliases.index.min.json` points to root/root-ID alias shards.
`lookup.index.min.json` points to broader Arabic form shards, including lexical
expressions and QAC surface/stem/lemma forms. Form lookup aliases are
candidate-level recall aids; confirm identity against root cards.

For root aliases, open `by-initial/uXXXX-uYYYY.min.json`, where `XXXX` and
`YYYY` are the four-digit Unicode code points of the first two lowercased,
non-space, non-diacritic query characters. One-character aliases use
`uXXXX.min.json`.

For broader form lookup, use the first four non-space, non-diacritic query
characters. For hamza/alif forms (`ء أ إ ؤ ئ آ ا ٱ`), also try the same bucket
after candidate-only folding those letters to `ا`, then inspect plausible
candidate cards.

Examples:

- Root `ح م م`: `aliases/by-initial/u062d-u0645.min.json`
- Root `أ ت ي`: exact `aliases/by-initial/u0623-u062a.min.json`; folded `aliases/by-initial/u0627-u062a.min.json`
- Weak final query `د ع ي`: inspect weak-letter candidates such as `د ع و` by card comparison.
- Form `ٱتَّقُ`: exact `lookup/by-initial/u0671-u062a-u0642.min.json`; folded `lookup/by-initial/u0627-u062a-u0642.min.json`

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

Bare alif `ا` is never authoritative identity for radical hamza `ء`; hamza/alif
folding is candidate recall only. QAC join-key normalization folds hamza forms
to `ء`, while agent retrieval may also expose folded recall aliases that must be
checked against root cards and `routes.min.json`.

## GitHub Pages

The included Pages workflow builds the compact `public/` surface from `main`,
smoke-tests key files, and uploads it as the Pages artifact. The live
mobile-agent entry point is:

```text
https://ahmetrasit.github.io/dictionary/agent/START_HERE.md
```
