# Turkish Translation Spec

**Version:** 2.0  
**Date:** 2026-06-06  
**Parent:** `_translations/translation-spec.md`

## Governing Policies

- `_corpus/docs/03-loanword-policy.md` — Arabic-origin religious terms should not be primary glosses when they obscure the explorable meaning range
- `_corpus/docs/05-gloss-menu-policy.md` — 2-3 genuinely distinct options per lexeme; up to 5 when each is user-useful
- `_corpus/docs/08-language-agent-contract.md` — required decision flow, meaning-honest defaults, per-language flags, gap type definitions

## Turkish-Specific Principles

### 1. Two-Layer Comprehension

- **`default_render`** — comprehensive idea at a glance. Self-sufficient. Multi-word is correct when single-word would mislead.
- **`render_options` (gloss menu)** — complete picture on exploration. Every meaning facet visible. After Phase 3: annotated alternatives explain concept mismatches.

### 2. Gap Detection

**Narrower / subset (gap_type = 1):**
Turkish word (often a loanword) covers LESS than the Arabic concept.

| Arabic | Common TR | Problem | Concept-faithful TR |
|---|---|---|---|
| اهدنا (ihdinā) | ilet | Drops progressive nurturing | dimdik ve dosdoğru yola ulaştırıp ilerlet |
| عبد (ʿabd) | ibadet et | Only ritual worship | kulluk et |
| صلاة (ṣalāh) | namaz | Only the ritual | bağ kur |

**Broader / superset (gap_type = 2):**
Turkish word covers MORE than the Arabic concept.

| Arabic | Common TR | Problem | Concept-faithful TR |
|---|---|---|---|
| اقرأ (iqra') | oku | Includes silent reading | derleyip duyur |
| كتاب (kitāb) | kitap | Implies bound book | yazılıp belirlenmiş (kayıt) |

### 3. Loanword Handling

Arabic loanwords in Turkish are common but dangerous — they *feel* like translations while hiding meaning shifts. The Phase 1 agent must:

1. Recall the common Turkish translation (Diyanet, Elmalılı, general usage)
2. Compare the Arabic original's full meaning footprint with the Turkish word's actual usage
3. If they differ → the common word is NOT `default_render`
4. Set gap_type = 1 (narrower) or 2 (broader) accordingly

**Exception:** When a loanword preserves the full Arabic meaning in Turkish usage (e.g., "Allah"), it can be `default_render` with gap_type = 0.

### 4. Function Words

Turkish function words usually have direct equivalents. Set gap_type = 3 for these unless the particle carries unusual semantic weight in context.

## Three-Phase Workflow

### Phase 1 — Gloss + Flags (Parallel)

Agent reads universal input bundle (Arabic + WORD rows + grammar hint).
Agent produces 8-column TSV:

```
ref	default_render	render_options	gap_type	has_polysemy	has_conceptual_gap	tr_transliteration	concept_basis
```

No annotations. No lexeme_keys. No commentary. Pure linguistic decisions + transliteration + diagnostic trace.

Rules:
- Translation path: Arabic → Turkish only
- Every content word: recall common TR translation, compare footprints, set gap_type
- Multi-word renderings when single word fails
- Vary phrasing — no formulaic patterns
- When uncertain about gap_type: pick the more likely type, never default to 0 to avoid work
- No tab characters in any field
- No square brackets in render_options (reserved for Phase 3 annotations)

### Pass 2 — Consolidation (Script)

Deterministic script:
1. Collect all Phase 1 output
2. Group by root + morph class
3. Construct lexeme_keys using corpus convention
4. Detect conflicts → flag for human review
5. Build canonical lexeme inventory

### Phase 3 — Annotation (Agent)

For every lexeme where gap_type = 1 or 2:
- Write bracket annotations on render_options (~10-15 words, Turkish)
- Write concept_commentary (~30-50 words, Turkish teaching moment)
- Write flag_note per word instance

Agent sees ALL instances of a flagged lexeme at once.

### Validation (Script)

After each phase:
- All input words present in output
- gap_type and has_conceptual_gap consistent (1 or 2 → true; 0 or 3 → false)
- No tabs in fields
- No brackets in Phase 1 render_options
- Row count matches

## Phase 1 Output Schema

| Column | Description |
|---|---|
| ref | surah:ayah:word (copied from input) |
| default_render | Concept-faithful Turkish rendering |
| render_options | Semicolon-separated alternatives (no brackets in Phase 1) |
| gap_type | 0 (exact), 1 (narrower/subset), 2 (broader/superset), 3 (function word) |
| has_polysemy | true/false |
| has_conceptual_gap | true/false (must match gap_type: 1 or 2 → true) |
| tr_transliteration | Arabic pronunciation in Turkish orthographic conventions (see `tr-transliteration-guide.md`) |
| concept_basis | Diagnostic note (4-22 words): `arabic_force=...; tr_gap=...` — reasoning trail for Phase 3 |

## Quality Bar

This is an A+ app. Turkish renderings are the foundation of the Turkish user experience. Every word the user sees must honestly represent the Arabic concept — never a convenient approximation.
