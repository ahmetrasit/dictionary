# Dictionary

Agent root checks start here:
[https://ahmetrasit.github.io/dictionary/agent/START_HERE.md](https://ahmetrasit.github.io/dictionary/agent/START_HERE.md)

Machine-readable access descriptor: [agent-access.json](agent-access.json)

## Agent root lookup quickstart

If you are a chat or coding agent asked to "check my dictionary repo" for an
Arabic root, do not start by searching the full `data/output/root_packets/`
directory. The root packets are large and will waste context.

Use the static agent access layer instead:

If the request is "check my dictionary repo for roots x, y, z", resolve each
requested root separately through this access layer, open each candidate card,
and report every candidate root ID inspected. Do not search full root packets
first. Default to the public static access layer:

[https://ahmetrasit.github.io/dictionary/agent/START_HERE.md](https://ahmetrasit.github.io/dictionary/agent/START_HERE.md)

1. Open the public static entry point above. In a local-only environment, build
   with `python3 scripts/build_agent_pages.py` and then open
   `public/agent/START_HERE.md`.
2. Resolve root IDs through `public/agent/aliases.index.min.json` shards, or
   `public/agent/aliases.min.json` when whole-file search is available. For
   Arabic surfaces/stems/lemmas or lexical forms, use
   `public/agent/lookup.index.min.json` shards as candidate recall.
   Examples: `ح م` -> `aliases/by-initial/u062d-u0645.min.json`;
   `أ ت` -> also try folded `aliases/by-initial/u0627-u062a.min.json`;
   `ٱتَّقُ` form lookup -> also try folded
   `lookup/by-initial/u0627-u062a-u0642.min.json`.
3. Open the compact card at `public/agent/root/<root_id>/card.md`.
4. If variant strength, source-root provenance, or composite-root membership
   matters, open `public/agent/root/<root_id>/routes.min.json`.
5. For branch audit, open `public/agent/root/<root_id>/branches.select.min.json`,
   choose the branch by `branch_image_ar`, `what_is_ar`, and `what_is_not_ar`,
   then open only the selected row's `source` path.
6. Open `public/agent/root/<root_id>/branches.json` only when QNet branch evidence
   is needed.
7. Open `public/agent/root/<root_id>/occurrences.compact.json` when Quranic usage
   is needed.
8. Open the full packet only after the compact card, selected branches, and
   compact occurrences are insufficient.

Arabic-script root identity and opaque `root_...` IDs are authoritative. ASCII
or Latin aliases are lookup candidates only; if an alias returns multiple
candidates, inspect every candidate card before analysis.
Bare alif `ا` is never authoritative identity for radical hamza `ء`; hamza/alif
folding is candidate recall only. Use `routes.min.json` to audit exact versus
variant V4 routes.

Build the static access layer with:

```sh
python3 scripts/build_agent_pages.py
```

See [docs/agent_static_pages.md](docs/agent_static_pages.md) and
[AGENTS.md](AGENTS.md) for the full access contract.

## Current production workflow

Current encyclopedia entry development and production use `v2/`. Legacy
root-level workflow files are reference material and are not the current
orchestration.

An agent that will control an entry run must start at the
[v2 orchestration entry point](v2/orchestration/README.md). That README routes
the controller to:

1. the normative orchestration contract;
2. the controller prompt;
3. the production command runbook; and
4. the authored-entry schema contract.

Do not start from a historical work manifest or invoke the retired branch-writer
or root-profile-writer prompts.

## Current Quran-corpus Turkish status

As of 2026-07-27, the Quran-corpus Turkish entry build is complete at the
Agent A/B working-output stage for every available Quranic packet envelope.

| Item | Count |
| --- | ---: |
| Quranic packet envelopes in `data/output/root_packets/` | 1,679 |
| Prepared Turkish work roots in `v2/work/entry_creation/<root>/tr/` | 1,679 |
| Live writer outputs in `v2/work/entry_creation/<root>/tr/output/` | 1,679 |
| Agent B review outputs in `v2/work/entry_creation/<root>/tr/review/output/` | 1,679 |
| Reviewed Turkish gloss results in `v2/gloss_generation/results/tr/` | 1,679 |
| Final Quranic JSON entries in `entries/tr/` | 850 |

`entries/tr/` is the finalized Turkish JSON location for downstream use. It
contains only final Quran-corpus JSON files plus `manifest.json`; it must not
contain Markdown, work artifacts, gloss-generation outputs, or non-Quranic
`furuq` roots.

`v2/work/entry_creation/<root>/tr/output/<root>_entry.json` is the reviewed
Agent A/B staging output and source of deterministic assembly. It is not the
finalized production path. `v2/entries/tr/` is the v2 assembly/rendering area
and may contain JSON plus Markdown. The root-level final surface is generated
from its validated Quranic JSON files with:

```sh
python3 v2/scripts/promote_final_entries.py --language tr
python3 v2/scripts/promote_final_entries.py --language tr --check
```

The current staging set is complete for the 1,679 Quranic packet envelopes,
while `entries/tr/` still has 829 Quranic packet envelopes awaiting
finalization into root-level JSON. `v2/entries/tr/` also currently contains 357
non-Quranic `furuq` Markdown files; those are outside the Quran-corpus count and
are not promoted into `entries/tr/`.

The completed staging set's Agent B verdicts are 865 `pass`, 560 `repair`, and
254 `editorial_review`. An `editorial_review` file is a completed reviewer
artifact, not a missing output, but it remains explicitly flagged for human
judgment under the orchestration contract.

`v2/gloss_generation/results/tr/` is the reviewed Turkish gloss output surface.
As of 2026-07-27 it is complete for the current Quranic-scoped Turkish gloss
target set: 1,679 accepted result JSON files, 0 pending target roots, and 0
extra accepted files outside that target set. These files are downstream gloss
results, not dictionary-entry completion authority.

## Root packet preparation

Root packet generation is deterministic coordinator work, not agent work. The
current v4 packet preparation script is:

```sh
python3 scripts/prepare_missing_root_packets.py
```

The packet inventory is split by corpus:

- Quranic branch-backed packet envelopes live in `data/output/root_packets/`.
- Non-Quranic `furuq` packet envelopes live in
  `data/output/furuq/root_packets/`.

`data/working/furuq_v4.sqlite` has 1,700 distinct Quranic
`dictionary_entries.root_id` values, but 10 of those do not currently have
Quranic branch-image evidence and therefore are not packet envelopes:
`root_000062`, `root_000077`, `root_000207`, `root_000518`, `root_000525`,
`root_000646`, `root_000667`, `root_000765`, `root_001374`, and
`root_001584`. The branch-backed Quranic packet scope has 1,690 V4 root IDs,
represented as 1,679 workflow envelopes because 11 normalized alias pairs are
composite packages. See
[`COMPOSITE_ROOT_PACKAGES.md`](COMPOSITE_ROOT_PACKAGES.md) for that lookup
table.

`scripts/prepare_missing_root_packets.py` calls:

```sh
python3 scripts/root_packet.py <root_id>
```

for each missing representative root. `scripts/root_packet.py` skips an
envelope when its JSON packet already exists, unless `--force` is passed.

## Start an orchestration

Start the workflow by instructing one top-level controller agent. There is
intentionally no `--run-agents` command and no script that owns worker
lifecycles.

For one root envelope:

```text
Read v2/orchestration/README.md and run the current v2 entry orchestration
for root_000858 in tr. Writer workers: <model and reasoning profile>.
Reviewer workers: <model and reasoning profile>. Use <optional worker cap>
or the runtime's available capacity.
```

For a campaign:

```text
Read v2/orchestration/README.md and run the current v2 entry orchestration
for the first <N> packet envelopes in tr. Writer workers: <model and reasoning
profile>. Reviewer workers: <model and reasoning profile>. Worker cap: <N>.
```

Replace every placeholder with the intended run configuration. A named,
existing campaign configuration may supply the worker settings instead. The
controller must not invent a model, reasoning profile, service tier, or
concurrency limit.

Prepared input bundles under `v2/work/entry_creation/` are reused. Missing
writer or review output is not a reason to prepare them again. Only the
controller may use native delegation: Agent A writes a missing output, then
Agent B reviews it and applies only the bounded corrections recorded in its own
findings. Agent A is never used for repair, and there is no second review.

## Campaign completion

For the current agent workflow, a root is complete when its writer output is
schema-valid, Agent B's review is schema-valid, and Agent B has applied any
recorded surgical correction before returning. A `pass` requires no edit; a
`repair` means Agent B recorded and applied bounded corrections; an
`editorial_review` remains unresolved.

Completion does not depend on workflow states, content hashes, acceptance
copies, publication, or rendered Markdown. Report missing writer outputs and
writer outputs awaiting Agent B directly from the two output locations
documented in
[`v2/orchestration/entry-creation.spec.md`](v2/orchestration/entry-creation.spec.md).
