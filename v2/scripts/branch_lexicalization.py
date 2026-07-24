"""Deterministic branch lexicalization profile helpers."""

from __future__ import annotations

from collections import Counter


BASIS = "furuq.lexical_unit_senses.unit_kind"


def branch_lexicalization_profile(lexical_units: list[dict]) -> dict:
    """Classify whether a branch is bare or has non-bare lexical units."""
    counts = Counter(
        str(unit.get("unit_kind", "")).strip()
        for unit in lexical_units
        if str(unit.get("unit_kind", "")).strip()
    )
    unit_kind_counts = dict(sorted(counts.items()))
    has_collocation = counts.get("collocation", 0) > 0
    has_non_bare = any(kind != "form" for kind in counts)
    if not counts:
        branch_kind = "unresolved"
    elif not has_non_bare:
        branch_kind = "bare"
    elif set(counts) == {"collocation"}:
        branch_kind = "collocation"
    elif "form" in counts or len(counts) > 1:
        branch_kind = "mixed_non_bare"
    else:
        branch_kind = "non_bare"
    return {
        "branch_kind": branch_kind,
        "has_non_bare": has_non_bare,
        "has_collocation": has_collocation,
        "unit_kind_counts": unit_kind_counts,
        "basis": BASIS,
    }
