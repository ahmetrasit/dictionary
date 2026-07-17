# Branch Encyclopedia Entry Writer Prompt

Write one evidence-grounded encyclopedia entry block for one frozen V4 branch.
The result will later receive a dedicated gloss/collision review and be
assembled into a complete root page.

## Inputs

```text
FOCUS_BRANCH={{FOCUS_BRANCH}}
FOCUS_BUNDLE={{FOCUS_BUNDLE}}
FOCUS_SCAFFOLD={{FOCUS_SCAFFOLD}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
ROOT_PACKET={{ROOT_PACKET}}
OUTPUT_FRAGMENT={{OUTPUT_FRAGMENT}}
```

Read:

- `ENTRY_GENERATION_PLAN.md`;
- `TRANSLITERATION_POLICY.md`;
- `schema/entry.schema.md`;
- the entire focus bundle;
- the entire generated focus scaffold;
- and the complete sibling roster in the root bundle.

## Task

Copy the generated focus scaffold and replace every explicit `REVIEW REQUIRED`
field to produce one complete branch block from:

```markdown
<!-- BEGIN BRANCH <root_id>/<branch_id> -->
```

through:

```markdown
<!-- END BRANCH <root_id>/<branch_id> -->
```

Follow the schema headings exactly.

The scaffold owns packet-backed identity, Arabic boundaries, linked lexical
rows, source-routing metadata, and evidence-bundle handles. Preserve those
fields exactly. If one is wrong, report a packet, bundle, or script defect
instead of silently rewriting it.

## Method

### 1. Preserve the generated V4 identity

Verify the stable root ID, branch ID, Arabic image, English scaffold,
provenance, source handles, and linked lexical rows against the focus bundle.
Do not regenerate them. The V4 branch is frozen. Do not debate whether it
exists, merge it with a sibling, or rewrite its Arabic boundary.

### 2. Read the Arabic boundary before writing target prose

Use `branch_image_ar`, `what_is_ar`, `what_is_not_ar`, `source_phrase_ar`,
linked lexical units, and the classical source entries. Existing English V4
text is a scaffold, not final prose.

### 3. Write the concept accounts independently

Write:

- a clear English account for a curious reader who knows no Arabic;
- and a Turkish account derived independently from the Arabic evidence.

Each account must explain the whole concept, its internal image or mechanism,
and its limits. Do not translate the English paragraph into Turkish or the
Turkish paragraph into English.

In English prose, pair every Arabic unit as `Arabic (English
transliteration)`. In Turkish prose, pair it as `Arabic (Turkish
transliteration)`. Repeat the pair on every mention. Never use transliteration
as a substitute for the Arabic anchor.

### 4. Establish the boundary and contrasts

Use the full sibling roster to explain the material same-root distinctions.
Use cross-root or form/collocation contrasts only when V4 or dictionary
evidence establishes them. QNet candidates may tell you what to inspect but
cannot support the published claim.

For every contrast, state:

- the shared zone;
- the distinguishing axis;
- and the evidence handle.

Do not use Quran occurrence distribution as branch evidence.

### 5. Explain lexical units and examples

Attach every relevant V4 lexical unit to the focus branch. Preserve the level
of bare form, derived form, or governed collocation. Explain source examples in
plain English and Turkish without promoting a collocational result into another
branch.

### 6. Write the source audit

For each materially relevant dictionary:

- give the stable source reference;
- quote the exact Arabic source phrase or excerpt;
- classify the relationship using the schema vocabulary;
- explain its contribution in English and Turkish;
- preserve examples, derivations, and restrictions;
- distinguish explicit disagreement from nuance, different organization, and
  silence.

The generated routing status and route note are lookup metadata, not source
relationship classifications. A `no_match` routing gap does not authorize
`no_located_attestation`, sole attestation, silence, or disagreement.

Keep an exact Arabic quotation unchanged. On the next lines, give a complete
English transliteration and a complete Turkish transliteration before the two
language explanations.

If only one source attests a branch or detail, say so plainly. Do not treat
single-source support as invalidity.

### 7. Draft renderings without forcing brevity

Supply initial English and Turkish rendering tables so the next reviewer has
concrete candidates to test. Give one to three candidates per language. The
first candidate may be a phrase or coordinated clauses and should attempt to
preserve the entire concept.

Mark familiar mainstream terms and loanwords as `recognition`, not `primary`.
Do not claim their actual modern-language footprint without evidence.

## Forbidden moves

- No branch activation or branch-specific Quran occurrence claims.
- No tafsir, theology, or contemporary commentary as lexical evidence.
- No model-memory source claims.
- No source quotation that is absent from the supplied evidence.
- No statement that dictionaries disagree merely because one is silent.
- No English-to-Turkish relay translation.
- No one-word requirement for glosses.
- No bare Arabic or bare Arabic transliteration in target-language prose.
- No invented target-language collision just to fill a section.

## Output

Return only the complete Markdown branch block. Do not return planning notes,
an evidence summary outside the block, or proposed software changes.
