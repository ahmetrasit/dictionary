# S1 dictionary sampling audit — 2026-09-24

## Outcome

User-requested GPT-6 Sol Max screening covered **19 existing root entries and all 157 branches** linked from S1 (Al-Fātiḥah), including both documented `اسم` alternatives, `سمو` and `وسم`. All branches of those entries were included, even when a branch is not used in S1. The selection is a targeted sample, not a random corpus sample.

- Initial screen: 138 `no_flag`, 13 `needs_review`, 6 `insufficient_evidence`.
- Deeper examination of the 19 flags: **9 branches with supported correction findings; 10 flags dismissed** using fuller existing evidence or the recorded applicability of narrower glosses. No unresolved flag remains in this sample.
- 148 English prose definition drafts retained; 9 held pending corrections. Drafts translate the Turkish definition paragraph, not all entry notes, facets or glosses. They are not a published English release.
- No canonical entry, sealed production review, mapping, app or live CDN artifact was changed by this audit. The nine findings below are **documented proposals, not applied repairs**.

All 157 Arabic source phrases match the static branch anchors. All screened authored fields match between dictionary production output and quran-data export for all 19 roots. The retained issues are therefore present in authored entries, not transfer corruption.

## Method and limits

Eight GPT-6 Sol Max screening assignments used existing source phrases, identity qualifications, Turkish definitions, usage scope and gloss profiles. Workers received no verse context and did not select a preferred root or Quran-specific sense. Multiple roots, source disagreement, proper names and legitimate narrower applications were preserved. Full original generation evidence was examined only for flags, by separate GPT-6 Sol Max reviewers. The controller checked their findings and exact cited substrings; no new source-discovery campaign was performed.

A `no_flag` means no apparent issue was identified in this compact check. It is not a certificate of correctness. The initial excerpt-only screen produced ten false alarms among nineteen referred branches; future screening should continue to investigate before repairing. In particular, a contextual or otherwise explicitly narrower gloss need not cover every branch usage, and `fit` must be read with applicability.

An independent deterministic English spot check (first, middle and last clean result in each batch) examined 24 drafts: 23 accepted as drafts and one terminology correction (`ilgeç`: “preposition” rather than “particle”). Controller review also corrected “dark sediment” to “thick sediment” and restored “arrows and sticks” in two other drafts. Deeper-review drafts were constrained to definition-only translation after two initially included extra evidence details. English production needs its own acceptance gate; these drafts remain separate from Turkish production.

## Supported correction findings

These findings concern eight definitions and one gloss, with associated fields noted in the detailed proposals. They do not establish a root-assignment error. Source-bound participant distinctions and qualifications should be preserved without introducing new contextual restrictions.

| Branch | Finding | Proposed direction |
|---|---|---|
| `root_000532/B005` | Dairy sheep/goats raised at home generalized to any female animal. | Retain small-livestock and milk-purpose qualification. |
| `root_000532/B007` | A she-camel’s attachment to a male camel generalized to any animal and mate. | Preserve the attested participants in this particular application. |
| `root_000532/B012` | “Small tree” adds an unattested size restriction. | Remove “small”; retain tree/plant alternatives. |
| `root_000532/B013` | “Gathered or abundant water” makes gathering alone sufficient. | Require abundant water; keep gathering as the source’s explanation of the name. |
| `root_000973/B003` | Worshipful orientation made necessary even for human-directed humbling. | Distinguish human-directed humility from religious worship and attributed special usages. |
| `root_000355/B005` | Favor-reminding definition excludes claiming praise for expenditure on oneself. | Preserve both attested uses within the directed construction. |
| `root_001092/B004` | Hardness made universal despite qualified source descriptions of a rock. | Attribute hardness, accumulation and roundness to their source variants. |
| `root_001583/B009` | Gloss says “person” although the definition and cited expressions specify a man. | Align the gloss with the recorded male referent. |
| `root_000913/B003` | “No redress was sought” adds a claim to “unavenged.” | Remove the unsupported statement about attempts to seek redress. |

Detailed Arabic quotations, reasons and proposed field edits are in [results.json](v2/audits/s001-2026-09-24/results.json). These are surgical repair proposals and still require the existing production repair/provenance workflow before export or publication.

## Why ten flags were dismissed

Fuller evidence expressly supports the tax/pledge analogy, the sign of the approaching Hour, completion of an affair, Basra as the referent of a place expression, labor like a slave, oil/fat as ship coatings, the extension of the offering-name to camels, and prolonged harm in the severe-day expression. Two other flags wrongly required narrower glosses to cover every attested application. One retained branch (`root_000973/B003`) also had a separate false-power sub-flag dismissed while its human-directed scope problem remained.

## Provenance and artifacts

- Dictionary input commit: `f85d2c907d9785bf10981c8d0f731c33ec54536c`.
- quran-data input commit: `216705d16e6b626c749635efd7c79e8280c1b7e8`.
- Selection: Reader generation 12 S1 core plus exact scoped alternatives. The 25 unlinked prefix/function morphemes are recorded, not counted as missing dictionary entries.
- [Manifest and entry/input hashes](v2/audits/s001-2026-09-24/manifest.json).
- [Instructions](v2/audits/s001-2026-09-24/SCREENING-INSTRUCTIONS.md), [screening validation](v2/audits/s001-2026-09-24/validation.json), [source parity](v2/audits/s001-2026-09-24/source-anchor-check.json), [transfer parity](v2/audits/s001-2026-09-24/transfer-parity-check.json).
- Raw screen outputs, separate deeper reviews, English spot review and aggregate results are retained under `v2/audits/s001-2026-09-24/`. Source paths record this session’s sibling-checkout locations; evidence hashes and exact quotes identify the inspected artifacts. `validate.py` checks saved screen structure; `compile_results.py` additionally requires those local generation evidence files.

## Scope correction to the earlier audit recommendation

The earlier repair-session recommendation was broader than the demonstrated semantic evidence warranted. Newly produced drafts were corrected during their normal writer/reviewer cycle, and mapping, transfer, runtime and badge problems were separate causes. Those observations alone did not establish widespread errors in existing definitions. This user-requested sample now provides concrete examples in existing entries, but its deliberately selected roots cannot support a corpus-wide error-rate estimate. The agreed approach remains compact screening followed by extensive review of flagged cases; it does not reopen all source anchoring or use Quran context to choose roots.

## Follow-up: blind Luna comparison

The subsequent [blind Luna comparison](S1-LUNA-BLIND-COMPARISON-2026-09-24.md)
found two additional bounded wording issues (`root_001525/B008` and
`root_000355/B002`) and one unresolved precision concern (`root_001273/B021`).
Thus this report's original counts describe the first audit stage, not the
final combined repair queue: eleven confirmed branches now await repair.
Previous English drafts for those three branches are held for reconsideration.
Luna passed six of the original nine problem branches. No canonical entry or
live data changed during either audit.
