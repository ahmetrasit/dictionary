# Entry Generation Orchestration Spec

This file explains how to turn one frozen V4 root inventory into one complete
English–Turkish concept-dictionary root page.

Read [ENTRY_GENERATION_PLAN.md](ENTRY_GENERATION_PLAN.md) for the editorial
principles and [schema/entry.schema.md](schema/entry.schema.md) for the required
shape of the finished entry. This run spec should not duplicate or weaken those
documents.

Read [TRANSLITERATION_POLICY.md](TRANSLITERATION_POLICY.md) for the hard rule
that every Arabic unit remains visible and carries a target-language-specific
transliteration.

## Cold-agent start here

This spec is the cold-start contract. A new agent should need only:

```text
working directory: /Volumes/OZTURK/_projects/dictionary
requested V4 root_id: for example root_001210
```

It must not rely on conversation history.

Read in this order:

1. `spec.md` completely;
2. `ENTRY_GENERATION_PLAN.md` completely;
3. `TRANSLITERATION_POLICY.md` completely;
4. `schema/entry.schema.md` completely;
5. every prompt named under Prompt sequence before invoking it.

Then:

1. Verify that `data/working/furuq_v4.sqlite` and
   `data/working/qac.sqlite` exist. Run `./scripts/sync_upstream.sh` only when
   they are missing or upstream refresh is explicitly required.
2. Run `python3 scripts/root_packet.py <requested-root_id>`.
3. Read the printed `root_envelope_id` and packet paths. A requested root ID
   may resolve to an envelope containing more than one V4 root record.
4. Run `python3 scripts/build_entry_bundles.py <requested-root_id>`.
5. Open `data/output/entry_bundles/<root_envelope_id>/INDEX.md` and perform the
   Required preflight below.
6. Instantiate `prompts/orchestrator.md` with the resolved paths and execute the
   complete Prompt sequence.
7. If delegation is available, independent branch drafts may be delegated with
   the supplied branch-writer prompt. If it is not available, the same agent
   performs the prompt roles sequentially. The evidence rules do not change.
8. Finish only after the Root-wide completion check passes and the final entry
   exists at `entries/<root_envelope_id>.md`.

Do not ask for stylistic choices already fixed by the plan or schema. Stop and
report only when evidence is genuinely missing, target-language usage cannot be
verified, or a new decision would change the linguistic claim.

Resolve the orchestrator inputs directly from the envelope ID:

```text
ROOT_ENVELOPE_ID=<root_envelope_id>
PACKET_JSON=data/output/root_packets/<root_envelope_id>.json
ROOT_BUNDLE=data/output/entry_bundles/<root_envelope_id>/ROOT.md
BRANCH_BUNDLE_DIR=data/output/entry_bundles/<root_envelope_id>/branches
DRAFT_DIR=data/output/entry_drafts/<root_envelope_id>
FINAL_ENTRY=entries/<root_envelope_id>.md
```

For each role prompt, derive its file inputs from these paths and the bundle
index. For `TARGET_LANGUAGE_SOURCES`, use the approved list when one exists; if
none has yet been fixed, verify claims in reputable monolingual sources, cite
what was used, and leave an explicit evidence note for anything unverified.

This is a complete cold-agent contract for producing a full draft. It is an
agent-readable orchestration runbook, not a one-command software pipeline: the
agent performs the supplied prompt roles, either by delegation or sequentially,
and checks their combined output. The publication choices listed at the end do
not block a clearly marked draft.

## Run unit and completion unit

The run unit is one normalized Quranic root envelope. The completion unit is a
single root page containing every V4 `(root_id, branch_id)` in that envelope.

The filesystem identity is `root_envelope_id`:

```text
one V4 root record:       root_000123
multiple alias records:  root_001210--root_001211
```

It is formed from the ordered V4 root IDs joined with `--`. Arabic root text is
display and linguistic data only; it is never used as a directory or filename.

Do not move to a new root while the current root contains a polished familiar
branch and unfinished rare branches.

## Source authority

Use each source only for the job it owns:

| Source | Use |
|---|---|
| V4 | Frozen branch inventory, branch boundary, lexical units, classical source handles and phrases |
| Classical dictionary entries in V4 | Source audit, examples, derivations, nuances, and explicit disagreement |
| QAC | Complete positioned root occurrences and morphology |
| Attachment enrichment | Observable syntax, argument structure, and constructions |
| QNet | Neighbor discovery only |
| Target-language dictionaries and corpora | Actual English or Turkish usage and collision/error analysis |

Quran context, QNet keywords, mainstream translations, and target-language
usage cannot alter a V4 branch.

## Files used in a run

```text
ENTRY_GENERATION_PLAN.md
TRANSLITERATION_POLICY.md
spec.md
schema/entry.schema.md
prompts/orchestrator.md
prompts/branch-entry-writer.md
prompts/gloss-collision-reviewer.md
prompts/quran-observatory-writer.md
prompts/root-editor.md
data/output/root_packets/<root_envelope_id>.json
data/output/entry_bundles/<root_envelope_id>/
data/output/entry_drafts/<root_envelope_id>/
entries/<root_envelope_id>.md
```

Generated packets, bundles, and drafts are replaceable work products. The
durable authored artifact is `entries/<root_envelope_id>.md`.

## Preparing a root

Synchronize upstream sources when they have changed:

```bash
./scripts/sync_upstream.sh
```

Generate the complete evidence packet:

```bash
python3 scripts/root_packet.py root_001210
```

Generate compact root and branch bundles:

```bash
python3 scripts/build_entry_bundles.py root_001210
```

The first command writes the full JSON/Markdown evidence packet. The second
command does not invent or summarize meaning; it only rearranges that packet
into convenient reading bundles.

## Required preflight

Before drafting:

1. Read the packet summary and branch roster.
2. Confirm that the bundle branch count equals the V4 packet branch count.
3. Confirm that every branch bundle contains `source_phrase_ar`, `source_refs`,
   linked lexical units, source entries, and its QNet discovery material when
   available.
4. Record all V4 root IDs in the root envelope.
5. Do not collapse aliases or overlapping V4 records.
6. Confirm that the Turkish transliteration guide is available at
   `docs/upstream/turkish-transliteration-guide.md`.

If packet evidence is unexpectedly absent, repair the packet or source lookup.
Do not compensate from model memory.

## Prompt sequence

### 1. Orchestrator

Start with `prompts/orchestrator.md`. It owns the branch roster, paths, order,
and final completeness check. It does not write unsupported linguistic claims.

The orchestrator creates:

```text
data/output/entry_drafts/<root_envelope_id>/branches/
data/output/entry_drafts/<root_envelope_id>/quran-observatory.md
```

No database or status ledger is needed. Existing branch fragments show what
has been drafted; the root editor checks the roster before completion.

### 2. Branch entry writer

For every V4 branch, run `prompts/branch-entry-writer.md` with:

- the focus branch bundle;
- the root bundle and full sibling roster;
- `ENTRY_GENERATION_PLAN.md`;
- and `schema/entry.schema.md`.

Write one fragment to:

```text
data/output/entry_drafts/<root_envelope_id>/branches/<root_id>--<branch_id>.md
```

The writer produces the source audit, concept accounts, boundary explanation,
lexical units, and verified Arabic contrasts. It must not assign Quran
occurrences to the branch.

Branches may be drafted independently only when every writer sees the complete
sibling roster. Parallel drafting never removes the final root-wide review.

### 3. Gloss and collision reviewer

Run `prompts/gloss-collision-reviewer.md` over each branch fragment after the
concept and source audit are stable.

The reviewer:

- writes one to three English renderings and one to three Turkish renderings;
- permits multi-word and multi-clause primary glosses;
- tests what every rendering preserves, loses, and adds;
- checks sibling and verified cross-root target-language collisions;
- treats mainstream translations and loanwords as explained secondary
  recognition terms only;
- and returns a complete revised branch fragment, not disconnected notes.

Where a claim depends on actual target-language use, cite a reputable English
or Turkish dictionary, corpus, or documented translation convention. If that
evidence is unavailable, mark the claim for target-language evidence rather
than asserting it from intuition.

### 4. Quran occurrence observatory writer

Run `prompts/quran-observatory-writer.md` once per root with the root bundle and
full packet JSON.

The result belongs at:

```text
data/output/entry_drafts/<root_envelope_id>/quran-observatory.md
```

It describes the complete occurrence census, forms, morphology, constructions,
and attachments. It may group mechanically by form or frame. It may not name,
rank, score, color, or imply an activated branch.

### 5. Root editor

Run `prompts/root-editor.md` with:

- the full branch roster;
- every reviewed branch fragment;
- the occurrence-observatory fragment;
- the entry schema;
- and the root packet for fact checking.

The editor assembles:

```text
entries/<root_envelope_id>.md
```

The editor may repair clarity, duplication, cross-references, citation shape,
and target-language consistency. It may not silently change a V4 boundary,
remove a branch, add a branch, or invent evidence.

## Source-audit rules during a run

- Quote the relevant Arabic source phrase exactly.
- Explain what the quotation contributes in both English and Turkish.
- Distinguish explicit support, compatible support, additional nuance,
  explicit disagreement, sole attestation, and no located attestation.
- Never call absence disagreement.
- Never infer source silence merely from a missing parsed excerpt.
- Describe different organization as different organization unless a source
  explicitly disputes the other position.
- Keep examples attached to the source that supplies them.

## Contrast rules during a run

There are two contrast passes:

1. **Arabic contrast:** why this frozen branch is not a sibling or verified
   semantic neighbor.
2. **Target-language contrast:** how an English or Turkish rendering may hide
   that Arabic distinction.

QNet may nominate the comparison. V4 and dictionary evidence must establish
the published distinction.

A target-language collision is recorded even when a gloss is reasonable in
isolation. For example, conventional Turkish `yol` can hide the distinction
between `ṣirāṭ` and `sabīl`. The entry must explain the verified Arabic
difference and the misconception created by the shared Turkish label.

## Gloss rules during a run

- Give one to three renderings in each target language.
- Put the most faithful usable rendering first.
- Do not reward brevity or one-word form.
- Use a phrase or coordinated clauses whenever the concept requires them.
- Do not turn explanatory additions into alleged lexical dimensions.
- Classify internal fit as `none`, `narrowing`, `broadening`, `displacement`,
  or `drifted_loanword`.
- Record target-language collision separately; it can coexist with any fit
  error.
- State the actual lost, added, or confused dimensions in plain language.
- A mainstream render or loanword is never the first-class primary rendering.

## Citation rules

Every material lexicographic statement must point to a V4 source reference or
classical dictionary entry. Preserve exact Arabic quotation separately from its
English and Turkish explanation.

Preserve exact Arabic quotations unchanged, then add complete English and
Turkish transliteration lines. In ordinary prose, use `Arabic
(target-language transliteration)` on every mention, including individual
letters, forms, roots, and both sides of a comparison.

Target-language usage claims need target-language citations when they are not
obvious or when they support a criticism of a familiar translation.

Quran observations cite QAC references and ayah references. Attachment claims
cite the relevant attachment unit or sample reference.

## Handling evidence gaps

The frozen branch remains part of the entry. If the bundle lacks evidence
needed to explain a source nuance:

1. check the full packet;
2. check the copied V4 dictionary entry;
3. report the missing lookup plainly;
4. leave a visible draft marker if necessary;
5. never fill it from memory or quietly omit the branch.

Draft markers must be resolved or explicitly retained as editorial notes before
the root page is called complete.

## Root-wide completion check

The editor must verify:

- exact equality between the V4 branch roster and the final branch headings;
- stable `(root_id, branch_id)` identities;
- no branch activation claims in the occurrence observatory;
- no QNet-only published contrasts;
- source phrases and references for each source audit;
- independent English and Turkish prose;
- no bare Arabic or bare Arabic transliteration in target-language prose;
- complete English and Turkish transliteration lines for source quotations and
  Arabic ayah contexts;
- one to three renderings per language for every branch;
- faithful multi-word rendering first where needed;
- explicit limitations for every mainstream or loanword rendering;
- collision checks against siblings and verified neighbors;
- and accessibility to a reader who knows no Arabic.

## Resuming a root

Resume by reading the branch roster and listing existing files under
`data/output/entry_drafts/<root_envelope_id>/branches/`. Continue with the first missing
or incomplete branch, then rerun the root-wide editor. No separate resume state
is required.

## First run

The first run is requested as `root_001210` and resolves to
`root_001210--root_001211`, representing `ق ر ء / ق ر أ`. Preserve both V4 root
records and all 19 branch records. Use the reading/recitation branch to
establish voice and the `read/recite/proclaim` and Turkish `oku` analyses, but
finish every branch before treating the pilot as complete.

## Decisions still needed before publication

These do not block the first authored pilot, but they should be settled from
that pilot rather than guessed in advance:

1. **Neutral occurrence context in English and Turkish.** A zero-Arabic reader
   needs verse context, but an existing translation of the focus word can bias
   branch judgment. Preferred direction: show the full Arabic ayah and a
   target-language context line with focus-root tokens masked or left as Arabic
   identity labels.
2. **Target-language source list.** Name the preferred English and Turkish
   monolingual dictionaries/corpora used to justify gloss-risk claims.
3. **Citation display.** Decide after the pilot whether public entries use
   inline source labels, footnotes, or expandable source blocks.
4. **Gold entry.** Once the first root is approved, preserve it as the style and
   depth example for later roots.
5. **Publication attribution and licensing.** Before public release, verify the
   attribution and reuse terms of the digitized dictionary editions and any
   target-language corpora quoted.

Do not solve these by adding infrastructure. Record the chosen conventions in
this file after the pilot.
