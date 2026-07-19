# Entry Generation Orchestration Spec

This file is the cold-start runbook for turning one frozen V4 root inventory
into two encyclopedia entries: one English and one Turkish. The durable
editorial source is JSONL. Markdown is a deterministic projection and is never
hand-edited.

Read [ENTRY_GENERATION_PLAN.md](ENTRY_GENERATION_PLAN.md) for the linguistic
principles, [schema/authored-entry.schema.md](schema/authored-entry.schema.md)
for the JSONL contract, and
[TRANSLITERATION_POLICY.md](TRANSLITERATION_POLICY.md) for Arabic display and
target-language transliteration.

## Responsibility boundary

The top-level orchestrator owns the run. It reads this spec, starts and
monitors agents, runs scripts, reviews rendered output, and decides when
validation has passed. It must not delegate orchestration to a worker or ask an
editorial agent to manage other agents. Agent runs use immutable prompt
snapshots: monitor a running agent without injecting clarification, correction,
or redirection. Corrections are new runs started only after the current run has
completed.

Agents own editorial judgments:

- concept accounts and branch boundaries in explanatory prose;
- source relationships, contributions, and analysis;
- verified contrasts and target-language distinction notes;
- gloss choice, fit analysis, and collision analysis;
- language-specific transliteration where the schema explicitly requests it;
- target-language bibliography notes.

Scripts own everything mechanically recoverable from the packet or JSONL:

- root and branch identity, roster, ordering, Arabic images, and provenance;
- source and lexical-unit keys already present in the packet;
- Quran census, forms, counts, morphology, attachments, occurrence order,
  QAC references, Arabic surfaces, lemmas, and Arabic ayah text;
- validation, language separation, section/table construction, Markdown
  escaping, generated markers, and deterministic rendering.

An agent must never retype packet-owned occurrence facts merely to fill a
Markdown table. If the renderer needs a mechanical value, extend the script or
packet contract. If the value requires linguistic judgment, add only the
smallest keyed editorial field to JSONL.

Agents never edit rendered files. The top-level orchestrator also never
manually repairs authored JSONL or rendered Markdown: it sends substantive
corrections to the producing agent in a fresh run and reruns the renderer. When
a completed run exposes a general failure mode, update the reusable prompt
before rerunning. Do not overfit orchestration chat or a prompt to the current
root's literal forms, branch IDs, or sources.

Do not stop or close an agent without explicit user authorization. A completed
agent remains available for follow-up review or correction until the user
authorizes closure.

## Cold start

A run starts with only:

```text
working directory: /Volumes/OZTURK/_projects/dictionary
requested V4 root_id: <requested-root-id>
```

Read in this order:

1. `spec.md`;
2. `ENTRY_GENERATION_PLAN.md`;
3. `TRANSLITERATION_POLICY.md`;
4. `schema/authored-entry.schema.md`;
5. every prompt used in the run.

Then:

1. Verify `data/working/furuq_v4.sqlite` and `data/working/qac.sqlite` exist.
   Run `./scripts/sync_upstream.sh` only when they are missing or refresh was
   explicitly requested.
2. Run `python3 scripts/root_packet.py <requested-root_id>`.
3. Read the resolved `root_envelope_id`. An envelope may contain multiple V4
   root records.
4. Run `python3 scripts/build_entry_bundles.py <requested-root_id>`.
5. Run `python3 scripts/build_entry_scaffolds.py <requested-root_id>` while the
   legacy scaffold remains useful as a reading aid. It is not an authored
   output and is not copied into the canonical JSONL.
6. Perform the preflight below.
7. Produce independent candidate JSONL files with the requested editorial
   agents. Every candidate must follow the same schema and see the complete
   sibling roster. Freeze the prompt snapshot for the duration of each run.
8. Review candidates for evidence, depth, gloss quality, transliteration, and
   cross-language independence after their runs finish. General defects update
   the reusable prompts; then route correction through a fresh run by the
   candidate's producing agent. A reviewing agent may produce a revised
   candidate; the orchestrator does not hand-edit it.
9. Select the reviewed artifact as
   `entries/source/<root_envelope_id>.jsonl`.
10. Run the deterministic renderer to create both language entries.
11. Inspect both rendered files, including deep lexical analysis and the full
    Quran appendix. After the relevant current run completes, route editorial
    defects through the producing prompt and renderer defects through the
    script implementer's reviewed task.
12. Finish only after focused tests and renderer `--check` pass.

## Paths

```text
ROOT_ENVELOPE_ID=<root_envelope_id>
PACKET_JSON=data/output/root_packets/<root_envelope_id>.json
ROOT_BUNDLE=data/output/entry_bundles/<root_envelope_id>/ROOT.md
BRANCH_BUNDLE_DIR=data/output/entry_bundles/<root_envelope_id>/branches
SCAFFOLD_DIR=data/output/entry_scaffolds/<root_envelope_id>
CANDIDATE_DIR=data/output/entry_drafts/<root_envelope_id>__<agent_label>
AUTHORED_JSONL=entries/source/<root_envelope_id>.jsonl
ENGLISH_ENTRY=entries/en/<root_envelope_id>.md
TURKISH_ENTRY=entries/tr/<root_envelope_id>.md
```

The JSONL is the durable machine-readable intellectual artifact. The two
Markdown files are durable human-readable generated artifacts. Packets,
bundles, scaffolds, and candidate drafts are replaceable work products.

## Source authority

| Source | Use |
|---|---|
| V4 | Frozen branch inventory, boundary, lexical units, classical source handles and phrases |
| Classical dictionary entries in V4 | Source audit, examples, derivations, nuances, and explicit disagreement |
| QAC | Complete positioned root occurrences and morphology |
| Attachment enrichment | Observable syntax, argument structure, and constructions |
| QNet | Neighbor discovery only |
| Target-language dictionaries and corpora | English or Turkish usage and collision/error analysis |

Quran context, Quran frequency, QNet keywords, mainstream translations, and
target-language usage cannot establish, narrow, broaden, rank, or call any V4
branch meaning dominant. They also cannot select or sharpen a primary gloss.

## Required preflight

Before authoring:

1. Confirm the packet root envelope and ordered V4 root IDs.
2. Confirm packet, bundle, and scaffold branch counts agree.
3. Confirm every branch bundle contains its Arabic boundary, source phrase and
   references, linked lexical units, and routed source entries.
4. Record the exact frozen `(root_id, branch_id)` roster.
5. Do not collapse aliases or overlapping V4 records.
6. Confirm `docs/upstream/turkish-transliteration-guide.md` is available.
7. Confirm all generated manifests match the current packet by running the
   bundle and scaffold builders successfully. Their manifest hash is computed
   from canonical JSON serialization via `packet_sha256`; a raw byte hash of
   the packet file is a different value and must not be compared with it.

If evidence is unexpectedly absent, repair the packet or lookup. Do not
compensate from model memory.

## Agent sequence

### 1. Top-level orchestrator

The current top-level agent follows `prompts/orchestrator.md` directly. This
role is not delegated. It owns paths, agent assignments, monitoring, review
routing, script execution, and final completeness.

### 2. Independent editorial candidates

When parallel comparison is requested, start independent agents with the
requested models and reasoning levels. Give each:

- the complete packet and root bundle;
- every branch bundle and the full sibling roster;
- the editorial plan, transliteration policy, and authored JSONL schema;
- the branch, gloss, Quran transliteration, and root-editor prompts;
- a distinct candidate output path.

Each agent writes one complete candidate JSONL. Parallel agents must not see or
edit one another's candidates during independent drafting. Prompt snapshots
remain corpus-general: the root selector and input/output paths are template
values, not permission to add root-specific rules, expected readings, glosses,
or source conclusions.

### 3. Review

Use a persistent review agent for scripts and another editorial review pass as
needed. For script work:

1. the script implementer writes code and focused tests;
2. a code-review agent reviews the actual patch;
3. findings are sent back to the same implementer;
4. the implementer applies fixes and reruns tests;
5. the reviewer checks the revised patch.

For editorial work, findings go to the agent that produced the candidate. The
reviewer or producer writes the revised JSONL; the orchestrator never patches
linguistic content manually.

### 4. Canonical JSONL

The root editor returns JSONL records only. It does not assemble Markdown. The
canonical file contains editorial content and keyed transliterations, never
duplicated packet facts. It must include exactly the record types and keys
required by `schema/authored-entry.schema.md`.

### 5. Deterministic rendering

Render both entries with:

```bash
python3 scripts/render_language_entries.py \
  entries/source/<root_envelope_id>.jsonl \
  --packet data/output/root_packets/<root_envelope_id>.json \
  --output-dir entries
```

After corrections, replace renderer-owned files with `--force`. Confirm the
checked-in projections are current with:

```bash
python3 scripts/render_language_entries.py \
  entries/source/<root_envelope_id>.jsonl \
  --packet data/output/root_packets/<root_envelope_id>.json \
  --output-dir entries --check
```

`--check` is mandatory before completion.

## Human-readable entry requirements

English and Turkish are separate encyclopedia entries, not bilingual audit
dumps. Each file must be readable without the other and must contain:

- root identity and a branch overview;
- every frozen branch exactly once;
- a prominent primary gloss immediately below each branch heading;
- alternatives and their fit/collision analysis;
- a deep concept account, scope, exclusions, Arabic contrasts, lexical units,
  source audits with exact Arabic quotations, and target-language notes;
- one neutral root-level Quran observatory generated from packet facts;
- complete occurrence and ayah coverage without branch activation claims;
- bibliography and stable evidence handles.

The primary gloss is orientation, not a substitute for the concept account.
Depth, source auditability, and accessible prose remain required.
The prose in each file must use standard target-language orthography. In
particular, Turkish prose may not be flattened to ASCII in place of Turkish
letters and diacritics.

## Linguistic rules

### Source audits

- Quote only Arabic text present in supplied evidence.
- Classify relationships as explicit support, compatible support, additional
  nuance, explicit disagreement, sole attestation, or no located attestation.
- Never turn absence or a routing failure into disagreement.
- Keep examples and claims attached to their source references.
- Every external-source record identifies the inspected entry location, access
  date, source language, bilingual display title and locator, and a short exact
  supporting excerpt. An Arabic excerpt includes separate English and Turkish
  transliterations. A query shell, maintenance page, snippet, or inaccessible
  result is not verification.

### Contrasts

- Distinguish Arabic contrast from target-language collision.
- QNet may nominate a neighbor; V4 or dictionary evidence must establish the
  published distinction.
- Quran occurrence distribution is never branch evidence.

### Glosses

- Give one to three candidates per branch per language and exactly one
  `primary` candidate.
- Prefer a phrase or coordinated clauses when one word drops a dimension.
- Roles are `primary`, `alternative`, or `recognition`.
- Fit values are `none`, `narrowing`, `broadening`, `displacement`, or
  `drifted_loanword`.
- State what each candidate preserves, loses, adds, and may confuse.
- Familiar translations and loanwords are secondary, never primary by
  familiarity alone.
- The primary gloss must orient to the complete source-established perimeter
  of the branch. Quran frequency or familiarity cannot narrow that perimeter
  or determine which gloss is primary.
- Full-perimeter fidelity does not make the primary gloss an inventory. It is a
  compact, idiomatic orientation to the central concept; derivatives, caveats,
  and source qualifications belong in the deeper encyclopedia sections.

### Arabic anchors and citations

Every Arabic unit in English prose carries English transliteration; every
Arabic unit in Turkish prose carries Turkish transliteration. Exact Arabic
source quotations remain unchanged and receive the language-appropriate full
transliteration in the rendered entry. Material claims cite packet-backed V4,
dictionary, QAC, attachment, or verified target-language handles.

### Quran neutrality

No occurrence is assigned, ranked, scored, colored, or described as probably
belonging to a branch. Quran forms, contexts, translations, and frequencies
also cannot establish, sharpen, rank, or label a branch meaning or gloss as
dominant. Occurrence tables and ayah contexts are rendered from the packet.
Editorial JSONL may supply only schema-approved keyed linguistic material; it
may not copy or override packet fields.

## Completion check

The top-level orchestrator must verify:

- exact branch roster equality;
- complete source-audit and lexical analysis for every branch;
- independent English and Turkish prose;
- standard English and Turkish orthography, without ASCII-flattened Turkish;
- prominent primary glosses plus full encyclopedia depth;
- no unsupported, memory-supplied, or QNet-only claims;
- no branch activation language in Quran material;
- exact authored form and ayah key coverage, plus complete script-generated
  packet occurrence coverage using form-derived surface transliterations;
- correct language-specific transliteration and no bare Arabic anchors;
- localized external-source titles and locators, with no bare Arabic evidence
  excerpt in either language projection;
- no unresolved placeholders;
- focused script tests pass;
- renderer `--check` passes;
- `git diff --check` passes.

An agent's count or visual scan never replaces deterministic validation. A
passing validator also never replaces the top-level agent's deep lexical and
reader-quality review.

## Resuming and correction

Resume from the canonical JSONL, candidate files, active agent IDs, and `git
status`. Do not regenerate or overwrite a candidate that is under review.
Do not message or redirect an agent while it is running. Wait for completion,
classify the defect as root-specific or general, update the reusable prompt for
general defects, and start a fresh run with a new output path or an explicitly
owned replacement path.
Correction ownership is stable:

- editorial defect: producing editorial agent;
- renderer/schema/test defect: original script implementer;
- packet defect: packet pipeline owner.

Never repair a generated Markdown file manually. Rerender after its source or
renderer is corrected.

## Publication decisions

The pilot should settle the preferred target-language dictionaries/corpora,
citation display, neutral translated Quran context policy, gold-entry style,
and source licensing. These decisions do not justify weakening evidence or
mixing the two language files.
