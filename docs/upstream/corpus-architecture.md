# Corpus Data Architecture

## Cold-Start Summary

This file is the current cross-subproject architecture for `_corpus/`.

Use it when deciding where new data belongs, what an agent should query, and
which source is authoritative for a given job.

The runtime flow is:

```text
QAC positioned morphology
  -> V4 dictionary lookup
  -> QAC-to-V4 form bridge where form handles are needed
  -> semantic relation graph expansion
  -> contextual + attachment constraints
  -> Furuq contrast guardrails
  -> sense licensing / activation records
  -> Arabic commentary
  -> target-language translation and commentary
  -> dictionary examples and product exports
```

The core boundary:

```text
QAC identifies the positioned Arabic unit.
V4 supplies possible dictionary senses.
The QAC-to-V4 bridge resolves positioned QAC stems to governed V4 form handles
when the match is unique and downstream-usable.
The relation graph expands nearby semantic candidates.
Contextual + attachment data constrain what is live in the ayah.
Furuq prevents collapse into nearby concepts.
The licensing agent records activated Arabic senses.
Commentary explains them in Arabic.
Translation renders them into a target language.
Reviewed activations enrich dictionary examples.
```

Frozen corpus is legacy/reproducibility/debug material. It is not the future
runtime authority for morphology, dictionary identity, activation, or final
sense licensing.

## Source Layers, Synthesis Layers, Products

`_corpus/` is a workspace of subprojects. Do not force every data type into one
database or one "corpus" concept.

There are three broad kinds of data:

```text
source layers
  QAC, V4, Furuq, contextual profiles, attachment enrichment, CRITICALS,
  network sources, lexicon evidence

synthesis layers
  semantic relation graph, activation DB, Arabic commentary, target-language
  rendering adapters

products
  dictionary, book, mobile app, app exports
```

The source layers can overlap in evidence, but each owns a different contract.
The synthesis layers combine those contracts into reviewed outputs. Products
consume reviewed outputs, not raw drafts.

## Layer Ownership Matrix

| Layer | Owns | Does not own | Current resources |
|---|---|---|---|
| QAC morphology | Positioned word/morpheme morphology, root seed, lemma, POS, aspect/mood/voice, measure/form where available | Dictionary senses, Furuq claims, final activation | `_corpus/v4/quranic-corpus-morphology-0.4.txt` |
| QAC-derived occurrence indexes | Mechanical occurrence and co-occurrence indexes keyed by QAC positions, roots, lemmas, POS, measure/form, and windows | Dictionary senses, activation truth, reviewed semantic coactivation | future `_corpus/qac/` or `_corpus/sources/qac/` |
| V4 dictionary | Level 1 roots, branches, forms, lexical units, collocations/constructions when governed, positive sense handles | Ayah-context activation, commentary, target-language rendering | `_corpus/v4/` |
| QAC-to-V4 bridge | Derived lookup from QAC rooted stem morphemes to governed V4 form handles, with unique/ambiguous/unmatched status | Morphology source truth, dictionary truth, activation truth | `_corpus/qac_v4/` |
| Furuq v2 | V4-consuming translation-risk guardrails and dictionary-only contrast claims: semantic invariants, generic-gloss collapse risks, sibling/rare-branch preservation, what X is not, why X not Y, near-neighbor/synonym/antonym distinctions, external dictionary boundaries | Positive sense inventory, morphology authority, Quranic context activation truth, target-language prose itself | `_corpus/furuq/v2/` (active; BTRISK v1.4 planned, branch SAN v3 pilot complete, v2-native store planned); `_corpus/furuq/v1/` (frozen legacy reference and read-only coverage-audit input) |
| Semantic relation graph | Typed weighted edges among handles, fields, collocations, constructions, occurrences later | Final sense licensing by itself | future `_corpus/graph/` |
| Contextual profiles | Aggregated valence, collocation, role, referent, polarity, discourse, usage profiles | Local syntax for one occurrence, dictionary senses | `_corpus/contextual/output/final_v3_profiles/` |
| Attachment enrichment | Local attachment, referent, role, scope, discourse, formula/refrain evidence, argument structure | Dictionary truth, final activation by itself | `_corpus/attachment-enrichment/` |
| CRITICALS and networks | Dense word/ayah observations, phonetics, grammar, semantics, inter-ayah and distant-ayah links, Fatiha Lens material | Canonical dictionary senses, production app rows without distillation | `_json/`, `_corpus/reports/*normalized-critical-details.tsv`, commentary prompts |
| Activation | Per-position activated senses with evidence, strength, confidence, review status, window used | Dictionary definitions, raw translation prose | future `_corpus/activation/` |
| Arabic commentary | Arabic explanation of activated dominant and secondary senses | Re-deciding morphology or dictionary inventory | future commentary outputs |
| Translation/rendering | Target-language translation and commentary translation from activated Arabic concepts | Arabic sense adjudication from scratch | future language adapters |
| Frozen corpus | Legacy reproducibility, migration audits, debugging old decisions | Future runtime authority | `_corpus/sources/frozen/` |

## Canonical Runtime Query Flow

### 1. QAC Morphology Layer

The licensing agent starts from QAC.

QAC provides the stable positional key:

```text
qac_ref = surah:ayah:word:morpheme
```

QAC also provides the lookup seed:

```text
root_join_key
lemma
POS
aspect / mood / voice
measure or Arabic form where available
```

QAC is morphology. It should not be asked to decide dictionary sense, Furuq
truth, or target-language rendering.

Mechanical occurrence and co-occurrence indexes should be derived from QAC, not
stored in V4. These indexes may include:

```text
root occurrence counts
lemma occurrence counts
form/measure occurrence counts
ayah/window co-occurrence pairs
root/form window neighborhoods
position-to-position lookup tables
```

Those indexes are source-derived search and statistics layers. They are not the
same as reviewed semantic activation or coactivation. Reviewed activation and
coactivation records belong in the activation/graph layers after evidence and
review.

### 2. V4 Dictionary Lookup

The agent uses the QAC root seed to query V4 dictionary material:

```text
root handle
branch handle
lexical-unit handle
collocation/construction handle where governed
candidate dictionary senses
```

V4 is Level 1 dictionary inventory. It defines what an Arabic concept can mean
outside a particular ayah and provides governed positive handles. It should not
record "this sense is active in this ayah" as canonical V4 data.

### 2.5. QAC-to-V4 Form Bridge

Form-level lookup passes through the bridge:

```text
qac_ref
  -> QAC root_join_key + stem/lemma/POS/measure
  -> qac_v4_form_bridge
  -> V4 form handle if unique and downstream_usable
```

QAC and V4 are not form-string-identical. QAC preserves positioned vocalized
surface morphology. V4 form handles use normalized Quranic stems and richer
form tags. The bridge exists to make that mismatch explicit.

Activation agents may consume a bridged form handle only when:

```text
match_status = unique
AND downstream_usable = 1
AND selected_v4_form_handle IS NOT NULL
```

If the bridge row is ambiguous, unmatched, or has no V4 forms, activation may
still use root and branch candidates, but it must not promote a form-level
activation without review or additional evidence.

Every bridge build requires a QAC/bridge audit covering QAC source completeness,
surah/ayah coverage, rooted stem coverage, bridge status counts, and examples
of unique, ambiguous, and unmatched rows.

### 3. Semantic Relation Graph Expansion

The agent expands candidate attention through a typed, weighted graph.

Graph nodes may include:

```text
root handles
branch/sense handles
form handles
lexical-unit handles
collocation handles
construction/frame handles
domain-field nodes
ayah/occurrence nodes later
```

Graph edges may include:

```text
near_synonym
synonym
translation_collision
antonym
polarity_pair
same_field
domain_membership
form_variant
branch_of
collocation_with
construction_member
valence_role
furuq_contrast
coactivation_in_window
distant_ayah_network
fatiha_lens
```

Graph methods such as clustering or random walk are allowed for discovery and
ranking. They do not license a sense by themselves.

The graph tells the agent what may be resonating nearby. Explicit evidence is
still required before activation.

### 4. Contextual and Attachment Constraints

The licensing agent reads contextual profiles for broad behavior:

```text
valence profile
collocation profile
role profile
referent profile
polarity profile
discourse profile
argument/referent supplement profile
```

It reads attachment-enrichment outputs for local structure:

```text
attachment
referent
role
scope
discourse link
formula/refrain evidence
argument structure
```

QAC contributes morphology. Attachment enrichment contributes local grammar and
semantic relationships. Contextual profiles contribute aggregated deployment
patterns.

### 5. Furuq Guardrails

Furuq v2 records sharpen the candidate senses:

```text
what X is not
why X, not Y
where a synonym, antonym, or near-neighbor can collapse conceptually
```

Furuq may include side summaries from V4/governed handles so the contrast can be
read, but it does not own positive sense inventory. It can create graph edges
and activation guardrails only after claims are canonical, reviewed, dictionary
evidence-linked, and projected from the v2 canonical store. Raw recall, v0/v1
candidates, and draft grounding rows are frozen legacy discovery/audit inputs
only.

### 6. Sense Licensing / Activation

The licensing agent scans each ayah with a default rolling context window.

Default window:

```text
5-7 ayahs centered on the target ayah
```

The default is not a prison. The record must store the actual window used:

```text
intra_ayah
previous_next_ayah
centered_5
centered_7
pericope
refrain_formula
discourse_link
distant_network
fatiha_lens
custom
```

The activation record should be structured before prose.

Minimum fields:

```text
activation_id
qac_ref
surah
ayah
word
morpheme
root_join_key
lemma
pos
measure
aspect
voice
v4_root_handle
v4_branch_handle
v4_form_handle
v4_lexical_unit_handle
collocation_or_construction_handle
activated_sense_id
activation_strength
confidence
context_window_used
evidence_refs
relation_graph_support
contextual_support
attachment_support
furuq_support
contrast_notes
review_status
adjudication_status
```

Activation strengths should distinguish:

```text
dominant
secondary
weak
rejected
blocked
```

Rejected and blocked rows are useful. They preserve "why not this sense" for
future agents and for Furuq/dictionary feedback.

### 7. Arabic Commentary

Arabic commentary consumes reviewed or review-eligible activation records.

It should explain:

```text
dominant activated senses
secondary or hidden activated senses
why the context licenses them
which near concepts are blocked
what grammar and relation evidence matters
```

Arabic commentary comes before target-language translation because it preserves
the Arabic concept analysis without forcing it through English, Turkish, or any
other language.

### 8. Translation and Target-Language Commentary

Translation agents consume:

```text
activated Arabic senses
Arabic commentary
Furuq contrast notes
target-language adapter rules
app/book product goals
```

They should not redo Arabic sense licensing from scratch. Their job is to
render licensed Arabic concepts with target-language grammar, naturalness, and
gap awareness.

### 9. Dictionary Enrichment

Reviewed activation records feed dictionary examples.

They may say:

```text
V4 branch sense X
  Quran examples:
    qac_ref A activates X strongly
    qac_ref B activates X secondarily
    qac_ref C rejects X because contrast Y wins
```

They should not silently rewrite V4 senses. If repeated activation evidence
shows V4 needs a new branch, split, merge, or sense correction, that becomes a
reviewed dictionary change request.

## Semantic Relation Graph Contract

The graph should be typed, scoped, weighted, and evidence-linked.

Do not build one undifferentiated "word similarity" graph.

Each edge should preserve:

```text
source_handle
target_handle
edge_type
edge_subtype
scope
weight
directionality
evidence_source
evidence_refs
review_status
usable_for_activation
notes
```

Different edge types influence activation differently:

| Edge type | Activation effect |
|---|---|
| synonym / near_synonym | semantic reinforcement; possible translation collision |
| antonym / polarity_pair | tension, contrast, merism, field resonance |
| same_field | thematic context and candidate expansion |
| domain_membership | Quranic discourse domain, such as marriage, inheritance, worship, judgment |
| furuq_contrast | distinction guardrail and "why not Y" evidence |
| valence_role | grammatical licensing and argument compatibility |
| collocation_with | phrase/construction sense candidate |
| coactivation_in_window | resonance signal requiring further evidence |
| distant_ayah_network | long-range thematic or structural resonance |
| fatiha_lens | S1-based lens relation for non-Fatiha passages |

Candidate graph algorithms:

```text
one-hop and two-hop expansion
typed random walk
personalized PageRank from target ayah nodes
community detection / clustering
window-local subgraph scoring
field/domain resonance scoring
```

These algorithms rank candidates. The licensing agent still needs:

```text
QAC position
V4 sense
contextual/attachment support
relation graph support
Furuq distinction
confidence
review status
```

## Field and Domain Strategy

Use two kinds of fields.

Lexical semantic fields:

```text
motion
speech
fear
knowledge
kinship
legal-contract
divinity-worship
```

Quranic discourse/domain fields:

```text
marriage
inheritance
worship
faith
judgment
covenant
combat
charity
creation
resurrection
```

Field membership must be multi-label.

Example:

```text
س ك ن
  lexical field: dwelling/rest/stillness
  domain fields: marriage-peace, divine-tranquility, habitation

ن ش ز
  lexical field: height/rising/separation
  domain field: marriage-conflict
```

Start with existing lexical fields, then add hand-seeded Quranic domain fields.
Let activation/window scans propose additional memberships, but require review
before production use.

Initial seed resources:

```text
_corpus/semantic_maps/step1_data/step3_clustering_output.tsv
_corpus/furuq/v2/ (accepted claims once the v2 store exists)
_corpus/furuq/v1/recall/master_recall.tsv (read-only legacy audit input)
_corpus/contextual/output/final_v3_profiles/
_corpus/attachment-enrichment/
```

## Collocations, Constructions, and Formulas

Some meanings are not licensed by a single word.

The activation layer must support:

```text
word sense
form sense
lexical-unit sense
collocation sense
construction/frame sense
discourse formula sense
```

Attachment enrichment and contextual profiles provide much of the local and
aggregated evidence for these. Branch-map/grounded-senses frame material can
support review packets and future governed construction handles, but
placeholder frame handles should not be promoted as accepted V4-owned positive
truth until governance exists.

## Review and Confidence Gates

Production consumers should not read raw draft rows.

Use staged records:

```text
draft
needs_review
reviewed
accepted
blocked
rejected
```

Translation and commentary can consume different thresholds:

- dominant accepted activations: normal rendering/commentary;
- secondary accepted activations: nuance or deeper commentary;
- weak reviewed activations: optional note only if product policy allows;
- rejected/block rows: guardrails and "why not" evidence, not positive meaning.

Every activation should preserve enough evidence references for a later agent
to explain why the decision was made.

## Product Mapping

### Dictionary

The dictionary is organized by root/branch/form/lexical-unit.

It consumes:

```text
V4 dictionary handles
accepted Furuq contrasts
semantic relation graph edges
reviewed activation examples
Arabic concept commentary
target-language adapters
```

It should not turn occurrence examples into unreviewed V4 sense rewrites.

### Book

The book is the full reading synthesis.

It consumes:

```text
activation records
Arabic commentary
target-language rendering
CRITICALS-derived synthesis
sense and distant-ayah networks
Fatiha Lens
graph analysis
section and surah commentary
```

### Mobile App

The app consumes simplified, stable exports.

It should not read raw Furuq packets, raw CRITICALS, raw graph drafts, or active
research folders. It should consume product-data exports.

## Frozen Legacy Policy

Frozen corpus remains read-only historical material.

Use it for:

```text
historical reproducibility
migration audits
debugging old semantic-map / branch-map / V4 decisions
compatibility with old scripts until replaced
```

Do not use it as future authority for:

```text
runtime ayah lookup
QAC root confirmation
mechanical occurrence or co-occurrence indexing
V4 dictionary identity
occurrence activation
final sense licensing
```

QAC replaces frozen for runtime morphology and mechanical occurrence /
co-occurrence indexes. Attachment enrichment and contextual profiles replace
frozen for the contextual/valence/attachment signals that old pipelines
approximated.

## Implementation Phases

### Phase 0: Documentation and Boundary Cleanup

Current work.

Tasks:

- keep this file as the cold-start architecture entry point;
- cross-link it from root and `_corpus` docs;
- mark stale frozen/V4 occurrence-confirmation language as legacy;
- document QAC as morphology seed;
- document occurrence and co-occurrence indexes as QAC-derived source artifacts;
- document activation as future occurrence/context authority;
- keep pending Furuq work in the factory repo.

### Phase 1: Positive Handle Mapping

Finish the V4 positive-handle contract.

Required output:

```text
V4 row -> governed positive handle mapping
```

Scope:

```text
roots
branches
forms
lexical units
collocations/constructions where governed
```

Do not use occurrence activation as canonical V4 identity.

### Phase 1.5: QAC-to-V4 Form Bridge

Build the derived form bridge after QAC and V4 positive handles exist.

Required output:

```text
qac_ref -> V4 form handle candidates
```

Required statuses:

```text
unique
ambiguous
unmatched
no_v4_forms
not_applicable
```

Required audit:

```text
QAC source row count equals qac.sqlite row count
all 114 surahs and expected ayah counts are present
qac_words covers all qac_morphemes word refs
every rooted QAC STEM morpheme has one bridge row
bridge candidates reference existing V4 positive form handles
status counts and examples are recorded
```

Stop condition:

Do not let activation consume bridged form handles until the audit has no
blockers. Ambiguous bridge rows can be retained as candidates, but they are not
downstream-usable form matches.

### Phase 2: Semantic Relation Graph v0

Create the graph schema and seed import plan.

Initial edge families:

```text
near_synonym
antonym / polarity_pair
same_field
domain_membership
furuq_contrast
collocation_with
valence_role
```

Initial seeds:

```text
semantic_maps lexical fields
Furuq recall/canonical projections
contextual profiles
attachment enrichment
manual Quranic domain fields
```

### Phase 3: Activation Schema and Pilot

Create the activation DB/schema and run a small pilot.

Pilot should test:

```text
qac_ref as occurrence key
V4 dictionary lookup
graph expansion
contextual/attachment constraints
Furuq guardrails
dominant/secondary/rejected activation records
Arabic commentary handoff
dictionary example feedback
```

### Phase 4: Product-Data Export

Export reviewed artifacts to the future product-data repo.

See the root-level `MIGRATION_PLAN.md` for the factory-repo to product-data-repo
migration strategy.

## Stop Conditions

Stop and redesign if any pipeline requires:

- frozen corpus as runtime authority;
- V4 occurrence rows as final activation identity;
- V4 as the source of mechanical occurrence or co-occurrence indexes;
- raw Furuq recall rows as production contrast truth;
- graph random-walk score as final sense license without evidence;
- target-language translation agent to redo Arabic sense licensing;
- dictionary examples to rewrite V4 senses without review;
- product app to consume raw factory packets.

## Current Entry Points

Primary architecture:

```text
_corpus/ARCHITECTURE.md
_corpus/IMPLEMENTATION_STATUS.md
MIGRATION_PLAN.md
```

Layer docs:

```text
_corpus/v4/README.md
_corpus/v4/POSITIVE_HANDLES_SCHEMA.md
_corpus/qac/README.md
_corpus/qac/SCHEMA.md
_corpus/qac_v4/README.md
_corpus/qac_v4/SCHEMA.md
_corpus/graph/README.md
_corpus/graph/SCHEMA.md
_corpus/activation/README.md
_corpus/activation/SCHEMA.md
_corpus/commentary/README.md
_corpus/rendering/README.md
_corpus/product-data/EXPORT_CONTRACT.md
_corpus/furuq/v1/README.md
_corpus/furuq/v1/POSITIVE_HANDLE_CONTRACT.md
_corpus/furuq/v2/README.md
_corpus/contextual/README.md
_corpus/attachment-enrichment/README.md
_corpus/concepts/README.md
_corpus/semantic_maps/howto.md
```

Legacy/scaffold docs with caveats:

```text
_corpus/domain_activation/README.md
_corpus/docs/commentary-pipeline-spec.md
_corpus/semantic_maps/SPEC.md
_corpus/semantic_maps/grounded_senses/LAYER2_PACKET_CONTRACT.md
_translations/translation-spec.md
_translations/_methodologies/concept-envelope-gloss.md
docs/data-model.md
docs/word-card-product.md
```

Implementation specs are v0 contracts. They are sufficient entry points for
schema/script design, but production population still requires code/schema
review, deterministic validation, and review/adjudication fields.

Current data resources:

```text
_corpus/v4/quranic-corpus-morphology-0.4.txt
_corpus/v4/v4.sqlite.gz
_corpus/v4/positive_handles.sqlite.gz
_corpus/qac/qac.sqlite.gz
_corpus/qac_v4/qac_v4_form_bridge.sqlite.gz
_corpus/qac_v4/audit/qac_v4_bridge_audit.md
_corpus/furuq/v1/recall/master_recall.tsv
_corpus/furuq/v1/schema/canonical-claim.schema.tsv
_corpus/contextual/output/final_v3_profiles/
_corpus/attachment-enrichment/output/final_v3/
_corpus/sources/frozen/
```
