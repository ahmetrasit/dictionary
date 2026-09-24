# Reviewed supplemental entry workflow

Run commands from the dictionary repository root. This path serves reviewed
QAC dictionary gaps that have no frozen Furuq packet. The frozen Furuq
database, packet index, historical Arabic branch evidence, and legacy bundles
stay unchanged.

## Source ownership

`data/supplemental/registry.v1.json` is the stable ID ledger. A registry row
names one `entries/<id>.json` intake and pins its exact file SHA-256. The
independently reviewed intake owns Arabic identity, typed citations, scoped
QAC selector, analyses, senses, and Arabic claims. `sourceSnapshot` records
historical source provenance; a later quran-data commit alone does not rewrite
it. A task/export's `supplementalIntake.registrySha256` is also a historical
production snapshot. Appending an unrelated registry row does not invalidate
an unchanged selected ID, kind, intake path and intake hash. Transfer manifests
and app locks separately pin the complete current registry. Changing the
selected intake still requires deliberate re-preparation and review.
`data/supplemental/source-names.v1.json` is the lexicon title and badge
map. Lexicon sources alone receive badge codes; grammar and tafsir remain typed
citations with full titles and locators.

The accepted ID is supplied by the registry, never inferred from a Furuq
candidate or a global root alias. Lexical roots use `root_` IDs; grammatical
headwords use `headword_` IDs, no top-level `rootArabic`, and exact QAC
lemma/ref selectors. The preparer validates the current committed QAC rows,
selector ref-set digest, quote hashes, source-key ownership, sense roster,
analysis scope, and citation types. It does not build SQL overlays, QNet
packages, or attachment crosswalks. Its evidence file is sealed from the
reviewed intake.

## Prepare and author

```sh
python3 v2/scripts/prepare_supplemental_entry.py <id> --language tr
```

If quran-data is not at the sibling `../quran-data` path, add
`--quran-data /absolute/path/to/quran-data`. The checkout's
`data/morphology/qac.sqlite.gz` must equal committed HEAD bytes.

The command writes the canonical task and staged Agent A input under one of:

```text
v2/work/entry_creation/<root_id>/tr/
v2/work/entry_creation/headwords/<headword_id>/tr/
```

Agent A reads only the staged `input/` files, writes the response to the
declared `output.path`, and runs the exact validation argv in `input/task.json`.
Root responses contain `branches` and `root_profile`; grammatical responses
contain `senses` and `headword_profile`. Their claim, concept-map, gloss,
source-synthesis, and bounded neighbor rules are shared.

Do not author Turkish prose in the intake or source map. Do not put a proper
name into `lexicalUnits` unless the governed name queue can be completed; an
unresolved `{{lu_...}}` token is not publishable. Source names and Arabic
quotations are source-owned and restored at export.

## Independent review

After Agent A's staged validator passes, run:

```sh
python3 v2/scripts/prepare_supplemental_entry.py <id> --language tr --review
```

This stages Agent B's input and an exact pre-fix writer snapshot at
`review/input/writer_response.json`. Never replace that snapshot after a
review begins. New staging preserves the writer's original bytes so a later
repair remains verifiable against the canonical pre-fix digest. The shared
validator can be rerun after a bounded repair; it checks that anchored snapshot
and rejects edits outside the recorded fields. Agent B independently compares
it with sealed evidence,
writes and validates `review/output/root_review.json` or
`review/output/headword_review.json` **before** any live writer edit, then
applies only a recorded high-confidence `repair` to the live output. `pass`
leaves it unchanged. `editorial_review` remains unresolved and cannot export.
The review issue target is a branch/sense ref or the matching profile key.

## Export and transfer

```sh
python3 v2/scripts/export_reviewed_supplement.py <id> --language tr
```

The exporter checks the same intake, sealed evidence, QAC binding, writer
snapshot, reviewer finding, and bounded repair fields. It restores exact
source-owned Arabic, typed citations, source phrases, and QAC occurrence
records without changing the live writer response. Root exports retain the
normal `dictionary-v2-root-entry-draft-v1` envelope under
`v2/work/entry_creation/<root_id>/tr/export/`; headwords use the distinct
`dictionary-v2-headword-entry-draft-v1` envelope under
`v2/work/entry_creation/headwords/<headword_id>/tr/export/`.

For each sense, the Arabic source phrase is the exact ordered join of
`quotationAr (sourceId:sourceKey)` over its `sourceKeys`, separated by `؛ `.
It is hashed and compared after transfer. Root `sources` badges include only
lexicon citations, in first-cited order, while full `citations` preserve every
typed source. The immutable `citations` records equal their intake source
rows; translated writer summaries appear separately as per-sense or
per-branch `citationNotes` rows keyed by `sourceKey`. Entry-level
`phraseContext` evidence, when supplied, remains in the transferred intake
without becoming a sense citation or badge. The four reviewed root identities
join root resolution only after the
reviewed quran-data transfer; headwords remain exact selector entries, not
members of root counts or root alias indexes.
