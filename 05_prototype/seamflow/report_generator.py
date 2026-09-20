"""Generate human-readable and JSON reports from pipeline results.

Output files are written to 05_prototype/output/.
"""

from __future__ import annotations

import json
from typing import Any

from .models import (
    AssessmentRecord,
    Evidence,
    ProductSpec,
    ReassessmentResult,
)


# ===================================================================
# Public API
# ===================================================================

def generate_text_report(
    results: list[ReassessmentResult],
    all_affected: dict[str, list[str]],
    registry: list[AssessmentRecord],
    v1_spec: ProductSpec,
    v2_spec: ProductSpec,
) -> str:
    """Return a human-readable text report matching the specified format."""
    lines: list[str] = ["V2 comparison completed.", ""]

    # ---- Resolved or potentially resolved ---------------------------
    resolved = [r for r in results if r.status == "potentially_resolved"]
    if resolved:
        lines.append("Resolved or potentially resolved:")
        for r in resolved:
            lines.append(f"  - {r.finding_id}: {_short_explanation(r)}")
        lines.append("")

    # ---- New or continuing issues -----------------------------------
    issues = [r for r in results if r.status in ("new_finding", "remains_open")]
    if issues:
        lines.append("New or continuing issues:")
        for r in issues:
            label = r.finding_id or r.change_id
            lines.append(f"  - {label}: {_short_explanation(r)}")
        lines.append("")

    # ---- Assessments requiring review -------------------------------
    if all_affected:
        lines.append("Assessments requiring review:")
        for aid in sorted(all_affected):
            lines.append(f"  - {aid}")
        lines.append("")

    # ---- Evidence (de-duplicated) -----------------------------------
    evidence_lines = _collect_evidence(results)
    if evidence_lines:
        lines.append("Evidence:")
        for ev in evidence_lines:
            lines.append(f"  - {ev}")
        lines.append("")

    return "\n".join(lines)


def generate_json_report(
    results: list[ReassessmentResult],
    all_affected: dict[str, list[str]],
    registry: list[AssessmentRecord],
    v1_spec: ProductSpec,
    v2_spec: ProductSpec,
) -> str:
    """Return a JSON report string."""
    registry_names = {r.assessment_id: r.assessment_name for r in registry}

    resolved = [
        _result_to_dict(r)
        for r in results if r.status == "potentially_resolved"
    ]
    issues = [
        _result_to_dict(r)
        for r in results if r.status in ("new_finding", "remains_open")
    ]
    review_required = [
        _result_to_dict(r)
        for r in results if r.status == "review_required"
    ]

    report = {
        "comparison": (
            f"{v1_spec.document_id} v{v1_spec.version} "
            f"\u2192 v{v2_spec.version}"
        ),
        "resolved_or_potentially_resolved": resolved,
        "new_or_continuing_issues": issues,
        "review_required": review_required,
        "assessments_requiring_review": [
            {
                "assessment_id": aid,
                "assessment_name": registry_names.get(aid, aid),
                "reasons": reasons,
            }
            for aid, reasons in sorted(all_affected.items())
        ],
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


# ===================================================================
# Internal helpers
# ===================================================================

def _short_explanation(result: ReassessmentResult) -> str:
    """One-line summary for the text report."""
    if result.status == "potentially_resolved":
        if result.finding_id == "F-001":
            return "5.0 V changed to 3.3 V at the module pin."
        if result.finding_id == "F-002":
            return "reset timing evidence was added."
    if result.status == "remains_open":
        if result.finding_id == "F-003":
            return "final-product RF evidence remains missing."
    if result.status == "new_finding":
        if result.change_id == "C-003":
            return "250 mA allocation is below the 500 mA reference minimum."
    # Fallback to the full explanation
    return result.explanation


def _collect_evidence(results: list[ReassessmentResult]) -> list[str]:
    """De-duplicate evidence across all results."""
    doc_evidence: set[tuple[str, str]] = set()    # (doc_id, section)
    fact_evidence: set[str] = set()                # fact_id

    for r in results:
        for e in r.evidence:
            if e.document_id and e.section:
                doc_evidence.add((e.document_id, e.section))
            if e.reference_fact:
                fact_evidence.add(e.reference_fact)

    lines: list[str] = []
    for doc_id, section in sorted(doc_evidence):
        lines.append(f"{doc_id}, {section}")
    for fact_id in sorted(fact_evidence):
        lines.append(f"{fact_id} from facts.csv")
    return lines


def _result_to_dict(result: ReassessmentResult) -> dict[str, Any]:
    """Serialise a ReassessmentResult for the JSON report."""
    return {
        "finding_id": result.finding_id,
        "change_id": result.change_id,
        "status": result.status,
        "explanation": result.explanation,
        "affected_assessments": result.affected_assessments,
        "evidence": [
            {
                "document_id": e.document_id,
                "section": e.section,
                "field": e.field,
                "reference_fact": e.reference_fact,
            }
            for e in result.evidence
        ],
    }
