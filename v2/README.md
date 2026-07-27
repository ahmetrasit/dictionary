# Encyclopedia workflow v2

## Project direction

All further encyclopedia workflow development and production entry runs will use
v2. The legacy root-level workflow remains available as reference material, but
new features and fixes belong in `v2/` unless an explicit migration dependency
requires a legacy change.

Version 2 separates deterministic data functions from agent-authored encyclopedia
content. Each deterministic function gets its own script and generated namespace.

One comprehensive validated entry is the master record. It is projected rather
than copied wholesale to each consumer:

- translation agents receive concept-complete branch boundaries, gloss candidates, and
  preservation/loss/addition/collision notes;
- the user dictionary receives the concept-map definition, one faithful concept
  gloss, separate contextual glosses, and the first semantically typed key distinction;
- the scholar view receives the complete sources, neighbors, morphology,
  occurrences, and attachments.

## Agent entry point

The current production orchestration is
[`orchestration/entry-creation.spec.md`](orchestration/entry-creation.spec.md).
An agent controlling a run must begin with
[`orchestration/README.md`](orchestration/README.md), then read the normative
spec and [`prompts/entry-orchestrator.md`](prompts/entry-orchestrator.md).
[`PRODUCTION_RUNBOOK.md`](PRODUCTION_RUNBOOK.md) contains the exact
repository-root commands.

Start one root by giving a single top-level controller an instruction such as:

```text
Read v2/orchestration/README.md and run the current v2 entry orchestration for
root_000858 in tr. Writer workers: <model and reasoning profile>. Reviewer
workers: <model and reasoning profile>. Worker cap: <optional N>.
```

Use the same form with an explicit envelope list, `first <N> packet envelopes`,
or a through/until boundary for a campaign. Replace placeholders before the run
or name an existing campaign configuration that supplies them. The controller
must not infer worker model, reasoning, service tier, or concurrency settings.

## Compact multilingual gloss workflow

Target-language gloss generation is a separate, thinner workflow under
[`gloss_generation/`](gloss_generation/). It consumes an already validated
Turkish v2 entry and generates only independently reviewed concept, contextual,
and lexical translation glosses with per-gloss semantic error profiles. It
does not recreate the encyclopedia entry or occurrence section.

A cold controller must begin with
[`gloss_generation/RUNBOOK.md`](gloss_generation/RUNBOOK.md), then follow
[`gloss_generation/orchestrator.md`](gloss_generation/orchestrator.md). The
approved initial rollout covers 33 Western bridge and Muslim-audience locales;
English, German, and Turkish form the safe smoke set. Preparation is
deterministic, while target-language writing and independent locale review are
the only delegated roles.

For encyclopedia entry creation, there is no orchestration CLI and intentionally
no `--run-agents` option. Prepared bundles under `v2/work/entry_creation/` are
reused as-is. The controller uses native delegation only for Agent A, when
writer output is missing, and Agent B, which reviews the output and applies only
its own recorded surgical corrections. Do not create script-runner agents,
per-root controllers, or nested workers.

## Current Quran-corpus Turkish checkpoint

As of 2026-07-27, the Quran-corpus Turkish Agent A/B entry build is complete
for all 1,679 available Quranic packet envelopes.

The finalized Turkish entry path is `entries/tr/`. It contains only final
Quran-corpus JSON files plus `manifest.json`; no Markdown, work artifacts,
gloss-generation outputs, or non-Quranic `furuq` roots belong there. It
currently contains 850 final Quranic JSON entries, so 829 Quranic packet
envelopes still need deterministic finalization and promotion before the root
final surface is complete.

`v2/entries/tr/` is the v2 assembly/rendering area. It currently contains the
850 Quranic JSON/Markdown pairs that feed `entries/tr/`, plus 357 non-Quranic
`furuq` Markdown files that are outside the Quran-corpus count and are not
promoted into the root-level final surface.

The complete reviewed staging outputs live under
`v2/work/entry_creation/<root>/tr/output/<root>_entry.json`. They are the source
for deterministic assembly, not the finalized production location. For the
Quran-corpus scope, `v2/work/entry_creation/` currently has:

| Artifact | Count |
| --- | ---: |
| Prepared Turkish work roots | 1,679 |
| Live writer outputs | 1,679 |
| Agent B review outputs | 1,679 |

The Agent B verdict distribution is 865 `pass`, 560 `repair`, and 254
`editorial_review`. `editorial_review` is a completed review artifact but remains
flagged for human judgment under the orchestration contract.

`v2/work/` is resumable local execution state, not master data or production
provenance. Current root-writer tasks use task format 4 and minimal evidence
format `dictionary-v2-agent-root-evidence-v5`. V5 carries authoritative branch
claims separately from optional lexical attestations and includes a mechanical
bare/collocation profile. Older manifests are historical and are ignored;
rerunning `create_entry.py` in prepare mode writes the current task before any
model call.

Current production campaigns queue Quran-corpus roots from
`data/output/root_packets/root_*.json`, not from guessed numeric IDs. The queue
is sorted by root envelope, packet gaps are skipped, and combined envelopes such
as `root_000099--root_000100` are processed as one root workflow. Non-Quranic
`furuq` packets live separately under `data/output/furuq/root_packets/` and do
not count toward the Quran-corpus Turkish completion number. Campaign
orchestration uses only the worker capacity allowed by both the explicit run
configuration and the runtime. Workers have `SUBAGENTS: forbidden`; they do not
launch agents or operate root workflows. Agent A writes only when the writer
output is missing. Agent B reviews the output, records findings first, then
applies only bounded surgical corrections. Agent A is not retained for repair,
and no second review follows Agent B's correction. Packet creation is
coordinator-side deterministic preparation, not a worker session.

## Transitional neighbor-network checkpoint

Dictionary production can start without rebuilding the Quran-SLM global
networks. The audited corpus-only baseline/Neo pair (10,928 cards) and combined
Qurʾan/QAC + Furūq baseline/Neo pair (18,781 cards) both omit the same four
currently accepted, clean focus cards:

- `root_000086/B011`
- `root_000086/B012`
- `root_000086/B014`
- `root_001697/B002`

They are branches inside already represented QAC-attested roots, not missing
roots or Furūq-only roots. Quran-SLM is an optional semantic nomination lane,
not a required canonical input to the current entry-creation command, so these
omissions must not stop initial authoring.

Use QNet as a provenance-labeled discovery fallback, with the actual coverage
kept explicit: B011 and B012 have exact frozen QNet ports; B002 uses the frozen
copy of Latent Activation's comprehensive `v11` post-fix thematic assignment;
B014 has no exact QNet port and can use only indirect root/theme candidates.
QNet never counts as a dictionary, an indirect candidate never becomes
focus-branch evidence, and no QNet result may be labeled as a Quran-SLM/Neo
score.

After the Quran-SLM catalogs are rebuilt to 10,932 and 18,785 cards, run a
reviewed manual enrichment pass on these four master-entry branches. Merge new
semantic candidates by stable `(root_id, branch_id)`, verify every retained
contrast against current Furūq boundaries, preserve the five-neighbor limit,
reconsider which distinction belongs first in the user-dictionary projection,
and revalidate, rerender, and reproject the entry. The full normative policy is
in `schema/README.md`.

For the exact cold-start commands and campaign procedure, use
[`PRODUCTION_RUNBOOK.md`](PRODUCTION_RUNBOOK.md).

## Encyclopedia entry schema

`schema/encyclopedia-entry.schema.json` is the canonical v2 authored-entry
contract. One JSON document represents one root envelope in one target language;
English and Turkish are authored and validated separately.

The packet-bound validator checks the machine shape plus exact root and branch
rosters, packet hashes, exhaustive per-branch dictionary bases, dictionary and
passage counts, gloss ordering, common-loanword placement, Furuq neighbor links,
packet-backed lexical realizations, evidence qualifiers, neighbor coverage, and
deterministically reproduced QAC morphology, ayahs, occurrences, and attachment
alignment:

```sh
python3 v2/scripts/validate_entry.py v2/examples/root_000858.tr.entry.json
```

The normative field rules and ownership boundary are documented in
`schema/README.md`. The Turkish `ṣirāṭ` JSON file is a complete draft fixture,
not a published lexical decision.

The minimal agent workflow, branch evidence package, role boundaries, and
completion criteria are defined in
`orchestration/entry-creation.spec.md`. The production contract uses one
initial root-level writer invocation per root envelope and target language. That
invocation sees the minimal evidence for all accepted branches and returns
branch-shaped fragments plus the short root profile. Semantic workers never
receive Quran ayahs, occurrence data, QAC morphology, attachment records, full
branch packages, the master entry schema, or the orchestration spec.

Older work directories may still contain branch-per-agent manifests and
state-oriented task metadata. Those are not completion authorities for the
current workflow. Reuse the prepared writer and review bundles; do not reprepare
them merely because output is pending. The evidence contains compact source
claims and lexical unit IDs, not raw passages.

The controller follows `prompts/entry-orchestrator.md`, delegates Agent A only
for a missing writer output, and delegates Agent B for review. Agent B writes
its findings before editing and may change only the fields named in bounded,
high-confidence findings. Uncertain or structural issues pause for editorial
judgment without an edit. There is intentionally no `--run-agents` script
option:

```text
Run the v2 entry orchestrator for root_000858/tr.
```

Agent A writes `output/<root>_entry.json`. Agent B reviews its immutable
pre-fix snapshot, writes `review/output/root_review.json`, and either leaves the
writer output unchanged for `pass` or applies only its recorded surgical
corrections for `repair`. Agent A is never called for repair, and the corrected
output receives no second review. Structural/schema validation follows each
authored output. Assembly into `v2/entries/<language>/` is separate downstream
work. Promotion from `v2/entries/<language>/` into root-level
`entries/<language>/` is the final JSON-only publication step for downstream
consumers.

Promote finalized Quran-corpus JSON entries with:

```sh
python3 v2/scripts/promote_final_entries.py --language tr
python3 v2/scripts/promote_final_entries.py --language tr --check
```

Use `--require-complete` only when the language is expected to have every
Quranic packet envelope finalized. The promoter writes
`entries/<language>/manifest.json`, refuses non-Quranic or non-packet roots, and
prunes stale root JSON files from the destination by default.

Export all validated entries as deterministic, one-entry-per-line JSONL:

```sh
python3 v2/scripts/export_jsonl.py --language tr --entries-dir entries/tr
```

Every line is one complete schema-v4 entry. The exporter validates all source
bindings and rejects duplicate entry IDs or mixed languages before writing.

Project one validated entry without exposing unrelated master fields:

```sh
python3 v2/scripts/project_entry.py entries/tr/root_000154.json \
  --projection user_dictionary
```

Export a bounded projection for the whole language corpus:

```sh
python3 v2/scripts/export_jsonl.py --language tr --entries-dir entries/tr \
  --projection translation_agent
python3 v2/scripts/export_jsonl.py --language tr --entries-dir entries/tr \
  --projection user_dictionary
python3 v2/scripts/export_jsonl.py --language tr --entries-dir entries/tr \
  --projection scholar_view
```

Shared Arabic evidence is reused across target languages. A new target language
needs its own root-writer pass because natural glosses and their loss, addition,
and collision profiles are language-specific; it does not need new packets,
Furūq discovery, QAC extraction, QNet nomination, or attachment alignment.
Consumer projections require no further model call.

The current machine contracts support `en` and `tr`. Adding another language also
requires extending the schema enums, transliteration policy, renderer labels, and
CLI language choices before its language-specific agent pass can run.

Each root writer receives the regular
`v2/work/entry_creation/<root>/<language>/input/` package and is instructed not
to inspect any other path. It writes only
`v2/work/entry_creation/<root>/<language>/output/<root>_entry.json`. Agent B
receives the prepared `review/input/` evidence and immutable writer snapshot,
writes `review/output/root_review.json`, and then applies only its recorded
surgical corrections to the live writer output. Copied report-only reviewer
instructions in older prepared bundles are obsolete; the current
`prompts/root-reviewer.md` governs Agent B without requiring the evidence bundle
to be prepared again. Both agent artifacts receive structural/schema
validation. The orchestration controller owns timeouts, process monitoring, and
every deterministic command.
The existing plural `inputs/` directory is coordinator-only state; it is not
part of the writer package.

Every validated branch retains its frozen Arabic branch image, Arabic boundary,
and Arabic source phrase. Downstream consumers receive compact dictionary codes
and dictionary-keyed prose notes; exact references remain internal.
The accepted work artifact exposes the dictionary code roster and concise
dictionary-keyed notes for any distinctive additions, variants, or disputes.
The master also carries root-level QAC occurrences with morphology and aligned
attachment details. Occurrences are not placed under branches unless a separate
evidence layer later establishes that assignment. The translation-agent
projection exposes the full mechanical occurrence layer; the compact user
dictionary exposes its summary and artifact link.

Canonical entry creation accepts only the packet and evidence locations shown
above. Existing draft outputs may be regenerated, but reviewed or published
entries and unmarked Markdown require the explicit `--force-entry` override.
The validated JSON and Markdown are staged together and published as a pair.
Reviewed and published entries also protect their pinned occurrence and shared
branch evidence during prepare-only runs. `--force-entry` is required before
those dependencies can be regenerated.

The root packet and deterministic branch evidence define the branch roster for
an agent task and assembled entry. Packet gaps, missing source claims, missing
source references, or unsafe corpus-wide count claims stop the affected root as
evidence blockers; they do not stop the campaign queue.

The deterministic functions can also run independently:

```sh
python3 v2/scripts/build_branch_evidence.py root_000858
python3 v2/scripts/assemble_entry.py root_000858 --language tr
python3 v2/scripts/render_entry.py v2/entries/tr/root_000858.json
```

The standalone evidence generators apply the same reviewed/published pin guard
when writing their canonical default paths. Use `--check` for reproducibility,
`--output`/`--output-dir` for an unpinned alternate artifact, or explicit
`--force` when intentionally replacing pinned canonical evidence.

## Occurrence renderer

`scripts/render_occurrences.py` renders root-level Quran evidence from an existing
root packet. It does not choose a dictionary branch or sense.

For every exact QAC occurrence form, it emits:

- the lemma, rooted surface, part of speech, and morphology;
- every occurrence in Quran order with its contextual word;
- the reviewed attachment-instance grammar, when safely joined;
- every linked attachment with relation, focus role, counterpart, review status,
  and confidence;
- mechanical grouped attachment patterns; and
- unresolved or missing joins without guessed replacements.

Attachment word numbers belong to their own source and are never interpreted as
QAC references. The renderer first writes a deterministic crosswalk under
`v2/output/alignments/`; downstream occurrence rows retain `qac_word_ref` as
their canonical identity. Corpus-wide counts come only from the QAC census, not
from attachment grammar prose.

Build the input packet separately when it does not exist:

```sh
python3 scripts/root_packet.py "ص ر ط"
```

Render by root ID, root envelope, Arabic root, or an Arabic word found in the
packet:

```sh
python3 v2/scripts/render_occurrences.py root_000858 --language tr
python3 v2/scripts/render_occurrences.py "ص ر ط" --language en
python3 v2/scripts/render_occurrences.py "صراط" --language tr
```

The default output is
`v2/output/occurrences/<root-envelope>.<language>.md`. Use `--check` to verify
that committed output still matches its packet, or `--output` to choose another
generated file. Canonical output pinned by a reviewed or published entry requires
`--force`; `--check` never mutates it.

QAC supplies occurrence forms and morphology. The packet's attachment enrichment
supplies per-instance grammar and syntactic relations. Free-prose attachment
grammar remains visibly labeled as source text; structured labels are rendered in
English or Turkish.
