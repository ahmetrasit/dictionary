# Legacy branch writer (not used by current production orchestration)

Current production uses `root-writer.md`. This file remains only for historical
fragment compatibility and must not be selected by the entry orchestrator.

Write one target-language semantic branch from the task's minimal immutable
evidence. Return only the JSON object required by the response schema. All prose
and glosses must be in the requested target language.

The response has three main jobs:

1. define the focus branch without collapsing it into the whole root;
2. rank natural target-language glosses and state their translation risks;
3. distinguish the branch from the genuinely useful Arabic neighbors.

## Decision procedure

Work through these decisions silently before producing JSON.

### 1. Establish the branch boundary

- Treat `branch_image_ar`, `what_is_ar`, and `source_phrase_ar` as frozen evidence.
- Use `branch_image_ar` as the compact semantic image, `what_is_ar` as its stated
  extent, and `source_phrase_ar` as the only basis for `source_summary`, usage
  notes, and evidence qualifiers.
- Do not turn an etymological origin into the definition when the focus is a
  conventional specialized branch. Do not import meanings from sibling branches.
- `summary` is a concise reader-facing explanation. `semantic_definition` is one
  self-contained dictionary-definition sentence that captures the whole focus
  branch and no neighboring branch.
- `image_transliteration` transliterates the supplied Arabic branch image; it does
  not translate or paraphrase it. Follow the bound transliteration policy.

### 2. Choose target-language glosses

- Rank 1 is the most natural target-language expression covering the largest
  part of this branch in its actual register. Prefer ordinary target-language
  wording for a general branch; when the branch itself is specialized, an
  established specialist term may be rank 1 if it is genuinely the normal term.
- Add another selected gloss only when it serves a distinct real context. Return
  1-5 useful glosses, with consecutive ranks and no synonym padding.
- A contextually valid natural translation remains selected; describe its
  narrowing or added implication in its error profile. Exclude only a tempting
  wording that is wrong, displaced to another branch, or materially misleading.
- A common target-language loanword may appear only at rank 2. An established
  specialist loanword follows the specialist-term rule above. Classify the word
  by its real target-language use, not by the rank you want to give it, and state
  its actual drift or collision; never rank it first merely because it resembles
  the Arabic form.
- Judge every error profile against the full focus-branch boundary:
  `preserves` says what survives, `loses` what becomes unavailable, `adds` what
  the target expression implies beyond the branch, and `collision` what other
  target-language sense or branch a reader may confuse it with. Keep each note
  concrete and concise; do not use empty labels such as "none" as prose.

### 3. Select Arabic-neighbor distinctions

- The supplied roster is recall-oriented and may contain remote thematic or
  keyword neighbors. Assess all records, but publish only meanings whose boundary
  is genuinely useful for distinguishing the focus branch. A discovery relation
  by itself is not a semantic distinction.
- Use only supplied neighbor records and copy their `root_id` and `branch_id`
  exactly. Never invent an Arabic form, root, branch, or source claim.
- For each selected neighbor, make `shared_zone` the real overlap and make
  `distinction` the shortest diagnostic difference a reader could use to choose
  between them. Do not merely restate the two descriptions.
- Select 1-5 nonredundant distinctions. Put the likeliest reader confusion first;
  this becomes the compact user dictionary's `key_distinction`. If exactly one is
  materially useful, use `single_sufficient` and explain why the remaining roster
  is remote or redundant. Otherwise use `complete` and summarize the assessed
  roster without pretending every nominated candidate was a near synonym.

## Evidence and ownership limits

- Keep `root_id`, `branch_id`, and `language` exactly as supplied.
- The coordinator owns source references, dictionary rosters, lexical data,
  morphology, attachments, Quran occurrences, and Arabic fields. Do not recreate
  or cite them.
- Write `source_summary` as a faithful target-language synthesis of
  `source_phrase_ar` only. Do not attribute claims to sources you cannot see.
- Return empty `usage_notes` or `evidence_qualifiers` when the source phrase does
  not explicitly support register, constraint, technical, disputed, or rare
  claims. Do not infer those labels from general knowledge.
- Do not add morphology, syntax, valency, evidence handles, Quranic/non-Quranic
  classification, occurrence assignments, or commentary outside the JSON.

Before returning, confirm that rank 1 is usable in running target-language text,
the definition is exactly one sentence, every risk note concerns that gloss, and
the first neighbor row is the strongest reader-facing contrast.
