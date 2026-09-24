"""Reviewed supplemental identities, citations, QAC bindings, and evidence.

This module never reads or rewrites the frozen Furuq packet/database namespace.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path

from v2.scripts.assemble_entry import PROJECT, canonical_sha256, sha256_file
from v2.scripts.branch_lexicalization import branch_lexicalization_profile
from v2.scripts.validate_entry import ContractError, load_json


REGISTRY_PATH = PROJECT / "data/supplemental/registry.v1.json"
SOURCE_NAMES_PATH = PROJECT / "data/supplemental/source-names.v1.json"
ID_KIND = ((re.compile(r"root_[0-9]{6}\Z"), "lexical_root"),
           (re.compile(r"headword_[0-9]{6}\Z"), "grammatical_headword"))
SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
ID_PATTERN = {"lexical_root": re.compile(r"B[0-9]{3}\Z"),
              "grammatical_headword": re.compile(r"S[0-9]{3}\Z")}
QAC_GZIP = "data/morphology/qac.sqlite.gz"


def entry_kind(ident: str) -> str:
    for pattern, kind in ID_KIND:
        if pattern.fullmatch(ident):
            return kind
    raise ContractError(f"Invalid supplemental ID: {ident}")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def work_dir(ident: str, language: str) -> Path:
    kind = entry_kind(ident)
    if language != "tr":
        raise ContractError("Supplemental authoring currently requires --language tr")
    base = PROJECT / "v2/work/entry_creation"
    if kind == "grammatical_headword":
        base /= "headwords"
    return base / ident / language


def quran_data_dir(override: Path | None = None) -> Path:
    path = override or PROJECT.parent / "quran-data"
    path = path.resolve()
    if not (path / QAC_GZIP).is_file():
        raise ContractError(f"Missing QAC source at {path / QAC_GZIP}; use --quran-data")
    return path


def committed_qac_bytes(quran_data: Path) -> bytes:
    path = quran_data / QAC_GZIP
    raw = path.read_bytes()
    result = subprocess.run(["git", "-C", str(quran_data), "ls-files", "-s", "--", QAC_GZIP],
                            capture_output=True, text=True, check=True)
    if not result.stdout.strip():
        raise ContractError("QAC gzip is not tracked in quran-data")
    # Git LFS pointers are not accepted as a QAC source. The checked-out bytes
    # must match the committed blob, so local edits cannot change a binding.
    committed = subprocess.run(["git", "-C", str(quran_data), "show", f"HEAD:{QAC_GZIP}"],
                               capture_output=True, check=True).stdout
    if committed != raw:
        raise ContractError("QAC morphology differs from committed quran-data HEAD")
    return raw


def qac_connection(quran_data: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.deserialize(gzip.decompress(committed_qac_bytes(quran_data)))
    return connection


def source_names() -> dict[str, dict]:
    value = load_json(SOURCE_NAMES_PATH)
    names = value.get("sources") if isinstance(value, dict) else None
    if value.get("schemaVersion") != "dictionary-supplemental-source-names-v1" or not isinstance(names, dict):
        raise ContractError("Invalid supplemental source-name map")
    codes = set()
    for ident, row in names.items():
        if (not re.fullmatch(r"[a-z][a-z0-9_]*", ident)
                or not isinstance(row, dict) or set(row) != {"sourceTitle", "badgeCode"}
                or not isinstance(row["sourceTitle"], str) or not row["sourceTitle"]
                or not isinstance(row["badgeCode"], str) or not re.fullmatch(r"[A-Z]{2}", row["badgeCode"])
                or row["badgeCode"] in codes):
            raise ContractError(f"Invalid supplemental source-name row: {ident}")
        codes.add(row["badgeCode"])
    return names


def source_phrase(keys: list[str], sources: dict[str, dict]) -> str:
    if not isinstance(keys, list) or not keys or len(keys) != len(set(keys)) or any(key not in sources for key in keys):
        raise ContractError("Invalid ordered supplemental source keys")
    return "؛ ".join(
        f"{sources[key]['quotationAr']} ({sources[key]['sourceId']}:{key})"
        for key in keys
    )


def check_frozen_identity_collision(ident: str, intake: dict, quran_data: Path) -> None:
    """Reject a new lexical identity already owned by the frozen Quranic map."""
    if entry_kind(ident) != "lexical_root":
        return
    for path in (
        PROJECT / "data/output/root_packets" / f"{ident}.json",
        PROJECT / "data/output/furuq/root_packets" / f"{ident}.json",
        PROJECT / "v2/work/entry_creation/furuq" / ident,
    ):
        if path.exists():
            raise ContractError(f"Supplemental ID collides with frozen root path: {path}")
    resolutions = quran_data / "data/bridges/qac-dictionary-root-resolutions.json"
    if resolutions.is_file():
        value = load_json(resolutions)
        key = intake["binding"]["selector"]["qacRootJoinKey"]
        for row in value.get("roots", []):
            if (row.get("qacRootJoinKey") == key and row.get("rootIds")
                    and row["rootIds"] != [ident]):
                raise ContractError(f"Supplemental root identity already resolves in frozen map: {key}")


def selected_rows(connection: sqlite3.Connection, binding: dict) -> list[dict]:
    if not isinstance(binding, dict) or not isinstance(binding.get("selector"), dict):
        raise ContractError("Missing supplemental QAC binding")
    selector = binding["selector"]
    scope = "qacLemma" if "qacLemma" in selector else "qacRef"
    if set(selector) != {"qacRootJoinKey", scope} or not all(
        isinstance(value, str) and value for value in selector.values()
    ):
        raise ContractError(f"Invalid supplemental QAC selector: {selector}")
    column = "lemma_ar" if scope == "qacLemma" else "qac_ref"
    rows = [dict(row) for row in connection.execute(
        f"SELECT * FROM qac_morphemes WHERE root_join_key=? AND {column}=? ORDER BY surah,ayah,word_index,morpheme_index",
        (selector["qacRootJoinKey"], selector[scope]),
    )]
    if not rows:
        raise ContractError(f"Supplemental QAC selector has no rows: {selector}")
    refs = sorted(row["qac_ref"] for row in rows)
    expected = digest(json.dumps(refs, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if binding.get("selectorRefsSha256") != expected:
        raise ContractError(f"Supplemental QAC selector ref set drift: {selector}")
    return rows


def validate_sources(intake: dict, names: dict[str, dict]) -> dict[str, dict]:
    rows = intake.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ContractError("Supplemental intake requires source citations")
    by_key = {}
    for source in rows:
        if not isinstance(source, dict):
            raise ContractError("Supplemental citation must be an object")
        key = source.get("sourceKey")
        quote = source.get("quotationAr")
        if (not isinstance(key, str) or not SOURCE_KEY.fullmatch(key) or key in by_key
                or source.get("sourceType") not in {"lexicon", "grammar", "tafsir"}
                or not isinstance(source.get("sourceId"), str) or not source["sourceId"]
                or not isinstance(source.get("sourceTitle"), str) or not source["sourceTitle"]
                or not isinstance(source.get("author"), str) or not source["author"]
                or not isinstance(source.get("edition"), str) or not source["edition"]
                or not isinstance(source.get("locator"), str) or not source["locator"]
                or not isinstance(quote, str) or not quote or quote != quote.strip()
                or source.get("quotationSha256") != digest(quote.encode("utf-8"))):
            raise ContractError(f"Invalid supplemental citation or quotation: {key}")
        hosted = isinstance(source.get("sourceUrl"), str) and source["sourceUrl"].startswith("https://")
        frozen = (isinstance(source.get("sourceRef"), str) and bool(source["sourceRef"])
                  and isinstance(source.get("sourceSha256"), str) and bool(SHA.fullmatch(source["sourceSha256"])))
        if not (hosted or frozen):
            raise ContractError(f"Unlocated supplemental citation: {key}")
        if "parentEntrySha256" in source and (not frozen or source["parentEntrySha256"] != source["sourceSha256"]):
            raise ContractError(f"Parent entry digest differs from frozen row: {key}")
        if source["sourceType"] == "lexicon":
            named = names.get(source["sourceId"])
            if named is None or named["sourceTitle"] != source["sourceTitle"]:
                raise ContractError(f"Lexicon source title is outside source map: {key}")
        elif source["sourceId"] in names:
            raise ContractError(f"Lexicon source ID is mistyped as grammar/tafsir: {key}")
        by_key[key] = source
    return by_key


def validate_intake(ident: str, intake: dict, connection: sqlite3.Connection, names: dict[str, dict]) -> list[dict]:
    kind = entry_kind(ident)
    if (intake.get("schemaVersion") != "dictionary-supplemental-intake-v1"
            or intake.get("id") != ident or intake.get("kind") != kind
            or not isinstance(intake.get("headwordArabic"), str) or not intake["headwordArabic"].strip()):
        raise ContractError(f"Invalid supplemental intake identity: {ident}")
    if kind == "lexical_root":
        root = intake.get("rootArabic")
        if (not isinstance(root, str) or not root.strip()
                or root.replace(" ", "") != intake.get("binding", {}).get("selector", {}).get("qacRootJoinKey")):
            raise ContractError(f"Supplemental root identity differs from QAC selector: {ident}")
    if kind == "grammatical_headword" and "rootArabic" in intake:
        raise ContractError(f"Grammatical headword must not assert a root: {ident}")
    selector = intake.get("binding", {}).get("selector")
    if not isinstance(selector, dict):
        raise ContractError(f"Missing supplemental QAC selector: {ident}")
    snapshot = intake.get("sourceSnapshot")
    if (not isinstance(snapshot, dict) or not isinstance(snapshot.get("quranDataCommit"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", snapshot["quranDataCommit"])
            or not isinstance(snapshot.get("qacMorphologyGzipSha256"), str)
            or not SHA.fullmatch(snapshot["qacMorphologyGzipSha256"])):
        raise ContractError(f"Invalid historical source snapshot: {ident}")
    rows = selected_rows(connection, intake["binding"])
    sources = validate_sources(intake, names)
    context = intake.get("phraseContext")
    if context is not None:
        if (kind != "grammatical_headword" or not isinstance(context, dict)
                or not isinstance(context.get("statementAr"), str)
                or not context["statementAr"].strip()):
            raise ContractError(f"Invalid grammatical phrase context: {ident}")
        source_phrase(context.get("sourceKeys"), sources)
    analyses = intake.get("analyses")
    if not isinstance(analyses, list) or not analyses:
        raise ContractError(f"Supplemental analyses are missing: {ident}")
    seen_analyses = set()
    for index, analysis in enumerate(analyses):
        aid = analysis.get("analysisId") if isinstance(analysis, dict) else None
        if (not isinstance(aid, str) or aid in seen_analyses
                or analysis.get("standing") not in {"primary", "documented_alternative"}
                or (index == 0 and analysis["standing"] != "primary")
                or (index > 0 and analysis["standing"] == "primary")
                or analysis.get("rootArabic") is not None and not isinstance(analysis.get("rootArabic"), str)
                or analysis.get("patternAr") is not None and not isinstance(analysis.get("patternAr"), str)
                or not isinstance(analysis.get("scopeNoteAr"), str) or not analysis["scopeNoteAr"].strip()):
            raise ContractError(f"Invalid supplemental analysis: {ident}/{aid}")
        source_phrase(analysis.get("sourceKeys"), sources)
        seen_analyses.add(aid)
    senses = intake.get("senses")
    if not isinstance(senses, list) or not senses:
        raise ContractError(f"Supplemental senses are missing: {ident}")
    seen = set()
    qac_ref_set = {row["qac_ref"] for row in rows}
    declared_ref_sets = []
    for sense in senses:
        sid = sense.get("senseId") if isinstance(sense, dict) else None
        if not isinstance(sid, str) or not ID_PATTERN[kind].fullmatch(sid) or sid in seen:
            raise ContractError(f"Invalid supplemental sense ID: {ident}/{sid}")
        seen.add(sid)
        for field in ("imageAr", "whatIsAr", "whatIsNotAr"):
            if not isinstance(sense.get(field), str) or not sense[field].strip():
                raise ContractError(f"Missing Arabic sense evidence: {ident}/{sid}/{field}")
        sense_keys = sense.get("sourceKeys")
        source_phrase(sense_keys, sources)
        claims = sense.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ContractError(f"Missing sense claim roster: {ident}/{sid}")
        claim_ids = set()
        for claim in claims:
            cid = claim.get("claimId") if isinstance(claim, dict) else None
            if (not isinstance(cid, str) or not re.fullmatch(r"bc_[0-9]{3}", cid) or cid in claim_ids
                    or not isinstance(claim.get("statementAr"), str) or not claim["statementAr"].strip()):
                raise ContractError(f"Invalid sense claim: {ident}/{sid}/{cid}")
            source_phrase(claim.get("sourceKeys"), sources)
            if not set(claim["sourceKeys"]) <= set(sense_keys):
                raise ContractError(f"Sense claim cites a source outside sense authority: {ident}/{sid}/{cid}")
            claim_ids.add(cid)
        units = sense.get("lexicalUnits")
        if not isinstance(units, list):
            raise ContractError(f"Missing lexicalUnits roster: {ident}/{sid}")
        unit_ids = set()
        for unit in units:
            uid = unit.get("lexicalUnitId") if isinstance(unit, dict) else None
            if (not isinstance(uid, str) or not re.fullmatch(r"lu_[0-9]{3,}", uid) or uid in unit_ids
                    or unit.get("unitKind") not in {"form", "collocation", "lexical_unit", "review"}
                    or unit.get("renderingPolicy") not in {"ordinary", "proper_name"}
                    or not isinstance(unit.get("expressionAr"), str) or not unit["expressionAr"].strip()
                    or not isinstance(unit.get("senseAr"), str) or not unit["senseAr"].strip()):
                raise ContractError(f"Invalid lexical unit: {ident}/{sid}/{uid}")
            source_phrase(unit.get("sourceKeys"), sources)
            if not set(unit["sourceKeys"]) <= set(sense_keys):
                raise ContractError(f"Lexical unit cites source outside sense authority: {ident}/{sid}/{uid}")
            unit_ids.add(uid)
        neighbors = sense.get("neighbors")
        if not isinstance(neighbors, list):
            raise ContractError(f"Missing neighbors roster: {ident}/{sid}")
        for neighbor in neighbors:
            if (not isinstance(neighbor, dict) or not re.fullmatch(r"(?:root_[0-9]{6}/B[0-9]{3}|headword_[0-9]{6}/S[0-9]{3})", str(neighbor.get("neighborRef")))
                    or not isinstance(neighbor.get("imageAr"), str) or not neighbor["imageAr"].strip()
                    or not isinstance(neighbor.get("whatIsAr"), str) or not neighbor["whatIsAr"].strip()):
                raise ContractError(f"Invalid neighbor card: {ident}/{sid}")
        if "qacMorphemeRefs" in sense:
            refs = sense["qacMorphemeRefs"]
            if (not isinstance(refs, list) or len(refs) != len(set(refs))
                    or not set(refs) <= qac_ref_set):
                raise ContractError(f"Invalid sense QAC ref partition: {ident}/{sid}")
            declared_ref_sets.append(set(refs))
    if declared_ref_sets and (len(declared_ref_sets) != len(senses)
                              or set.union(*declared_ref_sets) != qac_ref_set
                              or sum(map(len, declared_ref_sets)) != len(qac_ref_set)):
        raise ContractError(f"Sense QAC refs do not partition binding: {ident}")
    audit = intake.get("qacAudit")
    if audit is not None:
        if not isinstance(audit, dict):
            raise ContractError(f"Invalid supplemental QAC audit: {ident}")
        refs = sorted(qac_ref_set)
        pos_counts: dict[str, int] = {}
        for row in rows:
            pos_counts[row["pos"]] = pos_counts.get(row["pos"], 0) + 1
        if (audit.get("qacMorphemeRefs") != refs
                or audit.get("qacPosCounts") != pos_counts
                or audit.get("qacNRefs") != sorted(row["qac_ref"] for row in rows if row["pos"] == "N")
                or not isinstance(audit.get("observationNote"), str)):
            raise ContractError(f"Supplemental QAC audit differs from committed rows: {ident}")
    return rows


def load_reviewed_intake(ident: str, quran_data: Path) -> tuple[dict, dict, dict, list[dict]]:
    entry_kind(ident)
    registry = load_json(REGISTRY_PATH)
    if registry.get("schemaVersion") != "dictionary-supplemental-registry-v1" or not isinstance(registry.get("entries"), list):
        raise ContractError("Invalid supplemental registry")
    names = source_names()
    rows = registry["entries"]
    if len({row.get("id") for row in rows if isinstance(row, dict)}) != len(rows):
        raise ContractError("Duplicate supplemental registry ID")
    for entry in rows:
        eid = entry.get("id") if isinstance(entry, dict) else None
        if (not isinstance(eid, str) or entry.get("kind") != entry_kind(eid)
                or entry.get("intakePath") != f"entries/{eid}.json"):
            raise ContractError(f"Invalid supplemental registry row: {eid}")
        entry_path = REGISTRY_PATH.parent / entry["intakePath"]
        if not entry_path.is_file() or entry.get("intakeSha256") != sha256_file(entry_path):
            raise ContractError(f"Supplemental registry closure drift: {eid}")
    selected = [row for row in rows if row.get("id") == ident]
    if len(selected) != 1:
        raise ContractError(f"Supplemental ID is not in reviewed registry: {ident}")
    row = selected[0]
    if (row.get("kind") != entry_kind(ident) or row.get("intakePath") != f"entries/{ident}.json"
            or not isinstance(row.get("reviewedOn"), str)
            or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row["reviewedOn"])):
        raise ContractError(f"Invalid supplemental registry ownership: {ident}")
    path = REGISTRY_PATH.parent / row["intakePath"]
    if not path.is_file() or row.get("intakeSha256") != sha256_file(path):
        raise ContractError(f"Supplemental intake hash drift: {ident}")
    intake = load_json(path)
    check_frozen_identity_collision(ident, intake, quran_data)
    with qac_connection(quran_data) as connection:
        qac_rows = validate_intake(ident, intake, connection, names)
    meta = {
        "registryPath": "data/supplemental/registry.v1.json",
        "registrySha256": sha256_file(REGISTRY_PATH),
        "intakePath": f"data/supplemental/entries/{ident}.json",
        "intakeSha256": sha256_file(path),
    }
    return intake, meta, names, qac_rows


def evidence_from_intake(intake: dict) -> dict:
    ident = intake["id"]
    headword = intake["kind"] == "grammatical_headword"
    collection = "senses" if headword else "branches"
    ref_key = "sense_ref" if headword else "branch_ref"
    sources = {row["sourceKey"]: row for row in intake["sources"]}
    neighbor_registry = []
    neighbor_by_ref = {}
    result = []
    for sense in intake["senses"]:
        neighbors = []
        for row in sense["neighbors"]:
            card = {"neighbor_ref": row["neighborRef"], "branch_image_ar": row["imageAr"], "what_is_ar": row["whatIsAr"]}
            if card["neighbor_ref"] in neighbor_by_ref and neighbor_by_ref[card["neighbor_ref"]] != card:
                raise ContractError(f"Conflicting supplemental neighbor card: {card['neighbor_ref']}")
            if card["neighbor_ref"] not in neighbor_by_ref:
                neighbor_by_ref[card["neighbor_ref"]] = card
                neighbor_registry.append(card)
            neighbors.append(card["neighbor_ref"])
        units = [{"lexical_unit_id": unit["lexicalUnitId"], "unit_kind": unit["unitKind"],
                  "expression_ar": unit["expressionAr"], "sense_ar": unit["senseAr"],
                  "source_phrase_ar": source_phrase(unit["sourceKeys"], sources),
                  "rendering_policy": unit["renderingPolicy"], "source_keys": unit["sourceKeys"]}
                 for unit in sense["lexicalUnits"]]
        profile = branch_lexicalization_profile(units)
        profile["basis"] = "supplemental_intake.lexicalUnits.unitKind"
        result.append({
            ref_key: f"{ident}/{sense['senseId']}",
            "branch_image_ar": sense["imageAr"],
            "what_is_ar": sense["whatIsAr"],
            "what_is_not_ar": sense["whatIsNotAr"],
            "source_phrase_ar": source_phrase(sense["sourceKeys"], sources),
            "source_keys": sense["sourceKeys"],
            "citations": [sources[key] for key in sense["sourceKeys"]],
            "branch_claims": [
                {"claim_id": claim["claimId"], "source_phrase_ar": source_phrase(claim["sourceKeys"], sources),
                 "statement_ar": claim["statementAr"], "source_keys": claim["sourceKeys"],
                 "source_ids": list(dict.fromkeys(sources[key]["sourceId"] for key in claim["sourceKeys"]))}
                for claim in sense["claims"]
            ],
            "lexicalization_profile": profile,
            "lexical_units": units,
            "neighbor_refs": neighbors,
        })
    return {"format": "dictionary-v2-agent-headword-evidence-v1" if headword else "dictionary-v2-agent-root-evidence-v5",
            "entryKind": intake["kind"], "headwordArabic": intake["headwordArabic"],
            "analyses": intake["analyses"], collection: result,
            "neighbor_registry": neighbor_registry,
            "source_roster": intake["sources"]}


def occurrence_evidence(qac_rows: list[dict], connection: sqlite3.Connection) -> dict:
    rows = sorted(qac_rows, key=lambda row: (row["surah"], row["ayah"], row["word_index"], row["morpheme_index"]))
    forms_by_key = {}
    for row in rows:
        key = (row["lemma_ar"], row["stem_ar"], row["pos"], row["morph_features"])
        forms_by_key.setdefault(key, []).append(row)
    form_by_ref = {}
    forms = []
    for index, (key, members) in enumerate(forms_by_key.items(), 1):
        fid = f"F{index:03d}"
        forms.append({"form_id": fid, "lemma_ar": key[0], "stem_ar": key[1], "pos": key[2],
                      "measure": members[0]["measure"], "morph_features": key[3], "occurrence_count": len(members)})
        for row in members:
            form_by_ref[row["qac_ref"]] = fid
    ayah_refs = sorted({(row["surah"], row["ayah"]) for row in rows})
    ayahs = []
    for surah, ayah in ayah_refs:
        words = connection.execute("SELECT surface_ar FROM qac_words WHERE surah=? AND ayah=? ORDER BY word_index", (surah, ayah)).fetchall()
        ayahs.append({"ayah_ref": f"{surah}:{ayah}", "surface_ar": " ".join(word[0] for word in words)})
    occurrences = []
    for row in rows:
        record = {field: row[field] for field in (
            "qac_ref", "qac_word_ref", "surah", "ayah", "word_index", "morpheme_index",
            "surface_ar", "stem_ar", "lemma_ar", "root_raw", "root_ar", "root_join_key",
            "source_pos", "pos", "morpheme_role", "measure", "aspect", "mood", "voice", "morph_features")}
        record["ayah_ref"] = f"{row['surah']}:{row['ayah']}"
        record["form_id"] = form_by_ref[row["qac_ref"]]
        occurrences.append(record)
    return {
        "summary": {"morpheme_count": len(rows), "word_count": len({row["qac_word_ref"] for row in rows}),
                    "ayah_count": len(ayah_refs), "surah_count": len({row["surah"] for row in rows})},
        "forms": forms, "ayahs": ayahs, "occurrences": occurrences,
    }
