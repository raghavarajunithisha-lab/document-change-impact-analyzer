"""Detect atomic field changes between V1 and V2 product specifications,
then cluster them using the configured grouping rules.

Changes are detected first; grouping is applied second.
C-006 is treated as an unchanged-finding check for F-003 (the field value
did not change, but the finding remains open).
"""

from __future__ import annotations

from . import config
from .models import DetectedChange, ProductSpec


# ===================================================================
# Public API
# ===================================================================

def detect_changes(v1: ProductSpec, v2: ProductSpec) -> list[DetectedChange]:
    """Compare V1 and V2 field-by-field and return atomic changes."""
    changes: list[DetectedChange] = []
    all_keys = sorted(set(v1.fields) | set(v2.fields))

    for key in all_keys:
        v1_field = v1.fields.get(key)
        v2_field = v2.fields.get(key)

        v1_val = v1_field.value if v1_field else "Not present"
        v2_val = v2_field.value if v2_field else "Not present"

        section = (
            v2_field.source_section if v2_field
            else v1_field.source_section if v1_field
            else "Unknown"
        )

        if v1_val == v2_val:
            # Unchanged — only emit if this is an unchanged-finding check
            group = config.CHANGE_GROUPING.get(key)
            if group == "C-006":
                changes.append(DetectedChange(
                    field=key,
                    old_value=v1_val,
                    new_value=v2_val,
                    change_kind="unchanged_finding_check",
                    section=section,
                    related_finding_id=_find_related_finding(key),
                ))
        else:
            changes.append(DetectedChange(
                field=key,
                old_value=v1_val,
                new_value=v2_val,
                change_kind=_classify_change(key, v1_val, v2_val),
                section=section,
                related_finding_id=_find_related_finding(key),
            ))

    return changes


def group_changes(
    changes: list[DetectedChange],
) -> dict[str, list[DetectedChange]]:
    """Cluster atomic changes by their configured change-group ID."""
    groups: dict[str, list[DetectedChange]] = {}
    for change in changes:
        group_id = config.CHANGE_GROUPING.get(change.field, "UNGROUPED")
        groups.setdefault(group_id, []).append(change)
    return groups


# ===================================================================
# Internal helpers
# ===================================================================

def _classify_change(key: str, old_val: str, new_val: str) -> str:
    """Return the change-kind tag for a detected field difference."""
    # Evidence fields
    if key in ("reset_evidence", "final_rf_evidence"):
        old_missing = ("no" in old_val.lower() or "not" in old_val.lower())
        new_present = ("no" not in new_val.lower() and "not" not in new_val.lower())
        if old_missing and new_present:
            return "evidence_added"
        return "unchanged_finding_check"

    # Applicability changes (evidence context shifted, not a simple value swap)
    if key in ("antenna_installation_evidence", "rf_impedance_scope"):
        return "applicability_change"

    return "design_change"


def _find_related_finding(key: str) -> str | None:
    """Return the finding ID whose change-group matches this field, or None."""
    group = config.CHANGE_GROUPING.get(key)
    if group is None:
        return None
    for finding_id, change_id in config.FINDING_CHANGE_MAP.items():
        if group == change_id:
            return finding_id
    return None
