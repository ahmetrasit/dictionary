# Attachment Enrichment — Syntax, Discourse, and Translation Evidence

## Purpose

Produce systematic Quranic Arabic syntax and deployment evidence at full-surah
scope. The project started as syntactic attachment enrichment for verb/noun
valency, but the full-surah scan makes it practical to collect related layers
that activation, commentary, translation, and product exports need:

- local clauses and explicit attachments;
- span anchors and preposition-token anchors;
- cross-references and discourse antecedents;
- implicit arguments and ellipsis;
- language-neutral translation-support guardrails.

The primary synthesis consumer is now the activation layer described in
`_corpus/ARCHITECTURE.md`. Translation still consumes these signals, but mainly
after Arabic sense licensing and Arabic commentary have been produced.
Turkish, English, and other target languages handle Arabic valency, ellipsis,
pronouns, and discourse compression differently. Translators need to know what
the Arabic permits and what it leaves open, not just one likely interpretation.

These outputs are Quran-instance deployment evidence. They should feed
activation, contextual profiles, graph/domain edges, commentary, translation,
and product-data exports; they should not contaminate V4 or semantic-map
dictionary-level meaning.

## Current Status

As of 2026-06-18:

- Pass 1 syntax is merged for all 114 surahs.
- Pass 1 valence pilot covers the full Quran: 19,138 occurrence rows, 6,582
  grouped frame rows, 3,076 form summaries, 0 skipped frames.
- Pass 1 is the current usable source for grounded-senses construction/valence
  work.
- Pass 1c ambiguity sweep and the proposed 1d PP audit are retired/deferred
  from the active pipeline. Ambiguity is now recovered by multi-ayah
  concept-discovery and translation-support agents as coverage uncertainty
  inside their own read scopes.
- Pass 2 output directories exist for all 114 surahs. The original Pass 2
  tables and standalone 2c refrain patches remain under `output/pass2/sNNN/`.
- Pass 3 reads the preserved merged surface under
  `output/pass2_merged_2c/sNNN/sNNN_discourse.tsv`, which applies the 2b sweep
  and 2c refrain patch without overwriting the original Pass 2 files.
- Downstream contextual final_v3 deliberately parks Pass 2c `SR_XREF`/`SR_CAND`
  refrain-chain evidence instead of mixing it into ordinary XREF/CAND counts.
  Treat `output/pass2/sNNN/sNNN_refrain.tsv` as a potential resource for Layer 2
  packet flags, furūq formula work, translation/commentary support, and app
  motif/refrain trails.
- Pass 3 translation support is complete: all 661 manifest-listed blocks are
  present, all 114 canonical `output/pass3/sNNN/sNNN_support.tsv` files exist,
  and all canonical Pass 3 files validate clean against Pass 1 and the
  preserved Pass 2 merged surface. See
  `output/pass3/pass3_validation_manifest.tsv`.
- Reviewed finalization is complete in `output/final_v3/`. The finalizer
  ingests the validated v3 Pass 1/2/3 TSVs and emits reviewed corpus tables for
  clauses, attachments, cross-references, implicit arguments, ellipsis,
  translation support, review issues, verb/noun instances, and aggregate
  verb/noun patterns.
- Legacy `output/final/` remains mechanical-only. New downstream consumers
  should read `output/final_v3/` unless they explicitly need a legacy
  mechanical control.

See `progress.md` for the detailed pass table and current counts.

## Problem

The ayah JSONs (`_json/ayah_json/`) contain an ATTACH disambiguation type, but
coverage is too sparse for distributional analysis:

| Metric | Value |
|--------|-------|
| Total content words | 50,974 |
| Total verbs | 19,105 |
| Unique verb roots | 994 |
| Words with ATTACH annotation | 2,266 (4.4% of content words) |
| Verbs with ATTACH annotation | ~287 (1.5% of verbs) |

The disambiguation agent only annotated notable or ambiguous attachment cases.
The relation types are inconsistent — 60+ distinct labels, many appearing once
(e.g., `"yawma tubaddalu attached to yuʾakhkhiruhum (ayah 42)..."` as a
relation type). The data is a curated highlight reel, not a systematic survey.

### What already exists (do not duplicate)

- **cooccurrencePairs** in ayah JSONs: 267,809 entries across 1,453 roots.
  Proximity-based co-occurrence with root, partner root, partner form tag,
  frequency, and ayah refs. Complete but *not syntactic* — cannot distinguish
  "X modifies Y" from "X and Y are nearby."

- **Existing ATTACH entries**: 2,266 entries. Useful relation types when present
  (`pp-verb`, `adjective`, `ḥāl`, `apposition`, `khabar`, `iḍāfa`), but too
  sparse and too inconsistent for aggregation. Can be used as seed/validation.

- **ROLE disambiguation**: 12,646 entries (24.8% of content words). Contains
  grammatical role labels (`mafʿūl-bihi`, `iḍāfa-subjective`, `naʿt`, `ẓarf`,
  `ḥāl`). Overlaps with attachment but from the dependent's perspective rather
  than the head's.

## What to produce

### 0. Multi-pass reviewed ayah objects

The redesigned review flow emits one final reviewed ayah object with:

```json
{
  "sura": 18,
  "ayah": 5,
  "clauses": [],
  "attachments": [],
  "cross_refs": [],
  "implicit_arguments": [],
  "ellipsis": [],
  "translation_support": [],
  "review_issues": []
}
```

The active production prompt set lives in `prompts/v3/`:

- `prompts/v3/pass1-core-{model}-v3.md`
- `prompts/v3/pass2-discourse-ellipsis-v3.md`
- `prompts/pass2-discourse-structure-v1.1.md`
- `prompts/v3/pass2b-surah-sweep-v3.md`
- `prompts/v3/pass2c-refrain-sweep-v3.md`
- `prompts/v3/pass3-translation-support-v3.md`
- `prompts/v3/ORCHESTRATION-v3.md`

The older JSON/batch prompt files under `prompts/` remain as reference and
pilot history; production uses the surah-keyed TSV lane.

The pass split is intentional:

1. **Syntax surface**: present-word syntax only.
2. **Discourse and ellipsis**: references and absent/recoverable material.
2b. **Discourse structure**: backbone, cross-ayah chains, key findings — a
   separate low-obligation pass so the expensive discourse layer keeps its own
   output budget.
3. **Translation support**: language-neutral risks and guardrails, not final
   renderings.

Every non-surface claim carries `claim_status` and `evidence_basis`, and
ambiguous candidates are grouped with stable IDs. This preserves Arabic-licensed
ambiguity instead of collapsing it into tafsir-like certainty.

### 1. Verb valency frames

For each (root, form_tag) verb combination attested in the Quran, produce:

- **Argument structure**: what arguments the verb takes and how often
  - Direct object (mafʿūl bihi) — present vs absent (absolute usage)
  - Prepositional complement — which preposition(s), and frequency of each
  - Double object (for verbs like أعطى، سأل)
  - Cognate accusative (mafʿūl muṭlaq)
  - Clausal complement (أنّ / أن clause)
- **Absolute usage ratio**: how often the verb appears without an explicit object
  when it could take one. This is the خَلَقَ (96:1) signal — absolute vs
  transitive deployment.
- **Prepositional profile**: which prepositions bind to this verb form, with
  frequency. هدى إلى vs هدى + accusative; آمن بـ vs آمن لـ.

### 2. Noun governing patterns (lower priority)

For high-frequency nouns (50+ occurrences), produce:

- **iḍāfa patterns**: what appears in the muḍāf-ilayhi position
- **Adjectival modification**: which adjectives attach and how often
  (صراط + مستقيم = 73% is the canonical example)
- **Prepositional government**: which prepositions this noun governs or is
  governed by

### 3. Output format

TSV keyed by (root_arabic, form_tag), joinable to form-dimensions.tsv and to
the contextual profiles.

Proposed columns:

| Column | Description |
|--------|-------------|
| root_arabic | Space-separated Arabic root (join key) |
| form_tag | Controlled vocab tag: PV:I, IV:II, NOUN_CONCRETE, etc. |
| instance_count | Total Quranic instances of this (root, form_tag) |
| arg_direct_object | Count of instances with explicit direct object |
| arg_absolute | Count of instances with no explicit object (absolute usage) |
| arg_prep_profile | Semicolon-separated `prep:count` pairs (e.g., `بـ:15; إلى:8; لـ:3`) |
| arg_clausal | Count of instances with أنّ/أن clausal complement |
| arg_cognate | Count of instances with cognate accusative |
| arg_double_object | Count of instances with two objects |
| absolute_ratio | arg_absolute / instance_count |
| top_prep | Most frequent prepositional complement |
| notes | Agent notes on unusual patterns |

For nouns (lower priority), a separate file with iḍāfa/adjective/preposition
profiles.

Current source-of-truth note: the reviewed v3 aggregate
`output/final_v3/verb_valency_frames.tsv` is the current corpus-wide valence
table. The older `output/final/verb_valency_frames.tsv` is legacy mechanical
output and should only be used as a control. For diagnostics or traceability,
the underlying v3 Pass 1 `FRAME` and `ATTACH` rows remain available in
`output/pass1/sNNN/sNNN_syntax.tsv` and block files.

Archived 1c/1d ambiguity pilots, when present, live alongside the canonical
Pass 1 files rather than overwriting them:

- `output/pass1/sNNN/blocks/sNNN_AAA-BBB_amb.tsv` — per-block ambiguity patch
- `output/pass1/sNNN/sNNN_syntax_amb.tsv` — merged syntax with 1c patches
- `output/pass1/sNNN/sNNN_registry_amb.tsv` — registry built from that merge

Use `sNNN_syntax.tsv` for surface-valence aggregation and the active Pass 3
translation-support pipeline. Treat archived ambiguity rows as optional audit
evidence only; missing ambiguity rows mean "not recorded", not "resolved".

Pass 1 is enough for first-pass surface valence:

- direct object and clitic object
- governed preposition
- clausal complement
- subject/pro-drop signal
- absolute, intransitive, passive, and copular usage labels

Pass 2 can later enrich implicit or discourse-recovered arguments. Pass 3 is
translation support and is not needed for valence aggregation.

### 4. Reviewed final TSVs

The reviewed v3 final output files are in `output/final_v3/`. They are generated
by `scripts/merge_and_finalize_v3.py` from the validated v3 pass outputs and
validated by `scripts/validate_final_v3.py`.

- `clauses.tsv` from Pass 1 `CLAUSE` rows.
- `attachments.tsv` from Pass 1 `ATTACH` rows, with stable IDs, span fields,
  `prep_wid`, and bridge fields for concept/translation consumers.
- `cross_references.tsv` from Pass 2 cross-reference rows and candidate
  antecedent inventories.
- `implicit_arguments.tsv` from Pass 2 implicit/pro-drop argument rows.
- `ellipsis.tsv` from Pass 2 ellipsis rows.
- `translation_support.tsv` from Pass 3 `SUPPORT` and `ALT` rows, including
  ambiguity, scope, ellipsis, construction, and context-window guardrails.
- `review_issues.tsv` from `ISSUE` rows across the reviewed passes.
- Refreshed aggregate files from v3 reviewed rows:
  `verb_instances.tsv`, `noun_instances.tsv`, `verb_valency_frames.tsv`, and
  `noun_governing_patterns.tsv`.

The validator currently passes with these counts:

```text
58427 attachments
10636 XREF rows
11170 CAND rows
23782 SUPPORT rows
1153 ALT rows
```

Downstream ingestion now means building consumer-specific indexes or app/context
retrieval layers from `output/final_v3/`. It does not require more Pass 1/2/3
agent dispatch, and it no longer means creating the reviewed final TSVs.

## Approach

### Option A: Mechanical extraction + agent review

1. Parse each ayah JSON, identify verbs by grammar field
2. For each verb, scan surrounding words in the same ayah for:
   - Accusative nouns (potential direct objects) — heuristic from grammar field
   - Prepositions — identified by grammar tag
   - أنّ/أن particles — clausal complement markers
3. Agent reviews and corrects the mechanical extraction for ambiguous cases

Pro: cheap, deterministic base. Con: Arabic word order is flexible; mechanical
proximity heuristics miss fronted objects and misattribute shared-ayah nouns.

### Option B: Agent annotation per ayah (recommended)

1. For each ayah, give the agent the full word list with grammar tags
2. Agent identifies, for each verb: its subject, object(s), prepositional
   complements, and whether it's used absolutely
3. Output structured per-verb annotation

Pro: handles Arabic syntax correctly (pro-drop, fronting, distant objects).
Con: expensive (6,236 ayahs × agent call).

### Option C: Hybrid — mechanical draft + agent correction

1. Run Option A to produce a draft
2. Flag low-confidence cases (no object found for typically transitive verbs,
   multiple candidate objects, ambiguous prepositional attachment)
3. Agent reviews only flagged cases

Pro: balances cost and quality. Con: still needs a good mechanical parser to
produce useful drafts.

### Batching strategy

For any agent-based approach:

- Group by surah (natural batching unit)
- Small surahs (< 20 ayahs) can be batched together
- Large surahs (50+ ayahs) may need splitting by pericope/section
- Estimated: ~200-300 agent calls for full Quran coverage with Option B
- Can start with high-frequency verb roots (top 100 roots cover ~60% of verb
  instances) for a useful first pass

## Relation to other pipelines

```
Attachment enrichment (this work)
  → instance-level syntax/discourse/ellipsis/translation evidence
  → valency frames per (root, form_tag)
  → construction frames per Quranic occurrence
  → feeds _corpus/concepts Arabic units and Layer 2 deployment constraints
  → feeds translation pipeline as guardrails, not final renderings

Contextual profiles (_corpus/contextual/)
  → REFERENT + ROLE + SCOPE per (root, form_tag)
  → independent pipeline, runs in parallel
  → shares the same form-level keying

Furūq v2 (_corpus/furuq/v2/)
  → translation-risk/SAN guardrails (what a root is NOT, what would collapse)
  → independent pipeline, consumes legacy v1 only as audit/discovery input

All three feed Layer 2 (Quranic concept map) in _corpus/semantic_maps/
```

Attachment enrichment is fully independent. It reads the same ayah JSONs as
the contextual pipeline but produces separate output. It can be run, paused,
and resumed without affecting the other pipelines.

For grounded-senses specifically, the required bridge is a Quran-attested
construction table keyed by occurrence and by `root + stem + tag`. This lets
radial-polysemy roots be reviewed by frame before falling back to root image:
for example direct-object usage, `fi al-ard` usage, `mathal` object usage, or
other governed constructions may license different dictionary-attested
applications of the same root image.

### Concept-map bridge

`scripts/build_review_batches.py` now enriches each input word with deterministic
bridge fields:

- `unit_id` (`q:sura:ayah:wid`)
- `unit_type`
- `root_norm`
- `concept_root_norm`
- `form_tag`
- `concept_entity_id`
- `concept_form_group`
- `layer_scope`
- `feeds`
- `do_not_use_for`

Agents cite `unit_id` values, but they do not compute concept joins. Merge and
validation scripts should derive final bridge columns from the input word
objects. The bridge explicitly marks this data as `quran_instance` evidence and
prevents use for `layer1_dictionary_definition`.

## Scope decisions (resolved)

- **Approach**: Multi-pass hybrid. Mechanical extraction remains a baseline;
  agents annotate from scratch in syntax/discourse/translation-support passes.
- **Scope**: All verbs (19,396 instances) + all nouns (32,678 instances)
- **Agent model**: model can vary by pass; old docs assumed Opus. Prompt review
  has used GPT-5.5 high reasoning.
- **Output location**: `_corpus/attachment-enrichment/output/`

See `ORCHESTRATION.md` for the full agent execution guide.

## Possible venues with valency data

Beyond the primary consumers (translation pipeline, ayah JSON backfill, Layer 2
concept maps), the valency frame data enables:

### 1. Gloss disambiguation

When a verb root has multiple meanings, its valency frame often disambiguates.
هدى + إلى = "guide toward" vs هدى + accusative = "guide (directly)". The
attachment data can feed the gloss menu selection logic in the standardized
corpus — picking the right meaning based on which arguments the verb actually
takes in that instance.

### 2. Argument-aware commentary

The tier 1 commentary pipeline currently works word-by-word. With attachment
data, it could produce argument-aware commentary: "خَلَقَ here is used
absolutely (no object) — emphasizing the act of creation itself, not what was
created." The `absolute_ratio` and `arg_prep_profile` fields are directly
usable as commentary evidence in `1_30_assemble_word_ayah.py`.

Pass 3 also feeds ayah-level commentary through `context_window` support rows:
when an ayah's activated sense or ambiguity depends on surrounding ayat, the
translation/commentary layer can tell the reader or listener which intra-surah
window to check and why.

### 3. Cross-language argument mapping

Turkish and Arabic handle verb arguments differently (Arabic بـ → Turkish
direct accusative; Arabic absolute → English obligatory object). The valency
frames per verb become a systematic transfer table for the translation
pipeline, beyond just individual ayah lookups. A translation agent working on
an ayah can query `verb_instances.tsv` by `sura:ayah:wid` and know exactly
what argument pattern to expect for the target language.

### 4. Syntactic concordance / search

"Find all instances where آمن takes بـ" or "all verbs used absolutely in surah
96" become trivial queries on `attachments.tsv`. This is a queryable syntactic
concordance of the entire Quran — something not available in existing tools,
which only offer lexical concordance without syntactic structure.

### 5. Root network enrichment

The `cooccurrencePairs` in ayah JSONs are proximity-based, not syntactic. The
attachment data upgrades "root X appears near root Y" to "root X governs root Y
as its direct object" — a much stronger signal for the concept map. Syntactic
co-occurrence is the difference between "these roots appear together" and "this
root acts on that root."

## References

- Ayah JSONs: `_json/ayah_json/{surah}/{surah}-{ayah}.json`
- Form dimensions: `_corpus/semantic_maps/form-dimensions.tsv`
- Grammar parser: `_corpus/semantic_maps/scripts/build_form_inventory.py` (`parse_grammar()`)
- Existing ATTACH data: inside ayah JSON disambiguation arrays (2,266 entries)
- cooccurrencePairs: inside ayah JSON word entries (267,809 entries)
- Contextual plan: `_corpus/contextual/PLAN.md`
