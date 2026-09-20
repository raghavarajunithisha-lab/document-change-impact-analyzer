#!/usr/bin/env python3
"""Seamflow Prototype — pipeline entry point.

Usage:  python run.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the prototype package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
from seamflow.report_generator import generate_json_report, generate_text_report
from seamflow.validator import run_all_validations


DIVIDER = "=" * 60
VERIFY_FIELDS = [
    "module_supply",
    "regulator_capacity",
    "module_part_number",
    "antenna_type",
    "antenna_clearance",
    "reset_evidence",
    "final_rf_evidence",
]


def main() -> None:
    data_dir = config.DATA_DIR
    print(f"Data directory: {data_dir}")
    print(DIVIDER)

    # ------------------------------------------------------------------
    # Step 1 — Validate
    # ------------------------------------------------------------------
    print("\n--- Step 1: Structural Validation ---\n")
    validations = run_all_validations(data_dir)
    all_passed = True
    for v in validations:
        tag = "PASS" if v.passed else "FAIL"
        print(f"  {v.check_name}: {tag}")
        for detail in v.details:
            print(f"    {detail}")
        if not v.passed:
            all_passed = False

    if not all_passed:
        print("\nValidation failed. Fix the issues above before continuing.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2 — Parse
    # ------------------------------------------------------------------
    print("\n--- Step 2: Parsing ---\n")
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

    print(f"  V1 spec: {v1_spec.document_id} v{v1_spec.version}"
          f" (Rev {v1_spec.hardware_revision})")
    print(f"  V2 spec: {v2_spec.document_id} v{v2_spec.version}"
          f" (Rev {v2_spec.hardware_revision})")
    print(f"  Reference facts: {len(facts)}")
    print(f"  Existing findings: {len(findings)}")
    print(f"  Dependencies: {len(dependencies)}")
    print(f"  Assessment registry: {len(registry)}")

    # Print the seven key fields for verification
    for label, spec in [("V1", v1_spec), ("V2", v2_spec)]:
        print(f"\n  {label} extracted fields:")
        for key in VERIFY_FIELDS:
            field = spec.fields.get(key)
            print(f"    {key}: {field.value if field else 'NOT EXTRACTED'}")

    # ------------------------------------------------------------------
    # Step 3 — Detect changes
    # ------------------------------------------------------------------
    print("\n--- Step 3: Change Detection ---\n")
    changes = detect_changes(v1_spec, v2_spec)
    cgroups = group_changes(changes)

    print(f"  Atomic changes detected: {len(changes)}")
    print(f"  Change groups: {len(cgroups)}")
    for gid, glist in sorted(cgroups.items()):
        print(f"    {gid}: {len(glist)} field(s)")
        for c in glist:
            print(f"      {c.field}: {c.old_value!r} -> {c.new_value!r}"
                  f"  [{c.change_kind}]")

    # ------------------------------------------------------------------
    # Step 4 — Trace impacts
    # ------------------------------------------------------------------
    print("\n--- Step 4: Impact Tracing ---\n")
    per_group_affected = trace_impacts(cgroups, dependencies)
    all_affected       = get_all_affected(per_group_affected)

    print(f"  Total assessments affected: {len(all_affected)}")
    for aid, reasons in all_affected.items():
        print(f"    {aid}: {len(reasons)} reason(s)")

    # ------------------------------------------------------------------
    # Step 5 — Reassess findings
    # ------------------------------------------------------------------
    print("\n--- Step 5: Finding Reassessment ---\n")
    results = reassess_findings(
        findings, changes, cgroups, v2_spec, facts, per_group_affected,
    )
    for result in results:
        label = result.finding_id or result.change_id
        print(f"  {label}: {result.status}")
        print(f"    {result.explanation}")

    # ------------------------------------------------------------------
    # Step 6 — Generate reports
    # ------------------------------------------------------------------
    print("\n--- Step 6: Report Generation ---\n")
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    text_report = generate_text_report(
        results, all_affected, registry, v1_spec, v2_spec,
    )
    text_path = config.OUTPUT_DIR / "report.txt"
    text_path.write_text(text_report, encoding="utf-8")
    print(f"  Text report: {text_path}")

    json_report = generate_json_report(
        results, all_affected, registry, v1_spec, v2_spec,
    )
    json_path = config.OUTPUT_DIR / "report.json"
    json_path.write_text(json_report, encoding="utf-8")
    print(f"  JSON report: {json_path}")

    # ------------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------------
    print(f"\n{DIVIDER}")
    print(text_report)


if __name__ == "__main__":
    main()
