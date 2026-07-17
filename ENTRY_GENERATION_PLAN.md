# Concept Dictionary Entry Generation Plan

This project builds an Arabic-rooted concept dictionary in English and Turkish.
It is not a list of one-word equivalents. Each entry explains a frozen V4
branch as a complete concept, shows its lexicographic evidence and boundaries,
and lets a reader observe the root's Quranic occurrences without being told
which branch is active in an occurrence.

The work is linguistic and editorial. The repository should remain a simple
workbench: copied sources, deterministic packet/bundle/scaffold scripts,
structural validation, and human-readable root entries.

## Purposes of the dictionary

The dictionary has seven connected purposes.

### 1. Faithful concept rendering

Render the Arabic concept faithfully in each target language by explaining:

- what the branch includes;
- what it excludes;
- its irreducible semantic dimensions;
- how it differs from sibling branches, similar roots, forms, and
  collocational branches;
- and where a target-language rendering loses, adds, or shifts meaning.

The translation target is the concept, not a conventional dictionary token.

### 2. Understanding for a reader with no Arabic

Give a curious English- or Turkish-speaking reader a genuinely deeper
understanding without assuming knowledge of Arabic grammar, morphology, or
lexicography. Arabic expressions and source phrases remain visible, but every
important point is explained in clear target-language prose. Necessary
technical terms are explained rather than left as jargon.

Every Arabic word, form, root, phrase, or individual letter used in
target-language prose is written in Arabic script first and followed by a
language-appropriate transliteration. The Arabic anchor is never replaced by
transliteration, and a reader is never left with unexplained Arabic script.

### 3. Quranic occurrence observation

Show every Quranic occurrence of the root, together with its word form,
morphology, construction, and attachments. This is an observatory, not an
activation result. The reader receives the evidence needed to compare the
occurrences with the branch inventory and decide for himself or herself which
branch may be relevant.

### 4. Scholarly auditability

Make the lexicographic argument visible. An entry should show:

- which reference dictionaries contribute to or support the branch;
- the exact Arabic source phrases and examples used;
- where sources converge;
- where they add different nuances or derivations;
- where they explicitly disagree;
- and where a branch or detail is attested by only one source.

The reader should be able to inspect how the entry was formed rather than
having to trust an unexplained definition.

### 5. Preservation of every branch

Keep every frozen V4 branch alive. Branch inclusion, order, detail, or
prominence must not depend on whether the branch appears likely, frequent, or
activated in the Quran. Rare, source-specific, and non-observed branches remain
part of the dictionary.

### 6. Correct semantic level

Keep branch, form, lexical-unit, and collocational meaning at their proper
levels. V4 already gives governed collocations their own branches where
appropriate. Those collocational branches receive their own entries; their
results must not be inflated into a different bare-root branch. Corpus
attachment patterns may illustrate deployment, but they do not create new
dictionary branches.

### 7. Translation literacy

Teach readers how translations can mislead without presenting the lesson as a
warning against translation itself. The entry explains narrowing, broadening,
displacement, loanword drift, and collisions in which one target-language word
hides the difference between separate Arabic concepts. A reader should
gradually learn to ask what a translation preserves, loses, adds, or confuses.

## Governing principles

### The V4 branches are frozen

V4 supplies the authoritative branch inventory and branch boundaries for this
project. The branches have already been audited repeatedly. Entry generation
does not reopen, merge, reject, downgrade, or invent branches.

Any V4 review or provenance metadata is preserved as source information, not
treated as a new work queue. Describing disagreement among dictionaries
explains the history and structure of the concept; it does not put the branch
itself back on trial.

Every entry keeps the stable identity:

```text
(root_id, branch_id)
```

Filesystem paths use a V4-derived `root_envelope_id`, never Arabic root text.
For one V4 root record it is that `root_id`; when normalized aliases share one
root envelope, their ordered IDs are joined with `--`, for example
`root_001210--root_001211`. This storage identity does not merge or alter any
`(root_id, branch_id)` identity inside the entry.

When more than one V4 root record belongs to the same normalized root, all
identities remain visible. Overlapping branches may cross-reference one
another, but they are never silently merged.

### Arabic evidence is authoritative

V4 Arabic boundaries, Arabic source phrases, and the allowed classical
dictionary texts ground the concept. Existing English V4 fields are useful
scaffolds, not final English prose and never a source to be translated into
Turkish.

English and Turkish are written independently from the Arabic evidence. They
must describe the same branch boundary, but neither language is translated
from the other.

### Arabic anchors and target-language transliteration

Follow [TRANSLITERATION_POLICY.md](TRANSLITERATION_POLICY.md) everywhere in a
published entry.

In English prose, write Arabic first and then English-oriented transliteration:

```text
سَبِيل (sabīl)
صِرَاط (ṣirāṭ)
```

In Turkish prose, write Arabic first and then Turkish-oriented transliteration:

```text
سَبِيل (sebîl)
صِرَاط (ṣirâṭ)
```

This applies to every mention, including roots, individual letters, forms,
collocations, comparisons, headings, tables, gloss notes, and Quran examples.
Do not use bare Arabic in target-language prose and do not use a bare
transliteration without its Arabic anchor.

Exact Arabic source quotations remain unchanged. Put a complete English
transliteration and a complete Turkish transliteration immediately below the
quotation rather than inserting Latin text inside it.

### Evidence precedes target-language wording

The drafting order is deliberately:

```text
source evidence
  -> branch boundary and contrasts
  -> English and Turkish concept prose
  -> Quran occurrence observatory
  -> target-language glosses and error analysis
```

Common translations, loanwords, Quranic frequency, and familiar theological
language must not reshape the branch before its evidence has been understood.

### The gloss is not a simplification

A gloss is the most appropriate and faithful target-language rendering that
can be offered at compact scale. It is not required to be one word. It may be
a phrase or several coordinated clauses when the target language distributes
across several words what Arabic packages into one concept.

For example, a Turkish rendering of `ihdinā` need not be reduced to `doğru
yola ilet` when the established branch includes showing the right way,
bringing someone to it, and advancing or sustaining that person along it. A
multi-clause rendering such as `doğru yolu göster, o yola ilet, o yolda
ilerlet` can be more faithful.

Longer wording is not automatically more accurate. A multi-word gloss may
unpack only source-grounded dimensions. It must not add an unsupported temporal
sequence, purpose, agent, intensity, causality, doctrinal association, or
register.

### Languages package concepts differently

Different languages lexicalize different combinations of semantic dimensions.
One Arabic root or word may package dimensions that Turkish or English normally
expresses with several words. Conversely, one Turkish or English word may span
several Arabic concepts that Arabic keeps distinct.

This is tested branch by branch. The project does not need a universal claim
that one language is richer, poorer, or always more atomizing than another.

## Evidence used for each root

### V4 branch evidence

The evidence packet should retain the linguistically useful V4 fields,
including:

- `root_id`, `root_norm`, and `source_root_norm`;
- `branch_id`;
- `branch_image_ar`;
- `what_is_ar`;
- `what_is_not_ar`;
- `branch_image_en`, `what_is_en`, `image_en_fit`, and
  `image_en_gap_note` as scaffolding only;
- `source_refs`;
- `source_phrase_ar`;
- `status`, `review_note`, `origin_corpus`, and `contaminated` as preserved
  provenance metadata;
- linked lexical units, senses, branch links, examples, and their source
  phrases;
- and the full relevant classical dictionary entries.

The authored entry also supplies verified English and Turkish transliterations
for every Arabic unit; raw QAC or Buckwalter fields are evidence, not
reader-facing transliteration.

The exact source text matters because a source reference alone cannot show
whether a dictionary supplies the branch itself, an example, a derivation, a
restriction, or a competing analysis.

### QAC occurrence evidence

For every morpheme assigned to the normalized root, retain at least:

- Quran reference and word position;
- exact Arabic surface;
- stem and lemma;
- root spelling;
- part of speech;
- form or measure where available;
- aspect, mood, and voice;
- and the full morphology features.

QAC is a positioned morphology and occurrence source. It is not a dictionary
authority and does not assign occurrences to branches.

### Attachment enrichment

Use attachment enrichment to show how words of the root are deployed:

- verb and noun instances;
- direct objects and object types;
- prepositions and their complements;
- subjects and omitted arguments;
- modifiers, possessors, and governed noun patterns;
- valency frames;
- and representative constructional examples.

These rows help the reader observe Quranic usage and help the writer explain
forms and constructions. They do not create a branch or decide activation.

### QNet

Use QNet to discover possible semantic neighbors for comparison. Consensus
keywords and shared keyword neighborhoods are prompts for investigation, not
lexicographic evidence.

A QNet neighbor enters published distinction prose only after the relevant V4
and classical dictionary evidence confirms the shared zone and difference.
Generic keyword overlap must never become a semantic claim by itself.

### Target-language evidence

When an error claim depends on how a Turkish or English word is actually used,
consult reputable monolingual dictionaries, usage corpora, and established
translation practice. Mainstream translations show that a rendering is
conventional; they do not establish the Arabic meaning.

## Source audit for a branch

The source audit is explanatory rather than numerical. For each dictionary,
state its actual contribution in prose or a compact table.

| Source relationship | Meaning |
|---|---|
| Explicit support | The source directly states the branch or sense. |
| Compatible support | It describes substantially the same concept in different terms. |
| Additional nuance | It adds a restriction, derivation, example, subcase, or different emphasis. |
| Explicit disagreement | It rejects or materially disputes another recorded position. |
| Sole attestation | This source alone supplies the branch or detail among the consulted sources. |
| No located attestation | No support was located; this is not called disagreement. |

For each relevant source, include:

- dictionary name and stable reference;
- the exact `source_phrase_ar` or excerpt;
- an English explanation;
- a Turkish explanation;
- a complete English transliteration of the Arabic phrase;
- a complete Turkish transliteration of the Arabic phrase;
- what the phrase contributes to the branch;
- any illustrative lexical form or example;
- and any difference in derivation, grouping, or boundary.

Silence is not disagreement. A missing parsed excerpt is also not proof that a
dictionary is silent. Explicit conflict must be distinguished from absence,
different organization, and complementary nuance.

## Published unit: one root page

The practical publication unit is one human-readable root page. It contains:

1. root identity and orthographic aliases;
2. a branch index listing every frozen V4 branch;
3. one encyclopedia entry for each `(root_id, branch_id)`;
4. cross-references among overlapping or neighboring branches;
5. a root-level Quran occurrence observatory;
6. and the source bibliography used on that page.

This keeps all branches together so readers can compare them without erasing
their individual V4 identities.

## Encyclopedia entry for one branch

Each branch entry should contain the following content. The headings may be
adapted for readability, but the substance should remain.

### Identity and orientation

- Arabic root and normalized root;
- V4 `root_id/branch_id`;
- Arabic branch image;
- English and Turkish transliterations of the root, branch image, and every
  cited Arabic unit;
- associated lexical units, forms, and collocations;
- and a short reader-facing orientation in English and Turkish.

### English concept account

Independent English prose explaining the whole concept to a reader with no
Arabic. It should present the positive concept, internal dimensions, image or
mechanism, and important limits.

Every Arabic unit in the English account uses the form `Arabic (English
transliteration)`.

### Turkish concept account

Independent Turkish prose derived from the Arabic evidence. It should not be a
translation of the English account and should address Turkish-specific ways of
packaging or confusing the concept.

Every Arabic unit in the Turkish account uses the form `Arabic (Turkish
transliteration)`.

### Boundary and Arabic contrasts

Explain:

- what belongs to the branch;
- what does not;
- what it shares with sibling branches or neighboring roots;
- the precise axis on which they differ;
- relevant form distinctions;
- and relevant collocational-branch distinctions.

Every published contrast must be source-grounded. QNet may help find the
candidate but cannot supply the conclusion.

### Lexicographic account

Tell the source history of the branch:

- which dictionaries support it;
- how each formulates it;
- exact Arabic source phrases and examples;
- consensus and complementary nuance;
- explicit disagreements;
- sole-source material;
- and different choices of derivation or organization.

This should read as an accessible scholarly explanation, not as a dump of
database fields.

### Target-language rendering and confusions

For English and Turkish separately, explain:

- which expressions best render the concept;
- why a single word may be insufficient;
- which common translations or loanwords readers are likely to recognize;
- what those familiar terms lose, add, or shift;
- which distinct Arabic branches or roots become confused under the same
  target-language word;
- and why the focus concept is not those neighboring concepts.

This is target-language Furūq: the Arabic distinction must remain visible even
where the target language normally collapses it.

### Gloss menu

Give one to three English glosses and one to three Turkish glosses. Any gloss
may be:

- a single word;
- a multi-word phrase;
- or several coordinated clauses.

The first gloss should be the most faithful usable rendering, not the shortest
or most conventional one.

For each gloss, record:

- its role: primary faithful rendering, alternative, or recognition term;
- what it preserves;
- what it loses;
- what it adds;
- its main error type, if any;
- target-language concepts with which it may be confused;
- and a concise explanation of the resulting misconception.

Mainstream translations and Arabic loanwords may be mentioned and may
occasionally appear among the secondary glosses. They are never first-class
concept definitions or primary glosses. Whenever included, the entry must say
why they are familiar and exactly how they mislead.

## Gloss error and confusion analysis

### Internal fit errors

| Type | Test |
|---|---|
| Exact or no material distortion | The rendering preserves the branch without adding a foreign dimension. |
| Narrowing | The rendering drops one or more dimensions carried by the branch. |
| Broadening | It imports meanings or uses the Arabic branch does not carry. |
| Displacement | It simultaneously drops Arabic dimensions and imports foreign ones, producing a shifted concept. |
| Drifted loanword / false friend | A borrowed Arabic word has narrowed, broadened, moralized, institutionalized, or otherwise moved in the target language. |

A short note should name the actual lost or added facets. The category alone is
not an explanation.

Secondary notes may identify root-image loss, form-force loss, register shift,
modern technical associations, or added doctrinal and cultural load.

### Target-language collision

A collision occurs when one target-language expression is conventionally used
for two or more Arabic concepts whose distinction matters.

For example, Turkish `yol` is commonly used in connection with both `ṣirāṭ`
and `sabīl`. This can hide the fact that the Arabic concepts have different
boundaries. The `ṣirāṭ` entry must therefore use the verified Furūq evidence to
explain why `ṣirāṭ` is not `sabīl`, then explain how Turkish `yol` collapses
that distinction. The corresponding `sabīl` entry should make the reverse
comparison.

Collision is relational and can coexist with another error. A gloss may, for
example, be both narrowing and collision-producing.

Collision checks should cover:

- sibling branches of the same root;
- verified near-neighbor roots;
- opposite or adjacent concepts where the same gloss is conventional;
- mainstream translation conventions;
- and target-language loanwords with inherited religious associations.

As the dictionary grows, existing entries should be searched for reuse of a
candidate gloss. This can reveal a new collision without requiring a separate
software system.

## Quran occurrence observatory

The occurrence observatory belongs to the root page rather than being copied
under individual branch entries. This avoids implying that an occurrence has
already been assigned to a branch.

It should contain:

- the complete occurrence list in Quran order;
- counts by surface form, lemma, part of speech, and form or measure;
- constructional groupings derived from attachment enrichment;
- objects, prepositions, complements, modifiers, and other observable
  relations;
- representative examples chosen for constructional variety;
- and plain-language notes on recurring deployment patterns.

Complete Arabic ayah contexts carry both a readable English-oriented
transliteration and a Turkish-oriented transliteration. Buckwalter is not a
reader-facing substitute.

The observatory must not contain:

- an activated branch field;
- branch probabilities or scores;
- likely/unlikely branch rankings;
- branch-colored occurrence displays;
- or statements that a branch is Quranically active or inactive.

Mechanical links between an occurrence and its lemma, form, or construction
are allowed. Semantic assignment is left to the reader or to a separate
activation project.

## Root-by-root writing strategy

For each root:

1. Generate the evidence packet with all V4 branches and root-level evidence.
2. Generate hash-tracked evidence bundles and packet-backed entry scaffolds.
3. Confirm mechanically that every frozen branch identity and Quran occurrence
   is present.
4. Read the classical sources and write the editorial source audit for every
   branch without converting lookup status into source relationship.
5. Establish sibling and verified neighbor contrasts from the frozen boundary
   and source evidence.
6. Write the English and Turkish concept accounts independently.
7. Review the script-generated neutral Quran occurrence observatory, resolving
   transliterations and flagged joins without recreating packet-backed rows.
8. Draft one to three glosses per language, allowing multi-word and
   multi-clause renderings.
9. Test every gloss for internal error and target-language collision.
10. Add familiar mainstream or loanword renders only as explained secondary
   recognition terms.
11. Read the root page as a whole to ensure that every branch remains distinct,
    present, and equally independent of activation assumptions.
12. Run deterministic validation without allowing placeholders.

Complete one root before beginning the next. This keeps the sibling system
visible and prevents familiar branches from receiving polished entries while
rare branches remain placeholders.

## Linguistic completion check

A root page is ready when:

- every frozen `(root_id, branch_id)` has an encyclopedia entry;
- every substantive lexicographic statement has a source reference and Arabic
  phrase or excerpt;
- agreement, nuance, disagreement, sole attestation, and absence are described
  accurately;
- no Quran occurrence is assigned to a branch;
- every occurrence is available for reader observation;
- QNet-derived comparisons have been checked against dictionary evidence;
- English and Turkish accounts independently preserve the same Arabic
  boundary;
- each language has one to three glosses, with a faithful rendering first;
- multi-word glosses are used whenever a one-word gloss would reduce or shift
  the concept;
- every imperfect gloss explains its actual loss, addition, or displacement;
- target-language collisions with neighboring Arabic concepts are explained;
- every Arabic word, form, root, phrase, and letter in target-language prose
  has its Arabic anchor and the correct language-specific transliteration;
- exact Arabic quotations and ayah contexts have complete transliteration
  lines;
- mainstream translations and loanwords are secondary and carry explicit
  problem notes;
- and a reader with no Arabic can understand the entry without losing access
  to the Arabic evidence.

This is an editorial read-through, not a software certification process.

## First pilot: `ق ر ء / ق ر أ`

The first root page will use the normalized `ق ر ء` envelope while preserving
both V4 identities `root_001210` and `root_001211`. In the current source
snapshot they contain 19 frozen branch records. QAC contains 88 rooted
morphemes for the normalized root.

This root is a useful pilot because it exercises:

- overlapping V4 records and orthographic aliases;
- collection, recitation, teaching, time, menstrual-cycle, pregnancy, and
  other distinct branches;
- source consensus, different organization, explicit nuance, and
  source-specific material;
- collocational and lexical-unit evidence;
- Quran forms such as `قرأ`, `قرآن`, and `قروء`;
- the English `read/recite/proclaim` field;
- and the Turkish `oku` problem, including broadening, narrowing, and overall
  displacement.

The reading and recitation branch can establish the prose voice and gloss
analysis, but the pilot is not complete until all 19 V4 branch records have
full entries on the same root page.

## Simple project shape

Keep only what supports the linguistic work:

```text
ENTRY_GENERATION_PLAN.md       this editorial plan
TRANSLITERATION_POLICY.md      Arabic-anchor and per-language romanization rules
data/upstream/                 copied canonical sources
data/working/                  hydrated read-only source databases
data/output/root_packets/      disposable generated evidence packets
data/output/entry_bundles/     hash-tracked generated reading bundles
data/output/entry_scaffolds/   immutable packet-backed entry scaffolds
data/output/entry_drafts/      replaceable authored working fragments
scripts/sync_upstream.sh       copy and refresh the source material
scripts/root_packet.py         collect one root's evidence
scripts/build_entry_bundles.py build hash-tracked evidence bundles
scripts/build_entry_scaffolds.py build deterministic entry scaffolds
scripts/validate_entry.py      check final Markdown against packet facts/schema
entries/                       authored human-readable root pages
```

No authoring database, workflow engine, confidence scoring system, or complex
application architecture is required. The durable intellectual product is the
authored root page and its traceable evidence.

## Relevant inherited documentation

The principal inherited methodological references are copied under
`docs/upstream/`:

- `meaning-methodology.md`;
- `concept-envelope-gloss.md`;
- `furuq-v2-current-status.md`;
- `attachment-enrichment.md`;
- `gloss-menu-policy.md`;
- `loanword-policy.md`;
- `language-agent-contract.md`;
- `turkish-translation-spec.md`;
- `turkish-transliteration-guide.md`;
- and `corpus-architecture.md`.

They remain background evidence. This document records the agreed editorial
contract for this dictionary.
