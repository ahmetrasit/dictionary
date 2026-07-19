# Complete Root Editorial JSONL Prompt

Produce or revise one complete authored JSONL artifact for a root envelope.
This is the final root-wide linguistic consistency pass. It does not assemble
Markdown and it does not regenerate packet facts.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
ROOT_PACKET={{ROOT_PACKET}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
BRANCH_BUNDLE_DIR={{BRANCH_BUNDLE_DIR}}
CANDIDATE_JSONL={{CANDIDATE_JSONL}}
TARGET_LANGUAGE_SOURCES={{TARGET_LANGUAGE_SOURCES}}
OUTPUT_JSONL={{OUTPUT_JSONL}}
```

Read `ENTRY_GENERATION_PLAN.md`, `TRANSLITERATION_POLICY.md`, `spec.md`,
`schema/authored-entry.schema.md`, the complete packet and bundles, and the
entire candidate when revising one.

## Required result

Write a complete schema-conforming JSONL file containing every required record
type and exact packet key. The renderer will produce separate English and
Turkish encyclopedia entries. Do not write either Markdown file.

Check:

- exact root envelope and frozen branch roster coverage;
- one deep `branch` record for every frozen identity;
- one exact `branch_source` record for every branch/source handle, with a
  packet-substring selected quotation;
- one `lexical` identity record for every lexical unit and one
  `branch_lexical` interpretation for every packet link;
- exactly one prominent-quality primary gloss and one to three glosses per
  branch per language;
- independent English and Turkish concept accounts;
- complete boundaries, verified contrasts, lexical-unit analyses, and source
  audits with exact Arabic quotations;
- complete keyed language-specific transliterations required by the schema;
- exact transliteration-only `quran_form` and `quran_ayah` key coverage;
- no authored `quran_occurrence` records: occurrence rows and their surface
  transliterations are derived mechanically from packet order and the exact
  form-group overlays;
- structured `external_source` records, with stable IDs, valid URLs, bilingual
  display titles and locators, access date, source language, and a short exact
  supporting excerpt, for target-language or non-packet sources actually used;
  every Arabic excerpt has keyed English and Turkish transliterations;
- no QNet-only published distinction, branch activation claim, unsupported
  source claim, or unresolved placeholder.

## Root-wide evidence audit

Perform these passes over the complete root before accepting a candidate:

1. **Vocalization and form identity.** Inventory every Arabic unit and every
   transliteration. Preserve source vocalization; resolve unvocalized text only
   from inspectable authoritative evidence. Identical consonantal spelling does
   not prove identical pronunciation, lemma, morphology, lexical category, or
   meaning. Compare same-spelling units across all branches and lexical records
   and describe orthographic versus phonological identity accurately.
2. **Inflection and phrase coverage.** Verify person, number, gender, voice,
   case, construct state, suffixes, definite-article behavior, and complete
   quotation coverage. Recheck every reuse rather than fixing a single overlay.
3. **External-source availability.** Open every non-packet URL and confirm that
   the specific cited entry content is readable and supports the stated note.
   Query URLs, snippets, maintenance notices, blocked pages, and empty
   client-side shells are not evidence. Record the actual inspected location
   and a short exact supporting excerpt in the source's `verification` object.
   Supply independent English and Turkish display titles and locators. When the
   excerpt is Arabic, preserve it exactly and supply both required target-
   language transliterations. Remove unsupported claims or report a research
   gap.
4. **Cross-language independence.** Read English and Turkish fields separately;
   verify their own transliteration conventions, idiomatic glosses, collision
   analyses, and Arabic anchors.
5. **Rendered reading.** Validate the JSONL, render both languages to an
   isolated preview directory, run renderer `--check`, and read every branch,
   source-evidence section, lexical unit, Quran form group, and bibliography.
   Repair the JSONL, never the Markdown.

When non-packet evidence resolves a vocalization or supports a usage claim,
include a structured `external_source` record. Do not cite a source that was
not successfully inspected during the run.

## Editorial depth

The rendered result must read as an encyclopedia entry, not an audit checklist.
The primary gloss orients the reader immediately, while the concept account,
scope, exclusions, contrasts, lexical units, source analysis, and gloss-risk
discussion provide the depth. Do not shorten those fields merely because the
renderer will structure them.

Derive each branch concept and primary gloss from its complete source-backed
perimeter. Quran frequency, contexts, translations, and occurrence patterns
may not establish, sharpen, rank, or label any branch meaning or gloss as
dominant.

The primary gloss remains a compact, idiomatic dictionary orientation to the
central generative concept. Covering the full perimeter does not mean appending
an inventory of every derivative, source qualification, exception, or audit
finding to the gloss. Put that depth in the concept, scope, lexical-unit, and
source sections. Reject literal calques that are not natural standalone English
or Turkish phrases.

Every source claim must be traceable to supplied evidence. Preserve exact
Arabic quotation text. Do not infer disagreement from silence. Keep examples,
derivations, restrictions, and collocational effects at the level established
by their source.

In every free-text English field, pair each Arabic mention with its English
transliteration. In every free-text Turkish field, pair each Arabic mention
with its Turkish transliteration. Keyed overlay fields cover Arabic inserted by
the renderer; they do not repair bare Arabic typed into editorial prose.
Write standard idiomatic English and Turkish. Do not replace Turkish letters
or required Turkish transliteration diacritics with ASCII approximations.
Read the rendered bibliography in each language and reject untranslated display
metadata or bare Arabic excerpts.

The bundle/scaffold preflight validates freshness using the repository's
canonical JSON packet hash. Do not compare a raw packet file SHA-256 with the
manifest's canonical hash or report a mismatch on that basis.

## Mechanical boundary

Use only fields permitted by `schema/authored-entry.schema.md`. Do not duplicate
packet-owned Arabic, identity, ordering, counts, morphology, attachments,
occurrence cells, ayah text, or bibliography handles. Do not manually repair a
packet defect. Report it separately and leave `OUTPUT_JSONL` unchanged when it
prevents a truthful complete artifact.

## Output

Write only valid JSONL to `OUTPUT_JSONL`, one object per physical line in schema
order. Return a short completion report with expected/authored branch counts,
Quran-key counts, and unresolved evidence or target-language research gaps.
