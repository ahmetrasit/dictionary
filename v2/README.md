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

## Current corpus checkpoint

As of 2026-07-21, the repository contains 140 Turkish schema-v4 entries, all in
`draft` status. They validate as master records, but most authored fragments were
created under the earlier input-heavy workflow and then migrated mechanically.
Schema validity must not be read as proof that an entry was freshly authored by
the current minimal-input workflow.

`v2/work/` is resumable local execution state, not master data or production
provenance. Current root-writer tasks use task format 4 and minimal evidence
format `dictionary-v2-agent-root-evidence-v4`. Older manifests are historical
and are ignored; rerunning `create_entry.py` in prepare mode writes the current
task before any model call.

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

For the exact cold-start commands and first production pilot, use
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

The minimal agent workflow, branch evidence package, fragment ownership map,
retry rules, and acceptance criteria are defined in
`orchestration/entry-creation.spec.md`. The production contract uses one
root-level writer invocation per root envelope and target language. That
invocation sees the minimal evidence for all accepted branches and returns
branch-shaped fragments plus the short root profile. Agents never receive Quran
ayahs, occurrence data, QAC morphology, attachment records, full branch
packages, the master entry schema, or the orchestration spec.

Older work directories may still contain branch-per-agent manifests. They are
ignored: prepare mode writes one current `tasks/root_writer.json`, one
deduplicated `inputs/root_evidence.json`, and coordinator-only review state
before any model call. The evidence contains compact source claims and lexical
unit IDs, not raw passages. A reviewed coordinator policy classifies every
lexical unit as ordinary or proper-name before the writer runs. Transliteration
never enters writer context; protected proper names use placeholders. Missing
used anchors or name forms pause assembly in
`inputs/transliteration_review.json` or `inputs/name_review.json` without
invalidating or rerunning the writer.

Prepare deterministic evidence and resumable task manifests without making any
model calls:

```sh
python3 v2/scripts/create_entry.py root_000858 --language tr
```

Hand the prepared task to the top-level orchestration agent defined in
`prompts/entry-orchestrator.md`. The orchestrator invokes the root writer, then
an evidence-bound semantic reviewer, and finally the deterministic publication
scripts. The reviewer reports issues but never rewrites prose; uncertain issues
pause for editorial judgment. There is intentionally no
`--run-agents` script option:

```text
Run the v2 entry orchestrator for root_000858/tr.
```

The orchestrator resumes hash-matching writer and review responses and reruns
stale output. Each worker writes to its real repository output, runs the exact
read-only validator carried by its staged task, and corrects that same file in
place until it passes. A failed response is not discarded or replaced by a new
candidate. At most two later repair continuations return to the same writer;
bounded repairs cannot change unaffected branches and invalidate the earlier
semantic review. Outputs are written to `v2/entries/<language>/`, while task and
fragment state stays under `v2/work/entry_creation/`.

Export all validated entries as deterministic, one-entry-per-line JSONL:

```sh
python3 v2/scripts/export_jsonl.py --language tr
```

Every line is one complete schema-v4 entry. The exporter validates all source
bindings and rejects duplicate entry IDs or mixed languages before writing.

Project one validated entry without exposing unrelated master fields:

```sh
python3 v2/scripts/project_entry.py v2/entries/tr/root_000154.json \
  --projection user_dictionary
```

Export a bounded projection for the whole language corpus:

```sh
python3 v2/scripts/export_jsonl.py --language tr --projection translation_agent
python3 v2/scripts/export_jsonl.py --language tr --projection user_dictionary
python3 v2/scripts/export_jsonl.py --language tr --projection scholar_view
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
`v2/work/entry_creation/<root>/<language>/output/<root>_entry.json`. After raw
response validation, deterministic acceptance enriches that same file with
Arabic fields, compact source codes, dictionary-keyed prose notes, and
root-level occurrence/attachment evidence. Exact references remain internal. The
semantic reviewer receives only `review/input/` and writes only
`review/output/root_review.json`. Both agents validate and, when necessary,
repair those files in place before returning. The
orchestration agent owns timeouts and process monitoring. Operational failures
stop immediately, while invalid agent JSON remains preserved for correction.
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

Only frozen focus branches marked `accepted` and `contaminated: no` can enter an
agent task or assembled entry. Other branch states stop with `needs_evidence`.

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
