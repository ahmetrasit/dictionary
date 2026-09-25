"""Collect screening, deeper review and English draft calibration results."""
import hashlib
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
deep = {}
evidence_files = {}
for path in sorted((BASE / "deep").glob("*.json")):
    for row in json.loads(path.read_text())["results"]:
        assert row["branch_ref"] not in deep, row["branch_ref"]
        deep[row["branch_ref"]] = row
        for citation in row["evidence"]:
            source = Path(citation["path"])
            content = source.read_text()
            assert citation["quote_ar"] in content, (row["branch_ref"], citation["quote_ar"])
            evidence_files[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
spot = {r["branch_ref"]: r for r in json.loads((BASE / "english-spot-review.json").read_text())["results"]}
rows = []
for path in sorted((BASE / "output").glob("batch-*.json")):
    for original in json.loads(path.read_text())["results"]:
        row = {"branch_ref": original["branch_ref"], "screening_verdict": original["verdict"], "screening_issues": original["issues"]}
        followup = deep.get(row["branch_ref"])
        if original["verdict"] == "no_flag":
            assert followup is None
            row.update(status="no_flag", definition_en=original["definition_en"])
        else:
            assert followup is not None, row["branch_ref"]
            row.update(status="flag_dismissed" if followup["disposition"] == "dismissed" else followup["disposition"], definition_en=followup["definition_en"], deeper_review=followup)
        calibration = spot.get(row["branch_ref"])
        if calibration:
            row["english_calibration"] = calibration
            assert calibration["verdict"] != "source_question", row["branch_ref"]
            if calibration["verdict"] == "translation_fix":
                row["definition_en"] = calibration["definition_en"]
        row["english_status"] = "draft" if row["definition_en"] else "pending_reviewed_correction"
        rows.append(row)
assert len(rows) == 157
result = {"schema": "s1-dictionary-audit-summary-v1", "canonical_entries_modified": False, "published": False, "status_counts": dict(Counter(r["status"] for r in rows)), "english_drafts": sum(bool(r["definition_en"]) for r in rows), "source_evidence_sha256": evidence_files, "results": rows}
(BASE / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in {"results", "source_evidence_sha256"}}, indent=2))
