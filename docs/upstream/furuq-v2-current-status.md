# Furūq v2 Current Status

Date: 2026-07-09

## Current Direction

Furūq v2 now has two related but distinct jobs:

1. **Translation-risk axis coverage over V4 branches.** This is the current
   concept-map/rendering priority. V4 already owns the positive branch
   definitions; this pass protects semantic invariants, sibling boundaries,
   rare/source-grounded branches, and generic-gloss collapse risks so later
   target-language agents can render concepts faithfully.
2. **Arabic-internal SAN discovery where needed.** Branch SAN remains the
   high-recall Arabic-neighbor path for cases where translation-risk rows show
   that a fuller Arabic contrast is needed.
3. **Axis-normalized root neighbourhoods.** Branch-axis information will later
   support a root similarity/neighbourhood map, but only after axis rows are
   curated, normalized, and categorized. Raw axis labels are scaffold, not graph
   edges.

The current leading executable prompt is:

- `prompts/branch-translation-risk-discovery-v1_4.md`
- `prompts/branch-translation-risk-discovery-v1_4-plan.md`
- `prompt_id=branch_translation_risk_discovery`
- `prompt_version=1.4.0`
- `substrate_version=V4`
- `target_lang_scope=generic`
- row type: `BTRISK`

This prompt is language-neutral. It does not write Turkish, English, or other
target-language translations. It writes Arabic semantic invariants and
concept-map/rendering risk rows that target-language modules can consume later.

The completed production-candidate axis nomination prompt is:

- `prompts/candidate-harvest-v1.md`
- `prompts/candidate-harvest-improvement-followup-v1.md`
- `prompt_id=candidate_harvest`
- `prompt_version=1.18.0`
- `substrate_version=V4`
- row shape: 13-field candidate TSV

This prompt consumes V4 branch-image batches plus axis-inventory TSV batches. It
does not adjudicate claims and does not create graph edges. It nominates Arabic
dictionary-lookup candidates from semantic and collocational axes; variant,
etymological, and structural axes stay skipped by contract.

## Authority Boundary

V4 remains the authority for:

- roots;
- branches;
- forms;
- lexical units and governed collocations/constructions;
- positive handles;
- branch images and Arabic/English prose;
- source references.

Furūq does not recreate V4 and does not invent branch definitions. It consumes
V4 and asks what would collapse, blur, or be mistranslated if a later concept
map or rendering layer used a generic gloss.

Quran attestation defines inventory scope only. It is not evidence for branch
salience, contextual meaning, theology, occurrence distribution, activation, or
translation behavior. Mufradat and other allowed dictionary excerpts may contain
Quran citations as source-internal dictionary text, but those citations must not
change agent behavior.

Allowed Layer 1 evidence families remain:

```text
maqayis
ayn
jamhara
sihah
tahdhib
mufradat
```

## V4 Branch Contamination Gate

`furuq_v4.sqlite.gz` now includes a temporary `branch_images.contaminated`
column with only `yes`/`no` values. The purpose is operational suppression:
Quranic-origin branch images marked `yes` should not feed downstream sense
activation until the affected roots are rewritten and released.

The column was applied from:

`../../../_audits/v4_branch_contamination/derived/branch_activation_flags_final.tsv`

The checked-in updater is:

`scripts/apply_v4_contamination_flags.py`

Mapping:

- `yes`: final audit gate `hold_for_rewrite` or `suppress_from_activation`;
- `no`: final audit gate `allow_by_first_pass` or `allow_after_review`;
- Furūq-origin rows were outside the audit and remain `no`.

Current `branch_images` counts:

- all rows: 364 `yes`, 19,588 `no`;
- Quranic-origin rows: 364 `yes`, 11,275 `no`;
- Furūq-origin rows: 0 `yes`, 8,313 `no`.

The column is not an evidence verdict, theological label, rewrite decision, or
replacement for the audit files. It is a temporary gate to keep contaminated
dictionary entries out of activation work while preserving the full DB.

## Branch SAN v3 Status

`branch_san_discovery_v3` is implemented as the current branch SAN recall
contract in `prompts/branch-san-discovery-v2.md`.

The v3 pilot used three focus branches:

- `خ و ف:B001`
- `ط ر ق:B002`
- `ع ل م:B001`

Initial BRSAN output:

- 37 rows total;
- all three files mechanically validated;
- row profile: 25 `near_neighbor`, 6 `synonym`, 6 `antonym`;
- recall basis profile: 16 `packet_dict`, 20 `arabic_lexical_recall`, 1
  `mixed`.

Raw legacy floor misses:

- `خ و ف`: 13;
- `ط ر ق`: 26;
- `ع ل م`: 90;
- total: 129.

Protected branch-floor rescue over those misses:

- `adopt`: 27;
- `already_covered`: 3;
- `decline`: 99.

Interpretation:

- v3 is better as a contract: provenance, normalization, axis-first traversal,
  level discipline, and neutrality are materially improved;
- v3 alone is not enough as a high-recall engine, especially for broad cognitive
  branches like `ع ل م`;
- protected floor rescue is useful but branch-local. It is not global category
  coverage and does not replace form, lexical-unit/collocation, symmetry, or
  dictionary-excerpt rescue.

## Translation-Risk v1.4 Status

The v1.4 plan was reviewed by GPT-5.5 xhigh and revised, then converted into
an executable prompt, packet schema, output schema, packet builder, validator,
and validation fixture. The key change after review was to make the output a
robust concept-map interface instead of loose risk notes.

The implemented `BTRISK` row encodes:

- semantic invariant;
- generic-gloss loss;
- axis dimension;
- focus and contrast axis values;
- relation to focus;
- concept-map action;
- source traceability;
- rarity/source-only preservation;
- `needs_san_escalation` for cases requiring fuller Arabic SAN discovery;
- `no_material_risk` audit rows so no focus branch silently disappears.

Pilot behavior over four branches:

- `س ب ل:B001` path/means: produced common generic-gloss and sibling-collapse
  guardrails;
- `س ب ل:B010` eye disease: correctly preserved the source-only Sihah medical
  branch and blocked defaulting to the common path/road sense;
- `ع ل م:B001` knowledge: preserved the core invariant and sibling boundary
  against the sign/mark branch, but did not independently surface many
  cross-root cognitive neighbors;
- `خ و ف:B001` fear: preserved expectation-of-harm, causative sibling, scalar
  boundary, and opposition to `أ م ن`.

Current implementation files:

- `prompts/branch-translation-risk-discovery-v1_4.md`
- `schema/branch-translation-risk-packet.schema.tsv`
- `schema/branch-translation-risk-output.schema.tsv`
- `scripts/build_branch_translation_risk_packets.py`
- `scripts/validate_branch_translation_risk_output.py`
- `tests/fixtures/validation_branch_translation_risk_packet.tsv`
- `tests/fixtures/validation_branch_translation_risk_output.txt`

The current validator fixture passes with 32 output fields and zero findings.
The builder smoke test writes a focused `س ب ل:B010` packet from V4 and the
portable lexicon. GPT-5.5 medium code/schema reviews are required for the two
schemas and two scripts before treating this implementation as review-cleared.

## Candidate Harvest v1.18 Completion Status

Candidate-harvest v1.18 is the completed production-candidate nomination pass
over the generated branch-axis inventory. It uses the v1.12 base contract with
shard-scale work units, canonical shard filenames, capacity-stop handling,
automation limited to integrity checks, and hard validation before any
corrective quality follow-up. The prompt writes 13-field recall hypotheses for
semantic and collocational axes and preservation receipts for skipped
variant/etymological/structural axes.

Completion checkpoint:

- completed on 2026-07-04;
- committed output pass: `f4eed41e` (`Add candidate harvest shard outputs`);
- final all-shard pairing audit: 739 manifests checked, 0 missing paired
  outputs;
- late missing shards in batch008 were run, validated, followed up,
  revalidated, and closed before the final audit;
- all candidate-harvest outputs remain recall hypotheses only, not accepted
  Furūq claims, evidence verdicts, resolver decisions, graph edges, or concept
  profiles.

Current candidate lookup DB:

- canonical DB: `candidate_root_map.sqlite`;
- builder: `scripts/build_candidate_root_map_db.py`;
- schema version: `candidate_root_map.v1.4`;
- canonical v1.18 shard files ingested: 739;
- raw candidate/receipt rows preserved: 100,389;
- noncanonical TSV-like files skipped and hashed: 68;
- reviewed target-root rows preserved from lexicon-build/v1.18 review
  artifacts: 2,019;
- row-level reviewed target provenance rows preserved: 907.

`candidate_root_map.sqlite` is a provenance and lookup DB. It keeps all
canonical v1.18 rows, including exact V4 candidates, Furūq-v4 targets,
self-root rows, blank-root rows, unresolved rows, and receipt rows. It must not
be treated as accepted Furūq evidence, a concept profile store, a graph edge
store, or Quranic activation data.

The canonical checked-in DB omits secondary lookup indexes to stay below
GitHub's 100 MB file limit. Rebuild locally with
`scripts/build_candidate_root_map_db.py --with-lookup-indexes` when indexed ad
hoc querying is needed; primary-key integrity indexes remain present either
way.

Batch001 v1.6 result:

- 397 candidate rows;
- 0 receipt rows;
- 350 candidate-bearing axes;
- relation profile: 295 `near_neighbor`, 93 `synonym`, 9 `antonym`;
- recall-basis profile: 329 `axis_basis`, 49 `lexical_recall`, 19
  `branch_prose`;
- all production probes passed: `root_000001:B001:A01:بياض:antonym`,
  `root_000002:B002:A05:حرام`, `root_000015:B001:A05:نفع`;
- production validator exited 0 with warnings only.

v1.18 guardrails for any repair-only rerun:

- build first-pass and follow-up tasks with
  `scripts/build_candidate_harvest_task.py`;
- require the canonical shard output filename
  `batchNNN_candidate_harvest_rSTART-END.tsv`, with prompt/model provenance in
  the manifest;
- validate the first-pass TSV before sending any protected follow-up;
- send the protected follow-up turn on the same agent only after first-pass
  validation passes;
- validate with `scripts/validate_candidate_harvest_output.py --production-qc`;
- treat validator errors as batch failures;
- keep batch-family known-answer probes when their axes exist;
- track warnings for high-priority blank roots, generic templates,
  candidate-name warnings, one-candidate-axis ratios, basis dominance, low
  lexical_recall share, relation collapse, abstract axis-label candidates, and
  single axis-basis rows without `deep-neighbor unavailable:` notes.

v1.6 remains the batch001 calibration baseline. v1.7-v1.8 broad attempts showed
that the baseline could not be scaled safely without a deterministic task
ledger and first-pass validation gate. v1.9-v1.17 recorded the main failed
prompt/process experiments: canonical-opposite misses, slash-packed candidates,
missed basis heads (`حرام`, `نفع`), invalid UTF-8, skipped-axis follow-up rows,
basis dominance, relation collapse, abstract axis-label candidates, root
normalization failures, and enum placement errors. v1.18 returned to the
stronger v1.12 base and made the production unit small enough for reliable
validation and follow-up. xhigh remains a sampled recall-audit mode, not the
main production mode.

## Reference Outputs

Pilot and generated reference documents committed in this checkpoint include:

- `output/branch_san_pilot/`
- `output/branch_san_pilot_v3/`
- `output/s29_36_49_v4_branch_images.md`
- `output/s87_v4_branch_images.md`

`s87_v4_branch_images.md` covers S87:1-19 with:

- 41 distinct QAC roots;
- 43 mapped V4 root records;
- 365 V4 branch rows;
- 0 unmapped roots.

## Next Work

1. Treat `candidate_root_map.sqlite` as the first-class v1.18 candidate
   universe DB and keep it rebuilt from canonical v1.18 TSVs plus reviewed
   target-root artifacts.
2. Produce a coverage/quality summary over the DB: shard counts, axis
   coverage, relation profile, recall-basis profile, warning clusters, duplicate
   candidate pairs, and unresolved/low-confidence rows.
3. Design and run the resolver boundary: normalize raw candidate names, map to
   V4 positive handles or external dictionary lookup units, dedupe symmetric
   pairs, and route noise/ambiguous rows.
4. Start evidence adjudication only after resolver packets exist, using
   `prompts/evidence-adjudication-v2.md` and allowed dictionary excerpts.
5. Feed accepted evidence-backed claims into
   `prompts/concept-profile-writer-v2.md`; do not import raw candidate-harvest
   rows directly into profiles or graph edges.
6. Finish GPT-5.5 medium review disposition for the two BTRISK schemas and two
   BTRISK scripts.
7. Commit the review-cleared BTRISK v1.4 production prompt, schemas, builder,
   validator, fixture, and docs.
8. Pilot BTRISK over S87 and one larger branch-rich sample, then audit
   `no_material_risk` rows manually.
9. Tune the `needs_san_escalation` behavior for broad same-gloss/common-gloss
   branches based on pilot output.
10. Keep branch SAN v3 as the escalation path, not the default all-branch pass.
11. Add an axis-normalization design before treating axis inventory as a root
   neighbourhood graph. The design should type genus, differentia, opposition,
   carrier-bound, structural/variant/etymological, and residual-confusable
   axes, then define how curated axis profiles create root/branch similarity
   candidates.
12. Design the v2 canonical store after the BTRISK/SAN boundary and
   axis-normalization boundary are stable.

Schema status for steps 1-2: `candidate_root_map.sqlite` is the current
canonical DB contract for v1.18 candidate lookup. The later resolver output
schema has not been formalized yet. Treat resolver fields listed above as the
required design target, not as a committed TSV contract, until new schema files
are added under `schema/`.
