# Branch writer

Write one target-language encyclopedia branch from the task's minimal immutable
evidence projection. Return only the JSON object required by the response schema.

Rules:

- Keep `root_id`, `branch_id`, and `language` exactly as the task gives them.
- Follow the transliteration policy named in the task's entry contract.
- Treat `branch.branch_image_ar`, `what_is_ar`, and `source_phrase_ar` as frozen.
- The coordinator owns all source references, dictionary rosters, lexical data,
  morphology, attachments, and Quran occurrences. Do not recreate or cite them.
- Write `source_summary` only from the supplied Arabic source phrase.
- Select 1-5 target-language glosses and 1-3 excluded or confusable alternatives.
  `semantic_definition` is the broad meaning anchor; selected glosses must be
  usable target-language wording. Mark each as general, contextual,
  explanatory, technical, or a proper name, state when it applies, and explain
  preservation, loss, addition, and collisions. Do not exclude a natural gloss
  merely because it is valid only in some contexts.
- A common target-language loanword cannot be the first gloss. If selected, it may
  only be rank 2 and needs its target-language drift or collision profile.
- Every published Arabic-neighbor distinction must use one supplied minimal
  neighbor record. Include its exact `neighbor_root_id` and `neighbor_branch_id`.
- Assess the complete packaged neighbor roster and include every materially useful
  contrast, up to five. When only one is useful, return `single_sufficient` with a
  concrete reason; do not stop merely because the schema minimum is one.
- Record only source-phrase-grounded register, constraints, and technical usage in
  `usage_notes`. Mark disputed, rare, or technical evidence only when explicit in
  that phrase. Do not add morphology, syntax, valency, evidence handles, a
  Quranic/non-Quranic classification, or occurrence assignments.
