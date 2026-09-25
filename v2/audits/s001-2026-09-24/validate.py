"""Validate the S1 screening artifacts; no canonical data is modified."""
import hashlib
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
manifest = json.loads((BASE / "manifest.json").read_text())
errors = []
counts = Counter()
seen = []
for batch in manifest["batches"]:
    src = BASE / "input" / batch["file"]
    if hashlib.sha256(src.read_bytes()).hexdigest() != batch["sha256"]:
        errors.append(f"Input hash mismatch: {src.name}")
    entries = json.loads(src.read_text())["entries"]
    branches = {b["branch_ref"]: b for e in entries for b in e["branches"]}
    dest = BASE / "output" / batch["file"]
    if not dest.exists():
        errors.append(f"Missing output: {dest.name}")
        continue
    output = json.loads(dest.read_text())
    if output.get("batch") != batch["batch"] or output.get("model") != "gpt-6-sol" or output.get("reasoning_effort") != "max":
        errors.append(f"Invalid batch/model metadata: {dest.name}")
    rows = output["results"]
    if Counter(r["branch_ref"] for r in rows) != Counter(branches.keys()):
        errors.append(f"Branch coverage mismatch: {dest.name}")
    for row in rows:
        ref = row["branch_ref"]
        seen.append(ref)
        if ref not in branches:
            continue
        branch = branches[ref]
        verdict = row["verdict"]
        counts[verdict] += 1
        if verdict not in {"no_flag", "needs_review", "insufficient_evidence"}:
            errors.append(f"Invalid verdict: {ref}")
        if verdict == "no_flag":
            if row["issues"] or not isinstance(row["definition_en"], str) or not row["definition_en"].strip():
                errors.append(f"Invalid clean result: {ref}")
        elif not row["issues"] or row["definition_en"] is not None:
            errors.append(f"Invalid flagged result: {ref}")
        for issue in row["issues"]:
            if issue["anchor_ar"] and issue["anchor_ar"] not in branch["source_phrase_ar"]:
                errors.append(f"Arabic quote is not exact: {ref}")
            if issue["text_tr"] and issue["text_tr"] not in json.dumps(branch, ensure_ascii=False):
                errors.append(f"Turkish quote is not exact: {ref}")
expected = [b for r in manifest["roots"] for b in r["branch_refs"]]
if Counter(seen) != Counter(expected):
    errors.append("Overall branch coverage mismatch")
report = {"branches": len(seen), "counts": dict(counts), "errors": errors}
(BASE / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
