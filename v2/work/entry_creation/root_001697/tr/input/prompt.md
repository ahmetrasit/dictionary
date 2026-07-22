# Root writer

Write one target-language concept map for every focus branch in the bound root
evidence. Write only the JSON object required by the response schema to the
`output.path` named in the task; do not modify any other file.
`output.path` is the repository-local sibling
`output/{root_envelope_id}_entry.json`. Write there directly. The coordinator
will inject Arabic fields, dictionary attribution, source agreement/dispute
metadata, occurrences, and attachments into that same accepted artifact. Do
not write to `/tmp`, `/private/tmp`, any operating-system
temporary directory, or any runtime scratch path, even as an intermediate copy.
After writing, run the exact argv in `task.json.validation.command` from the
repository root. If it fails, preserve and correct that same output file using
the exact error, then rerun the validator. Return only after it passes.

Use clear, ordinary task-language wording. Do not use Arabic script,
transliterated Arabic, or an Arabic/source-language loanword as a shortcut for
explaining a concept. Source titles may remain names. In the initial entry
response, never invent, normalize, or transliterate a person or place name. Each
source claim carries the coordinator-owned `rendering_policy`; copy it exactly
into `rendering_kind`. For a `proper_name` claim, leave `target_gloss` null and
refer to it in authored prose only with its exact token `{{lexical_unit_id}}`,
for example `{{lu_014}}`. The coordinator replaces that token after the
generated proper-name queue is completed.
Placeholder tokens are allowed only for lexical units declared `proper_name`.
Never write the token of an ordinary derivation, collocation, or example merely
because its expression contains a protected name. Explain the ordinary unit in
plain language. It may reference the underlying coordinator-protected name token
when identity is required, including inside an ordinary target gloss; it must
never use its own ordinary lexical-unit token as a surrogate name.

## 1. Build the concept map

- Use `branch_image_ar` as the compact semantic image and `what_is_ar` as the
  branch boundary. Use the compact `source_claims` as the complete lexical and
  source-detail roster; do not import meanings from siblings or outside files.
- Create facets before writing the definition. Mark each facet as `core`,
  `specialization`, `extension`, `associated_use`, `example`, or
  `source_variant`, and bind it to the supporting claim IDs.
- Put the semantic core first. A specialized realization, scope extension,
  associated construction or event, example, and source disagreement must stay
  dependent on that core. Do not coordinate an associated event with the core as
  though it defines the referent.
- The definition may use one or two sentences. Preserve every constitutive
  operation, relation, stage, participant shift, and result, but do not promote
  examples or merely associated uses into constitutive meaning.
- Preserve internal conditions: an offered indication is not its acceptance or
  result, and what one participant can do need not equal a causative or divine
  use supported by another construction.

## 2. Synthesize source claims

- `source_synthesis` is the only source-discussion output. Put genuinely shared
  material in `common_summary`. Put an example, disagreement, restriction,
  extension, implication, derivation, or sole attestation in a source-detail row
  with its exact claim IDs.
- Do not repeat dictionary names or codes in prose. The coordinator converts
  claim IDs into the compact `sources` roster and dictionary-keyed
  `source_note`; exact references remain internal.
- When sources differ, make each source-detail summary stand on its own as
  concise reader-facing prose. The final entry groups that prose under the
  supporting dictionary code and omits the internal detail category.
- Account for every supplied claim exactly once across `common_claim_ids`,
  source-detail `claim_ids`, `supporting_claim_ids`, and `duplicate_claims`.
  `supporting` means relevant evidence that need not be stated separately;
  `duplicate` is allowed only when the claim adds no content beyond the named
  claim. Never omit a distinctive example, dispute, restriction, derivation, or
  implication merely for brevity.

## 3. Write distinct kinds of gloss

- `concept_gloss` is the shortest natural wording that best represents the
  complete core map. Completeness outranks brevity, and a multiword phrase is
  preferable to a familiar word that deletes a core operation. It need not claim
  exact fit when no natural target-language wording carries the whole map.
- `contextual_glosses` are natural running-text translations for distinct real
  contexts. They are not competitors in one global ranking. State the facets and
  applicability of each.
- `lexical_glosses` cover the exact lexical-unit roster separately. For an
  ordinary unit, provide a plain target-language rendering of its attested sense.
  For a proper name, use the protected-name procedure above. Do not force a
  name-derived form into the branch-level concept gloss.
- Every error profile states what survives. Use null for a loss, addition, or
  collision that does not exist. `fit: none` permits no constitutive loss or
  addition; `narrowing` requires a real loss; `broadening` requires a real
  addition. Exclude only wording that is displaced or materially misleading.

## 4. Verify neighbor relations

Assess every neighbor reference, but publish only 0-5 useful, nonredundant
contrasts. Put the likeliest reader confusion first. Copy `neighbor_ref` exactly.

- `synonym`: the compared branch cores and boundaries permit substitution;
  differing examples alone do not defeat synonymy. Use `boundary_match: exact`
  with both asymmetry fields null.
- `near_synonym`: the cores substantially overlap but at least one scope,
  condition, participant, or implication differs. Use `partial` and state the
  real asymmetry.
- `near_neighbor`: meaningful overlap exists without ordinary substitution.
- `same_field`: the branches share a domain or participants but have different
  cores.
- `thematic`: they participate in the same scenario with little semantic
  overlap.
- `antonym` and `polarity_pair` require a shared semantic axis.

`boundary_match: exact` is valid only with `relation_type: synonym` and both
asymmetry fields null. A boundary-level extra scope, participant, condition, or
specialized domain requires `near_synonym`/`partial`; a merely dependent example
or derivation does not by itself defeat synonymy.

QNet, Neo, and other networks nominate candidates only. Verify every published
relation from the supplied focus and neighbor cards. If none sharpens the
boundary, return no distinctions and explain why.

Write the root profile from the complete branch set in one or two sentences. Do
not make occurrence or collocation claims.

## 5. Make surgical corrections

When your validator reports an error, preserve the complete response and change
only the smallest field set that resolves that exact error. Do not regenerate a
valid branch, reorder unaffected material, rephrase unrelated prose, or turn a
mechanical correction into a new lexical judgment. Examples include replacing
an illegal ordinary-unit placeholder with plain wording, completing one missing
claim disposition, correcting a facet reference, or aligning one relation label
with its boundary fields. Rerun the validator after every correction.

When `task.json` carries a bounded repair scope from semantic review, treat the
previous response as protected state. Edit only the permitted branch indexes or
root profile and only the fields identified by the supplied issue. If the exact
error cannot be fixed without changing protected material or making an
evidence-ambiguous judgment, stop and report that conflict instead of widening
the repair yourself.

## 6. Complete surface-form queues

After the accepted entry response passes semantic review, finalization may
generate `inputs/transliteration_review.json` and/or `inputs/name_review.json`.
If the orchestrator resumes you with those exact queue paths, this is still your
writer task. Read and write only the named queue files. Do not inspect unrelated
files and do not modify `output/{root_envelope_id}_entry.json`,
`fragments/`, `review/`, evidence, or task files.

For every pending row in the transliteration queue, choose the natural
target-language display form for the listed Arabic anchor, using
`suggested_value` when it is suitable and correcting it when it is not. For
every pending row in the name queue, choose the natural target-language surface
form for the listed protected person, place, or object name. Set
`status` to `approved` and put the chosen form in `value`. Preserve every
`key`, `arabic`, and, when present, `suggested_value` field exactly. Values
must be target-language text, must contain no Arabic script, and must not be
empty. Use one consistent spelling for repeated protected names unless the
Arabic anchor genuinely identifies a different form.

The coordinator owns IDs other than local facet IDs, language, ranks, branch
count, Arabic text, source names and references, morphology, attachments,
occurrences, provenance, and the generated queue shape. You own only the
target-language values in generated surface-form queues.

Before writing output, confirm exact branch order; sequential facet IDs within
each branch; exact claim and lexical-unit coverage; deliberate concept versus
contextual gloss separation; proper-name placeholders only in the initial entry
response; and relation labels consistent with boundary/asymmetry fields.
