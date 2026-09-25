# S1 blind Luna–Sol comparison — 2026-09-24

## Decision

Keep GPT-6 Sol Max as the main compact screener and English-definition drafter for this workflow, with deeper review of flags. Luna Max can contribute an additional independent pass, but this run does not support using Luna as the sole gate deciding which entries Sol sees. It passed six of the nine previously retained problem branches.

Luna nevertheless found two additional wording issues missed in the completed Sol audit. Independent Astra review retained both with bounded corrections and downgraded another proposed error to unresolved. Model disagreement was useful; Sol's results were not treated as an exhaustive answer key.

## Controlled run

The user requested a blind repeat of all S1 entries and then asked for comparisons as each batch finished. Eight fresh GPT-6 Luna Max agents received the same eight input files, byte for byte, as the earlier GPT-6 Sol Max run: **19 roots, 157 branches**, including both اسم alternatives and all branches of those roots. The screening instruction file changed only the model name. No previous findings or outputs were supplied. Comparisons and deeper reviews began on completed batches while other Luna workers continued.

Blindness used fresh agent contexts and explicit access restrictions in a shared workspace; it was not enforced by separate operating-system sandboxes. Input/output hashes, original results and the two structural-only repair types are saved in [RUN-MANIFEST.json](v2/audits/s001-luna-blind-2026-09-24/RUN-MANIFEST.json). The model output repairs only set a flagged English draft to null and restored exact Arabic quotation spelling. No verdict or semantic reason was changed.

## Screening comparison

| Measure | Sol Max | Luna Max |
|---|---:|---:|
| Branches screened | 157 | 157 |
| Branches referred for deeper review | 19 | 14 |
| Of the previous nine problem branches, referred | 9 | 3 |
| Of those nine, returned `no_flag` | 0 | 6 |

Luna's three overlapping referrals were `root_000532/B005`, `root_000532/B007`, and `root_000973/B003`. Its explanations questioned whether animal/mate senses and false-power usages were supported. Fuller sources do support those usages. Luna did **not explicitly identify the retained participant-scope problems or the worship/human-directed-humbling problem**. These referrals create opportunities for deeper review; they are not three independently correct diagnoses.

Luna passed the other six retained problem branches: `root_000532/B012` (small tree), `root_000532/B013` (abundant water), `root_001583/B009` (male-referent gloss), `root_000913/B003` (unavenged versus no attempt at redress), `root_001092/B004` (source-qualified rock description), and `root_000355/B005` (praise-seeking scope).

Of Luna's 14 literal flag explanations after adjudication, two identify additional correction-worthy wording, one remains unresolved, and eleven are dismissed. Three dismissed explanations occur in branches that do have different previously retained problems; therefore these counts must not be converted into a simple branch error rate. Many dismissals were caused by information absent from the compact excerpt but present in the original generation evidence.

## Additional findings and adjudication

| Branch | Final disposition | Reason and boundary |
|---|---|---|
| `root_001525/B008` | Confirmed, limited definition issue | “Hızla dağılıp ayrılması” requires speed for the dispersal alternative. Sources also allow unqualified dispersal. Preserve rapid departure as an attested variant and retain continuing travel; do not replace it with merely starting a journey. Sol had reviewed a different gloss concern in this branch and missed this wording issue. |
| `root_000355/B002` | Confirmed, necessary-condition overstatement | Prior testing/experience is attested as an example but repeatedly made a requirement in the Turkish branch. Preserve the testing example while allowing the productive “find someone praiseworthy” use. Do not impose fixed-phrase status on the whole mixed branch. Part of the restriction already occurs in the provisional generated Arabic summary; that summary is not additional primary evidence. |
| `root_001273/B021` | Unresolved editorial precision | “Intact visible eye structure” may sound overprecise, but الحدقة is not securely equivalent to the modern anatomical pupil alone. Astra rejected automatic pupil-only replacement because it could itself narrow the source. |

Astra examined the initially retained new findings after the controller questioned overconfident lexical scope conclusions and proposed fixes. The original Sol reviews and final Astra adjudications are both retained. Exact original Arabic evidence supports local claims; the eye terminology also received one targeted [Lisān al-ʿArab lookup](https://www.islamweb.net/amp/ar/library/content/122/1649/حدق). No root, Quran-context sense or source disagreement was resolved by preference.

Together with the earlier nine findings, there are now **eleven documented branches needing bounded correction and one unresolved wording concern**. No canonical entry has been repaired by these audit sessions; none of these findings has yet been exported or published. These are proposals requiring the existing repair/provenance workflow.

## English comparison

The 24-branch deterministic sample from the earlier audit was retained. Two selected branches had no Luna draft, leaving **22 paired definitions**. A fresh Sol Max reviewer saw randomized A/B labels per branch, the Turkish paragraph, and its existing Arabic anchor/qualification; model labels and prior findings were withheld.

| Paired-review judgment | Sol drafts | Luna drafts |
|---|---:|---:|
| Acceptable draft | 22 | 16 |
| Minor fidelity deviation | 0 | 5 |
| Substantive semantic error | 0 | 1 |

The substantive Luna error in `root_001092/B001` is “a consequence of punishment”: it reverses the relation intended by the divine-use punishment result. Minor deviations include added “before God,” omitted gentle manner, camels described as burdened without that qualification, benefit narrowed to kindness, and an added derivational “by extension.” These are experiment outputs, not changes to the live dictionary.

This is one small, nonrandom comparison, not a guarantee that Sol drafts are error-free. The previous English spot review had recommended a terminology adjustment, and two controller corrections to earlier Sol drafts are documented in the first audit. The latter two corrected drafts are outside this paired sample. The paired review used the saved initial screening outputs, not a newly optimized Sol rerun.

## Artifacts and limits

- [Full comparison and per-flag dispositions](v2/audits/s001-luna-blind-2026-09-24/comparison/results.json).
- [Earlier S1 audit](S1-DICTIONARY-AUDIT-2026-09-24.md); baseline dictionary commit `d503c52db`.
- Saved inputs, normalized outputs, immutable raw Luna outputs, blinded English pairs, hidden assignment key, reviewer judgments and Astra adjudications are under `v2/audits/s001-luna-blind-2026-09-24/`.
- [English hold list](v2/audits/s001-luna-blind-2026-09-24/ENGLISH-DRAFT-HOLDS.json) flags previous drafts requiring reconsideration. All Luna drafts remain experimental and unapproved.
- One run per model cannot estimate general sensitivity, stability or a corpus error rate. The initial nine reference findings are not exhaustive truth; additional findings remain open to evidence-based revision. No actual comparative token billing was measured.
- No canonical dictionary, quran-data export, application or live CDN release changed. The comparison and new repair proposals are documented only.
