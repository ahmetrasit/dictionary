# Dictionary audit and English definition plan

**Status: PENDING — full-corpus execution has not started.**

Updated: 2026-09-24. Owner: the top-level dictionary audit controller.

This document records the agreed next campaign. The completed S1 pilots are
calibration evidence; they do not mark the full audit or its repairs complete.
The present documentation task does not launch workers, repair entries, or
publish a release.

## 1. Purpose and accepted decisions

Check whether existing, source-anchored dictionary meanings are faithfully
represented by their Turkish definitions and glosses. Start with compact
inputs; examine fuller existing evidence only for flagged cases and a small
sample of entries passed by both checkers. Add English prose definitions that
preserve the full accepted Turkish definition paragraph.

The user-approved operating choices are:

- **Sol Max** performs the main semantic screen and drafts English definitions.
- **Luna Max runs in parallel as an independent, inexpensive checker.** It
  sees the same semantic inputs, without Sol's findings or English output.
- **Sol Max** investigates the combined flags and performs bounded repairs.
- **Astra Max** adjudicates difficult, unsupported, or disputed conclusions
  after the controller has inspected the earlier work.
- A separate **Sol Max** reviewer checks English definitions independently.
- **Every agent uses `reasoning_effort: max`.** Never silently reduce effort or
  substitute another model. The controller alone delegates.
- **Eight active workers maximum across all roles combined**, not eight per
  model or stage. Routine editorial decisions belong to the controller, with
  their reasoning recorded. Unsettled evidence can remain unsettled.

No audit stage chooses the correct root or a preferred sense from Quranic
context. Preserve documented alternatives, including Basra/Kufa derivations
of اسم, weak-root alternatives, source disagreements, and grammatical
headwords that do not assert a consonantal root. Missing coverage, transfer
faults, semantic wording problems, and runtime display faults are reported
separately.

## 2. Starting evidence and scope

Read these before operating:

1. [Agent navigation](AGENTS.md) and `public/agent/START_HERE.md`.
2. [Production runbook](v2/PRODUCTION_RUNBOOK.md),
   [orchestration contract](v2/orchestration/entry-creation.spec.md), and current
   writer/reviewer prompts linked from [orchestration](v2/orchestration/README.md).
3. [Furuq transfer](v2/FURUQ_TRANSFER_RUNBOOK.md) and
   [supplemental entries](v2/SUPPLEMENTAL_RUNBOOK.md) for their respective paths.
4. [S1 Sol audit](S1-DICTIONARY-AUDIT-2026-09-24.md) and
   [blind Luna comparison](S1-LUNA-BLIND-COMPARISON-2026-09-24.md).
5. The sister repository's
   [CDN update runbook](https://github.com/ahmetrasit/quran-apps/blob/main/CDN-UPDATE-RUNBOOK.md)
   before downstream transfer, app integration, or publication.

### Inventory to freeze at campaign start

The September 24 baseline has **1,700 root entries / 11,756 branches**, plus
**two grammatical headwords / three senses**. Count those separately: 1,702
entry objects and 11,759 branch/sense screening units. The cost estimates below
use the 11,756-branch root corpus; the three extra senses are negligible at
that precision.

Build the authoritative roster from the committed quran-data root and headword
manifests and their recorded dictionary source paths. Resolve back to the
owning dictionary outputs/exports. Include Quranic, Furuq, and supplemental
entries; do not infer the queue from numeric root ranges, an old static index,
or the 1,679-root multilingual-gloss rollout. A combined root envelope remains
one entry, and every branch of each selected entry is included.

Record both repository commits, manifest hashes, per-entry hashes, IDs,
branch/sense rosters, workflow namespaces, exact source paths, and prompt
versions. The completed comparison is dictionary commit `b76b4e139`; its
quran-data session note is `a43ca45f9`. These documentation commits are not new
data-release pins. Re-read the manifests and current pins before execution.

Scope is the authored branch/sense definitions, selected glosses and their
qualifications. Root-profile prose, every facet, every lexical-unit gloss,
neighbor distinctions and occurrence analyses are not all semantically
certified by the compact pass; read relevant ones during deeper investigation.
Report this coverage limit rather than calling all fields reviewed.

## 3. What the pilots establish

S1 covered 19 linked roots and all 157 branches, not a random corpus sample.
Sol referred 19 branches; deeper review retained nine. Luna independently
referred 14, passing six of those nine problem branches. Its three overlapping
referrals did not explicitly identify the retained problems. Luna nevertheless
raised two other wording issues retained by Astra and one unresolved concern.

The two screens referred **27 distinct branches in their union** (six shared
referrals). Retain distinct issues within a shared branch: Sol and Luna can
flag different fields or different defects in the same sentence. Agreement is
not proof of correctness, and disagreement is not a majority-vote decision.

The blind English comparison of 22 shared drafts found five minor fidelity
deviations and one substantive error in Luna drafts; Sol drafts were accepted
in that comparison. This supports Sol as the English author/reviewer, while
Luna supplies independent semantic observations. These small-run findings do
not establish a general error rate or guarantee future detection.

### Existing pending repair queue

Use the saved full reviews and final Astra adjudications, not just this table.
**None of these eleven branch corrections has been applied or published.**

| Priority | Branch | Bounded issue |
| --- | --- | --- |
| First | `root_000973/B003` | Distinguish worship from human-directed humbling; preserve supported false-power usages. |
| First | `root_000913/B003` | Unavenged does not imply that no redress was sought. |
| Next | `root_000355/B005` | Preserve the attested praise-seeking use for expenditure on oneself. |
| Next | `root_000532/B005` | Preserve the dairy sheep/goat qualification in the animal application. |
| Next | `root_000532/B007` | Preserve she-camel/male-camel participants in the mate-attachment application. |
| Next | `root_000532/B012` | Remove an unsupported small-size condition on the tree. |
| Next | `root_000532/B013` | Require abundant water; treat gathering as the source's naming explanation. |
| Next | `root_001092/B004` | Attribute rock descriptions to source variants instead of requiring hardness universally. |
| Next | `root_001583/B009` | Align the general-person gloss with the entry's recorded male referent. |
| Next | `root_001525/B008` | Preserve unqualified dispersal, rapid-departure variants and continuing travel separately. |
| Next | `root_000355/B002` | Keep testing as an attested example, not a mandatory condition of finding someone praiseworthy. |

`root_001273/B021` remains **unresolved editorial precision**, not a twelfth
confirmed error. Do not mechanically replace الحدقة with a pupil-only term:
the proposed fix can itself narrow the source. Follow the final Astra note.

Honor the [English draft hold list](v2/audits/s001-luna-blind-2026-09-24/ENGLISH-DRAFT-HOLDS.json).
The earlier nine confirmed branches already lack accepted English drafts in
the first aggregate. Drafts for the two additional findings and the unresolved
eye terminology also need reconsideration. All Luna drafts are experimental.

## 4. Stage A — deterministic preparation

1. Inspect all three worktrees. Use an ignored repository-local `.scratch/`
   directory and isolated checkouts when necessary. Preserve unrelated local
   files; never reset a dirty sibling to prepare the campaign.
2. Freeze the committed manifest roster and compare exported screened fields
   with their dictionary originals. Record mechanical drift separately from
   semantic findings. S1's 157 anchors and 19 transferred entries matched.
3. Locate existing prepared generation evidence. Use compact cards, selected
   branch source records and exact source IDs before any full packet. Reuse
   the source grounding; do not regenerate it for every entry.
4. Prepare one compact semantic payload per root, packing roots into balanced
   batches initially around 15–25 branches. Keep a root together where
   practical; split unusually large roots at explicit branch boundaries with
   the same root metadata. Tune batch size using measured tokens.
5. Supply each checker only the assigned instructions and payload. Keep prior
   audit verdicts, the other model's output, and Quran verse context out of
   screening inputs. Supply prior findings only to later investigation roles.

Compact branch payload:

```text
root ID / exact Arabic identity / branch or sense ref
source_phrase_ar
identity_judgment (status, rationale, boundary note)
concept_map.definition in Turkish
lexicalization_scope
concept_gloss, contextual_glosses, excluded_glosses:
  text, applicability, existing error_profile, stable field/index
```

The controller retains the whole-entry/source hashes outside the linguistic
payload. Omit full packets, verse occurrences, unrelated neighbors, renderer
data and old review verdicts. Headwords receive their exact headword identity
and equivalent sense fields, without fabricating a root.

`source_phrase_ar` is the primary short anchor. Generated `what_is_ar` and
`branch_image_ar` are provisional aids, not additional primary attestations.
Keep recorded qualifications that intentionally correct those aids. If the
excerpt does not settle a detail, request deeper evidence instead of deleting
an unfamiliar sense.

## 5. Stage B — independent parallel screening

Dispatch Sol Max and Luna Max separately on the same semantic payload. A
reasonable initial allocation is four Sol and four Luna workers; drain
completed work before allocating slots to deeper review or English review.
The global cap stays eight during follow-up work and retries.

Both checkers look for:

- changes to the semantic core, participants, polarity or causal direction;
- unsupported necessary conditions, added meanings or lost qualifications;
- conflation of source alternatives or proper names with generic meanings;
- bare-versus-construction usage mistakes;
- gloss/profile inconsistencies interpreted with their applicability.

Do not flag style alone, ordinary brevity, nonconstitutive missing examples,
attested unusual senses, or a legitimate narrower gloss. `adds`/`loses`
nullability does not mechanically determine `fit`. Existing legacy
`mixed_non_bare`, `non_bare`, or `unresolved` enums do not create extra lexical
branch types or prove bad content. Preserve the two reader-facing classes,
bare and collocation/construction, and qualify uncertainty separately.

Each branch receives a compact `no_flag`, `needs_review`, or
`insufficient_evidence` result. A clean result needs no explanatory paragraph.
Issues name the exact field and quoted Arabic/Turkish spans with a short
reason. Do not require a lengthy report for every clean entry.

Sol additionally drafts an English definition for a branch it passes. Luna's
routine deliverable is the semantic check, not a second publication candidate
in English. This differs from the comparison experiment, which produced both
versions to measure quality; calibrate the lighter Luna prompt before scale.
Any English draft is put on hold if **either** checker flags its branch.

Compare each completed pair promptly. Queue a single merged investigation
task containing the union of distinct issues, preserving attribution. A
shared branch is not enough to declare that both models found the same error.
No entry is cleared merely because Sol and Luna agree.

## 6. Stage C — Sol Max investigation, then Astra Max when needed

A fresh Sol Max investigator reads the flagged branch's existing full Turkish
fields, targeted generation evidence, exact claims and relevant source
passages. Inspect only the necessary adjacent lexical/facet material. No
fresh whole-corpus source-discovery campaign is required.

For each distinct concern, record:

- `confirmed_issue`, `dismissed`, or `unresolved`;
- the precise affected field, smallest defensible correction, and severity;
- exact Arabic evidence quotations with source IDs/paths and hashes;
- why the source supports the finding, including any counterevidence;
- whether the problem arose in authored Turkish, a provisional Arabic summary,
  an export, or a consumer; and which associated fields actually need repair.

Read the full branch for related scope inconsistencies, without opportunistic
rewriting. A flag can be dismissed while a different problem is discovered in
the same branch. Report those separately, as happened in the pilots.

The controller checks the proposed decision and patch scope. Escalate to
**Astra Max** when terminology is disputed, a correction could narrow the
source, the supporting evidence is insufficient, source variants conflict,
or the Sol review is unsatisfactory. A targeted primary-source lookup is
appropriate only when existing evidence does not settle that concrete issue.
Do not automatically send every flag to Astra or treat Astra's opinion as a
replacement for supporting evidence.

The controller may make the authorized editorial decision and records why.
Preserve ambiguity when no correction is justified. Unresolved cases get an
explicit hold and a concrete next-evidence question, not an invented answer.

### Check for missed problems

Independently inspect a reproducible, stratified sample of branches passed by
both screens: initially 2% of dual-pass branches, with a minimum of 30 per
campaign checkpoint where enough are available. Include source-roster sizes,
bare/construction uses, common/rare senses, and supplemental/ordinary entries.
Use fresh Sol Max reviewers and escalate doubtful conclusions to Astra Max.
Do not select only examples expected to be clean.

If a substantive false negative appears, inspect the same failure class in
that completed tranche, revise the screening rule with examples outside the
next blind sample, and rerun only affected units. Track repeat misses and
excessive referrals before expanding the next tranche. These checks monitor
misses; they do not certify every unflagged branch.

## 7. Stage D — bounded repairs with preserved history

The current Agent A/B production workflow treats an already passed entry as
complete and does not define a new audit revision of every sealed review.
This campaign is a separately requested audit. **Do not overwrite a sealed
pre-fix snapshot, replace an old verdict, or restart Agent A to repair an
existing entry.**

Before applying the first audited correction, prepare a small, explicit
revision mechanism compatible with the current validators and exporters:

1. Bind an audit revision to the current entry bytes, source/evidence snapshot,
   original production review and audit finding IDs.
2. Preserve those original artifacts. Give one reviewer-editor a declared
   pre-fix snapshot and a proposed current output with an exact writable field
   list. Record the repair before editing.
3. Have the reviewer-editor apply only the accepted bounded fields and run the
   task's schema and preservation validation. Enforce one writer per root;
   do not run a second reviewer-editor concurrently on that root.
4. Record old/new field values, rationale and source references. A schema fix
   is not permission for a new semantic change.
5. Require the owning exporter to recognize the accepted revision and reject
   unreviewed changes. Demonstrate this on the S1 repair queue before scaling.

The exact revision adapter/commands are **pending implementation and review**;
the existing initial-production scripts must not be assumed to provide it.
Screening and evidence review can proceed while that bounded adapter is
prepared. If a validator/exporter cannot accept a revision, keep the proposed
patch pending rather than bypassing its checks or adding a large replacement
workflow. Reuse existing schema and repair-preservation helpers where suitable.

Source-owned Arabic, IDs, branch/sense rosters, citations, selectors and root
alternatives stay protected during prose repair. A necessary upstream source
correction gets its own documented scope and review. Never patch quran-data's
compiled entry to bypass dictionary source ownership.

## 8. English definitions and their acceptance

English is a full prose equivalent of the final Turkish
`concept_map.definition`, including its qualifications. It is not a shorter
gloss, a translation of all facets/source notes, or an occasion to add an
etymology or theological explanation. Do not silently repair Turkish meaning
inside English while returning `no_flag` for the source.

After Turkish issues are resolved:

1. Bind each English draft to the exact final Turkish definition hash and
   existing Arabic anchor. Regenerate only drafts invalidated by a repair.
2. Have a separate Sol Max reviewer compare every definition with that Turkish
   paragraph and its anchor/qualification. Check scope, negation, agency,
   cause/result, proper names, ambiguity and all necessary information.
3. Record `accepted`, `repair_required`, or `held`; repair only the named
   English problem and preserve the reviewed draft history. Escalate semantic
   uncertainty to Astra Max.
4. Keep experimental Luna English and held Turkish-dependent drafts outside
   accepted outputs. A translation-quality pass does not resolve an uncertain
   Arabic/Turkish source question.

Use a separate definition artifact keyed by stable branch/sense ref, source
hash and review status. Its production schema, export and consumer contract
still need to be implemented before publication. Existing
[multilingual gloss generation](v2/gloss_generation/README.md) creates compact
gloss sets; it is not automatically the English prose-definition pipeline.
Do not overwrite its English gloss files or assume KK/TM already consume a
new `definition_en` field.

## 9. Keep orchestration small and resumable

Use one controller and a small set of campaign artifacts, for example:

```text
v2/audits/<campaign>/
  run.json                  source/prompt/model pins, roster, usage totals
  input/batch-NNN.json       shared compact semantic input
  sol/batch-NNN.json         first-pass findings and English drafts
  luna/batch-NNN.json        independent findings
  findings.jsonl            merged issues, evidence, decisions and repair state
  definitions.en.jsonl       drafts/accepted definitions with source hashes
  SUMMARY.md                progress, decisions, costs and remaining holds
```

These are proposed campaign files, not a new required production state
machine. Reuse completed S1 work only when exact input/prompt scope remains
valid; carry its open findings and English holds. Do not silently treat either
pilot as an accepted full production revision. A changed entry invalidates
only affected results and dependent English definitions.

Track screening coverage for each model, investigation disposition, repair
application, English acceptance, export and live release as separate facts.
Operational failures such as invalid JSON, quote mismatch, timeout or missing
evidence are retries/holds, not semantic errors. Preserve raw worker output
before a structural correction. Retry the missing or invalid assignment;
never rerun an entire completed campaign for a formatting error.

Run the initial production-shaped tranche on about 200 branches outside S1,
with existing failures retained as explicit regression examples separately.
Measure actual input, cached input, visible output, reasoning tokens, latency,
referrals, false alarms, missed-problem samples and English defects. Compare
completed batches immediately; then continue in tranches of roughly 500–1,000
branches, adjusting batch size and scheduling within the eight-worker cap.

## 10. Cost plan with the added Luna layer

The earlier $250–400 expectation / $550 reserve covered Sol screening, deeper
Sol review, limited Astra escalation and English checks. Adding Luna costs
little in its own calls but may increase the combined investigation queue.
The S1 union referred 27/157 branches; use that only as calibration, not a
population-rate claim.

For planning, allow 15–20% of branches to reach deeper review and 1–2% to
reach Astra. Include the dual-pass sample in the investigation allowance and
adjust with measured usage. At Standard API rates, with all agents on Max:

| Work | Planning allowance |
| --- | ---: |
| Sol compact screen and English drafts | $55–110 |
| Parallel Luna semantic check | $3–10 |
| Sol investigation, missed-problem samples and bounded repair work | $80–220 |
| Astra escalations | $30–90 |
| Independent English review | $20–50 |
| Model work before contingency | $188–480 |

**Updated expected range: about $300–450; planning reserve: about $600.**
These are estimates, not measured bills or a spend authorization. The root
corpus's compact screening fields measured about 26.1 million characters;
tokenization, reasoning and repeated evidence reads remain uncertain. The
first tranche must record actual usage so the forecast can be updated before
further scale. Report a material forecast increase instead of silently lowering
reasoning effort, dropping a checker, or consuming an unbounded budget.

Pricing basis checked September 24: Sol $2/$10, Luna $0.10/$0.50, and Astra
$10/$50 per million input/output tokens. Reasoning is included in the output
allowances. [Official pricing](https://developers.openai.com/api/docs/pricing).
Fast mode approximately doubles model charges; Codex subscription/credit
accounting differs from a Standard API invoice. Batch discounts require a
compatible implementation and are not assumed here. Deployment and a new
whole-source research campaign are outside this model-work estimate.

## 11. Transfer and downstream publication

Keep audit completion, accepted source repair, quran-data transfer, English
consumer support and live publication separate. A completed screen never
updates the CDN by itself.

After accepted revisions export through their owning workflow, commit the
dictionary changes and record source hashes. Use a clean quran-data checkout
and its existing committed-source transfer:

```sh
python3 scripts/dictionary/sync_turkish_entries.py --source /path/to/dictionary
python3 scripts/dictionary/sync_turkish_entries.py --source /path/to/dictionary --check
python3 scripts/dictionary/check_turkish_entries.py
```

These commands exist; they do not establish that a future English-definition
or audit-revision contract is already supported. Add only the necessary
adapter/schema support before including such artifacts in a release. Review
exact entry diffs, hashes and manifest changes, then commit/push quran-data.

For quran-apps, follow the linked CDN runbook: select the reviewed committed
quran-data ref, use `npm run data:update`, inspect/check both channels, publish
Tafsir evidence before Reader, then verify both live consumers. Keep the
Cloudflare Free publication design. Data-only updates do not require a shell
deployment; new English fields may require contracts, rendering and compatible
KK/TM shells first. Commentary uses its separate runbook path and is not
implicitly refreshed by this dictionary audit.

Verify changed definitions, source badges, gloss qualifications and retained
root alternatives in KK and TM with fresh/cached desktop/mobile sessions.
Include slow-load/navigation behavior so TM does not show old demonstration
roots. Record source commits, catalog hashes/generations and visible results.
Keep tokens, signing keys and browser profiles outside committed artifacts.

## 12. Completion and next operator checklist

Report exact counts for both screens, investigations dismissed/confirmed/held,
repairs applied/pending, English accepted/held, and releases prepared/live.
An audit can finish with a clearly enumerated unresolved queue; it must not
claim those entries are repaired or certified. Unresolved material may retain
its last accepted source version, with new English held, while independently
accepted corrections proceed through the release workflow.

- [ ] Full manifest roster and source snapshots frozen; supplemental senses counted separately.
- [ ] Small audit-revision adapter and English-definition acceptance/export contract prepared.
- [ ] Eleven known repairs reviewed against current bytes and applied through the bounded path.
- [ ] Eye terminology resolved or explicitly held; no pupil-only automatic substitution.
- [ ] Initial non-S1 tranche completed with Sol Max + Luna Max and actual usage recorded.
- [ ] Both independent screens cover every planned unit or list operational holds.
- [ ] Union of distinct flags investigated; sampled dual-pass findings adjudicated.
- [ ] Necessary Astra Max decisions and their reasoning recorded.
- [ ] Every accepted English definition independently reviewed against final Turkish bytes.
- [ ] Source changes and exports committed/pushed; quran-data transfer verified and committed.
- [ ] Compatible KK/TM consumers prepared if English support requires changes.
- [ ] Intended releases published and verified through both apps; remaining work stated plainly.

Until execution is explicitly resumed, the campaign remains **PENDING**. Keep
the quran-data README pointer marked pending until its stated work is actually
complete, and update the dated session logs as milestones are reached.
