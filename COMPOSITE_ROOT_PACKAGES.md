# Composite Root Packages

This document is a lookup table for Quranic root workflow envelopes that combine
more than one v4 root ID into a single dictionary-entry package.

The workflow package ID is the authoritative `root_envelope_id` used by
`data/output/root_packets`, `v2/work/entry_creation`, writer tasks, review tasks,
and downstream entry artifacts. The original v4 root IDs remain visible inside
each packet under `v4_roots`.

Use this table when reconciling counts:

- `furuq_v4.sqlite` counts distinct Quranic `dictionary_entries.root_id` values.
- The dictionary workflow counts root packages by `root_envelope_id`.
- A composite package with two v4 roots counts as one workflow package but two
  v4 root IDs.

The DB does not currently store a dedicated composite-envelope lookup table.
The DB-level signal is duplicated `roots.root_norm` with distinct
`roots.source_root_norm` variants. The explicit mapping is materialized in
`data/output/root_packets/*--*.json` under `v4_roots`.

## Lookup Table

| root_envelope_id | root_norm | root_join_key | branch_count | v4 root IDs |
| --- | --- | --- | ---: | --- |
| `root_000090--root_000091` | ب د ء | بدء | 16 | `root_000090`, `root_000091` |
| `root_000099--root_000100` | ب ر ء | برء | 14 | `root_000099`, `root_000100` |
| `root_000146--root_000147` | ب ك ي | بكي | 9 | `root_000146`, `root_000147` |
| `root_000161--root_000162` | ب و ء | بوء | 10 | `root_000161`, `root_000162` |
| `root_000281--root_000282` | ج ي ء | جيء | 9 | `root_000281`, `root_000282` |
| `root_000466--root_000467` | د ر ء | درء | 16 | `root_000466`, `root_000467` |
| `root_000831--root_000832` | ش ي ء | شيء | 16 | `root_000831`, `root_000832` |
| `root_000919--root_000920` | ض و ء | ضوء | 6 | `root_000919`, `root_000920` |
| `root_000938--root_000939` | ط ف ء | طفء | 2 | `root_000938`, `root_000939` |
| `root_001210--root_001211` | ق ر ء | قرء | 19 | `root_001210`, `root_001211` |
| `root_001409--root_001410` | م ر ء | مرء | 11 | `root_001409`, `root_001410` |

## Detail Table

| root_envelope_id | v4 root ID | root_norm | source_root_norm | registry_status | covered_by | surahs |
| --- | --- | --- | --- | --- | --- | --- |
| `root_000090--root_000091` | `root_000090` | ب د ء | ب د ء | `pass1_complete` | `maqayis;sihah;mufradat` | `9;29;34;85` |
| `root_000090--root_000091` | `root_000091` | ب د ء | ب د أ | `pass1_complete` | `maqayis` | `7;10;12;21;27;29;30;32` |
| `root_000099--root_000100` | `root_000099` | ب ر ء | ب ر ء | `pass1_complete` | `maqayis;ayn;jamhara;sihah;tahdhib;mufradat` | `3;4;5;12;60` |
| `root_000099--root_000100` | `root_000100` | ب ر ء | ب ر أ | `pass3_complete` |  | `2;6;8;9;10;11;24;26;28;33;43;54;57;59` |
| `root_000146--root_000147` | `root_000146` | ب ك ي | ب ك ى | `pass1_complete` | `ayn;jamhara;sihah;tahdhib;mufradat` | `44` |
| `root_000146--root_000147` | `root_000147` | ب ك ي | ب ك ي | `pass1_complete` |  | `17;19;53` |
| `root_000161--root_000162` | `root_000161` | ب و ء | ب و ء | `pass1_complete` | `maqayis;ayn;jamhara;sihah;tahdhib;mufradat` | `3;5;10;12;16;29;39;59` |
| `root_000161--root_000162` | `root_000162` | ب و ء | ب و أ | `pass1_complete` | `maqayis` | `2;3;7;8;10;22` |
| `root_000281--root_000282` | `root_000281` | ج ي ء | ج ي ء | `pass1_complete` | `maqayis;jamhara;sihah;tahdhib;mufradat` | `35;39;89` |
| `root_000281--root_000282` | `root_000282` | ج ي ء | ج ي أ | `pass2_complete` | `maqayis` | `2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;23;24;25;26;27;28;29;30;33;34;35;36;37;38;39;40;41;42;43;44;45;46;47;49;50;51;53;54;57;58;59;60;61;63;67;69;71;79;80;89;98;110` |
| `root_000466--root_000467` | `root_000466` | د ر ء | د ر ء | `pass3_complete` | `maqayis;ayn;sihah;tahdhib;mufradat` | `3;13;28` |
| `root_000466--root_000467` | `root_000467` | د ر ء | د ر أ | `pass3_complete` |  | `2;24` |
| `root_000831--root_000832` | `root_000831` | ش ي ء | ش ي ء | `pass2_queued` | `maqayis;ayn;jamhara;sihah;tahdhib;mufradat` | `2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17;18;19;20;21;22;23;24;25;26;27;28;29;30;31;32;33;34;35;36;38;39;40;41;42;44;45;46;47;48;49;50;51;52;53;54;57;58;59;60;64;65;66;67;72;76;78;80;82;85` |
| `root_000831--root_000832` | `root_000832` | ش ي ء | ش ي أ | `pass2_queued` | `maqayis` | `2;3;4;5;6;7;8;9;10;11;12;13;14;16;17;18;21;22;23;24;25;26;27;28;29;30;32;33;34;35;36;37;39;40;41;42;43;47;48;50;53;56;57;59;62;73;74;76;78;80;81;82;87` |
| `root_000919--root_000920` | `root_000919` | ض و ء | ض و ء | `pass1_complete` | `maqayis;ayn;jamhara;sihah;tahdhib;mufradat` | `24` |
| `root_000919--root_000920` | `root_000920` | ض و ء | ض و أ | `pass1_complete` | `maqayis` | `2;10;21;28` |
| `root_000938--root_000939` | `root_000938` | ط ف ء | ط ف ء | `pass1_complete` | `maqayis;ayn;sihah;tahdhib;mufradat` | `9;61` |
| `root_000938--root_000939` | `root_000939` | ط ف ء | ط ف أ | `pass3_complete` |  | `5` |
| `root_001210--root_001211` | `root_001210` | ق ر ء | ق ر ء | `pass3_complete` | `maqayis;ayn;sihah;tahdhib;mufradat` | `2;4;5;6;7;9;10;12;13;15;16;17;18;20;25;27;28;30;34;36;38;39;41;42;43;46;47;50;54;55;56;59;69;72;73;75;76;84;85;87` |
| `root_001210--root_001211` | `root_001211` | ق ر ء | ق ر أ | `pass2_queued` |  | `2;16;17;26;75;96` |
| `root_001409--root_001410` | `root_001409` | م ر ء | م ر ء | `pass1_complete` | `maqayis;ayn;sihah;tahdhib;mufradat` | `4` |
| `root_001409--root_001410` | `root_001410` | م ر ء | م ر أ | `pass1_complete` | `maqayis` | `2;3;4;7;8;11;12;15;19;24;27;28;29;33;51;52;66;70;74;78;80;111` |

## Regeneration

The current table can be regenerated from packets with:

```bash
python3 - <<'PY'
import json
from pathlib import Path

for p in sorted(Path("data/output/root_packets").glob("root_*--root_*.json")):
    packet = json.loads(p.read_text())
    print(p.stem, packet["root_norm"], packet["root_join_key"], packet["v4_roots"])
PY
```
