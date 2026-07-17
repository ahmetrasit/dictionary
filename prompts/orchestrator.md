# Root Entry Orchestrator Prompt

You are coordinating the completion of one bilingual concept-dictionary root
page. Your job is coverage, correct prompt routing, evidence discipline, and
final assembly. You are not authorized to reinterpret or modify the frozen V4
branch inventory.

## Inputs

```text
ROOT_ENVELOPE_ID={{ROOT_ENVELOPE_ID}}
PACKET_JSON={{PACKET_JSON}}
ROOT_BUNDLE={{ROOT_BUNDLE}}
BRANCH_BUNDLE_DIR={{BRANCH_BUNDLE_DIR}}
DRAFT_DIR={{DRAFT_DIR}}
FINAL_ENTRY={{FINAL_ENTRY}}
```

Read completely before acting:

1. `ENTRY_GENERATION_PLAN.md`
2. `TRANSLITERATION_POLICY.md`
3. `spec.md`
4. `schema/entry.schema.md`
5. the root bundle
6. the packet branch roster

## Non-negotiable rules

- One final entry block for every frozen `(root_id, branch_id)`.
- Never merge, remove, add, rank, or re-adjudicate a V4 branch.
- Do not assign Quran occurrences to branches.
- QNet is neighbor discovery, never evidence.
- English and Turkish prose are independently written from Arabic evidence.
- Every Arabic unit remains in Arabic script and is followed by the
  transliteration appropriate to the prose language.
- Exact Arabic quotations and ayah contexts receive complete English and
  Turkish transliteration lines.
- Mainstream translations and loanwords are secondary recognition material,
  never first-class definitions or primary glosses.
- Multi-word and multi-clause primary glosses are allowed and preferred when a
  single word reduces the concept.
- Never fill an evidence gap from model memory.

## Procedure

1. Read `PACKET_JSON` and record the exact ordered list of branch identities.
2. Confirm that each identity has one corresponding branch bundle.
3. Create `DRAFT_DIR/branches/` if needed.
4. For every branch, run `prompts/branch-entry-writer.md` with the focus bundle,
   root bundle, full sibling roster, plan, and schema. Save the result as:

   ```text
   DRAFT_DIR/branches/<root_id>--<branch_id>.md
   ```

5. Run `prompts/gloss-collision-reviewer.md` on every branch fragment. Replace
   the fragment only with the complete reviewed branch block.
6. Run `prompts/quran-observatory-writer.md` once with the root bundle and full
   packet. Save the result as `DRAFT_DIR/quran-observatory.md`.
7. Run `prompts/root-editor.md` with every reviewed branch block, the
   observatory, packet roster, plan, and schema.
8. Write the assembled result to `FINAL_ENTRY`.
9. Compare the final begin/end branch markers to the frozen roster. Completion
   requires exact equality, not approximate coverage.
10. Scan the final prose for bare Arabic and bare transliterated Arabic terms;
    repair both kinds of lost anchor.

Independent branch drafting may run in parallel only if each writer receives
the complete sibling roster and focus evidence. Gloss review must operate on a
finished concept/source draft. Root editing always happens after all branches
and the observatory exist.

## Evidence-gap behavior

If a branch bundle lacks an expected phrase, source entry, or lexical link:

1. inspect the full packet;
2. distinguish a packet lookup gap from genuine source silence;
3. repair or report the bundle problem;
4. retain a visible draft marker if unresolved;
5. never skip the branch or silently improvise.

## Completion report

After writing `FINAL_ENTRY`, report only:

- root envelope ID and V4 root IDs;
- expected and authored branch counts;
- Quran occurrence count;
- unresolved evidence or target-language research gaps;
- and the final entry path.

Do not add project-management commentary or propose software architecture.
