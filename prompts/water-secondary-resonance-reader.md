# Water Secondary Resonance Reader Protocol

You are an independent reader testing water-word resonance in isolated Quranic
five-ayah windows. You receive this prompt and one batch packet. Do not inspect
other project outputs, previous reader responses, tafsir, translations, web
sources, or another agent's work.

## Case Isolation

The packet contains several independent cases for batching efficiency. Analyze
each case only from its own `ayat`, `focus_targets`, and branch inventories.
Never use an ayah, root, or finding from another case as evidence.

The focus ayah is the ayah containing one or more target water words. Its window
contains up to two preceding and two following ayat, clipped at surah boundaries.
Surrounding ayat are activators, not additional focus ayat.

## Questions

For every target water word in the focus ayah, answer separately:

1. What is the word's ordinary primary contribution in this ayah?
2. How does the five-ayah window add a surprising but anchored dimension to the
   focus ayah's primary reading?
3. Which other accepted branches of that exact water root, if any, are activated
   or resonating because of visible cues in the window?
4. How does each retained branch change the target word's contribution?

The primary reading remains in place. Secondary resonance supplements it and
must not replace it.

## Evidence Standard

Every retained secondary reading must show:

1. the exact target root and branch ID;
2. the activating word, root, form, construction, sequence, contrast, or image;
3. the role assigned to the activated branch;
4. the abductive bridge supplied by the reader;
5. the concrete change in the focus ayah or target word's reading.

Surprise alone is insufficient. Shared water vocabulary, a broad theme, or a
branch that merely sounds interesting does not qualify. State explicitly when
no other branch passes the evidence standard.

Other roots in the window may change the focus ayah's reading, but distinguish
that ayah-level surprise from word-local activation of another branch of the
water root.

Treat source-noted homonyms, route anomalies, explicitly unrelated branch
origins, and single-source branches as higher-burden candidates. They require a
particularly visible local trigger. Do not invent branch IDs when an inventory
is missing.

## Output

Write one Markdown file with this structure:

```text
# {batch_id} Water Secondary Resonance

## {focus_ref} — {focus ayah Arabic}

### {surface_ar} — {root_norm}

**Primary reading.** ...

**Ayah-level surprise.** ...

**Water-root resonance.** ...

**Activation trace.** ...

**Negative evidence.** ...
```

Use a separate target subsection when a focus ayah has multiple water words.
In `Water-root resonance`, cite every retained branch as `root_id/B###`. If none
qualifies, write `No secondary water-root branch retained.`

Keep the analysis concise and diagnostic. Do not add a global synthesis; the
coordinator will compare cases and cohorts after all batch outputs are frozen.
