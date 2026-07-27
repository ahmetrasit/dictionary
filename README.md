# Dictionary

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

`v2/gloss_generation/results/tr/` is downstream gloss output. It is not a
dictionary-entry completion authority.

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
