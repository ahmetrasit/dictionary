# Encyclopedia workflow v2

Version 2 separates deterministic data functions from agent-authored encyclopedia
content. Each deterministic function gets its own script and generated namespace.

## Encyclopedia entry schema

`schema/encyclopedia-entry.schema.json` is the canonical v2 authored-entry
contract. One JSON document represents one root envelope in one target language;
English and Turkish are authored and validated separately.

The packet-bound validator checks the machine shape plus exact root and branch
rosters, packet hashes, exhaustive per-branch dictionary bases, dictionary and
passage counts, gloss ordering, common-loanword placement, Furuq neighbor links,
source quotations, and occurrence evidence references:

```sh
python3 v2/scripts/validate_entry.py v2/examples/root_000858.tr.entry.json
```

The normative field rules and ownership boundary are documented in
`schema/README.md`. The Turkish `ṣirāṭ` JSON file is a complete draft fixture,
not a published lexical decision.

The minimal agent workflow, branch evidence package, fragment ownership map,
retry rules, and acceptance criteria are defined in
`orchestration/entry-creation.spec.md`. The baseline uses only three agent roles:
branch writer, occurrence observer, and root profile writer.

Prepare deterministic evidence and resumable task manifests without making any
model calls:

```sh
python3 v2/scripts/create_entry.py root_000858 --language tr
```

Run the prepared workflow with Codex, assemble and validate the entry, and render
its Markdown form:

```sh
python3 v2/scripts/create_entry.py root_000858 --language tr --run-agents
```

The same command resumes hash-matching fragments. Stale fragments are rerun;
validation failures are routed to their owning role for at most two repair
rounds. Outputs are written to `v2/entries/<language>/`, while task and fragment
state stays under `v2/work/entry_creation/`.

The deterministic functions can also run independently:

```sh
python3 v2/scripts/build_branch_evidence.py root_000858
python3 v2/scripts/assemble_entry.py root_000858 --language tr
python3 v2/scripts/render_entry.py v2/entries/tr/root_000858.json
```

## Occurrence renderer

`scripts/render_occurrences.py` renders root-level Quran evidence from an existing
root packet. It does not choose a dictionary branch or sense.

For every exact QAC occurrence form, it emits:

- the lemma, rooted surface, part of speech, and morphology;
- every occurrence in Quran order with its contextual word;
- the reviewed attachment-instance grammar, when safely joined;
- every linked attachment with relation, focus role, counterpart, review status,
  and confidence;
- mechanical grouped attachment patterns; and
- unresolved or missing joins without guessed replacements.

Build the input packet separately when it does not exist:

```sh
python3 scripts/root_packet.py "ص ر ط"
```

Render by root ID, root envelope, Arabic root, or an Arabic word found in the
packet:

```sh
python3 v2/scripts/render_occurrences.py root_000858 --language tr
python3 v2/scripts/render_occurrences.py "ص ر ط" --language en
python3 v2/scripts/render_occurrences.py "صراط" --language tr
```

The default output is
`v2/output/occurrences/<root-envelope>.<language>.md`. Use `--check` to verify
that committed output still matches its packet, or `--output` to choose another
generated file.

QAC supplies occurrence forms and morphology. The packet's attachment enrichment
supplies per-instance grammar and syntactic relations. Free-prose attachment
grammar remains visibly labeled as source text; structured labels are rendered in
English or Turkish.
