# Water Secondary Resonance

This run tests strict Quranic water-word targets in independent five-ayah
windows. Each focus ayah has up to two preceding and two following ayat, clipped
at surah boundaries.

## Separation

- `interpretive_report.md` is the reader-facing answer to why each water word is
  selected and what neighboring words would change.
- `relationship_*.md` maps the participant and event arcs around the target
  words: before-state, water event, after-state, reversals, and changes of
  control.
- `adjudication/` contains the complete graded candidate tables, the consolidated
  draft, and an independent calibration audit.
- `cohort_profiles/` records common primary-context properties without proposing
  secondary resonances.
- `packets/` contains deterministic Arabic/QAC and branch-evidence inputs.
- `responses/` contains independent secondary-resonance readings.
- `manifest.json` records target counts, batch assignments, and resource hashes.

Cases inside a batch are independent. A reader may not use one case as context
for another. Multiple target water words in the same focus ayah are tested
separately inside one case.

## Build

```bash
python3 scripts/build_water_resonance_packets.py
python3 scripts/validate_water_resonance_packets.py
python3 scripts/validate_water_resonance_responses.py
python3 scripts/summarize_water_resonance_responses.py --require-complete
```

The strict list excludes clearly non-water homonyms or forms from the focus set,
while their accepted root branches remain eligible as higher-burden secondary
resonance candidates.
