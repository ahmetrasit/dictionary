# Final Dictionary Entries

This directory is the root-level finalized entry surface for downstream
consumers.

For each target language, finalized Quran-corpus dictionary entries live in:

```text
entries/<language>/<root_envelope_id>.json
entries/<language>/manifest.json
```

Rules:

- keep only final JSON files and `manifest.json` here;
- do not store Markdown, work directories, review outputs, gloss-generation
  results, or temporary artifacts here;
- do not mix non-Quranic `furuq` roots into Quran-corpus language folders;
- use `root_envelope_id` filenames, including composite envelopes such as
  `root_000099--root_000100.json`;
- regenerate this surface deterministically from validated v2 entries.

For Turkish:

```sh
python3 v2/scripts/promote_final_entries.py --language tr
python3 v2/scripts/promote_final_entries.py --language tr --check
```

The source assembly/rendering area remains `v2/entries/<language>/`. The
orchestration work area remains `v2/work/entry_creation/`.
