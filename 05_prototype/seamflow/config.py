"""Configuration constants for the Seamflow prototype.

All paths, expected file lists, field-name mappings, change-grouping rules,
and finding-to-change mappings live here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Base data directory: seamflow/config.py → seamflow/ → 05_prototype/ → data/
DATA_DIR = Path(__file__).resolve().parent.parent.parent

# Submission directories
V1_DIR = DATA_DIR / "02_submissions" / "v1"
V2_DIR = DATA_DIR / "02_submissions" / "v2"

# Output directory
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


# ---------------------------------------------------------------------------
# Expected files
# ---------------------------------------------------------------------------

# Files that MUST be present (15 synthetic / structured files)
REQUIRED_FILES = [
    "00_sources/source_manifest.json",
    "01_reference_facts/facts.csv",
    "02_submissions/v1/product_spec.md",
    "02_submissions/v1/power_assessment.md",
    "02_submissions/v1/rf_assessment.md",
    "02_submissions/v1/review_findings.json",
    "02_submissions/v2/product_spec.md",
    "02_submissions/v2/power_assessment.md",
    "02_submissions/v2/rf_assessment.md",
    "02_submissions/v2/review_findings.json",
    "02_submissions/v2/reset_timing_report.md",
    "03_relationships/assessment_dependencies.csv",
    "03_relationships/assessment_registry.csv",
    "04_ground_truth/change_manifest.csv",
    "04_ground_truth/expected_results.csv",
]

# Official Espressif PDFs — download separately (see README.md)
OPTIONAL_REFERENCE_PDFS = [
    "00_sources/official/esp-hardware-design-guidelines-en-master-esp32s3.pdf",
    "00_sources/official/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf",
]


# ---------------------------------------------------------------------------
# Staleness check pairs  (V1 path, V2 path, label)
# ---------------------------------------------------------------------------

STALENESS_CHECK_FILES = [
    ("02_submissions/v1/power_assessment.md",   "02_submissions/v2/power_assessment.md",   "AS-PWR-001"),
    ("02_submissions/v1/rf_assessment.md",      "02_submissions/v2/rf_assessment.md",      "AS-RF-001"),
    ("02_submissions/v1/review_findings.json",  "02_submissions/v2/review_findings.json",  "review_findings.json"),
]


# ---------------------------------------------------------------------------
# Field-name mapping: product-spec table header → internal key
# ---------------------------------------------------------------------------

FIELD_NAME_MAP = {
    "Module":                                    "module_part_number",
    "Antenna":                                   "antenna_type",
    "Flash":                                     "flash",
    "PSRAM":                                     "psram",
    "Module supply voltage at 3V3 pin":          "module_supply",
    "Supply capacity allocated to the module":   "regulator_capacity",
    "Module ambient operating-temperature target": "ambient_temp",
}


# ---------------------------------------------------------------------------
# Change-grouping rules
# Maps each internal field key to a configured change-group ID.
# Atomic field changes are detected first; this table clusters them.
# ---------------------------------------------------------------------------

CHANGE_GROUPING: dict[str, str] = {
    # C-001: Supply voltage and power-path changes
    "module_supply":                "C-001",
    "power_path":                   "C-001",
    "supply_tolerance":             "C-001",
    # C-002: Reset evidence added
    "reset_evidence":               "C-002",
    # C-003: Supply-capacity change
    "regulator_capacity":           "C-003",
    # C-004: Module and antenna configuration
    "module_part_number":           "C-004",
    "antenna_type":                 "C-004",
    "antenna_part_number":          "C-004",
    "antenna_connection":           "C-004",
    "antenna_mounting":             "C-004",
    "antenna_installation_evidence":"C-004",
    "rf_impedance_scope":           "C-004",
    # C-005: Antenna clearance
    "antenna_clearance":            "C-005",
    # C-006: Unchanged-finding check for F-003
    "final_rf_evidence":            "C-006",
}


# ---------------------------------------------------------------------------
# Finding-to-change-group mapping
# ---------------------------------------------------------------------------

FINDING_CHANGE_MAP: dict[str, str] = {
    "F-001": "C-001",
    "F-002": "C-002",
    "F-003": "C-006",
}
