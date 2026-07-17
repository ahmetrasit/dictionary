# Furuq v2 - Translation-Risk And SAN Discovery

Status: candidate-harvest v1.18 production output complete as of 2026-07-04;
the first-class candidate lookup DB is now `candidate_root_map.sqlite`. See
`CURRENT_STATUS.md` for the exact current state, completion audit, and next
work. Branch SAN discovery uses the v3 output contract with axis-first
traversal and explicit recall-basis provenance. BTRISK v1.4 remains the
language-neutral translation-risk layer over V4 branches. Axis-scoped
candidate harvest v1.18 is the stable completed process for turning
branch-axis inventory into dictionary-lookup candidates; its cold-agent
runbook remains in `output/candidate_harvest_v1/ORCHESTRATION.md` for reruns
and repair-only work. v1.6 remains the batch001 calibration baseline.

This directory owns canonical Furuq work going forward. Layer1 v1 (`../v1/`)
is abandoned as a pipeline and database target and is frozen legacy reference:
its docs record the inherited contracts (source families, gates, relation
classes), and its recall files serve only as read-only coverage-audit inputs.
v2 will own its own canonical store for candidates, claims, evidence, concept
profiles, and projections (see `PLAN.md`, Canonical Store And V1 Disposition).

## Core Change

The older same-root v1 pilot generated mechanical pair queues and asked agents
to classify rows. That approach is too expensive for broad production discovery:
it creates too many weak pairs and turns agents into pair filters.

v2 first reversed the flow for Arabic-internal branch SAN recall:

```text
dictionary entry + V4 branches/forms
  -> agent recalls SAN candidates
  -> resolver maps candidates to V4 or external dictionary handles
  -> dedupe/rank/route
  -> follow-up recall for missed candidates or form leads
  -> evidence lookup and adjudication later
```

SAN means:

```text
synonym
antonym
near_neighbor
```

SAN rows are recall hypotheses only. They are not accepted Furūq claims, not
dictionary evidence, not concept profiles, and not activation guardrails.

The scope correction from the current work is that faithful concept translation
does not require exhaustive SAN for every branch. V4 already gives positive
branch definitions. Furūq v2 should first identify where a branch's concept
would collapse under a generic gloss, where a sibling branch or rare
source-grounded branch must be protected, and where a fuller Arabic SAN pass is
actually needed.

The layer is scoped by Quran-attested inventory but context-neutral. Inventory
membership is identity metadata only; it must not introduce occurrence
salience, contextual meaning, theology, translation behavior, activation logic,
or downstream product pressure into dictionary recall or adjudication.

Allowed dictionary excerpts, especially from `mufradat`, may contain Quran
citations as part of the source text. Those citations may pass through as
dictionary text, but they must not change agent behavior or become contextual
evidence.

## Current Products

### Translation-Risk Axis Rows

The leading product is now generic translation-risk axis coverage:

- focus: V4 branch definitions and source refs;
- output: `BTRISK` rows with semantic invariants, generic-gloss loss, axis
  poles, map action, source traceability, rare-branch preservation, and
  `needs_san_escalation`;
- no target-language prose;
- no accepted evidence claims;
- no Quranic-context evidence.

The executable prompt is `prompts/branch-translation-risk-discovery-v1_4.md`.
The reviewed plan is retained at
`prompts/branch-translation-risk-discovery-v1_4-plan.md`.

### Branch/Root SAN Recall

Branch/root SAN recall remains the Arabic-neighbor discovery path:

- focus: V4 root branches and their dictionary entry context;
- output: root/branch-level synonym, antonym/opposition, and near-neighbor
  candidates;
- no accepted distinctions;
- no Quranic-context evidence;
- no target-language collision evidence;
- no full form harvest in the same pass.

Form-level discovery is separate. Branch agents may be followed by a protected
second turn that asks only for form-level leads naturally implied by the branch
review. A later form SAN pass should work over Quran-scoped V4/QAC form handles.

### Axis-Normalized Root Neighbourhoods

Branch-axis inventory is also a future graph substrate. Raw axis rows are not
root-neighbourhood edges yet: axis labels are free Arabic phrases, can overlap
across packets, and may mix genus, differentia, carrier, and residual
confusable-difference wording. After axis rows are curated, normalized, and
categorized, they should feed a root similarity/neighbourhood map.

The intended path is:

```text
V4 branch images
  -> branch axis inventory
  -> axis curation / normalization / categorization
  -> root and branch neighbourhood candidates
  -> evidence-backed Furūq claims where a contrast matters
  -> concept-map projection
```

The neighbourhood map should be axis-derived, not occurrence-derived. It must
not use Quranic context, salience, tafsir, translation behavior, or downstream
activation as similarity evidence. It should connect roots or branches because
their curated axis profiles show shared semantic zones, opposed poles, scalar
positions, carrier-bound fields, or recurrent confusability patterns.

### Axis-Scoped Candidate Harvest

Candidate harvest v1.18 is the stable process gate for axis batches. It consumes
one branch-image batch plus a shard of that batch's axis-inventory TSV, then
writes 13-field recall hypotheses for semantic and collocational axes.
Variant, etymological, and structural axes produce preservation receipt rows
under the current v1.18 contract.

Use the cold-agent runbook at:

`output/candidate_harvest_v1/ORCHESTRATION.md`

Production orchestration must keep:

- generated first-pass task files from
  `build_candidate_harvest_task.py`;
- canonical shard output filenames of the form
  `batchNNN_candidate_harvest_rSTART-END.tsv`, with prompt/model provenance in
  the manifest;
- one shard per agent, normally about 40-70 axis rows;
- first-pass validation before any corrective quality follow-up;
- inline same-agent repair for hard validation errors, followed by revalidation;
- the exact corrective quality follow-up message from the orchestration
  runbook, not generated `*_followup.md` files;
- `validate_candidate_harvest_output.py --production-qc`;
- batch-family known-answer probes where available;
- hard failure on validator errors;
- warning tracking for high-priority blank roots, generic templates,
  candidate-name warnings, one-candidate-axis ratios, basis dominance, low
  lexical recall share, relation collapse, and abstract axis-label candidates.

Batch001 v1.6 remains the calibration baseline, but broader v1.7-v1.8 attempts
exposed structural reliability failures: row-width drift, relation/level enum
swaps, rows for skipped axes, and axes present only in malformed rows. v1.9
added a deterministic axis ledger and a stricter run gate before scale, but its
first-three pilot still missed a canonical opposite and allowed a slash-packed
carrier candidate. v1.10 fixed those points and improved depth, but still
missed salient basis heads on batch001 (`حرام`, `نفع`). v1.11 fixed those
probe misses, but one run wrote invalid UTF-8 and one protected follow-up
introduced a skipped structural axis. v1.12 adds explicit UTF-8/plain-text
discipline and forbids follow-up rows on axes absent from turn one. It passed
hard validation on batches001-003, but Gauss rejected it for deep lexical
recall / false-negative risk: batch001 was basis-dominant, relation-collapsed,
fixed-density, and used abstract axis-label candidates. v1.13 keeps the same
13-field schema and adds deep-neighbour traversal plus QC warnings for those
failure modes, but failed the hard batch001 probe by missing `نفع` and still
copied frame/object words such as `ماء` and `مال` as candidates. v1.14 tightens
candidate identity with a lexical-comparator test, keeps `نفع`-style semantic
basis heads mandatory, and requires single axis-basis rows to state when no
deep neighbour is available. v1.14 still failed: it recalled `نفع` on the wrong
axis, filled the required axis with `يعود`, produced one-row-per-axis outputs,
and repeated evidence-question templates. v1.15 makes axis-local semantic-head
placement explicit and turns silent single axis-basis rows into production
errors. v1.15 improved axis-local `نفع` and recall depth on batch001, but still
failed hard on root normalization, missed axis-local `حرام`, produced invalid
UTF-8 on batch003, and collapsed batch002 to one row per axis. v1.16 adds
surface-vs-root normalization examples, hard `حرام`/`نفع` calibration language,
and explicit UTF-8 self-check permission.
v1.16 fixed UTF-8 and hard calibration probes on batch001, but still failed
production through relation/level enum swaps, relation collapse, and silent
single axis-basis rows. v1.17 was the capped final attempt in that line: it
made relation classification criteria explicit and restated the hard single-row
gate. v1.18 is now the stable contract: it returns to the stronger v1.12 base,
uses shard-scale work units, requires versioned filenames, supports capacity
stops, keeps automation limited to integrity checks, and moves orchestration to
hard validation -> inline repair -> revalidation -> optional corrective quality
follow-up. xhigh output remains a periodic recall audit source, not the main
production mode.

Completion checkpoint: on 2026-07-04, the generated candidate-harvest shard
inventory was audited after first-pass validation, required follow-up,
post-follow-up validation, and agent closure. The final pairing audit checked
739 manifests and found 0 missing paired outputs. The completed output pass is
committed as `f4eed41e` (`Add candidate harvest shard outputs`).

The production run must not be treated as accepted Furūq. It creates a
dictionary-lookup candidate inventory. The next boundary is aggregation,
candidate resolution, axis normalization, evidence adjudication, and only then
claim/profile import.

### Candidate Root Map DB

`candidate_root_map.sqlite` is the canonical v1.18 candidate-universe lookup
DB for Furūq v2. It is built by:

```text
scripts/build_candidate_root_map_db.py
```

The DB ingests only canonical v1.18 shard files matching
`batchNNN_candidate_harvest_rNNN-NNN.tsv` whose first line is exactly
`# candidate_harvest 1.18.0`. Noncanonical TSV-like files are skipped and
recorded with hashes.

The DB preserves all raw v1.18 rows, including rooted candidates, blank-root
candidates, nonroot leads, forms, collocations, external dictionary units, and
receipt rows. It also joins the reviewed candidate-root target artifacts under
`output/v1_18_surah_v4_check/`, main V4 roots, and
`../lexicon-build/furuq/furuq_v4.sqlite`.

The checked-in canonical DB omits secondary lookup indexes so the first-class
SQLite artifact stays below GitHub's 100 MB file limit. For local exploratory
querying, rebuild with `--with-lookup-indexes`; this does not change the tables
or views, only performance-oriented indexes.

Important tables/views:

- `raw_candidate_rows`: every canonical v1.18 row with source provenance.
- `candidate_resolutions`: simple root resolution status for each row.
- `focus_root_candidates`: all candidates for a focus root.
- `focus_branch_candidates`: all candidates for a focus root and branch.
- `concept_map_targets`: only candidates currently backed by `furuq_v4`.
- `target_roots` and `focus_candidate_rows`: reviewed target-root layer from
  the v1.18 aggregate/review TSVs.

Rows in this DB remain recall/provenance data. They are not accepted Furūq
claims, evidence verdicts, graph edges, concept profiles, Quranic activation
decisions, or Quranic/non-Quranic branch decisions.

### V4 Branch Contamination Gate

`furuq_v4.sqlite.gz` is the checked-in gzip copy of the local
`furuq_v4.sqlite` DB. On 2026-07-09, `branch_images` received one temporary
operational column:

```text
contaminated TEXT NOT NULL DEFAULT 'no' CHECK (contaminated in ('yes', 'no'))
```

The column is a suppression gate for Quranic-origin V4 branch images whose
dictionary wording may have been contaminated by Quranic usage, collocation
meaning, or theological assumptions. It is not a rewrite, deletion, evidence
verdict, or provenance store. The audit provenance remains in:

`../../../_audits/v4_branch_contamination/derived/branch_activation_flags_final.tsv`

The applied mapping is:

- `contaminated='yes'`: `final_activation_gate` is `hold_for_rewrite` or
  `suppress_from_activation`;
- `contaminated='no'`: `final_activation_gate` is `allow_by_first_pass` or
  `allow_after_review`;
- `origin_corpus='furuq'` rows are outside this audit and default to `no`.

Application script:

```text
scripts/apply_v4_contamination_flags.py
```

Post-application counts:

- all `branch_images`: 364 `yes`, 19,588 `no`;
- Quranic-origin rows: 364 `yes`, 11,275 `no`;
- Furūq-origin rows: 0 `yes`, 8,313 `no`.

Until contaminated branches are rewritten and released root-by-root, downstream
activation work should suppress `contaminated='yes'` branch images. Once this
temporary gate is no longer needed, the column can be removed.

## Prompt Architecture

The prompt design follows `../../../gpt55-instruction-rules.md`:

- one pass, one product;
- concrete output line contract;
- closed enums with validator-owned enforcement;
- worked examples that show the intended output shape;
- axis-first recall traversal before SAN classification;
- explicit recall-basis provenance for packet-grounded vs lexical-recall rows;
- small packets, because expected volume changes model behavior;
- second-turn recall for improvement or form leads;
- protected-output language in follow-up prompts.

## Current Files

- `CURRENT_STATUS.md` - latest state, pilot findings, reference outputs, and next work.
- `PLAN.md` - v2 design and implementation sequence.
- `schema/branch-san-discovery-packet.schema.tsv` - input packet row contract.
- `schema/branch-san-discovery-output.schema.tsv` - first-pass branch SAN output.
- `schema/branch-form-lead-output.schema.tsv` - protected follow-up form-lead output.
- `schema/branch-san-rescue-miss-input.schema.tsv` - coverage-report FLOORMISS line contract.
- `schema/branch-san-rescue-output.schema.tsv` - third-turn rescue disposition output.
- `schema/branch-translation-risk-packet.schema.tsv` - BTRISK v1.4 input packet row contract.
- `schema/branch-translation-risk-output.schema.tsv` - BTRISK v1.4 32-field output contract.
- `schema/evidence-adjudication-packet.schema.tsv` - PAIR + EXCERPT input contract.
- `schema/evidence-adjudication-output.schema.tsv` - evidence verdict output.
- `schema/concept-profile-packet.schema.tsv` - FOCUS + CLAIM input contract.
- `schema/concept-profile-output.schema.tsv` - concept profile output.
- `schema/candidate-harvest-output.schema.tsv` - candidate-harvest v1.18
  13-field output contract.
- `prompts/branch-san-discovery-v2.md` - turn 1: branch SAN recall, current
  prompt contract `branch_san_discovery_v3`.
- `prompts/candidate-harvest-v1.md` - candidate-harvest v1.18 axis-scoped
  nomination prompt after axis inventory.
- `prompts/candidate-harvest-improvement-followup-v1.md` - exact corrective
  quality follow-up message for candidate harvest v1.18.
- `output/candidate_harvest_v1/ORCHESTRATION.md` - stable v1.18 orchestration
  runbook for shard creation, agent dispatch, validation, inline repair, and
  follow-up handling.
- `prompts/branch-translation-risk-discovery-v1_4.md` - executable BTRISK v1.4
  prompt for language-neutral V4 branch translation-risk rows.
- `prompts/branch-translation-risk-discovery-v1_4-plan.md` - reviewed plan for
  generic V4 branch translation-risk axis rows (`BTRISK`).
- `prompts/branch-form-leads-followup-v2.md` - turn 2: protected form-lead follow-up.
- `prompts/branch-san-rescue-followup-v2.md` - turn 3: protected missed-neighbor rescue.
- `prompts/evidence-adjudication-v2.md` - fresh agent: dictionary-evidence verdicts per pair.
- `prompts/concept-profile-writer-v2.md` - fresh agent: Arabic concept profiles from accepted claims.
- `scripts/build_branch_translation_risk_packets.py` - read-only V4/lexicon
  packet builder for BTRISK v1.4.
- `scripts/validate_branch_translation_risk_output.py` - mechanical BTRISK
  packet/output validator.
- `scripts/validate_candidate_harvest_output.py` - mechanical candidate-harvest
  output validator joined against axis inventory TSV.
- `scripts/build_candidate_harvest_task.py` - generated first/follow-up task
  builder with harvested/skipped axis ledger and prompt-version filename guard.
- `reviews/` - review reports and disposition notes.
- `output/s29_36_49_v4_branch_images.md` and `output/s87_v4_branch_images.md`
  - generated V4 branch-image reference documents for local pilot/debug work.

A later form SAN pass over Quran-scoped form handles is deferred by design and
gets its own prompt when the branch pipeline has passed its gates.

## Non-Goals

- Do not write to, import into, or resume any v1 artifact; v1 is frozen
  legacy reference and read-only audit input.
- Do not import raw agent rows directly into accepted claims.
- Do not derive or own positive form meanings here; the derived form-meaning
  layer for dictionary-uncovered Quranic forms lives V4-side and is consumed,
  not produced, by Furuq.
- Do not use Quranic occurrence context, tafsir, translation, or activation as
  Layer 1 evidence.
- Do not ask one agent pass to do branch SAN, form SAN, evidence adjudication,
  and prose generation together.
