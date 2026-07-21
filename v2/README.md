# Encyclopedia workflow v2

## Project direction

All further encyclopedia workflow development and production entry runs will use
v2. The legacy root-level workflow remains available as reference material, but
new features and fixes belong in `v2/` unless an explicit migration dependency
requires a legacy change.

Version 2 separates deterministic data functions from agent-authored encyclopedia
content. Each deterministic function gets its own script and generated namespace.

## Encyclopedia entry schema

`schema/encyclopedia-entry.schema.json` is the canonical v2 authored-entry
contract. One JSON document represents one root envelope in one target language;
English and Turkish are authored and validated separately.

The packet-bound validator checks the machine shape plus exact root and branch
rosters, packet hashes, exhaustive per-branch dictionary bases, dictionary and
passage counts, gloss ordering, common-loanword placement, Furuq neighbor links,
packet-backed lexical realizations, evidence qualifiers, neighbor coverage, and
deterministically reproduced QAC morphology, ayahs, occurrences, and attachment
alignment:

```sh
python3 v2/scripts/validate_entry.py v2/examples/root_000858.tr.entry.json
```

The normative field rules and ownership boundary are documented in
`schema/README.md`. The Turkish `ṣirāṭ` JSON file is a complete draft fixture,
not a published lexical decision.

The minimal agent workflow, branch evidence package, fragment ownership map,
retry rules, and acceptance criteria are defined in
`orchestration/entry-creation.spec.md`. The baseline uses two agent roles:
one branch writer per branch and one root profile writer per entry. Agents never
receive Quran ayahs, occurrence data, QAC morphology, or attachment records.

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

Export all validated entries as deterministic, one-entry-per-line JSONL:

```sh
python3 v2/scripts/export_jsonl.py --language tr
```

Every line is one complete schema-v4 entry. The exporter validates all source
bindings and rejects duplicate entry IDs or mixed languages before writing.

Each agent runs in a temporary read-only workspace containing only its
hash-bound task inputs. The default per-process timeout is 30 minutes; change it
with `--agent-timeout`. Operational failures stop immediately, while invalid
agent JSON remains eligible for bounded repair.

The coordinator additionally denies agent reads from the repository with
`sandbox-exec` on macOS or bubblewrap on Linux. It stops before model execution
when neither confinement tool is available. A fatal parallel task terminates
the other active agent processes.

Canonical entry creation accepts only the packet and evidence locations shown
above. Existing draft outputs may be regenerated, but reviewed or published
entries and unmarked Markdown require the explicit `--force-entry` override.
The validated JSON and Markdown are staged together and published as a pair.
Reviewed and published entries also protect their pinned occurrence and shared
branch evidence during prepare-only runs. `--force-entry` is required before
those dependencies can be regenerated.

Only frozen focus branches marked `accepted` and `contaminated: no` can enter an
agent task or assembled entry. Other branch states stop with `needs_evidence`.

The deterministic functions can also run independently:

```sh
python3 v2/scripts/build_branch_evidence.py root_000858
python3 v2/scripts/assemble_entry.py root_000858 --language tr
python3 v2/scripts/render_entry.py v2/entries/tr/root_000858.json
```

The standalone evidence generators apply the same reviewed/published pin guard
when writing their canonical default paths. Use `--check` for reproducibility,
`--output`/`--output-dir` for an unpinned alternate artifact, or explicit
`--force` when intentionally replacing pinned canonical evidence.

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

Attachment word numbers belong to their own source and are never interpreted as
QAC references. The renderer first writes a deterministic crosswalk under
`v2/output/alignments/`; downstream occurrence rows retain `qac_word_ref` as
their canonical identity. Corpus-wide counts come only from the QAC census, not
from attachment grammar prose.

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
generated file. Canonical output pinned by a reviewed or published entry requires
`--force`; `--check` never mutates it.

QAC supplies occurrence forms and morphology. The packet's attachment enrichment
supplies per-instance grammar and syntactic relations. Free-prose attachment
grammar remains visibly labeled as source text; structured labels are rendered in
English or Turkish.
