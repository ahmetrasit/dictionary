# Meaning Infrastructure — What, How, Why

Current architecture note: this file explains the dictionary-grounded sense
inventory methodology. For the current end-to-end corpus workflow, including
QAC morphology, V4 lookup, semantic graph, activation, commentary, translation,
and product-data exports, read `_corpus/ARCHITECTURE.md`.

## What we are building

A complete, dictionary-grounded lexical foundation for every word in the
Quran. The goal is not to interpret the Quran — it is to build an honest
inventory of what each word *can* mean, so that contextual analysis can
reveal what is genuinely present in each passage without inventing anything.

The app user taps a word and sees its meaning, its root image, how its
construction shapes the result, what it shares with nearby words, and what
it excludes. Every claim traces to a classical Arabic dictionary entry.

## Why we are doing it this way

### The contamination problem

Modern LLMs have read dictionaries, tafsir, hadith, and contemporary
commentary — all blended in training. When you ask an LLM "what does this
Quranic word mean?", you get a plausible answer that mixes dictionary fact,
exegetical tradition, and model inference. You cannot tell which is which.

For a Quranic text project, this is unacceptable. The dictionary says what
Arabic *allows*; the context shows what the Quran *activates*. These are
different questions and must stay in different layers. If interpretation
leaks into the dictionary layer, the contextual layer has nothing honest to
check against.

### The auditability requirement

Every sense in our inventory traces to a specific dictionary entry:
Maqayis entry #31612, Sihah entry #1462, Mufradat entry #680. If a sense
cannot be traced, it is flagged. If an LLM invents a sense, the pipeline
rejects it. This is not possible with training-data-based generation.

### The completeness requirement

A Quranic passage often reveals its semantic range across multiple ayahs.
In 17:48–51, "be stones or iron" carries senses of hardness, enclosure,
impermeability — but these only become visible through contrast with what
follows (chests, something greater, and piercing through). To recover these
relationships honestly, the lexical layer must have a complete sense
inventory. A 95% inventory misses exactly the rare senses where the
interesting discoveries are.

## How it works

### Semantic units

There are two types of meaning-carrying units:

1. **Bare forms** — a word without a governing collocation. Carries senses
   from its root image and dictionary entries.

2. **Verb/noun + collocation units** — a word plus its argument frame
   (specific preposition, specific object, structural pattern). The
   collocation produces a distinct result. The root image senses are also
   present — they coexist, they don't disappear.

Senses flow **down** (root image → collocation inherits it) but never
**up** (collocation result does not become a bare-form sense). Every unit
reveals all its senses. The project does not pick winners.

**Example**: Root ض ر ب (forceful directed contact).
- Bare `daraba` = strike. That's its only sense.
- `daraba fi l-ard` = travel AND strike. Travel comes from the
  construction; strike is inherited from the root image.
- `daraba mathalan` = set forth AND strike. Same principle.

The root is monosemic. The collocations produce the variety. "Travel" is
not a sense of `daraba` — it is a sense of `daraba fi l-ard`.

### The pipeline

```
Classical dictionaries (Maqayis, Lisan, Ayn, Sihah, Tahdhib, Mufradat)
  ↓ branch extraction + 5-dictionary crosscheck
Branch map DB (1,811 roots, 2,770 branches, 12,536 forms)
  ↓ attachment enrichment final_v3 (reviewed syntax, verb/noun frames, discourse, ellipsis)
Construction-frame review (which frame licenses which result)
  ↓ sense triage (476 roots where dictionaries disagree)
Complete sense inventory per semantic unit
  ↓ contextual pass (per-occurrence activation levels)
  ↓ translation pipeline (per-language rendering)
App-facing data
```

Each layer reads from the one above and adds its own contribution.
No layer may use data from a lower layer as evidence.

### Dictionary authority

The five crosscheck dictionaries span the 8th–11th centuries:

| Dictionary | Period | Role |
|---|---|---|
| Ayn (al-Khalil) | 8th c. | Earliest systematic dictionary |
| Jamhara (Ibn Durayd) | early 10th c. | Independent early witness |
| Maqayis (Ibn Faris) | late 10th c. | Branch structure authority |
| Sihah (al-Jawhari) | late 10th c. | Concise, branch-rich |
| Tahdhib (al-Azhari) | late 10th c. | Critical verifier |
| Mufradat (al-Raghib) | 11th c. | Quran-vocabulary focused |

Maqayis provides the branch structure (how many distinct origins a root
has). The other dictionaries crosscheck it. When Mufradat is the sole
attestor for a sense, it gets a `quran_scoped_only` flag — it may be a
Quranic extension rather than base Arabic.

### Methodological positioning

We follow Maqayis's branch structure as the starting hypothesis and test
it with crosscheck evidence and Quranic construction frames.

Where al-Raghib (Mufradat) lists extended senses as stored sub-entries of
a root, we may reassign them to specific construction units. This is a
difference in **organization**, not content. Both approaches catalogue the
same senses from the same classical sources. Ours adds construction-level
granularity that tells the contextual pass exactly which unit carries which
sense.

This is a Maqayis-first methodology. His unificationist approach means we
start from monosemy as the default and require evidence for polysemy. That
is a theoretical commitment — the practical justification is parsimony.

### Arabic-first rule

Arabic senses are the authority. English glosses are scanning labels. Agents
write `sense_ar` first, `gloss_en` second. English uses transparent phrasing
that preserves the Arabic concept: `travel (beat a path through)` not just
`travel`. A Sonnet post-check assigns `gap_type` (0=exact, 1=narrower,
2=broader) to every Arabic-English pair.

### What the LLM does vs. what the data does

The LLM (agent) reads dictionary evidence from packets and makes structured
judgments: "this sense belongs to this construction unit, verdict A, frame =
fi + place." The agent does NOT generate senses from training memory. Every
claim must cite packet evidence. If the agent cannot cite evidence, it must
say so.

The data infrastructure ensures:
- **Completeness**: every root checked against 5 dictionaries mechanically
- **Consistency**: same sense inventory regardless of which agent runs
- **Auditability**: every sense → dictionary entry ID → source text excerpt
- **Contamination prevention**: agents see dictionary text only, never tafsir

The LLM is the reader; the dictionaries are the authority.

### Qnet graph layer: roots as nodes, branches as evidence

The semantic graph may use roots as the main production nodes, but branch-level
data must remain underneath every root-level link. A root can contain multiple
branch images, and a network connection is only interpretable if we know which
branch made the connection.

For Qnet keyword/theme networks, the raw branch-keyword incidence table is the
evidence layer:

```text
root_id
branch_id
keyword_type    # core or bridge
keyword/theme
replicate_votes
```

The frozen full raw incidence layer is the source of truth for Qnet v2 keyword
evidence:

```text
_corpus/activation/Qnet/v2/network/incidence_full/
  raw_keyword_incidence.sqlite
  branch_keywords.tsv
  keyword_inventory.tsv
```

It preserves both `core` and `bridge` keyword assignments. The frozen bridge
theme taxonomy and raw bridge keyword -> theme mapping are:

```text
_corpus/activation/Qnet/v2/network/themes/bridge_theme_taxonomy.v1.tsv
_corpus/activation/Qnet/v2/network/themes/bridge_keyword_theme.v1.tsv
```

The standalone production bridge-theme substrate is:

```text
_corpus/activation/Qnet/v2/network/bridge_theme_full/
  bridge_theme_staging.sqlite
  theme_keyword_nodes.tsv
  theme_keyword_roots.tsv
  branch_theme_inventory.tsv
  root_theme_inventory.tsv
  root_index                  # SQLite table
  quran_root_occurrences      # SQLite table
  quran_root_key_ambiguity    # SQLite table
```

This layer is bridge-only. Core keywords remain separate in the raw incidence
DB. Bridge themes are controlled through the reviewed two-level taxonomy, while
raw keyword evidence remains queryable underneath every theme assignment. The
production SQLite embeds the taxonomy, mapping, root/branch evidence, and
root-level QAC occurrence tables, so network builders can filter by surah/ayah
without reading the original replicate files.

Root-level graph views are useful for scoring, clustering, and navigation.
Branch-level underlay is required for branch-specific usage:

- which branches of a root are active in a theme or passage;
- which branches are silent across the whole Quran corpus;
- which branches are silent at the surah level but active elsewhere;
- which dense themes split into smaller keyword-driven subnetworks;
- which roots or branches connect otherwise separate subnetworks.

Silence is data, not absence of data. A totally silent branch, or a branch that
is silent in one surah while active elsewhere, constrains interpretation. These
silent/active contrasts help identify branch relevance, polysemic roots, and
key roots that deserve closer review.

The same root may also have different branches activated in different contexts.
Root-level networks are practical, but they can hide this profile: one passage
may activate one branch image while another passage activates a different branch
of the same root. Branch activation profiles must therefore be checked alongside
root-level links. For example, "stone" in 17:50 is contextually meaningful
because the passage may activate a specific branch profile rather than the root
as an undifferentiated node.

The root-level QAC occurrence layer in `bridge_theme_full` is deliberately not a
branch/sense activation layer. It tells us which roots occur in a surah or ayah
range, and it flags duplicate normalized root-key ambiguity explicitly. It does
not decide which branch of a root the Quranic occurrence activates. That
branch-specific activation profile remains a later contextual/sense assignment
layer.

## Road to complete sense inventory

The pipeline has 11 steps. The sense **inventory** closes at step 9. Steps
10-11 consume the inventory but do not add senses. A cold agent should read
the current step and resume from there.

| Step | What | Scope | Status |
|---|---|---|---|
| 1-3 | Sense triage P1+P2+P3 | 476 roots | DONE — 714 verdicts in DB |
| 4 | Gap_type + DB import | all 476 | DONE — Sonnet (P1) + GPT-5.5 (P2-P3) |
| 5 | Verdict D corrections | 68 findings | PARTIAL — 3 applied, 65 queued |
| 6 | Sense compilation | all 1,811 | DONE — 3,918 sense units compiled |
| 6b | Populate collocation units table | 6,582 verb frames | IN PROGRESS |
| 7 | Clean roots bridge | 538 roots | Not started — mostly scripted + Sonnet spot-check |
| 8 | Multi-branch root assignment | 693 roots | Not started — Opus, ~25-30 batches |
| 9 | Noun-only sense assignment | ~630 roots | Not started — mostly scripted |
| **= Complete sense inventory** | **All 1,811 roots** | | |
| 10 | Contextual pass | all Quranic words | Later — reads inventory only |
| 11 | Translation pipeline | per target language | Later |

### Architecture: two-table sense model

- **`quranic_collocation_units`** — all verb collocations from the valence
  pilot (6,582 entries). These are the structural units. Each is pre-classified:
  `mechanical` (no agent needed — branch image stamped by script),
  `light` (Sonnet spot-check), or `full` (agent review with dictionary
  evidence). The `sense_status` field tracks pending/reviewed/mechanical.

- **`branch_frame_senses`** — reviewed senses layer. Agent-verified sense
  assignments linked to collocation units. Grows as steps 7-8 complete.

- **Noun collocations** are handled contextually in step 10, not as
  pre-built sense units. The noun collocation harvest (30K occurrences,
  95.7% coverage) provides structural evidence for the contextual agent.
  Exception: dictionary-attested noun idioms from triage A/B verdicts go
  into `branch_frame_senses`.

### What each step produces

- **Steps 1-3 (triage):** A/B/C/D verdicts per crosscheck finding. Stored
  in `sense_triage_results`. 714 verdicts across 324 roots.
- **Step 4 (gap_type + import):** Arabic→English gloss fidelity assessed.
  576 exact, 42 narrower, 96 broader.
- **Step 5 (corrections):** 68 verdict D findings → governed branch-count
  corrections. 3 immediate fixes applied (data artifacts + root
  misattribution). 65 queued in `_corpus/dictionary-refinement/`.
- **Step 6 (compilation):** First complete sense inventory compiled:
  3,918 units in `output/sense_inventory/sense_units.tsv`.
- **Step 6b (collocation units):** Populate `quranic_collocation_units`
  with all 6,582 verb frames. Pre-classify review priority. Link existing
  reviewed senses. `mechanical` entries get branch image stamped by script
  with `sense_status=mechanical` evidence trail.
- **Step 7 (clean roots):** 538 single-branch roots. Script pre-assigns
  mechanical frames; Sonnet reviews `full`-priority frames (~15 batches).
  Dictionary attestation checked naturally during review.
- **Step 8 (multi-branch):** 693 roots with 2+ branches. Script pre-filters
  unambiguous form→branch assignments; Opus reviews ambiguous remainder
  (~25-30 batches). The hardest step.
- **Step 9 (noun-only):** ~630 roots with no verb frames. Single-branch
  noun roots → fully scripted. Multi-branch → Sonnet (~13 batches).
- **Step 10 (contextual):** Per-occurrence activation levels using the
  complete inventory. Noun collocation harvest provides structural context.
  Dictionary attestation of noun collocations checked here (option 3:
  emerges naturally during contextual review).
- **Step 11 (translation):** Per-language rendering with gap_type per
  target language.

### Model assignment

| Steps | Model | Why |
|---|---|---|
| 1-3, 8 | Opus | Arabic lexicographic judgment |
| 4, 7, 9 | Sonnet | Constrained/mechanical tasks |
| 5-6 | Script + Sonnet | Mostly mechanical with spot-checks |
| 10-11 | TBD | Depends on contextual pass design |

## Current state

Sense triage is in progress. P1 (99 roots) and P2 (198 roots) are complete.
P3 (179 roots) is running. After P3, steps 4-6 close the triage phase.

Detailed status and resume guides:

- `_corpus/README.md` — corpus workspace overview and methodology pointers
- `_corpus/semantic_maps/grounded_senses/PROGRESS.md` — branch map DB,
  sense triage, construction frames, current resume point
- `_corpus/semantic_maps/grounded_senses/SENSE_TRIAGE_PLAN.md` — semantic
  unit model, transparency categories, triage methodology
- `_corpus/semantic_maps/grounded_senses/noun-collocations/README.md` —
  noun structural patterns (95.7% coverage of 30,558 occurrences)
- `_corpus/dictionary-refinement/` — Maqayis errors, scholarly review,
  verdict D findings for correction workflow
- `_corpus/attachment-enrichment/progress.md` — syntax/valence pass status
