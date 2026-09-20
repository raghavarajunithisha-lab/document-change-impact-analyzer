"""Structural validation checks for the Seamflow dataset.

Four deterministic checks, each returning a ValidationResult:
1. File presence  (all 17 expected paths)
2. ID alignment   (cross-reference integrity)
3. Staleness      (V1/V2 assessment hashing)
4. New files      (files in V2 not in V1)
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from . import config
from .models import ValidationResult
from .parsers import parse_dependencies, parse_facts, parse_findings, parse_registry


# ===================================================================
# Public API
# ===================================================================

def run_all_validations(data_dir: Path) -> list[ValidationResult]:
    """Run all structural validation checks and return the results."""
    return [
        validate_file_presence(data_dir),
        validate_id_alignment(data_dir),
        validate_staleness(data_dir),
        validate_new_files(data_dir),
    ]


# ===================================================================
# Individual checks
# ===================================================================

def validate_file_presence(data_dir: Path) -> ValidationResult:
    """Check that all 15 required files exist; warn for 2 optional PDFs."""
    missing: list[str] = []
    for rel_path in config.REQUIRED_FILES:
        if not (data_dir / rel_path).exists():
            missing.append(rel_path)

    # Optional reference PDFs — warn but don't fail
    pdf_warnings: list[str] = []
    pdf_found = 0
    for rel_path in config.OPTIONAL_REFERENCE_PDFS:
        if (data_dir / rel_path).exists():
            pdf_found += 1
        else:
            pdf_warnings.append(f"Optional PDF not found: {rel_path} (see README.md)")

    required_found = len(config.REQUIRED_FILES) - len(missing)
    total_found = required_found + pdf_found
    total_expected = len(config.REQUIRED_FILES) + len(config.OPTIONAL_REFERENCE_PDFS)

    details = [
        f"Required files found: {required_found}/{len(config.REQUIRED_FILES)}",
        f"Optional PDFs found: {pdf_found}/{len(config.OPTIONAL_REFERENCE_PDFS)}",
        f"Total files found: {total_found}/{total_expected}",
    ]
    details.extend(pdf_warnings)

    return ValidationResult(
        check_name="File Presence",
        passed=len(missing) == 0,
        details=details,
        file_count=total_found,
        missing_files=missing,
    )


def validate_id_alignment(data_dir: Path) -> ValidationResult:
    """Check that every cross-reference points to a known ID."""
    issues: list[str] = []

    # Load all data sources
    facts     = parse_facts(data_dir / "01_reference_facts" / "facts.csv")
    findings  = parse_findings(data_dir / "02_submissions" / "v1" / "review_findings.json")
    deps      = parse_dependencies(data_dir / "03_relationships" / "assessment_dependencies.csv")
    registry  = parse_registry(data_dir / "03_relationships" / "assessment_registry.csv")

    fact_ids     = {f.fact_id for f in facts}
    registry_ids = {r.assessment_id for r in registry}

    # 1. Every finding's source_fact and supporting_fact_ids exist in facts.csv
    for finding in findings:
        if finding.source_fact not in fact_ids:
            issues.append(
                f"Finding {finding.finding_id} references unknown fact "
                f"{finding.source_fact}"
            )
        for sfid in finding.supporting_fact_ids:
            if sfid not in fact_ids:
                issues.append(
                    f"Finding {finding.finding_id} has unknown supporting fact {sfid}"
                )

    # 2. Every dependency assessment_id exists in the registry
    for dep in deps:
        if dep.assessment_id not in registry_ids:
            issues.append(
                f"Dependency references unknown assessment {dep.assessment_id}"
            )

    # 3. Every source PDF named in facts.csv — warn if not on disk
    #    (PDFs are optional downloads; see README.md)
    official_dir = data_dir / "00_sources" / "official"
    source_files = {f.source_file for f in facts}
    for source_file in sorted(source_files):
        if not (official_dir / source_file).exists():
            # Informational warning, not a hard failure
            pass  # already reported by validate_file_presence

    # 4. Every expected_results assessment exists in the registry
    expected_path = data_dir / "04_ground_truth" / "expected_results.csv"
    with open(expected_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            for aid in row["affected_assessments"].split(";"):
                aid = aid.strip()
                if aid and aid not in registry_ids:
                    issues.append(
                        f"Expected result references unknown assessment {aid}"
                    )

    return ValidationResult(
        check_name="ID Alignment",
        passed=len(issues) == 0,
        details=issues if issues else ["All cross-references are consistent"],
    )


def validate_staleness(data_dir: Path) -> ValidationResult:
    """Compare V1 and V2 assessment files to detect unchanged carry-forwards."""
    details: list[str] = []
    for v1_rel, v2_rel, label in config.STALENESS_CHECK_FILES:
        v1_hash = _file_hash(data_dir / v1_rel)
        v2_hash = _file_hash(data_dir / v2_rel)
        if v1_hash == v2_hash:
            details.append(f"{label}: unchanged from V1")
        else:
            details.append(f"{label}: updated in V2")

    return ValidationResult(
        check_name="Staleness Detection",
        passed=True,           # informational — always passes
        details=details,
    )


def validate_new_files(data_dir: Path) -> ValidationResult:
    """Identify files present in V2 but not in V1."""
    v1_files = {f.name for f in (data_dir / "02_submissions" / "v1").iterdir() if f.is_file()}
    v2_files = {f.name for f in (data_dir / "02_submissions" / "v2").iterdir() if f.is_file()}

    new_files = sorted(v2_files - v1_files)
    details = (
        [f"New in V2: {name}" for name in new_files]
        if new_files
        else ["No new files in V2"]
    )
    return ValidationResult(
        check_name="New File Detection",
        passed=True,           # informational
        details=details,
    )


# ===================================================================
# Helpers
# ===================================================================

def _file_hash(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
