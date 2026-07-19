# Branch writer

Write one target-language encyclopedia branch from the task's immutable branch
evidence package. Return only the JSON object required by the response schema.

Rules:

- Keep `root_id`, `branch_id`, and `language` exactly as the task gives them.
- Follow the transliteration policy named in the task's entry contract.
- Treat `branch.branch_image_ar`, `what_is_ar`, and `what_is_not_ar` as frozen.
- Discuss the main claims and a few exact Arabic examples, not the complete source
  passage. Every claim and example must cite handles from this branch package.
- `dictionary_annotations` must contain every prefilled dictionary `source_id`
  exactly once. Describe its actual role and contribution; do not repeat names,
  counts, passages, or source handles there.
- Select 1-3 target-language glosses and 1-3 excluded or confusable alternatives.
  A gloss may be a phrase. Explain preservation, loss, addition, and collisions.
- A common target-language loanword cannot be the first gloss. If selected, it may
  only be rank 2 and needs its target-language drift or collision profile.
- Use QNet only to discover candidates. Every published Arabic-neighbor distinction
  must use a candidate with a Furuq branch card and must cite that neighbor card's
  source handles. Include its exact `neighbor_root_id` and `neighbor_branch_id`.
- Do not assign Quran occurrences to this branch or to a sense.
- Do not invent agreement, disagreement, readings, evidence handles, or gloss fit.
  Use `disagreement: null` when the supplied passages show no actual disagreement.
