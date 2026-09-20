"""Reassess every existing finding against the complete V2 state and detect
regressions introduced by the revision.

Three passes:
1. Reassess each existing finding (F-001, F-002, F-003) against the V2 spec.
2. Detect new issues (e.g. the 250 mA regression) by comparing V2 values
   against reference facts.
3. Create review_required results for change groups that don't map to an
   existing finding or regression (e.g. C-004, C-005).
"""

from __future__ import annotations

import re

from . import config
from .models import (
    DetectedChange,
    Evidence,
    Finding,
    ProductSpec,
    ReassessmentResult,
    ReferenceFact,
)


# ===================================================================
# Public API
# ===================================================================

def reassess_findings(
    findings: list[Finding],
    changes: list[DetectedChange],
    change_groups: dict[str, list[DetectedChange]],
    v2_spec: ProductSpec,
    facts: list[ReferenceFact],
    per_group_affected: dict[str, dict[str, list[str]]],
) -> list[ReassessmentResult]:
    """Run all three reassessment passes and return the combined results."""
    results: list[ReassessmentResult] = []
    facts_lookup = {f.fact_id: f for f in facts}
    handled_groups: set[str] = set()

    # --- Pass 1: reassess each existing finding ----------------------
    for finding in findings:
        result = _reassess_single_finding(
            finding, v2_spec, facts_lookup, per_group_affected,
        )
        results.append(result)
        if result.change_id:
            handled_groups.add(result.change_id)

    # --- Pass 2: detect regressions ----------------------------------
    for regression in _detect_regressions(v2_spec, facts_lookup, per_group_affected):
        results.append(regression)
        if regression.change_id:
            handled_groups.add(regression.change_id)

    # --- Pass 3: review_required for remaining groups ----------------
    for group_id, group_changes in change_groups.items():
        if group_id in handled_groups or group_id.startswith("META") or group_id == "UNGROUPED":
            continue
        group_assessments = sorted(per_group_affected.get(group_id, {}).keys())
        if group_assessments:
            field_names = [c.field for c in group_changes]
            results.append(ReassessmentResult(
                finding_id=None,
                change_id=group_id,
                status="review_required",
                explanation=(
                    f"Design changes in {', '.join(field_names)} require "
                    f"assessment review."
                ),
                affected_assessments=group_assessments,
                evidence=[
                    Evidence(
                        document_id=f"{v2_spec.document_id} v{v2_spec.version}",
                        section=c.section,
                        field=c.field,
                    )
                    for c in group_changes
                ],
            ))

    return results


# ===================================================================
# Pass 1 — individual finding reassessment
# ===================================================================

def _reassess_single_finding(
    finding: Finding,
    v2_spec: ProductSpec,
    facts_lookup: dict[str, ReferenceFact],
    per_group_affected: dict[str, dict[str, list[str]]],
) -> ReassessmentResult:
    """Reassess one finding against the complete V2 state."""
    change_id = config.FINDING_CHANGE_MAP.get(finding.finding_id)
    source_fact = facts_lookup.get(finding.source_fact)

    dispatch = {
        "F-001": _reassess_f001,
        "F-002": _reassess_f002,
        "F-003": _reassess_f003,
    }
    handler = dispatch.get(finding.finding_id)
    if handler:
        return handler(finding, change_id, v2_spec, source_fact, per_group_affected)

    # Unknown finding — flag for manual review
    return ReassessmentResult(
        finding_id=finding.finding_id,
        change_id=change_id,
        status="review_required",
        explanation=f"Finding {finding.finding_id} could not be automatically reassessed.",
        affected_assessments=[finding.assessment_id],
    )


# -------------------------------------------------------------------
# F-001  Supply-voltage mismatch (5.0 V vs 3.0 – 3.6 V range)
# -------------------------------------------------------------------

def _reassess_f001(
    finding: Finding,
    change_id: str | None,
    v2_spec: ProductSpec,
    source_fact: ReferenceFact | None,
    per_group_affected: dict[str, dict[str, list[str]]],
) -> ReassessmentResult:
    supply = v2_spec.fields.get("module_supply")
    power  = v2_spec.fields.get("power_path")
    evidence: list[Evidence] = []

    if supply:
        volt_match = re.search(r"([\d.]+)\s*V", supply.value)
        if volt_match:
            v2_voltage = float(volt_match.group(1))
            if 3.0 <= v2_voltage <= 3.6:
                evidence.append(Evidence(
                    document_id=supply.source_document,
                    section=supply.source_section,
                    field="module_supply",
                    reference_fact=finding.source_fact,
                ))
                if power:
                    evidence.append(Evidence(
                        document_id=power.source_document,
                        section=power.source_section,
                        field="power_path",
                    ))
                return ReassessmentResult(
                    finding_id=finding.finding_id,
                    change_id=change_id,
                    status="potentially_resolved",
                    explanation=(
                        f"V2 specifies {v2_voltage} V at the module pin, within "
                        f"the 3.0–3.6 V operating range. F-001 is potentially "
                        f"resolved pending reviewer confirmation."
                    ),
                    affected_assessments=_group_assessments(change_id, per_group_affected, finding.assessment_id),
                    evidence=evidence,
                )

    return ReassessmentResult(
        finding_id=finding.finding_id,
        change_id=change_id,
        status="remains_open",
        explanation="Supply-voltage issue was not addressed in V2.",
        affected_assessments=[finding.assessment_id],
    )


# -------------------------------------------------------------------
# F-002  Missing reset-timing evidence
# -------------------------------------------------------------------

def _reassess_f002(
    finding: Finding,
    change_id: str | None,
    v2_spec: ProductSpec,
    source_fact: ReferenceFact | None,
    per_group_affected: dict[str, dict[str, list[str]]],
) -> ReassessmentResult:
    reset = v2_spec.fields.get("reset_evidence")

    if reset and "AS-RST-" in reset.value:
        return ReassessmentResult(
            finding_id=finding.finding_id,
            change_id=change_id,
            status="potentially_resolved",
            explanation=(
                f"Reset timing evidence ({reset.value}) was added in V2. "
                f"F-002 is potentially resolved pending reviewer confirmation."
            ),
            affected_assessments=_group_assessments(change_id, per_group_affected, finding.assessment_id),
            evidence=[Evidence(
                document_id=reset.source_document,
                section=reset.source_section,
                field="reset_evidence",
                reference_fact=finding.source_fact,
            )],
        )

    return ReassessmentResult(
        finding_id=finding.finding_id,
        change_id=change_id,
        status="remains_open",
        explanation="Reset timing evidence was not provided in V2.",
        affected_assessments=[finding.assessment_id],
    )


# -------------------------------------------------------------------
# F-003  Missing final-product RF validation evidence
# -------------------------------------------------------------------

def _reassess_f003(
    finding: Finding,
    change_id: str | None,
    v2_spec: ProductSpec,
    source_fact: ReferenceFact | None,
    per_group_affected: dict[str, dict[str, list[str]]],
) -> ReassessmentResult:
    rf = v2_spec.fields.get("final_rf_evidence")

    if rf and "no" in rf.value.lower():
        return ReassessmentResult(
            finding_id=finding.finding_id,
            change_id=change_id,
            status="remains_open",
            explanation=(
                "Final-product RF throughput and range evidence remains "
                "missing in V2. F-003 remains open."
            ),
            affected_assessments=_group_assessments(change_id, per_group_affected, finding.assessment_id),
            evidence=[Evidence(
                document_id=rf.source_document,
                section=rf.source_section,
                field="final_rf_evidence",
                reference_fact=finding.source_fact,
            )],
        )

    return ReassessmentResult(
        finding_id=finding.finding_id,
        change_id=change_id,
        status="potentially_resolved",
        explanation="Final-product RF evidence appears to have been added.",
        affected_assessments=[finding.assessment_id],
    )


# ===================================================================
# Pass 2 — regression detection
# ===================================================================

def _detect_regressions(
    v2_spec: ProductSpec,
    facts_lookup: dict[str, ReferenceFact],
    per_group_affected: dict[str, dict[str, list[str]]],
) -> list[ReassessmentResult]:
    """Check V2 values against reference facts for new issues."""
    regressions: list[ReassessmentResult] = []

    # ---- 250 mA vs REF-002 (minimum 0.5 A = 500 mA) ----------------
    capacity = v2_spec.fields.get("regulator_capacity")
    ref_002  = facts_lookup.get("REF-002")

    if capacity and ref_002:
        cap_match = re.search(r"(\d+)\s*mA", capacity.value)
        if cap_match:
            v2_mA = int(cap_match.group(1))
            if v2_mA < 500:
                regressions.append(ReassessmentResult(
                    finding_id=None,
                    change_id="C-003",
                    status="new_finding",
                    explanation=(
                        f"V2 allocates only {v2_mA} mA to the module, below "
                        f"the 500 mA minimum from {ref_002.source_file} "
                        f"section {ref_002.section}. This is a new "
                        f"document-level finding based on {ref_002.fact_id}."
                    ),
                    affected_assessments=_group_assessments("C-003", per_group_affected, "AS-PWR-001"),
                    evidence=[Evidence(
                        document_id=capacity.source_document,
                        section=capacity.source_section,
                        field="regulator_capacity",
                        reference_fact="REF-002",
                    )],
                ))

    return regressions


# ===================================================================
# Helpers
# ===================================================================

def _group_assessments(
    change_id: str | None,
    per_group_affected: dict[str, dict[str, list[str]]],
    fallback: str,
) -> list[str]:
    """Return the assessment IDs affected by a specific change group."""
    if change_id and change_id in per_group_affected:
        ids = sorted(per_group_affected[change_id].keys())
        if ids:
            return ids
    return [fallback]
