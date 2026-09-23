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

The enriched exports add 14 entries and 93 branch records. Transfer/publish
status is recorded separately in the quran-data companion log. No new root
alias was added: all six identity gaps remain intentional pending dedicated
lexical/root representation.


## Full six-identity audit and rejected alternatives

# Editorial review of six QAC root gaps — 2026-09-23

## Decision

**Add no new root-level reviewed aliases. Keep all six QAC keys unresolved.** The proposed `ث ب ي → ث و ب` and `س ن ه → س ن ن` links are legitimate lexical or etymological associations for individual words, but primary sources also support other radicals. The existing reviewed-alias schema publishes a single dictionary root identity for the QAC root, so it cannot represent these alternatives honestly. A source-attributed form-level link or a dedicated dictionary packet would preserve the associations without replacing the QAC analysis.

The QAC tokens below come from `the September 23 QAC gap audit`. Dictionary lookup followed `../dictionary/AGENTS.md` and `public/agent/START_HERE.md`: alias and form shards, then each candidate card, `routes.min.json`, `branches.select.min.json`, selected branch sources, and scoped frozen source text where the compact branch omitted a decisive phrase. Dictionary file links resolve from this report in `.scratch/`. Branch hashes are SHA-256 of the exact UTF-8 `source_phrase_ar` in the named `.source.json` file; they use the same rule as the existing reviewed-alias file.

| QAC key and token | Decision | Candidate root IDs actually inspected |
|---|---|---|
| `ء د د`, `19:89:4:1` إِدًّا | unresolved | `root_000021` |
| `ث ب ي`, `4:71:7:1` ثُبَاتٍ | unresolved; ثوب is one lexical explanation | `root_000192`, `root_000209`, `root_000212` |
| `س ن ه`, `2:259:42:1` يَتَسَنَّهْ | unresolved; ه / و / ن analyses compete | `root_000750`, `root_000751` |
| `ق ض ض`, `18:77:17:1` يَنقَضَّ | unresolved | `root_001543` |
| `ك ي ف`, 83 occurrences of كَيْفَ | unresolved | none returned by exact root or form lookup |
| `ل و ت`, `38:3:8:2` لَاتَ | unresolved | `root_001389` |

## Rejected root alias proposals

The branch hashes below document the proposed links and their evidence; **neither is approved as a root alias**. The frozen source text was checked against independent accounts of the same forms before making the final decision.

### `ثبي`: ثوب explains the form, but does not establish root identity

- The QAC noun denotes groups in `فَانْفِرُوا ثُبَاتٍ أَوِ انْفِرُوا جَمِيعًا`; see the [QAC verse](https://corpus.quran.com/grammar.jsp?chapter=4&verse=71). Exact `ث ب ي` and normalized `ثبات` form lookup did not return the correct root. A targeted frozen-source phrase search after compact lookup found the verse under `ث و ب`.
- [`root_000209/B001`](public/agent/root/root_000209/branch/root_000209--B001.source.json) includes `اجتماع الناس` and `جماعات يثاب إليها` in its `what_is_ar` (`sourcePhraseSha256 = 03948b05175bb51a1b882a93502c669fc8685681530496a406217d6e78f549d1`). Its lexical unit `lu_007` is `الثبة`, glossed `الجماعة التي يثوب بعضها إلى بعض`, linked to B001. The frozen Mufradat `ثوب` entry (`entry_text_sha256 = 0a93118a17e1f50149c9679d4c36d3f4580f32593fc8bb24109bcb496cd6128c`) explicitly says `الثبة: الجماعة الثائب بعضهم إلى بعض` and cites `فانفروا ثبات أو انفروا جميعا [النساء/71]`. Its route is exact to `root_000209`.
- The same broad Mufradat entry is also routed as a **weak-medial variant** to `root_000212` (`ث ي ب`), but that packet's sole B001 and lexical unit are `الثيب`, the previously married woman, and its `what_is_not_ar` excludes `ثبة الحوض` and general return. The historical observed `root_000192` (`ث ب ت`) B001 is firmness (`ثبت الشيء يثبت ثباتا وثبوتا`; `sourcePhraseSha256 = 1e7e7921a56ad61e6f0034d8baa4810838e6729129f80d098d235aa111a894f6`), a different `ثبات` sense.
- [Lisān al-ʿArab, ثبا](https://islamweb.net/ar/library/content/122/975/%D8%AB%D8%A8%D8%A7) states `أصلها ثبي` for the group noun and reports a possible final و. It distinguishes the basin noun's medial و from `ثاب يثوب`. [Al-Qurṭubī on 4:71](https://islamweb.net/ar/library/content/48/1083/%D9%82%D9%88%D9%84%D9%87-%D8%AA%D8%B9%D8%A7%D9%84%D9%89-%D9%8A%D8%A7-%D8%A3%D9%8A%D9%87%D8%A7-%D8%A7%D9%84%D8%B0%D9%8A%D9%86-%D8%A2%D9%85%D9%86%D9%88%D8%A7-%D8%AE%D8%B0%D9%88%D8%A7-%D8%AD%D8%B0%D8%B1%D9%83%D9%85-%D9%81%D8%A7%D9%86%D9%81%D8%B1%D9%88%D8%A7-%D8%AB%D8%A8%D8%A7%D8%AA-%D8%A3%D9%88-%D8%A7%D9%86%D9%81%D8%B1%D9%88%D8%A7-%D8%AC%D9%85%D9%8A%D8%B9%D8%A7) reports al-Naḥḥās distinguishing `ثُبَيّة` for a group from `ثُوَيبة` for a basin, while recording a proposed relationship as another opinion. These are competing accounts of which radical is missing. Mufradat's `ثوب` placement does not justify replacing QAC `ث ب ي` with a sole `ث و ب` identity. Retain the root gap; `root_000209/B001` can be recorded as a source-attributed link for this form if the consumer supports that distinction.

### `سنه`: the final ه has competing analyses

- [`root_000750/B005`](public/agent/root/root_000750/branch/root_000750--B005.source.json) gives `الحمأ المسنون المتغير المنتن` and `حمإ مسنون أي متغير`. Its branch image is `حَمَأ مسنون وصورة مملسة`, and its inclusion boundary explicitly includes change (`التغيير`). It was the proposed branch anchor for the doubled-ن analysis, though its compact source omits the verb `يتسنه`.
- In the frozen `sihah` entry attached to `root_000751` (`entry_text_sha256 = e8c760f77da3477e330325fa462c60bc7126a42f7394722e0235af7010509676`, route headword `سنأ`), the source says: `لم يتسن : لم يتغير، من ... حمأ مسنون ... فأبدل من إحدى النونات ياء`. The **two nuns** identify the etymological root `س ن ن`, despite that source entry's broad `سنأ` heading and its placement in the `س ن و` packet. The source reference begins `sihah:...:heading%3A5377:...:sha=e8c760f77da3477e`.
- In the frozen `mufradat` entry attached to `root_000751` (`entry_text_sha256 = 9a7faf22a7a4902cd33eec772db8197296a13afd7fd0a1e2c4efac01ed752dbc`), the source explicitly cites `لم يتسنه [البقرة/259]`, says `لم يتغير`, and calls the final `ه` `للاستراحة`. Thus the written `ه` is not necessarily a lexical radical **in this analysis**. The source reference begins `mufradat:...:heading%3A739:...:sha=9a7faf22a7a4902c`.
- The frozen ʿAyn entry directly supports QAC's `س ن ه`. Its marked `# سنه` subsection says `السنة نقصانها حذف الهاء ... وقال الله عز وجل لم يتسنه ... وإثبات الهاء أصوب`. The entry is `dictionary_entries` `source_id='ayn'`, `source_entry_id='1638'`, full `entry_text_sha256 = 39345c43483e0061899d66b98f99b436f06af49da2a3d4915d757d680fc970c9`, with `source_ref` ending `sha=39345c43483e0061`. This oversized source entry is indexed under `صهم` and duplicated on unrelated routes `root_000497`, `root_000717`, `root_000953`, and `root_001575`; those IDs are **not identity candidates**. The internal `# سنه` section, not the route label, is relevant.
- [Al-Ṭabarī on 2:259](https://islamweb.net/ar/library/content/50/765/%D8%A7%D9%84%D9%82%D9%88%D9%84-%D9%81%D9%8A-%D8%AA%D8%A3%D9%88%D9%8A%D9%84-%D9%82%D9%88%D9%84%D9%87-%D8%AA%D8%B9%D8%A7%D9%84%D9%89-%D9%81%D8%A7%D9%86%D8%B8%D8%B1-%D8%A5%D9%84%D9%89-%D8%B7%D8%B9%D8%A7%D9%85%D9%83-%D9%88%D8%B4%D8%B1%D8%A7%D8%A8%D9%83-%D9%84%D9%85-%D9%8A%D8%AA%D8%B3%D9%86%D9%87-) explicitly distinguishes a nonradical stop ه with و or doubled ن derivation from a radical ه reading, and favors the original-ه account. The shared gloss “did not change” cannot resolve the competing roots. `root_000751/B008` (`sourcePhraseSha256 = 8dfd6f23bfd2cb87b75b6c2377869b09bac79b4535d8700c9096e64128979fe4`) covers a year and staying one year under `س ن و` but does not directly attest this change/decay verb. Retain `س ن ه` unresolved; preserve `س ن ن/B005` as one attributed etymological explanation.

## Other unresolved identities

### `ءدد` — 19:89 إِدًّا

The QAC token is an adjective meaning “atrocious”; see the [QAC word context](https://corpus.quran.com/wordbyword.jsp?chapter=19&verse=89). Exact `ء د د` has no dictionary alias or card. The form lookup after folding `إِدّ` to `اد` and the nearby `ء د ا` weak-final alias recall `root_000021` (`ء د ي`) only as a **candidate**. Its route's `ء د ا` sources are weak-final variants of `أدى`, and its card/branches cover conveying, payment, equipment, aid, and unrelated idioms. For example, [`root_000021/B004`](public/agent/root/root_000021/branch/root_000021--B004.source.json) contains `الأداة الآلة` (`sourcePhraseSha256 = 5da7745bb0e492f9aa1f224cec9d1f61bbcf22f8ad43d86a4c4d6a2e41309cd7`). None attests the doubled-dāl adjective `إِدّ`. The shared unvoweled letters are insufficient for an alias.

### `قضض` — 18:77 يَنقَضَّ

The QAC identifies a form VII verb from `ق ض ض`, “collapse,” with `ن` as the form prefix; see its [morphology page](https://corpus.quran.com/wordmorphology.jsp?location=(18:77:17)). Exact `ق ض ض` has no dictionary card. The consonant-only form lookup `ينقض` and historical observation return `root_001543` (`ن ق ض`). Its [`B001`](public/agent/root/root_001543/branch/root_001543--B001.source.json) says `نقضت الحبل والبناء` and covers undoing a constructed thing (`sourcePhraseSha256 = 5cdac16e7f72adf1e6e1c426d312d5b8e38ca3ec496c224031d210d000935bc3`). This is a semantic neighbor, but there the `ن` is a radical and the `ض` is not doubled. A phrase hit for `يريد أن ينقض` in the frozen Maqayis `نقض` entry refers to a poet wanting to undo another's composition (`يريد أن ينقض ما أربه صاحبه`), not the verse's wall. No selected branch source attests `انقضّ الجدار` as this root. Keep the identities separate.

### `كيف` — 83 interrogative tokens

All 83 gap rows have lemma `كَيْف`, surface `كَيْفَ`, and QAC `POS:INTG`; the [QAC word analysis](https://corpus.quran.com/wordbyword.jsp?chapter=2&verse=28) calls it an interrogative noun. Exact `ك ي ف` alias and normalized `كيف` form lookup return no dictionary candidate. There is no branch evidence for assigning its 83 tokens to a nearby consonantal root. This needs a lexical/functional headword or explicit no-dictionary handling, not an alias.

### `لوت` — 38:3 لَاتَ

The target is `38:3:8:2` (`وَلَاتَ حِينَ مَنَاصٍ`), **not** the proper noun `اللَّات` at 53:19; [QAC distinguishes the latter](https://corpus.quran.com/wordmorphology.jsp?location=(53:19:2)). Exact `ل و ت` is absent. Weak-letter normalization of `ل و ت` and lexical lookup of `لات` recall only `root_001389` (`ل ي ت`) as a candidate. [`root_001389/B001`](public/agent/root/root_001389/branch/root_001389--B001.source.json) is the wishing particle `لَيْت` (`sourcePhraseSha256 = 833696b26bb4d52153a86601252f9e6b3e5b6a579530b4960c55933f8b3819bb`); [`B002`](public/agent/root/root_001389/branch/root_001389--B002.source.json) is `لاته يليته نقصه` (`sourcePhraseSha256 = 630c4ff23dbe359916495e9d618e8e3d913c0e21894c7eb4c63704173498e327`); `B003` is turning someone away. None of its selected branches contains the verse's negation/time construction. Its frozen Sihah entry **does** quote `ولات حين مناص` and reports `شبهوا لات بليس` and the analysis `هي لا، والتاء إنما زيدت في حين` (`entry_text_sha256 = 9ae3775a58b8ad0d8fa4706b844393728518b22e8ecde16f97ee6cd13541d984`). This is a grammatical note embedded in a `ليت` source entry, not an assertion that `لات` shares the root of wishing or diminishing. QAC [morphology](https://corpus.quran.com/wordmorphology.jsp?location=(38:3:8)) tags the token as a perfect verb from `ل و ت`, while the QAC [grammar page](https://corpus.quran.com/grammar.jsp?chapter=38&verse=3) calls `لات` a negating particle acting like `ليس`. This divergence increases the need for a dedicated lexical decision; it does not support `ل ي ت`.

## Source integrity note

The frozen source entry text in `the frozen Furuq database` was read only after compact navigation. `root_000209` contains Mufradat's `ثبات` interpretation, though B001's compact source phrase does not quote the verse; its boundary and `lu_007` cover groups. `root_000751` contains the Ṣiḥāḥ and Mufradat explanations of `يتسنه`, though its branch selection omits that verb. The earlier proposed branch hashes identify stable evidence anchors, not proof of root equivalence. **No reviewed-alias JSON should be added for these six under the current root-level schema; the resolution map should continue to show six `unresolved_identity` records.**
