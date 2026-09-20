"""Trace the impact of detected changes through the assessment dependency graph.

Input:  change groups + assessment_dependencies.csv + assessment_registry.csv
Output: per-group affected assessments and a global aggregate.

The dependency map (assessment_dependencies.csv) is the source of truth —
affected assessments are never hard-coded.
"""

from __future__ import annotations

from .models import AssessmentDependency, AssessmentRecord, DetectedChange


# ===================================================================
# Public API
# ===================================================================

def trace_impacts(
    change_groups: dict[str, list[DetectedChange]],
    dependencies: list[AssessmentDependency],
) -> dict[str, dict[str, list[str]]]:
    """Trace impacts per change group.

    Returns
    -------
    dict[change_id, dict[assessment_id, list[reason]]]
        For each change group, the set of affected assessments and the
        reasons (from the dependency map) why they are affected.
    """
    # Build lookup:  field → [(assessment_id, reason)]
    dep_lookup: dict[str, list[tuple[str, str]]] = {}
    for dep in dependencies:
        dep_lookup.setdefault(dep.field, []).append(
            (dep.assessment_id, dep.reason)
        )

    result: dict[str, dict[str, list[str]]] = {}

    for group_id, group_changes in change_groups.items():
        group_affected: dict[str, set[str]] = {}
        for change in group_changes:
            for assessment_id, reason in dep_lookup.get(change.field, []):
                group_affected.setdefault(assessment_id, set()).add(reason)
        # Convert sets → sorted lists for stable output
        result[group_id] = {
            aid: sorted(reasons)
            for aid, reasons in sorted(group_affected.items())
        }

    return result


def get_all_affected(
    per_group: dict[str, dict[str, list[str]]],
) -> dict[str, list[str]]:
    """Aggregate all affected assessments across every change group."""
    merged: dict[str, set[str]] = {}
    for _group_id, group_map in per_group.items():
        for assessment_id, reasons in group_map.items():
            merged.setdefault(assessment_id, set()).update(reasons)
    return {aid: sorted(reasons) for aid, reasons in sorted(merged.items())}


def get_assessment_name(
    assessment_id: str,
    registry: list[AssessmentRecord],
) -> str:
    """Look up the human-readable assessment name from the registry."""
    for record in registry:
        if record.assessment_id == assessment_id:
            return record.assessment_name
    return assessment_id
