#!/usr/bin/env python3
"""Validate pipeline output against ground-truth data.

Ground-truth files (change_manifest.csv, expected_results.csv) are used
ONLY here in the test module — never as normal pipeline input.

Usage:  python -m unittest discover tests       (from 05_prototype/)
        python -m unittest tests.test_pipeline   (from 05_prototype/)
        python tests/test_pipeline.py
"""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

# Ensure the prototype package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seamflow import config
from seamflow.change_detector import detect_changes, group_changes
from seamflow.finding_reassessor import reassess_findings
from seamflow.impact_tracer import get_all_affected, trace_impacts
from seamflow.parsers import (
    parse_dependencies,
    parse_facts,
    parse_findings,
    parse_product_spec,
    parse_registry,
)


# ===================================================================
# Ground-truth loader
# ===================================================================

def _load_expected_results(data_dir: Path) -> list[dict[str, object]]:
    """Load expected_results.csv (ground truth for test only)."""
    rows: list[dict[str, object]] = []
    path = data_dir / "04_ground_truth" / "expected_results.csv"
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "change_id": row["change_id"],
                "expected_status": row["expected_status"],
                "affected_assessments": sorted(
                    a.strip() for a in row["affected_assessments"].split(";")
                ),
            })
    return rows


# ===================================================================
# Shared pipeline fixture — runs once per module
# ===================================================================

def _run_pipeline():
    """Execute the full pipeline and return the objects needed by tests."""
    data_dir = config.DATA_DIR

    v1_spec = parse_product_spec(config.V1_DIR / "product_spec.md")
    v2_spec = parse_product_spec(config.V2_DIR / "product_spec.md")
    facts   = parse_facts(data_dir / "01_reference_facts" / "facts.csv")
    findings = parse_findings(
        data_dir / "02_submissions" / "v1" / "review_findings.json"
    )
    dependencies = parse_dependencies(
        data_dir / "03_relationships" / "assessment_dependencies.csv"
    )
    registry = parse_registry(
        data_dir / "03_relationships" / "assessment_registry.csv"
    )

    changes = detect_changes(v1_spec, v2_spec)
    cgroups = group_changes(changes)
    per_group_affected = trace_impacts(cgroups, dependencies)
    all_affected = get_all_affected(per_group_affected)

    results = reassess_findings(
        findings, changes, cgroups, v2_spec, facts, per_group_affected,
    )

    return {
        "v1_spec": v1_spec,
        "v2_spec": v2_spec,
        "facts": facts,
        "findings": findings,
        "changes": changes,
        "cgroups": cgroups,
        "per_group_affected": per_group_affected,
        "all_affected": all_affected,
        "results": results,
        "expected": _load_expected_results(data_dir),
    }


# Module-level cache so the pipeline runs only once across all tests
_PIPELINE = None

def _get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = _run_pipeline()
    return _PIPELINE


# ===================================================================
# Helpers
# ===================================================================

def _find_matching_result(change_id, results):
    """Locate the ReassessmentResult that corresponds to a change_id."""
    for r in results:
        if r.change_id == change_id:
            return r
    for finding_id, mapped_cid in config.FINDING_CHANGE_MAP.items():
        if mapped_cid == change_id:
            for r in results:
                if r.finding_id == finding_id:
                    return r
    return None


def _status_matches(matching, exp_status: str, actual_assessments: list[str]) -> bool:
    """Return True if the pipeline's status matches the ground truth."""
    if matching:
        if "potentially resolved" in exp_status and matching.status == "potentially_resolved":
            return True
        if "new finding" in exp_status and matching.status == "new_finding":
            return True
        if "remains open" in exp_status and matching.status == "remains_open":
            return True
        if "review required" in exp_status and matching.status == "review_required":
            return True
    if "review required" in exp_status and actual_assessments:
        return True
    return False


# ===================================================================
# Test cases
# ===================================================================

class TestGroundTruth(unittest.TestCase):
    """One test method per expected-results row (C-001 … C-006)."""

    def _check_change(self, change_id: str) -> None:
        """Shared assertion logic for a single change-group row."""
        p = _get_pipeline()
        exp_row = next(
            e for e in p["expected"] if e["change_id"] == change_id
        )
        exp_status: str = exp_row["expected_status"]            # type: ignore[assignment]
        exp_assessments: list[str] = exp_row["affected_assessments"]  # type: ignore[assignment]

        matching = _find_matching_result(change_id, p["results"])
        actual_assessments = sorted(
            p["per_group_affected"].get(change_id, {}).keys()
        )

        actual_label = matching.status if matching else "(no result)"
        self.assertTrue(
            _status_matches(matching, exp_status, actual_assessments),
            f"{change_id} status mismatch: expected '{exp_status}', "
            f"got '{actual_label}'",
        )
        self.assertEqual(
            actual_assessments,
            exp_assessments,
            f"{change_id} assessments mismatch",
        )

    # --- Individual test methods ---

    def test_c001_supply_voltage_resolved(self):
        """C-001: F-001 potentially resolved (5.0 V → 3.3 V)."""
        self._check_change("C-001")

    def test_c002_reset_evidence_resolved(self):
        """C-002: F-002 potentially resolved (timing evidence added)."""
        self._check_change("C-002")

    def test_c003_capacity_regression(self):
        """C-003: new finding (250 mA below 500 mA minimum)."""
        self._check_change("C-003")

    def test_c004_module_antenna_review(self):
        """C-004: review required (module + antenna configuration change)."""
        self._check_change("C-004")

    def test_c005_clearance_review(self):
        """C-005: review required (antenna clearance change)."""
        self._check_change("C-005")

    def test_c006_rf_evidence_remains_open(self):
        """C-006: F-003 remains open (RF validation still missing)."""
        self._check_change("C-006")


if __name__ == "__main__":
    unittest.main()
