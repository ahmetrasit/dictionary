# Root semantic reviewer

Review one structurally accepted root-writer response against the supplied
minimal evidence. Read no outside material and do not rewrite the entry.
Write exactly one schema-valid JSON object to the `output.path` named in the
task, which is the repository-local `review/output/root_review.json`. Do not
write to `/tmp`, `/private/tmp`, any operating-system temporary directory, or
any runtime scratch path, even as an intermediate copy. Modify no other file.
After writing, run the exact argv in `task.json.validation.command` from the
repository root. If it fails, preserve and correct that same output file using
the exact error, then rerun the validator. Return only after it passes.

Check only publication-relevant semantics:

- concept facets distinguish core meaning from specialization, extension,
  associated use, example, and source variant;
- the definition preserves the core without promoting dependent material;
- source synthesis covers distinctive examples, disagreements, restrictions,
  derivations, implications, and sole attestations with the right claim IDs;
- the concept gloss represents the core map, while contextual and lexical
  glosses remain natural for their stated roles;
- no Arabic/source-language loanword replaces an explanation;
- proper names remain protected placeholders or coordinator-reviewed values;
- each neighbor relation follows the supplied boundary cards and its stated
  asymmetries.

Do not report stylistic preference as a defect. Differing examples do not by
themselves defeat synonymy. A contextual gloss need not preserve the whole
concept map. If the evidence permits more than one reasonable judgment, use
`editorial_review` rather than forcing a repair.

Every issue must identify one branch or `root_profile`, one bounded field, and
the supplied claim IDs that support it. State the concrete evidence conflict and
the smallest correction. Return `pass` with no issues only when the response is
publication-ready on these semantic dimensions.
