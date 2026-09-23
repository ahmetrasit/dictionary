# Reviewed furuq writer transfer

Run from the dictionary repository root after Agent B has completed its
`pass` or bounded `repair` for a root in the Furuq namespace. Keep the reviewed
writer response at `v2/work/entry_creation/furuq/<root>/tr/output/`.

```sh
python3 v2/scripts/enrich_furuq_writer.py <root>
```

The command writes
`v2/work/entry_creation/furuq/<root>/tr/export/<root>_entry.json`.
It is idempotent when the existing file is byte-identical and refuses a
different existing export. The output is an enriched writer response for the
quran-data Turkish dictionary source directory, not a schema-v4 master entry.

Before writing, the script validates the final writer response, the staged
reviewer's immutable pre-fix snapshot, its review verdict, and the allowed
fields of any repair. It checks the sealed writer evidence and branch-package
digests, then requires
`data/output/furuq/root_packets/<root>.json` to match the packet digest in
the evidence index. Arabic branch fields and source attribution come from the
matched packages. The occurrence summary, forms, ayahs, and rows are computed
from that packet's QAC and attachment data. The script leaves the live writer
response untouched.

For example:

```sh
python3 v2/scripts/enrich_furuq_writer.py root_005406
```

Transfer the resulting JSON only after comparing it with the reviewed source
and recording its checksum and source commit. The quran-data projector rejects
raw writer responses and requires the injected Arabic fields, source roster,
and occurrence summary. The Quran-corpus master-entry finalizer, JSONL export,
and `entries/tr/` promoter are separate paths and do not publish these furuq
transfer artifacts.
