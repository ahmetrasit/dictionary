# Concept Envelope Gloss — Methodology

## Current Architecture Note

This is a historical methodology and target-language adapter background document. For the current end-to-end corpus architecture, read `_corpus/ARCHITECTURE.md`. Future target-language glossing should consume reviewed activation records and Arabic commentary, then render them into the target language; it should not independently re-adjudicate active Arabic senses from raw Quranic context except under a review/debug workflow.

A six-phase methodology for producing honest target-language glosses of
Quranic words. The gloss is derived from the full semantic envelope of the
Arabic — root image, morphological form, syntactic frame, Quranic usage
census, and furuq exclusions — not from translating a prior translation.

The method produces:
- A concept definition (what the Arabic word IS and IS NOT)
- A prose translation of the concept (not a single word)
- Ranked glosses with explicit gap analysis per target-language candidate

All examples below use ض-ر-ب (daraba) in Q 4:34 as the worked case.

---

## Phase 1 — Root Identity

Establish the root's branch structure from classical lexicography.

### Steps

1. Look up the root in the branch map (Maqayis-grounded, `branch_map.sqlite`)
2. Record branch count and each branch's core sense in Arabic
3. Cross-check against at least 3 other dictionaries (Lisan, Lane, Mufradat,
   Ayn, Sihah) — does the branch count hold independently?
4. If one branch: record the unified root image
5. If multiple branches: identify which branch the target word falls under

### Expected output

```
Root: ض ر ب
Branches: 1 (Maqayis: أصل واحد ثم يستعار ويحمل عليه)
Root image: إيقاع شيء على شيء — making one thing fall upon another
Cross-check: Lisan connects travel sense via ومن الباب (same chapter);
  Lane presents under one undivided article; Mufradat derives all senses
  from the إيقاع image. All confirm single branch.
```

---

## Phase 2 — Quranic Usage Census

Map every occurrence of the root in the Quran to build a frame-to-sense map.

### Steps

1. Grep every occurrence of the root across the complete Quran text
2. For each occurrence, record:
   - Verse reference
   - Exact word form (morphological form: I, II, IV, etc.; voice; mood)
   - Syntactic frame (transitive/intransitive, prepositions, object type)
   - Activated sense
3. Build the frame-to-sense map: which syntactic frame selects which sense
4. Calculate distribution: count and percentage per sense

### Expected output

```
Total occurrences: 58 (across 51 verses)

Frame-to-sense map:
  ضَرَبَ + مَثَلًا           → set forth a parable (30 occ, 55%)
  ضَرَبَ + direct object      → physical striking (14 occ, 25%)
  ضُرِبَ عَلَيْهِمُ + noun   → imposed condition (3 occ, 5%)
  ضَرَبَ فِى ٱلْأَرْضِ      → travel (6 occ, 11%)
  ضُرِبَ بَيْنَهُم بِـ      → barrier erected (1 occ, 2%)
  نَضْرِبُ عَنْكُمُ         → turn away (1 occ, 2%)

Key finding: transitive + human direct object (no preposition) maps to
physical striking in 100% of cases. No exceptions.
```

---

## Phase 3 — Target Word Analysis

Analyze the specific form in the target ayah.

### Steps

1. Identify the exact morphological form (Form I/II/III/IV, voice, mood)
2. Identify the syntactic frame (transitivity, prepositions, object type,
   attached pronouns)
3. Match against the frame-to-sense map from Phase 2
4. Check all canonical and shadhdh qira'at for variants that change the
   reading — specifically test for 5:6-type mechanisms (where i'rab on a
   governed noun shifts which verb governs it)
5. Test for multi-sense activation (17:50-type layering) — can two branches
   or senses co-activate in this syntactic frame? Requires that the secondary
   sense be compatible with the same argument geometry and target domain
6. Analyze verse-internal grammatical constraints (conditional triggers,
   sequence markers, cessation clauses, closing divine names)

### Expected output

```
Target: وَٱضْرِبُوهُنَّ (Q 4:34)
Form: Form I imperative (اضربوا) — unmarked, not intensive (vs Form II ضَرَّبَ)
Frame: transitive + direct object pronoun (هُنَّ), no preposition
Sense match: physical striking (100% frame match from census)

Qira'at check: no variant recorded across any canonical or shadhdh reading.
  Syntactic structure (3 coordinated imperatives with fused pronouns) has no
  5:6-type ambiguity — no loose noun between two potential governors.

Multi-sense test: BLOCKED. Travel sense requires في الأرض (ground as
  target); turning-away requires عن; parable requires مثلا. Each secondary
  sense needs a different target domain than هُنَّ provides. Unlike 17:50
  where noun branches describe the same referent from different angles, here
  the verb senses require incompatible argument geometry.

Verse-internal constraints:
  - Gated by: تَخَافُونَ نُشُوزَهُنَّ (specific trigger condition)
  - Position: third in graduated sequence (فَعِظُوهُنَّ → وَٱهْجُرُوهُنَّ → وَٱضْرِبُوهُنَّ)
  - Conjunction: وَ (not ثُمَّ) — permits both menu and escalation readings
  - Cessation: فَإِنْ أَطَعْنَكُمْ فَلَا تَبْغُوا۟ عَلَيْهِنَّ سَبِيلًا
    (nakira in scope of negation = absolute: no way at all)
  - Closing names: عَلِيًّا كَبِيرًا (divine authority dwarfs the granted permission)
```

---

## Phase 4 — Furuq (Negative Space)

Identify what the word IS NOT by analyzing what the Quran chose not to use.

### Steps

1. Identify all near-synonym roots in the same semantic field from the concept
   map neighbors and branch map
2. For each neighbor that is Quranically attested:
   - Pull its root image and branch structure
   - Find its Quranic usage to confirm it was available vocabulary
   - Articulate what semantic load it carries that the target root does NOT
3. Build the "what X is NOT" inventory from the rejected alternatives
4. Also check: was Form II (or another form) available and not selected? What
   does the form non-selection tell you?

### Expected output

```
ض-ر-ب IS NOT:
  - ج-ل-د (jalada): skin-marking prescribed punishment. Used in 24:2, 24:4
    with count (100/80 lashes), labeled عذاب, compassion suppressed.
    EXCLUDED: punitive corporal punishment apparatus.
  - ب-ط-ش (batasha): violent overpowering seizure. Used for God's wrath
    (85:12) and tyrannical rulers (26:130).
    EXCLUDED: crushing dominance, overwhelming force.
  - ن-ك-ل (nakkala): exemplary deterrent punishment. Used in 2:66, 79:25.
    EXCLUDED: spectacle-punishment to prevent repetition by others.
  - ر-ج-م (rajama): hostile stoning/expulsion. Used in 11:91, 19:46.
    EXCLUDED: communal hostility, ejection.
  - و-ك-ز (wakaza): fist-blow causing serious injury. Used in 28:15
    (Musa's fatal punch).
    EXCLUDED: injurious targeted fist-strike.
  - ق-ذ-ف (qadhafa): hurling force across distance. Used in 17:81.
    EXCLUDED: projectile action, gap between agent and target.

Form non-selection:
  - Form II (ضَرَّبَ) was available = intensive/repeated striking.
    Form I was selected = unmarked single-event contact.
  - No cognate accusative (ضَرْبًا), no instrument (بِـ), no body-part
    target, no manner adverb. Maximally bare.
```

---

## Phase 5 — Concept Definition

Synthesize everything into what the word IS and IS NOT.

### Steps

1. Combine: root image + form constraints + syntactic frame + furuq
   exclusions + verse-internal constraints
2. Write "what X IS" — the irreducible concept, grounded in the root image
   and constrained by form and frame
3. Write "what X is NOT" — derived from Phase 4 furuq exclusions, stated as
   semantic boundaries
4. Write a prose concept translation: not a single word, but the full semantic
   envelope rendered in the target language

### Expected output

```
WHAT IT IS:
  Directed contact-impact — an agent causes one thing to meet another.
  Form I: single, unmarked, unintensified.
  Frame: transitive with human direct object = physical striking.
  Root image (إيقاع شيء على شيء) encodes contact, agency, and direction.
  Does not encode severity, instrument, duration, repetition, or purpose.

WHAT IT IS NOT:
  - Not skin-marking punitive lashing (jalada)
  - Not overpowering violent seizure (batasha)
  - Not exemplary deterrent spectacle (nakkala)
  - Not hostile communal expulsion (rajama)
  - Not injurious targeted fist-blow (wakaza)
  - Not projectile force across distance (qadhafa)
  - Not intensive/repeated striking (Form II ضَرَّبَ)
  - Not gentle touching (lamasa) or pushing (dafa'a) either —
    the root carries real contact-impact, not euphemism

PROSE CONCEPT:
  A physical contact-impact of the most unspecified kind — not the
  skin-marking lash of legal punishment, not the crushing grip of
  domination, not the fist-blow that injures, not the stoning that
  expels — but the bare, unmarked act of making directed physical
  contact; carried in the most basic verb form the language offers,
  stripped of any amplifier, instrument, target, or repetition marker;
  authorized only under a named condition, positioned last in a
  graduated sequence, revoked upon compliance, and framed under divine
  surveillance.
```

---

## Phase 5.5 — Domain Activation Mapping

Narrow the root-level concept to context-specific meaning by mapping the
intersection of the root image with the domain concept network.

See `step6-domain-activation/README.md` for the full theory and method.

### Steps

1. Identify the domain from the word's Quranic context (marriage, warfare,
   worship, commerce, etc.)
2. Build the domain concept network from the Quran's own vocabulary for that
   domain — each node attested by a specific verse and root
3. Run the root image against each domain concept: does the physical logic
   of the root intersect with the structural shape of this concept?
4. Activated concepts = what the word means in this context
5. Non-activated concepts = what the word does NOT mean in this context
6. Carry the activated subset to Phase 6 as the translation target

### Expected output

```
Word: نُشُوز (Q 4:34)
Root image: rising / protrusion above a level surface
Domain: marriage

Domain network (from Quranic vocabulary):
  [tranquility/dwelling]  (30:21, س-ك-ن)
  [affection]             (30:21, و-د-د)
  [mercy]                 (30:21, ر-ح-م)
  [solemn covenant]       (4:21, و-ث-ق)
  [mutual covering]       (2:187, ل-ب-س)
  [shared living]         (4:19, ع-ش-ر)
  [partnership symmetry]  (2:187, mutual garment image)
  [structural upholding]  (4:34, ق-و-م)
  [financial provision]   (4:34, أَنفَقُوا)
  [parental obligation]   (2:233)

Activation mapping:
  ✓ [solemn covenant]       — rising above = acting as if covenant doesn't bind
  ✓ [tranquility/dwelling]  — rising disrupts the settled state
  ✓ [mutual covering]       — rising above = breaking the symmetric enclosure
  ✓ [shared living]         — rising above = withdrawing from shared arrangement
  ✓ [partnership symmetry]  — rising = unilateral elevation above shared plane
  ~ [affection]             — weakly activated (withdrawal from affection-space)
  ✗ [financial provision]   — root logic doesn't map to withholding resources
  ✗ [parental obligation]   — root logic doesn't map to parenting neglect

Context-specific meaning (activated subset):
  One spouse acting as if the marriage covenant no longer binds them,
  disrupting the shared tranquility, breaking the mutual covering,
  withdrawing from shared living, and unilaterally elevating above the
  partnership — while still nominally present.

Translation target: THIS cluster, not the bare root image.
```

---

## Phase 6 — Gloss Selection with Gap Analysis

Propose target-language glosses with explicit gap documentation.

### Steps

1. Propose 2-4 target-language glosses ranked by semantic closeness to the
   concept defined in Phase 5
2. For each gloss, perform gap analysis:
   - Does the target word ADD meaning the Arabic doesn't carry?
   - Does the target word LOSE meaning the Arabic does carry?
   - What is the gap type? (narrower, broader, connotation shift, register
     mismatch, repetition import, severity import)
3. Recommend a default render
4. Write a standing gap note for the recommended gloss — one sentence that a
   reader or downstream agent can use to understand what the English word
   doesn't fully capture

### Expected output

```
Gloss 1: "strike" (RECOMMENDED — default render)
  + Captures: single contact-impact event, directed, unspecified instrument
  - Adds: English "strike" carries connotation of decisive/sharp force
    that the Arabic doesn't encode. ض-ر-ب is the generic center of its
    field; "strike" sits slightly toward the forceful end of its English field.
  Gap type: connotation shift (slightly narrower toward force)
  Gap note: "strike" is slightly more marked than the Arabic, which is
    the most generic contact-impact word in the language.

Gloss 2: "hit"
  + Captures: contact-impact, unspecified severity
  - Loses: agent intentionality. English "hit" accommodates accidental
    and inanimate agents (a rock hits a window). Arabic ض-ر-ب encodes
    deliberate agent-initiated action (إيقاع = making something fall upon).
  - Loses: productive breadth. "Hit" doesn't extend to parables or travel,
    collapsing root range into only the physical sense.
  Gap type: broader (admits accidental usage Arabic excludes)

Gloss 3: "beat"
  + Captures: force applied to a person
  - Adds: REPETITION. English "beat" implies sustained/repeated blows.
    This is Form II (ضَرَّبَ) territory; the Quran selected Form I.
  - Adds: BRUTALITY connotation. In English domestic contexts, "beat"
    imports the semantic field of ب-ط-ش (violent overpowering) that the
    Arabic explicitly rejected by not selecting that root.
  Gap type: narrower + connotation shift (imports repetition and brutality
    the Arabic does not carry). WORST of the three options.
```

---

## When to use this methodology

- Any Quranic word where a single target-language gloss is known to be lossy
- Polysemous roots where the activated sense depends on syntactic frame
- Words where the furuq field is rich (multiple near-synonym roots available
  in Quranic Arabic)
- Words where the form choice (I vs II vs IV etc.) carries semantic signal
- Contested or frequently mistranslated words where the concept gap needs
  explicit documentation

## Multilingual Approach

Phases 1–5 produce a **language-neutral Arabic dossier**: root image, branch
structure, Quranic census, frame-to-sense map, furuq exclusions, and verse
constraints. This dossier is identical regardless of target language. Compute
it once.

Phase 6 requires deep knowledge of the target language's semantic field —
register, connotation, frame-sensitivity, and the furuq mirror (which target
words carry which excluded loads). This cannot be done at depth for multiple
languages in one pass.

**Architecture: one dossier, many agents.**

1. Run Phases 1–5 once. Output the Arabic dossier as a self-contained input
   document.
2. For each target language, run a dedicated Phase 6 agent that receives the
   Arabic dossier and works one language at full depth.
3. Each Phase 6 agent must:
   - Map the Arabic furuq field to target-language equivalents
   - Identify which target words carry which excluded semantic loads
   - Test each gloss candidate against the concept envelope
   - Document gaps per candidate

Do NOT batch 50+ languages in a single agent call. An agent doing many
languages will:
- Go shallow: pick dictionary equivalents without testing the full field
- Cross-contaminate: let one language's analysis bleed into another
- Miss register: connotations that matter in domestic/social contexts
  require native-level field knowledge per language
- Skip furuq mirroring: the Arabic-to-target mirror table requires knowing
  which target words carry which excluded loads

## Handling pushback on gloss candidates

When a gloss candidate is challenged, test the objection against the Arabic
source word:

1. Does the objection apply equally to the Arabic source?
   - If yes: the objection identifies a feature the Arabic deliberately
     carries. The target gloss should carry it too. Removing it would
     make the target narrower than the source — a concept distortion.
   - If no: the objection identifies a feature the target word adds
     that the Arabic doesn't carry. The objection is valid.

2. Example: "vurmak (Turkish) can mean shooting/killing"
   - Test: does ض-ر-ب also extend to lethal force?
   - Yes: Q 8:12 (decapitation), Q 47:4 (striking necks).
   - Conclusion: this is a shared feature, not a gap. The objection
     does not disqualify the candidate.

3. Example: "vurmak has no intensity limit"
   - Test: does ض-ر-ب have an intensity limit?
   - No: ranges from Q 38:44 (bundle of grass) to Q 8:12 (decapitation).
   - Conclusion: the unlimited range is the source word's own property.
     A target gloss that artificially limits intensity would distort the
     concept. Contextual narrowing belongs in commentary, not in the gloss.

Principle: **always be loyal to the original Arabic word concept.** If the
source word is broad, the target gloss should be broad. Narrowing that the
Arabic doesn't do should happen in the ayah-level commentary layer, not by
choosing a narrower gloss.

## When NOT to use this methodology

- Function words (particles, pronouns) where root semantics are vestigial
- Proper nouns
- Words with exact one-to-one equivalents in the target language (gap_type=0)

## Dependencies

- `branch_map.sqlite` — root branch structure, dictionary grounding
- `concept_map_layer1.tsv` — neighbors, core images, what_is/what_is_not
- `complete-quran.txt` — full Quran text for usage census
- Lexicon cache databases (Maqayis, Lisan, Lane, Mufradat, etc.)
- Qira'at reference (canonical 10 + shadhdh literature)
