# Root dictionary repair session — 2026-09-23

This record tracks the September 23 repair across `dictionary`, `quran-data`,
and `quran-apps`. Status is updated as work completes; a draft or schema-valid
writer response is not an accepted or published dictionary entry.

## Starting point and diagnosis

- Dictionary source baseline: `bf756f5d` (full source revision is recorded in
  quran-data's Turkish transfer manifest).
- quran-data repair commit: `c159182b38d3f7becc949a055ba0845489a2a67e`.
- quran-apps integration commit: `eea70a4215a64247e0cda90aee8e8d7cdfade0f2`.
- The initial audit checked 1,682 transferred Turkish entries and 11,648 Arabic
  branch records against source evidence. The frozen dictionary snapshot is
  newer than the released quran-data lexicon; four changed branch records are
  preserved as explicit Arabic evidence updates in quran-data.
- Occurrence-level root disagreements were incorrectly treated as root-wide
  dictionary equivalences. `اسم` consequently exposed unrelated `سمم` beside
  `سمو` and the observational `وسم` alternative. The corrected primary lookup
  is `سمو`; research alternatives do not become automatic identities.
- Incorrect source occurrences: `13:33:13:1` سمّوهم belongs to `سمو`, and
  `48:15:8:1` ذرونا belongs to `وذر`, not `ذور`.

## Remaining entry production

Fourteen missing Turkish entries cover 58 QAC morphemes. Existing Furuq
evidence and writer bundles are reused. Their unclassified registry/pass-3
status is not an additional production prerequisite in the current runbook.

User-selected execution: GPT-6 Sol, maximum reasoning, at most eight active
agents. Earlier GPT-5.5 workers were stopped on request. One already-written
entry (`root_005406`) was preserved and independently reviewed by GPT-6 Sol.
Each Agent A finishes before independent Agent B starts. Agent B records and
validates findings before surgical corrections; there is no writer repair
loop or second review. Structural or ambiguous decisions remain editorial.

| Root ID | Arabic identity | Status |
| --- | --- | --- |
| root_003789 | عضو | Completed: pass; validated export prepared |
| root_004482 | لدن | Completed: repair; validated export prepared |
| root_004706 | معن | Completed: pass; validated export prepared |
| root_004914 | نفي | Completed: repair; validated export prepared |
| root_005216 | وسن | Completed: pass; validated export prepared |
| root_005229 | وشي | Completed: repair; validated export prepared |
| root_005302 | وني | Completed: repair; validated export prepared |
| root_005348 | هلل | Completed: repair; validated export prepared |
| root_005351 | سطو | Completed: pass; validated export prepared |
| root_005406 | عنو | Completed: repair; validated export prepared |
| root_005440 | ءلل | Completed: repair; validated export prepared |
| root_005713 | عصو | Completed: repair; validated export prepared |
| root_005748 | غلو | Completed: repair; validated export prepared |
| root_005754 | فءي | Completed: pass; validated export prepared |

Authoritative per-root artifacts are under
`v2/work/entry_creation/furuq/<root>/tr/`: `input/`, `output/`,
`review/input/writer_response.json`, and `review/output/root_review.json`.
Review snapshots preserve what was reviewed before any correction.

## Proper-name findings

No QAC PN tagging occurs among the 146 morphemes in the combined gap list.
The wider dictionary nevertheless contains names:

- `root_005440/B006`: الإل / إيل as a divine name.
- `root_005440/B013`: الإل / ألال as a mountain/hill at Arafat.
- `root_004706/B006`: ordinary dwelling/place evidence mixed with معان.
- `root_005348/B004`: divine-name quotations within a speaking/tahlil branch;
  the branch itself is not a proper name.

The held entries contain zero lexical units and empty fallback name policies.
Current name policies attach to lexical-unit IDs. The user delegated editorial
decisions to the controller during this session. Decision: retain the existing
branch roster and zero lexical-unit roster; use descriptive Turkish branch prose
for divine-name/place-name senses, keeping their Arabic names in source-owned
fields. Do not invent Turkish name spellings or interpret a name as an ordinary
root gloss. In معن/B006, explicitly qualify the ordinary dwelling and named-place
facets. The source entries support both facets but no fabricated new lexical
unit. This avoids branch restructuring and preserves source distinctions. Empty policies
must not be interpreted as evidence that names are absent. Quranic إِلًّا at
9:8 and 9:10 is distinct from the dictionary divine-name branch. لَاتَ at 38:3
is a particle under identity review, not the deity اللّات at 53:19.

## Workflow repair introduced in this session

`v2/scripts/prepare_root_review.py` previously required an accepted/enriched
writer response. Acceptance required a canonical Quranic packet, which does
not exist for these Furuq-only roots. Actual source packets exist under `data/output/furuq/root_packets/` and match
the prepared evidence hashes; old indexes still reference the Quranic packet
directory. Review preparation now accepts a raw
writer response validated against its sealed staged task, preserving evidence
bindings, identity, semantic and structural checks. The accepted/enriched path
is retained. Regression: `v2.tests.test_prepare_root_review_raw` verifies raw
Furuq review preparation and rejection of a stale staged seal.

Downstream enrichment, transfer, and publication remain separate from the
two-agent review workflow. Raw writer output must not be transferred as a
completed enriched entry.

## Cross-repository and publication status

quran-data's root-level record of the same name contains transfer/mapping and
publication details. Its `data/bridges/ROOT-DICTIONARY-REVIEW.md` records the
source evidence and repeatable audits. quran-apps' `docs/root-data-updates.md`
documents the simplified update/publication commands; `docs/root-data-gap-plan.md`
tracks the remaining six identity decisions. At this checkpoint, Tafsir
evidence generation 5 and Reader generation 8 are live and verified. Reader
generation 9 is uploading. quran-apps publication fixes are committed at
`54702f9b`; Worker tests (110), tooling tests (12), and typechecking passed.


## Identity adjudication decision (2026-09-23)

The controller adopted the independent review: do not add single-target aliases
for ثبي or سنه. The original audit found plausible associations, but independent
review found explicit competing morphological analyses. All six exact root
identities therefore remain unresolved; no source interpretation is silently
promoted to a root-wide equivalence. The full audit and independent review follow.

# Independent root-identity review — 2026-09-23

## Recommendation

**Do not add either proposed single-target reviewed alias.** Keep QAC `ث ب ي` at 4:71:7:1 and `س ن ه` at 2:259:42:1 as `unresolved_identity` in the root-resolution file. The proposed dictionary branches are meaningful *interpretive and lexical candidates*, but the evidence does not establish either as the unique root identity of the QAC key. A form-level link or a dedicated dictionary packet can preserve the useful associations without silently replacing the QAC analysis.

The [bridge schema](quran-data/schemas/qac-furuq-v4-root-map.md) says published dictionary resolution uses exact root identity or a reviewed, source-bound alias; observed occurrence targets do not prove lexical equivalence. The [builder](quran-data/scripts/bridges/build_dictionary_root_resolutions.py) exposes an approved alias as `resolution: reviewed_alias` for every token of that QAC root. The decision is therefore stronger than finding a source that discusses the word under a nearby heading.

## `ث ب ي` — 4:71:7:1 `ثُبَاتٍ`

**Reject `root_000209` (`ث و ب`)/B001 as a sole root alias.** The [QAC root page](https://corpus.quran.com/qurandictionary.jsp?q=vby) assigns the verse's noun to `ث ب ي`. `root_000209` is a valid lexical association: its B001 includes `اجتماع الناس`, lexical unit `lu_007` gives `الثبة` as a group, and the frozen Mufradat entry under the *exact* `ثوب` route says `الثبة: الجماعة الثائب بعضهم إلى بعض` and quotes `فانفروا ثبات ... [النساء/71]`. The entry has SHA-256 `0a93118a17e1f50149c9679d4c36d3f4580f32593fc8bb24109bcb496cd6128c`; the proposed [B001 source phrase](public/agent/root/root_000209/branch/root_000209--B001.source.json) hashes to `03948b05175bb51a1b882a93502c669fc8685681530496a406217d6e78f549d1`. B001's source phrase mentions `ثبة الحوض`, while the exact verse and group noun occur in the longer Mufradat entry and the branch lexical unit.

There is substantive morphological disagreement. [Lisān al-ʿArab, `ثبا`](https://islamweb.net/ar/library/content/122/975/%D8%AB%D8%A8%D8%A7) places the group noun with `أصلها ثبي`, reports the alternative `ثبو`, and distinguishes the basin noun's derivation from medial `و` in `ثاب يثوب`. [Lisān al-ʿArab, `ثوب`](https://www.islamweb.net/ar/library/content/122/1095/%D8%AB%D9%88%D8%A8) preserves both the `ثاب` account and the weak-final `ثبية` account for the verse. [Al-Qurṭubī on 4:71](https://islamweb.net/ar/library/content/48/1083/%D9%82%D9%88%D9%84%D9%87-%D8%AA%D8%B9%D8%A7%D9%84%D9%89-%D9%8A%D8%A7-%D8%A3%D9%8A%D9%87%D8%A7-%D8%A7%D9%84%D8%B0%D9%8A%D9%86-%D8%A2%D9%85%D9%86%D9%88%D8%A7-%D8%AE%D8%B0%D9%88%D8%A7-%D8%AD%D8%B0%D8%B1%D9%83%D9%85-%D9%81%D8%A7%D9%86%D9%81%D8%B1%D9%88%D8%A7-%D8%AB%D8%A8%D8%A7%D8%AA-%D8%A3%D9%88-%D8%A7%D9%86%D9%81%D8%B1%D9%88%D8%A7-%D8%AC%D9%85%D9%8A%D8%B9%D8%A7) reports al-Naḥḥās distinguishing `ثبة الجماعة` (`ثُبَيّة` in diminutive) from `ثبة الحوض` (`ثُوَيبة`), while allowing a relationship as another opinion. This is a genuine difference in which radical was lost, not simply two spellings of one root. The dictionary contains no exact `ث ب ي` card or branch in its alias shard. `root_000212` (`ث ي ب`) is the married-person sense; `root_000192` (`ث ب ت`) is firmness. Neither replaces the missing group root.

**Recommended representation:** retain the gap; separately link the exact noun `ثُبَاتٍ` to `root_000209/B001` as a source-attributed Mufradat interpretation if a form-level link is available. Mark `ث ب ي`/`ث ب و` as the competing weak-final analysis for a later dictionary headword or packet review.

## `س ن ه` — 2:259:42:1 `يَتَسَنَّهْ`

**Reject `root_000750` (`س ن ن`)/B005 as a sole root alias.** The [QAC root page](https://corpus.quran.com/qurandictionary.jsp?q=snh) assigns this form V verb to `س ن ه`. The frozen Ṣiḥāḥ entry routed into `root_000751` under broad `سنأ` says `لم يتسن: لم يتغير` from `حمأ مسنون` and replaces one of two nūns with yāʾ. That is a real `س ن ن` derivation, supported by the change sense of [`root_000750/B005`](public/agent/root/root_000750/branch/root_000750--B005.source.json), whose source phrase hashes to `e766c1be25dbf74c3528761c569b593cc2d49a9cda9e36cef7e85cef80baef1e`. But B005 itself quotes `حمأ مسنون`, not `يتسنه`. The frozen Mufradat continuation routed under `سنا` also quotes `لم يتسنه` and calls final `ه` `هاء الاستراحة`, supporting a nonradical-hāʾ reading; its entry SHA-256 is `9a7faf22a7a4902cd33eec772db8197296a13afd7fd0a1e2c4efac01ed752dbc`.

The frozen ʿAyn entry **directly supports QAC's radical `ه`**. Its internal subsection reads `# سنه السنة نقصانها حذف الهاء وتصغيرها سنيهة ... وقال الله عز وجل لم يتسنه ... ومن جعل حذف السنة واوا قرأ لم يتسن ... وإثبات الهاء أصوب`. The entry is available in `the frozen Furuq database`, `dictionary_entries` at `source_id='ayn'`, `source_entry_id='1638'`, `source_ref` ending `sha=39345c43483e0061`, full entry SHA-256 `39345c43483e0061899d66b98f99b436f06af49da2a3d4915d757d680fc970c9`. It is an overbroad source entry indexed under `صهم` and duplicated on unrelated root routes, so **the route labels do not establish `صهم` as this word's root**; the clearly marked `# سنه` subsection is the relevant source evidence.

[Al-Ṭabarī on 2:259](https://islamweb.net/ar/library/content/50/765/%D8%A7%D9%84%D9%82%D9%88%D9%84-%D9%81%D9%8A-%D8%AA%D8%A3%D9%88%D9%8A%D9%84-%D9%82%D9%88%D9%84%D9%87-%D8%AA%D8%B9%D8%A7%D9%84%D9%89-%D9%81%D8%A7%D9%86%D8%B8%D8%B1-%D8%A5%D9%84%D9%89-%D8%B7%D8%B9%D8%A7%D9%85%D9%83-%D9%88%D8%B4%D8%B1%D8%A7%D8%A8%D9%83-%D9%84%D9%85-%D9%8A%D8%AA%D8%B3%D9%86%D9%87-) explicitly lays out the two readings and derivations: hāʾ as a stop letter with `س ن و` or `س ن ن` analyses, and hāʾ as the third radical from `س ن ه`; he favors the original-hāʾ analysis. [Lisān al-ʿArab, `سنه`](https://www.islamweb.net/ar/library/content/122/4033/%D8%B3%D9%86%D9%87) likewise records the original-hāʾ, weak-final-wāw, and doubled-nūn accounts. The shared gloss “did not change” is insufficient to decide the root. `root_000751/B008` covers the year/period sense under `س ن و` but does not itself attest this verbal form. No exact `س ن ه` dictionary card appears in its alias shard.

**Recommended representation:** retain the gap and record `س ن ن`/B005 as one etymological explanation. Preserve the original-hāʾ interpretation as the best direct match to the QAC key, with a dedicated `س ن ه` lexical packet or an explicitly attributed form-level link when supported.

## Provenance and scope

I inspected cards, `routes.min.json`, branch selection and selected branch sources for `root_000192`, `root_000209`, `root_000212`, `root_000750`, and `root_000751`; QAC morpheme rows in `the September 23 QAC gap audit`; and the scoped frozen dictionary entries named above. The SHA-256 values for both proposed branch phrases match the current UTF-8 `source_phrase_ar` values. They prove the branch anchors have not drifted; they do not resolve the competing derivations. The historical occurrence bridge's `ث ب ت` and `س ن ن` targets are observations only under its own consumer rule.


## وشـي documentary-branch decision

The user authorized controller editorial decisions with recorded reasoning.
B010 retains the disputed mixed-speech report together with its explicit source
rejection; B011 retains only the unspecified relation to sound. Neither is an
ordinary accepted translation. No branches were merged, removed or invented.
An agent curator changed only B010/B011 identity status and rationale; the
pre-curation response and source hashes are preserved under
`v2/work/entry_creation/furuq/root_005229/tr/editorial/`. A fresh first independent
Agent B review followed that curation and corrected only an unrelated B005
definition/facet that had incorrectly required repeated birth. This is an explicit source decision, not
a return to the original writer for a repair cycle.

## Source-production completion

All 14 writer responses, independent reviews, recorded repairs, and enriched
exports validate. Counts: **5 pass, 9 repaired, 0 unresolved editorial reviews,
0 missing writer outputs, 0 outputs awaiting review**. The original ambiguity
in وشـي remains explicit documentary uncertainty within the reviewed entry.

The enriched exports add 14 entries and 103 branch records. Transfer/publish
status is recorded separately in the quran-data companion log. No new root
alias was added: all six identity gaps remain intentional pending dedicated
lexical/root representation.
