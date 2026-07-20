-- Evidence repairs required by the first v2 water-root production pilot.
-- This migration is idempotent and is applied to furuq_v4.sqlite before the
-- checked-in gzip snapshot is regenerated.

BEGIN IMMEDIATE;

-- ي م م / B002: retain the ritual use as a lexicalized specialization of B001.
UPDATE branch_images
SET branch_image_ar = 'التيمم للصلاة بمسح الوجه واليدين بالتراب',
    branch_image_en = 'ritual dry ablution for prayer by wiping the face and hands with dust',
    image_en_fit = 'close',
    image_en_gap_note = '-',
    what_is_ar = 'يدخل فيه الاستعمال الصلاتي المتخصص: تيمم الصعيد الطيب للصلاة، وما صار إليه لفظ التيمم بكثرة الاستعمال من مسح الوجه واليدين بالتراب.',
    what_is_en = 'This branch covers the specialized prayer use: seeking clean earth and the conventionalized use of tayammum for wiping the face and hands with dust.',
    what_is_not_ar = 'لا يدخل فيه مطلق قصد الشيء وتعمده وتوخيه خارج الاستعمال الصلاتي، ولا اليم بمعنى البحر أو الماء العظيم، ولا اليمام الطير ولا اليمامة اسما أو موضعا.',
    status = 'accepted',
    review_note = 'Al-Sihah derives تيمم الصعيد from the broader التعمد والتوخي branch, then explicitly states that frequent usage conventionalized التيمم as wiping the face and hands with dust. B002 is retained as an analytical lexicalized ritual specialization of B001, not as a separate root أصل; B003 remains the unrelated اليم water branch.',
    contaminated = 'no'
WHERE root_id = 'root_001697' AND branch_id = 'B002';

-- ب ح ر / B011: keep the attested consumption and bodily-wasting cluster.
UPDATE branch_images
SET branch_image_ar = 'الداء المورث للسُّل وذهاب اللحم',
    branch_image_en = 'consumption-causing disease and bodily wasting',
    image_en_fit = 'close',
    image_en_gap_note = 'English does not encode the distribution across أبحر, البحر, and البحير or the camel-specific source discussion.',
    what_is_ar = 'يدخل فيه أبحر الرجل إذا أخذه السل، والبحر والبحير لمن به السل، والبحير للمسلول الجسم الذاهب اللحم، والبحر داء في الإبل يورث السل.',
    what_is_en = 'This branch covers consumption-causing disease and bodily wasting, including the cited human and camel expressions.',
    what_is_not_ar = 'لا يدخل فيه الفعل بحر بمعنى اشتد عطشه فلم يرو من الماء، ولا البَحْران الطبي، ولا البحر الماء أو ملوحته.',
    source_phrase_ar = 'أبحر الرجل إذا أخذه السل (tahdhib)؛ البحير والبحر الذي به السل (tahdhib)؛ البحر داء في الإبل وقد بحرت (sihah)؛ وأما البحر فهو داء يورث السل (tahdhib)؛ البحير المسلول الجسم الذاهب اللحم (tahdhib)',
    status = 'accepted',
    review_note = 'Rewritten and split from the former disease/thirst cluster. The accepted core is consumption and bodily wasting; Sihah''s unquenched-thirst verb moved to B014. Unsupported المبحر was removed; the cited form is البحير. Tahdhib''s correction of the camel water-condition remains an explicit source disagreement rather than part of the branch image.',
    contaminated = 'no'
WHERE root_id = 'root_000086' AND branch_id = 'B011';

-- ب ح ر / B012: later technical material is accepted only with its muwallad
-- chronological and register boundary made explicit.
UPDATE branch_images
SET branch_image_ar = 'المصطلحات المولَّدة: البُحْران الطبي والباحور',
    branch_image_en = 'muwallad medical-crisis and Tammuz-heat terminology',
    image_en_fit = 'close',
    image_en_gap_note = 'Sihah explicitly labels the medical crisis-day and Tammuz heat-day expressions as مولد; acceptance records later technical usage, not inherited or Quranic-era activation.',
    what_is_ar = 'يدخل فيه اصطلاح الأطباء البُحْران للتغير المفاجئ في الأمراض الحادة، ويوم بُحْران ليوم الأزمة الطبية، ويوم باحورى وباحور لشدة الحر في تموز؛ وجميع هذا موسوم في الصحاح بأنه مولَّد.',
    what_is_en = 'Later technical terminology explicitly attested by Sihah: buhran for the sudden crisis in an acute illness, yawm buhran for its crisis day, and yawm bahura/bahur for intense Tammuz heat; Sihah labels the whole set muwallad.',
    what_is_not_ar = 'لا يدخل فيه البحر المائي، ولا داء الإبل أو السل والعطش في B011، ولا يُتخذ هذا الاستعمال المولَّد دليلا على دلالة قرآنية أو عربية موروثة.',
    source_phrase_ar = 'التغير الذي يحدث للعليل دفعة في الأمراض الحادة بحران (sihah)؛ هذا يوم بحران بالإضافة (sihah)؛ يوم باحورى منسوب إلى باحور وباحوراء وهو شدة الحر في تموز؛ وجميع ذلك مولد (sihah)',
    status = 'accepted',
    review_note = 'Accepted as an explicitly bounded muwallad technical/calendar branch: Sihah directly attests بحران, يوم بحران, and يوم باحورى or باحور and labels the entire set مولد. Acceptance records the later usage without treating it as inherited Arabic or Quranic activation; it remains separate from B011 and B014.',
    contaminated = 'no'
WHERE root_id = 'root_000086' AND branch_id = 'B012';

-- ب ح ر / B014: split the separately attested severe-thirst verb from B011.
INSERT INTO branch_images (
    root_id, source_path, batch_id, root_norm, branch_id,
    branch_image_ar, branch_image_en, image_en_fit, image_en_gap_note,
    what_is_ar, what_is_en, what_is_not_ar, source_refs, source_phrase_ar,
    status, review_note, origin_corpus, contaminated
)
SELECT
    'root_000086',
    'v4/outputs/pass2_branches/root_000086.branches.tsv',
    'v4_all_pass1',
    'ب ح ر',
    'B014',
    'اشتداد العطش مع عدم الرِّيّ',
    'severe unquenched thirst',
    'close',
    'The English phrase renders فلم يرو من الماء but must not be extended to the disputed camel-disease terminology.',
    'يدخل فيه الفعل بحر بمعنى اشتد عطشه فلم يرو من الماء، كما أورده الصحاح عقب بحر الرجل.',
    'This branch covers the verb بحر meaning to become severely thirsty without being satisfied by water, as recorded in Sihah.',
    'لا يدخل فيه داء الإبل المسمى البحر، ولا السل وذهاب اللحم، ولا البحر الماء أو ملوحته.',
    'sihah:file=0393IbnHammadJawhari.SihahTajLugha.Shamela0023235-ara1:section=heading%3A1542:headword=%D8%A8%D8%AD%D8%B1:root=%D8%A8%20%D8%AD%20%D8%B1:sha=cb907cb357f97130;tahdhib:file=tahdhib.sqlite_original:section=parent_entry_id%3D238%3Bsegment_index%3D8:headword=%D8%A8%D8%AD%D8%B1:root=%D8%A8%20%D8%AD%20%D8%B1:sha=fb880a236603942c',
    'بحر إذا اشتد عطشه فلم يرو من الماء (sihah)؛ الداء الذي يصيب البعير فلا يروى من الماء هو النجر والبجر وكذلك البقر، وأما البحر فهو داء يورث السل (tahdhib)',
    'accepted',
    'New single-positive-attestation split for Sihah''s verbal thirst use. Tahdhib''s correction concerns camel-disease terminology and is retained only as negative boundary evidence; it does not explicitly reject Sihah''s verbal use.',
    'quranic',
    'no'
WHERE NOT EXISTS (
    SELECT 1 FROM branch_images
    WHERE root_id = 'root_000086' AND branch_id = 'B014'
);

UPDATE lexical_unit_senses
SET status = 'accepted',
    review_note = 'Accepted under the rewritten B011 consumption and bodily-wasting boundary.'
WHERE root_id = 'root_000086' AND lexical_unit_id = 'lu_025';

UPDATE lexical_unit_senses
SET unit_key = 'ب ح ر::form::البحر والبحير::الداء',
    expression_ar = 'البحر والبحير',
    status = 'accepted',
    review_note = 'Accepted under B011 after unsupported المبحر was removed from the expression roster.'
WHERE root_id = 'root_000086' AND lexical_unit_id = 'lu_026';

UPDATE lexical_unit_senses
SET branch_ids = 'B014',
    status = 'accepted',
    review_note = 'Accepted under the new B014 severe-unquenched-thirst branch; Tahdhib supplies a camel-disease boundary rather than a rejection of Sihah''s verbal use.'
WHERE root_id = 'root_000086' AND lexical_unit_id = 'lu_027';

UPDATE branch_lexical_unit_links
SET branch_id = 'B014'
WHERE root_id = 'root_000086'
  AND branch_id = 'B011'
  AND lexical_unit_id = 'lu_027';

UPDATE lexical_unit_senses
SET status = 'accepted',
    review_note = 'Accepted as explicitly muwallad medical-crisis terminology; it is not evidence for Quranic-era activation.'
WHERE root_id = 'root_000086' AND lexical_unit_id = 'lu_028';

UPDATE lexical_unit_senses
SET unit_key = 'ب ح ر::collocation::يوم بحران::الأزمة الطبية',
    expression_ar = 'يوم بحران',
    sense_ar = 'يوم الأزمة الطبية',
    sense_en = 'medical crisis day',
    source_phrase_ar = 'هذا يوم بحران بالإضافة (sihah)',
    status = 'accepted',
    review_note = 'Split from the former conflated يوم بحران وباحورى unit and accepted as explicitly muwallad medical terminology.'
WHERE root_id = 'root_000086' AND lexical_unit_id = 'lu_029';

INSERT INTO lexical_unit_senses (
    root_id, source_path, batch_id, root_norm, lexical_unit_id, unit_key,
    expression_ar, unit_kind, branch_ids, sense_ar, sense_en, sense_en_fit,
    sense_en_gap_note, source_refs, branch_source_refs, source_phrase_ar,
    status, review_note, corpus_link_status, corpus_link_count, origin_corpus
)
SELECT
    'root_000086',
    'v4/outputs/pass3_senses/root_000086.senses.tsv',
    'v4_all_pass1',
    'ب ح ر',
    'lu_033',
    'ب ح ر::collocation::يوم باحورى وباحور::حر تموز',
    'يوم باحورى وباحور',
    'collocation',
    'B012',
    'شدة الحر في تموز',
    'intense Tammuz heat or its day',
    'close',
    '-',
    'sihah:file=0393IbnHammadJawhari.SihahTajLugha.Shamela0023235-ara1:section=heading%3A1542:headword=%D8%A8%D8%AD%D8%B1:root=%D8%A8%20%D8%AD%20%D8%B1:sha=cb907cb357f97130',
    'sihah:file=0393IbnHammadJawhari.SihahTajLugha.Shamela0023235-ara1:section=heading%3A1542:headword=%D8%A8%D8%AD%D8%B1:root=%D8%A8%20%D8%AD%20%D8%B1:sha=cb907cb357f97130',
    'يوم باحورى منسوب إلى باحور وباحوراء وهو شدة الحر في تموز (sihah)',
    'accepted',
    'Split from the former conflated يوم بحران وباحورى unit and accepted as explicitly muwallad calendar and heat terminology.',
    'not_form_unit',
    0,
    'quranic'
WHERE NOT EXISTS (
    SELECT 1 FROM lexical_unit_senses
    WHERE root_id = 'root_000086' AND lexical_unit_id = 'lu_033'
);

INSERT INTO branch_lexical_unit_links (
    root_id, branch_id, lexical_unit_id, link_source
)
SELECT 'root_000086', 'B012', 'lu_033', 'water_pilot_review'
WHERE NOT EXISTS (
    SELECT 1 FROM branch_lexical_unit_links
    WHERE root_id = 'root_000086'
      AND branch_id = 'B012'
      AND lexical_unit_id = 'lu_033'
);

UPDATE branch_reviews
SET issue_target = 'B011;B014',
    status = 'resolved',
    review_note = 'Resolved by retaining consumption and bodily wasting in B011 and splitting Sihah''s severe-thirst verb into B014; Tahdhib''s camel-disease correction remains boundary evidence.'
WHERE root_id = 'root_000086' AND review_id = 'br_review_003';

UPDATE branch_reviews
SET status = 'resolved',
    review_note = 'Resolved by accepting B012 as an explicitly bounded muwallad technical and calendar branch, without treating it as inherited Arabic or Quranic activation.'
WHERE root_id = 'root_000086' AND review_id = 'br_review_004';

UPDATE sense_reviews
SET branch_ids = 'B011;B014',
    blocks_acceptance = 0,
    status = 'resolved',
    review_note = 'Resolved by the B011 disease/wasting rewrite and B014 severe-thirst split; the source disagreement is preserved as a branch boundary.'
WHERE root_id = 'root_000086' AND review_id = 'sense_review_003';

UPDATE sense_reviews
SET blocks_acceptance = 0,
    status = 'resolved',
    review_note = 'Resolved by accepting the branch as explicitly muwallad and splitting the medical crisis-day and Tammuz heat-day lexical units.'
WHERE root_id = 'root_000086' AND review_id = 'sense_review_004';

-- ب ء ر: restore the final SHA character omitted from Pass 2/Pass 3 refs.
UPDATE branch_images
SET source_refs = replace(
    source_refs,
    'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a',
    'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a3'
)
WHERE root_id = 'root_000078';

UPDATE branch_reviews
SET source_refs = replace(
    source_refs,
    'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a',
    'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a3'
)
WHERE root_id = 'root_000078';

UPDATE lexical_unit_senses
SET source_refs = replace(
        source_refs,
        'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a',
        'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a3'
    ),
    branch_source_refs = replace(
        branch_source_refs,
        'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a',
        'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a3'
    )
WHERE root_id = 'root_000078';

UPDATE sense_reviews
SET source_refs = replace(
    source_refs,
    'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a',
    'mufradat:file=0502RaghibIsbahani.Mufradat.Shamela0023636-ara1:section=heading%3A160:headword=%D8%A8%D8%A6%D8%B1:root=%D8%A8%20%D8%A1%20%D8%B1:sha=3db34c77723642a3'
)
WHERE root_id = 'root_000078';

COMMIT;
