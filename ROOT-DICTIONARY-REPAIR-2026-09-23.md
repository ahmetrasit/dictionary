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
generation 9 was prepared and partially uploaded. Its later activation attempt
is blocked by the Free Worker's per-request CPU quota; it is not live.
quran-apps publication fixes are committed at
`54702f9b`; Worker tests (110), tooling tests (12), and typechecking passed.


## Identity adjudication decision (2026-09-23)

**Later policy clarification, 2026-09-23:** The user requested that legitimate
competing derivations be visible in KK and TM. Preserve the global root identity
decisions below, and add separately sourced analyses scoped to an exact lemma or
morpheme. For اسم, show سمو first and وسم as an attributed disputed analysis,
explaining the Basra–Kufa disagreement. Exclude unrelated سمم. The alternative
must not appear on سماء or سمّوهم just because those words share سمو.

Order denotes the selected primary analysis, not a numerical claim about
scholarly consensus. Describe another analysis as disputed and explain the
source's reasoning; call it a minority view only if the evidence establishes
that standing. A missing primary dictionary entry remains visibly missing even
when an alternative has an available entry. This preserves useful scholarship
without hiding transfer or lexical gaps.

The follow-up source review also identified direct classical discussion of
18:77 ينقضّ under قضض: a نقض derivation is attributed to Abū ʿAlī al-Fārisī.
The earlier audit below rejected a root-wide alias based on the candidate
branch evidence then inspected; it did not exhaust all accounts of the word.
The scoped dataset in quran-data records the new evidence and attribution.
This correction is retained chronologically so the reason for the policy and
data changes remains visible.

The 14 reviewed Turkish entries have been transferred in quran-data commit
`86f66b302`, bringing the source transfer to 1,696 entries / 11,741 branches,
with zero missing resolved entries. Their live deployment is a separate step.
The user selected retaining Cloudflare Workers Free and redesigning publication
into bounded resumable requests after repeat CPU-limit failures. No paid plan
or recurring billing was authorized.

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


## Live publication and final integration — 2026-09-24

This checkpoint supersedes earlier publication-pending notes. The source
production and transfer are complete: 14 independently reviewed Turkish
entries, 93 added branches, 1,696 total entries and 11,741 branch records.
There are no missing entries among resolved root identities. Proper-name
handling and the documentary وشـي decisions above remain part of the record.

### Source revisions and editorial policy

- Dictionary production: `ee70049ad`; transfer source pin: `7daa18787`;
  policy/session checkpoint: `ac1dd765e`.
- quran-data transfer: `86f66b302`; scoped analyses and source contract:
  `e523a206c2d08718fd4b35c836ac83e272632ead`.
- The scoped source has 7 selectors, 127 QAC morphemes, 13 ordered analyses,
  37 evidence items, and 16 verified local SHA-256 evidence anchors.
- اسم presents primary سمو and attributed disputed وسم with the Basra–Kufa
  reason; سمم is excluded. وسم does not spread to سماء or سمّوهم.
- The six global identities ءدد, ثبي, سنه, قضض, كيف and لوت remain unresolved
  (88 canonical QAC morphemes). The review is complete; this is an explicit
  evidence decision. Word-scoped alternatives preserve competing accounts
  without asserting global root equivalence. Exact missing entries remain
  visible even when a linked alternative has an entry.
- Next editorial work: dedicated evidence-backed root entries for ءدد, ثبي,
  سنه and قضض, and grammatical headwords for كيف and لات. Prioritize كيف's
  83 occurrences. Do not route لات at 38:3 to the deity اللّات at 53:19.
- **Correction to the earlier embedded audit:** كيف has 80 QAC INTG and 3 N
  morphemes, not 83 INTG. All 83 share the selected lemma and root key.

### Live artifacts and application changes

- Reader generation 9 was activated first; generation **10** is now active.
  Final catalog:
  `/content/v2/catalogs/10.3950bd2ef28d4d6c658b45bd0fe1d51754572dc5b1870dfa210bab7b39b6995f.json`.
  All 229 packs and the source lock passed publication verification. The exact
  Worker-signed activation was adopted into the local mirror and plan.
- Tafsir evidence generation **6** is active. Catalog:
  `/evidence/generations/catalog.6a10b78b390ee04442e714404d816e98505811bc61b5d4abf2a699138f9c7745.json`.
  All 847 immutable objects (429,331,900 bytes) passed full-body verification;
  activation and both pinned legacy pointers were checked.
- Data publication commit in quran-apps: `e41b8f36`; scoped UI/compiler:
  `e58c618b`; final TM branch-title fix: `b02b3d4f`. That fix uses each
  branch's root identity because entry IDs include a language suffix (`/tr`).
- KK **0.1.62**, module `/assets/index-Dl3QKRZa.js`, and TM **0.2.14**, build
  `12cf3ddb7b350186902a8fb1`, are deployed. Primary and disputed root cards
  include the reason, attribution, source links, and relevant branch title.

### Free-plan publication and repeatability

The user chose to keep Cloudflare Free. Commit `c1f0edb3` routes the existing
publication handler through an internal SQLite Durable Object; deployed Worker
version `4b28e9b7-c37f-48e8-b079-bfd3eae96a4c`. Live generation 9 and 10
publication succeeded through this path. No paid-plan upgrade was made.
Authentication, checksums, signatures, receipts and activation compare-and-swap
remain enforced; CONTROL R2 is authoritative. Verified immutable objects are
reused on retry. The single publisher command is unchanged.

`npm run data:update -- --quran-data-ref e523a206c` was rerun after activation.
It reported Reader local/live generation 10 and current evidence, with no new
release. SHA-256 values of all eight source-lock/publication/activation files
were unchanged. Local source builds use committed Git snapshots. Unrelated
inter-ayah edits in the original quran-data checkout were preserved; that
checkout was not reset, stashed or merged over those edits. This documentation
checkpoint does not change the source revision used by the published data.

Regression results: Reader 282/282, contracts 97/97, publication Worker
113/113, deployment/tools 56/56, and final TM branch-display suite 5/5; focused
source, transfer and dictionary checks also passed. The Worker typecheck,
dry-run deployment, both application builds and live CDN verification passed.

Separate limitation: the existing iOS activation-transition check requires an
exact predecessor hash and may reject a client jumping from generation 8 to
10. This session deployed and verified KK and TM; it did not change or verify
iOS update behavior.

## Dictionary badge and gloss-assessment phase — 2026-09-24

This entry follows the Reader 10 / evidence 6 checkpoint above. The pinned
quran-data source is still `e523a206c2d08718fd4b35c836ac83e272632ead`;
later session documentation did not change the released lexical corpus. No new
root alias, branch meaning, gloss fit, or other source lexical judgment was
made for these badges. The six global identities ءدد, ثبي, سنه, قضض, كيف and
لوت remain unresolved and retain their explicit missing states.

### Editorial and projection boundary

Commit `b125d307` exposes source-authored usage, provenance, and Turkish gloss
assessments through the projector and Reader UI. The projection preserves all
**37,846** existing `error_profile` assessments: 11,741 concept glosses,
21,430 contextual renderings, and 4,675 excluded renderings. Each optional
`glossAssessments` record is tied to exactly one gloss by `kind`, zero-based
`index`, and exact `text`; absent profiles do not become an invented `none`
assessment. Excluded renderings remain excluded. A fit badge describes the
comparison with a branch's Arabic concept, not the correctness of a verse
translation or of the whole dictionary entry.

The governed `root_001123/B001` source exception is retained as authored:
“hâlâ yapmak” is `broadening` because it loses a mandatory negative
construction; “yapmayı bırakmamak” is `narrowing` because it adds an
intentional-choice implication. The apps do not infer fit from which
explanation field is populated. This preserves the existing editorial
assessment without weakening structural validation.

The only two linguistic usage types shown are **Yalın kullanım** (`bare`) and
**Kalıba bağlı kullanım** (`collocation`). Legacy `mixed_non_bare`, `non_bare`,
and `unresolved` classifier states are neutral usage metadata, not additional
branch types or claims about a selected word's affixes, case, or figurative
status. Branch provenance comes from `sources`, displayed as six consistent
colored circles: AY, JA, MQ, MU, SI, and TA. A source circle indicates a
source roster, not unanimous agreement; `sourceNotes` is not a substitute for
the roster, and no numeric count badge was added. Full names are available by
touch and keyboard. The shared wording and source names are recorded in
`docs/dictionary-badges.md` in quran-apps.

### Live data and application checkpoint

Reader generation **11** is live at
`/content/v2/catalogs/11.3f0ff12704e99f1143dcf42ccbdc8997a5d3c7b26f3d3b7f1dcf20411248c277.json`.
Tafsir evidence generation **7** is live at
`/evidence/generations/catalog.5a399a1edc5bf5a029daf3d664a8ebe8d68bf59791fb3b64762c67a50d6c21da.json`.
Each release passed independent full CDN verification; the evidence check
covered 847 objects totaling 450,750,732 bytes. These new generations reflect
the projector/schema and application work while retaining the same source pin.
The quran-apps data publication commit is `32125972`.

The Reader first-click fix `9c38fe01` keeps a clicked word panel open during
commentary hydration. The badge/projector change is `b125d307`; subsequent
badge wording and mobile source display were refined in `e0205cf2`. Reader
reported 287 passes in the full run; one build timed out there and passed on
an isolated rerun. The latest focused checks passed 11/11, contracts 97/97,
tools 56/56, TM badge/mobile 9/9, and the earlier ranked-analysis checks 5/5.

KK **0.1.63** is deployed with module `/assets/index-DL4mLdNW.js`; TM
**0.2.15** is deployed with build `95f417a4a49d9602af7a9f55`. Fresh live
root probes passed 11 KK and 8 TM cases; warm probes passed 3 KK and 2 TM
cases, all without failures. A cached KK generation 10 session updated to
generation 11 and module `/assets/index-DL4mLdNW.js`; a cached TM 0.2.14
session updated to build `95f417a4a49d9602af7a9f55` through the
service-worker prompt and reload. A repeat
`data:update -- --quran-data-ref e523a206c` found Reader 11 and evidence 7
already current and left all eight publication, lock, and activation SHA-256
values unchanged. The badge-specific desktop/mobile and first-click probes
passed **10/10** across KK and TM: ism, adhāb, and thawāb on desktop; ism
and thawāb on mobile. They verified branch source rosters (including SI alone
and MQ+TA together), circle color/geometry, usage labels, names on focus,
click and tap without changing the branch, exact concept `none` and contextual
`narrowing` kind/index/text bindings, and TM visible-source to editor roundtrip.
The settled panel opacity was 1; page errors, failed responses, and failures
were all zero. Report and ten screenshots are under
`.scratch/live-dictionary-badges/2026-09-24T16-34-06-324Z-29590b2e-`.
A read-only compatibility audit found that the older TM
0.2.14 loader ignores the new optional gloss profiles without invoking the
strict shard validator. The warm probe confirmed its service-worker prompt
and reload path. No iOS behavior was changed in this phase.

## Six-entry production opened — 2026-09-24

The original mapping history was retraced at the user's request. quran-data
commit `dfca1fdd051e9c765653218bebbe997b9e360111` (July 28) imported the split
bridge containing the unrelated سمم candidate in the سمو row. quran-data
`c159182b3` corrected the occurrence and separated candidates from identities;
quran-apps `eea70a42` consumed that policy. quran-data `e523a206c` subsequently
preserved valid word-specific alternatives. This is distinct from dictionary
entry restoration: the bad candidate did not mean that a legitimate سمم
dictionary entry itself should be removed.

After the preceding deployment, the user requested production for the six
remaining identities. Source curation completed for ءدد, ثبي, سنه, قضض, كيف,
and لوت. This section records decisions made before entry acceptance; it does
not claim that the new entries have been written, accepted, or published.

### Source and identity decisions

Four identities require dedicated lexical roots: ء د د, ث ب ي, س ن ه, and
ق ض ض. The proposed stable IDs are `root_900001`–`root_900004`, in that
order. Existing frozen registries and committed export paths contain none of
those IDs; the supplemental registry will enforce collision checks.

The other two records are grammatical headwords: `headword_000001` for
كَيْفَ and `headword_000002` for لَاتَ. Their exact selectors cover 83 and
one QAC morphemes respectively. The three nominal QAC tags for كَيْفَ are
retained. لَاتَ is bound to 38:3:8:2 and excludes the deity name at 53:19.
Neither headword creates a root identity or overwrites source morphology.

The source dossiers distinguish exact subsections of oversized frozen rows
from their misleading outer headings. External classical witnesses carry
their actual source titles, editions/locators, quotation hashes and URLs;
they do not acquire fabricated frozen entry IDs. Source claims and competing
analyses remain attributed. In particular, two sections in al-Mufradāt give
different accounts of ثبة; their coexistence must not be erased by selecting
one dictionary-wide derivation. The basin noun remains explicitly disputed.
For لَاتَ, the reported past-verb analysis is retained alongside the negative
time construction, without claiming to know QAC's rationale for its tag.

### Correction to the previous قضض review

The prior word-level explanation incorrectly named Abū ʿAlī's alternative
pattern from ن ق ض as Form IV, `أَفْعَلَ`. The vocalized text in
[Ibn Sīdah, al-Muḥkam 6:98](https://najafdesertlibrary.com/book/المحكم-والمحيط-الأعظم/v/6/p/98)
gives `افْعَلَّ`, Form IX. A source curator and the subsequent Astra review
independently confirmed that witness. The correction preserves the QAC-primary
Form VII analysis from ق ض ض and the attributed alternative; it corrects the
pattern and its explanation for 18:77:17:1. Agreement in the earlier agent
reviews cannot outweigh the vocalized source.

### Workflow decision and review history

The user selected GPT-6 Sol, maximum reasoning, with at most eight concurrent
workers, and authorized Astra agents after checking unsatisfactory output.
The controller reviewed two Sol infrastructure proposals and commissioned
GPT-6 Astra to review their unnecessary complexity and provenance coupling.
The accepted design uses one supplemental registry, sealed Arabic intake,
one preparation adapter, and one reviewed exporter. It does not require a
second Furuq database or QNet/packet reconstruction. Historical snapshot hashes
remain historical, with current validity checked against the affected
selectors and branch evidence.

Agent A writes a missing output; independent Agent B reviews its immutable
snapshot and records any bounded correction before editing. Structural or
ambiguous findings remain editorial decisions. The four lexical exports use
the established root format; grammatical exports have an explicit headword
format. App catalogs will carry the two headwords inline with bounded size.
Lexicon circles may add LI (Lisān), MH (al-Muḥkam), and TJ (Tāj al-ʿarūs);
grammar and tafsir sources remain typed citations, not dictionary circles.

### Source seal and authored review results

The six Arabic intakes were sealed in `data/supplemental/registry.v1.json` on
September 24 with registry SHA-256
`f1dd33df0ed475eb05d44cfb47f55d2f8c372622106196525342dad4d4086fd5`.
Independent source review accepted 15 lexical branches and three grammatical
senses. Before sealing, Astra inspected Tāj al-ʿarūs volume 4, internal page
1172 (PDF page 213), replacing an insufficient short excerpt with an exact
bounded transcription. It confirms the reported Abū Dharr opinion that لات
developed from a diminution verb into negation, without establishing that
opinion as consensus or as QAC's rationale. The intake records the digital
witness, transcription method and hashes.

Six separate GPT-6 Sol Max writers finished, followed by six independent
GPT-6 Sol Max reviewers. Outcomes:

| Entry | Authored units | Independent review |
| --- | ---: | --- |
| `root_900001` ءدد | 5 branches | pass |
| `root_900002` ثبي | 3 branches | pass |
| `root_900003` سنه | 2 branches | pass |
| `root_900004` قضض | 5 branches | pass |
| `headword_000001` كَيْفَ | 2 senses | repair completed |
| `headword_000002` لَاتَ | 1 sense | pass |

The كَيْفَ reviewer recorded its finding and validated the review before
changing only S001's identity rationale. The correction preserves the
different grammatical classifications reported by Ṣiḥāḥ and by ʿAyn/Tahdhīb.
Its immutable pre-fix snapshot remains in the review input. Both corrected
writer output and review validated. There are five unchanged passes, one
completed surgical repair, zero editorial-review holds, zero missing writers,
and zero writers awaiting review. These are authoring results; transfer and
publication are separate checkpoints.

The لَاتَ sense uses only its attested temporal construction as a lexical
unit. The separate bare headword unit was removed before sealing because it
duplicated the title and obscured the construction restriction. The كَيْفَ
core is bare, and its second sense is the `كيف يشاء` construction. Indirect
نوص/مناص citations remain intake context for لَاتَ, outside its sense source
roster and dictionary circles.

### Reviewed export and consumer contract

All six reviewed exports were produced and independently checked by Astra
against the dictionary export gate, quran-data intake and export validators,
and the app projector and JSON schemas. The exported total is 15 root branches
and three headword senses. The headword collection is approximately 35 KiB,
within the 128 KiB limit.

This integration review caught and corrected shared prompt-path expectations,
headword field projection, and citation-note attribution. Translated summaries
are separate `citationNotes` records keyed to each claim's exact source keys;
the original citation objects remain byte-faithful to intake. The headword
usage note preserves the reviewed identity rationale, including the كَيْفَ
classification correction. Intake-only context does not acquire a sense
citation or dictionary badge. Transfer validation accepts unique claim IDs
without imposing a per-sense numeric restart, and permits zero-occurrence
branches within a complete disjoint QAC partition. Neither fix renumbers or
alters the sealed source evidence.

The shared staged reviewer validator was corrected to validate the immutable
pre-fix snapshot and the recorded bounded repair. Rerunning it after a valid
correction no longer fails merely because the live writer bytes changed.
Future staged instructions now state the review-before-repair sequence
without contradictory command/edit restrictions. Existing sealed bundles
were not regenerated. All six actual staged reviewer validations pass.

A further workflow correction treats the registry digest sealed in each
production task/export as historical provenance. Current validation still
requires the exact selected ID, kind, intake path, and intake content hash;
release manifests pin the complete current registry. This avoids forcing new
editorial work for unchanged entries when an unrelated registry row is added.
Regression checks accept that unrelated append and reject a changed selected
intake. The six original source seals and reviewed responses are unchanged.

## Six-entry live publication — 2026-09-24

The reviewed source batch in dictionary
`e553f0afe23f32c422561bcd3ee7e65f0b503b2b` was transferred in quran-data
`aa2aef1966eceb4169660b2a874f3de2c081c748` and published through quran-apps.
Reader **generation 12** activated at `2026-09-24T18:46:31.744Z` with catalog
SHA-256 `4c022f0b22ec89a417cf134d51daf087db4902ecaf75d583afab53f9ab47cd58`.
Tafsir evidence **generation 8** has catalog SHA-256
`52d6ea7a57d7d665bf89028c915dff4850f3c0587349e9842af383990d01770b`.

KK **0.1.64** (`/assets/index-C-wcA-_W.js`) and TM **0.2.16**
(build `dd16911b8815ff75dafb0962`) are deployed. Their common dictionary has
1,700 root entries, 1,711 component roots and 11,756 branches, plus two
separate grammatical headwords covering 84 morphemes. The four lexical
additions cover four further morphemes. The lexical root-resolution keys
`كيف` and `لوت` intentionally remain unresolved as roots; their exact words
are served by grammatical entries. They are not outstanding entry-production
gaps. The raw QAC noun/verb tags and documented alternative analyses remain
available, and the deity at 53:19 is excluded from the grammatical لَاتَ entry.

The publication barrier and final remote evidence check verified all 847
immutable objects (451,007,837 bytes), the active pointer and the two pinned
legacy pointers. Reader uploaded 230 objects (229 packs plus its source lock),
validated the release, adopted the exact Worker-signed activation and passed
its separate live verification. Both channels were published on the existing
Cloudflare Free configuration. No commentary channel changed in this batch.

The quran-apps root `CDN-UPDATE-RUNBOOK.md` documents the committed-source
transfer, single `data:update` build, separate evidence/Reader publishers,
retry rules and live checks. Later documentation-only commits do not supersede
the source pins above or require another data release.

### Verification scope and remaining audit recommendation

The source/transfer checks, contract/runtime suites, application builds, live
CDN verification, and 31 sampled live static agent files passed. These establish
release integrity and the tested entry behavior; they do not certify the semantic
accuracy of every existing dictionary definition.

The complete legacy compiler suite still has two unrelated fixture setup
failures: the committed QAC crosswalk manifest expects a different quran-data
`RELEASE.json` hash, and the committed demo lock expects a different
`packages/content-compiler/target-mappings/s001.tr.json` hash. Both actual inputs
match their repository HEAD versions. The focused six-entry projector tests and
actual publication builds pass. Those old locks were not silently regenerated
as part of this dictionary release.

The controller recommends a whole-corpus mechanical audit of entry coverage,
root and exact-word mappings, transfer parity, citation/source ownership,
review provenance, branch type, and gloss-assessment consistency. Independent
editorial review should prioritize proper names, grammatical headwords, weak
and doubled roots, disputed derivations, and older review records. A stratified
sample of the remaining entries should determine whether a complete semantic
re-review is warranted. The six deliberately difficult gaps are not a random
sample, so their findings must not be extrapolated into a corpus-wide error
rate. This recommendation is documented; no new whole-corpus editorial
production campaign has been started.

### TM startup correction found by the live browser audit

The post-publication browser audit found that TM could still show the legacy
third `سمم` candidate for `اسم` while its bundled demonstration corpus was
visible. The generation-8 catalog and KK contained only the accepted `سمو`
and `وسم` analyses. TM treated a seeded ayah as already loaded, and its startup
loader chose a surah only after awaiting another catalog request. Navigation
during startup could therefore leave seeded research data in use.

The TM 0.2.17 correction tracks ayahs merged from live loader results, fetches
seeded ayahs when needed, captures the initial surah before awaiting the
catalog, and shares in-flight loads between startup and navigation. Production
research panels show loading or unavailable status until live data is ready;
the local demonstration mode is retained. The source dictionary and CDN
catalogs did not need another data release. This case is further evidence that
an audit must cover source-to-screen behavior in both clients, including slow
loads and navigation, as well as source content and transfer hashes.

TM 0.2.17 was subsequently deployed with build ID
`d6a0d86a16179f9b46b32bf0`. Its served HTML, application script and translations
match the reviewed build byte for byte. Independent review, all 25 TM tests
(including two new asynchronous startup/retry regressions), and the production
build passed. The application release is committed in quran-apps `79810f9e`;
the TM startup correction is committed in `0fbcd8ba`.

The final deployed browser audit passed **34/34 cases** on September 24
(8 existing-profile cases and 26 fresh desktop/mobile cases), with zero page
errors and zero failed application/CDN responses. It covered all four new
roots, both headwords, the three QAC noun-tagged كَيْفَ occurrences, the deity
exclusion, and اسم's two accepted roots without سمم. Source circles, usage
badges, typed citations, authored citation notes and gloss-assessment bindings
were checked against the live payloads. The existing TM profile visibly
upgraded from 0.2.16 to 0.2.17; the earlier KK 0.1.63/Reader-11 to
0.1.64/Reader-12 upgrade evidence was retained. The local quran-apps audit report
is `.scratch/six-live/2026-09-24T21-17-18-337Z-14b7ea1b-report.json`.

An additional live TM slow-load/navigation check also passed: delaying the
public evidence activation GET for three seconds showed loading status and
zero bundled root cards. Releasing the response displayed only `سمو`/`وسم`;
navigation `1:1 → 2:28 → 1:1` displayed the كَيْفَ headword and then restored
only those two اسم roots, including after settling. There were no page errors
or failed responses. The local report is
`.scratch/six-live/2026-09-24T21-22-14-436Z-e1a23ed4-delayed-tm-report.json`.

### S1 sampling audit after publication — September 24

At the user's request, GPT-6 Sol Max screened all 157 branches of the 19
existing root entries linked from S1, including both اسم alternatives.
Separate deeper checks retained nine branches for surgical correction and
dismissed ten initial flags. The 157 source anchors and the exported authored
fields matched their dictionary originals. Findings therefore concern existing
authored wording, not this transfer. No canonical data or CDN release changed.
148 English definition drafts were saved separately; nine remain pending.

The earlier broad audit recommendation is narrowed: the original mapping and
new-draft problems did not establish widespread semantic errors in existing
entries. This targeted sample provides concrete findings, not a corpus error
rate. Continue compact screening then deeper review only of flags, preserving
root ambiguity and existing source anchoring. Detailed rationale and proposed
repairs are in dictionary's root `S1-DICTIONARY-AUDIT-2026-09-24.md` and
`v2/audits/s001-2026-09-24/`. The nine proposals have not been applied.

### Blind Luna comparison of S1 — September 24

The user authorized a blind GPT-6 Luna Max repeat using the same 157 branch
inputs and instructions. Fresh workers saw no Sol findings; completed batches
were compared immediately. Luna referred three of the previous nine problem
branches and passed six. Its reasons did not explicitly identify those three
retained problems. It independently raised two other wording issues retained
by Astra review, plus one unresolved eye-terminology concern. The combined
queue is eleven documented correction branches and one unresolved concern.

A blinded comparison of 22 shared English drafts found five minor fidelity
deviations and one substantive error in Luna drafts, versus no errors in Sol
drafts in that particular comparison. Keep Sol as the main screener and
definition drafter; Luna may contribute an additional independent pass. Do not
use this one targeted sample as a corpus-wide error-rate estimate. All drafts
remain unapproved; no canonical source, export or live release changed.

Detailed reasoning, raw outputs, adjudications, and the English hold list are
in dictionary's root `S1-LUNA-BLIND-COMPARISON-2026-09-24.md` and
`v2/audits/s001-luna-blind-2026-09-24/`.
