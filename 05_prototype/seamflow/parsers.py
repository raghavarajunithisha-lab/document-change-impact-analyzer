"""Parsers for product specifications, reference facts, findings,
assessment dependencies, and the assessment registry.

Every extracted field stores the original section text and source location
so that downstream modules can trace evidence back to the document.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Optional

from . import config
from .models import (
    AssessmentDependency,
    AssessmentRecord,
    ExtractedField,
    Finding,
    ProductSpec,
    ReferenceFact,
)


# ===================================================================
# Product-specification parser
# ===================================================================

def parse_product_spec(filepath: Path) -> ProductSpec:
    """Parse a product-specification markdown file into a ProductSpec."""
    text = filepath.read_text(encoding="utf-8")

    doc_id  = _extract_metadata(text, "Document ID") or ""
    version = _extract_metadata(text, "Version") or ""

    sections    = _split_sections(text)
    table_fields = _parse_component_table(
        sections.get("Component Selection", ""), doc_id, version
    )
    text_fields = _extract_text_fields(sections, doc_id, version)

    # Merge: table fields first, then text-derived fields
    all_fields: dict[str, ExtractedField] = {}
    all_fields.update(table_fields)
    all_fields.update(text_fields)

    return ProductSpec(
        document_id=doc_id,
        version=version,
        hardware_revision=_extract_metadata(text, "Hardware revision") or "",
        supersedes=_extract_metadata(text, "Supersedes"),
        status=_extract_metadata(text, "Status") or "",
        product_id=_extract_metadata(text, "Product ID") or "",
        fields=all_fields,
        sections=sections,
        evidence_files=_extract_evidence_files(sections),
        referenced_facts=_extract_referenced_facts(text),
    )


# -------------------------------------------------------------------
# Metadata helpers
# -------------------------------------------------------------------

def _extract_metadata(text: str, key: str) -> Optional[str]:
    """Extract a metadata value from the header bullet list."""
    pattern = rf"^-\s*{re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _split_sections(text: str) -> dict[str, str]:
    """Split markdown into sections by ``## `` headings."""
    sections: dict[str, str] = {}
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    for part in parts[1:]:          # skip the preamble
        lines = part.split("\n", 1)
        name = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections[name] = body
    return sections


# -------------------------------------------------------------------
# Component Selection table
# -------------------------------------------------------------------

def _parse_component_table(
    section_text: str, doc_id: str, version: str
) -> dict[str, ExtractedField]:
    """Parse the Component Selection markdown table."""
    fields: dict[str, ExtractedField] = {}
    for line in section_text.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "---" in line:
            continue

        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]        # drop empty from leading/trailing |

        if len(cells) < 2:
            continue
        table_key, value = cells[0], cells[1]
        if table_key == "Field":               # header row
            continue

        internal_key = config.FIELD_NAME_MAP.get(table_key)
        if internal_key:
            fields[internal_key] = ExtractedField(
                key=internal_key,
                value=value,
                source_document=f"{doc_id} v{version}",
                source_section="Component Selection",
                source_text=line,
            )
    return fields


# -------------------------------------------------------------------
# Text-field extraction from free-text sections
# -------------------------------------------------------------------

def _extract_text_fields(
    sections: dict[str, str], doc_id: str, version: str
) -> dict[str, ExtractedField]:
    """Extract structured fields from free-text sections."""
    fields: dict[str, ExtractedField] = {}
    doc_ref = f"{doc_id} v{version}"

    # ---- Power Design ------------------------------------------------
    power = sections.get("Power Design", "")
    if power:
        fields["power_path"] = _make_field(
            "power_path",
            _extract_power_path(power),
            doc_ref, "Power Design", power,
        )
        fields["supply_tolerance"] = _make_field(
            "supply_tolerance",
            _extract_supply_tolerance(power),
            doc_ref, "Power Design", power,
        )

    # ---- Reset -------------------------------------------------------
    reset = sections.get("Reset", "")
    if reset:
        fields["reset_evidence"] = _make_field(
            "reset_evidence",
            _extract_reset_evidence(reset),
            doc_ref, "Reset", reset,
        )

    # ---- Antenna and Enclosure ---------------------------------------
    antenna = sections.get("Antenna and Enclosure", "")
    if antenna:
        fields["antenna_part_number"] = _make_field(
            "antenna_part_number",
            _extract_antenna_part(antenna),
            doc_ref, "Antenna and Enclosure", antenna,
        )
        fields["antenna_connection"] = _make_field(
            "antenna_connection",
            _extract_antenna_connection(antenna),
            doc_ref, "Antenna and Enclosure", antenna,
        )
        fields["antenna_clearance"] = _make_field(
            "antenna_clearance",
            _extract_antenna_clearance(antenna),
            doc_ref, "Antenna and Enclosure", antenna,
        )
        fields["antenna_mounting"] = _make_field(
            "antenna_mounting",
            _extract_antenna_mounting(antenna),
            doc_ref, "Antenna and Enclosure", antenna,
        )
        fields["antenna_installation_evidence"] = _make_field(
            "antenna_installation_evidence",
            _extract_antenna_installation_evidence(antenna),
            doc_ref, "Antenna and Enclosure", antenna,
        )
        fields["rf_impedance_scope"] = _make_field(
            "rf_impedance_scope",
            _extract_rf_impedance_scope(antenna),
            doc_ref, "Antenna and Enclosure", antenna,
        )

    # ---- Submitted Evidence ------------------------------------------
    evidence_sec = sections.get("Submitted Evidence", "")
    if evidence_sec:
        fields["final_rf_evidence"] = _make_field(
            "final_rf_evidence",
            _extract_final_rf_evidence(evidence_sec),
            doc_ref, "Submitted Evidence", evidence_sec,
        )

    return fields


# -------------------------------------------------------------------
# Individual extraction functions
# -------------------------------------------------------------------

def _extract_power_path(text: str) -> str:
    low = text.lower()
    # V2 explicitly states a regulator was added
    if "adds a regulator" in low or "regulated to" in low:
        return "5.0 V input regulated to 3.3 V before module pin"
    # V1 explicitly states no regulator and direct connection
    if "directly" in low or "no intermediate" in low:
        return "5.0 V input directly connected to module pin"
    return "Unknown power path"


def _extract_supply_tolerance(text: str) -> str:
    match = re.search(r"tolerance of \+/-(\d+) percent", text)
    if match:
        return f"+/-{match.group(1)} percent"
    return "Not specified"


def _extract_reset_evidence(text: str) -> str:
    match = re.search(r"(AS-RST-\d+\s+v[\d.]+)", text)
    if match:
        return match.group(1)
    if "not been provided" in text.lower() or "have not been" in text.lower():
        return "No startup/reset timing report"
    return "Unknown"


def _extract_antenna_part(text: str) -> str:
    match = re.search(r"(AS-ANT-\d+)", text)
    if match:
        return f"Fictional {match.group(1)}"
    return "Integrated module antenna; no separate antenna part"


def _extract_antenna_connection(text: str) -> str:
    low = text.lower()
    if "external antenna connector" in low or "module connector" in low:
        return "Module connector and coaxial cable; no host RF feed trace"
    if "no external antenna" in low or ("integrated" in low and "no" in low):
        return "Integrated antenna; no external connector or cable"
    return "Unknown"


def _extract_antenna_clearance(text: str) -> str:
    match = re.search(r"(?:at least|minimum)\s+(\d+)\s*mm", text)
    if match:
        return f"{match.group(1)} mm"
    return "Not specified"


def _extract_antenna_mounting(text: str) -> str:
    low = text.lower()
    if "external antenna" in low and ("mounting" in low or "geometry" in low):
        return "External antenna mounting geometry inside plastic enclosure"
    if "integrated pcb antenna" in low and ("edge" in low or "beyond" in low):
        return "Integrated PCB antenna extends beyond host-board edge"
    return "Unknown"


def _extract_antenna_installation_evidence(text: str) -> str:
    low = text.lower()
    if "installation guide" in low and "not supplied" in low:
        return "External antenna guide and gain/integration evidence missing"
    if "no external antenna" in low:
        return "Separate external antenna guide not applicable"
    return "Unknown"


def _extract_rf_impedance_scope(text: str) -> str:
    low = text.lower()
    if "internal radio design" in low or "module's internal" in low:
        return "50 ohm internal module RF-path reference"
    if "external" in low and ("feed" in low or "antenna" in low) and "50" in text:
        return "50 ohm external antenna feed claim"
    return "Unknown"


def _extract_final_rf_evidence(text: str) -> str:
    low = text.lower()
    # Explicit denial: "no final-product throughput …" or "no … throughput … range"
    if ("no final-product throughput" in low
            or ("no" in low and "throughput" in low and "range" in low)):
        return "No final-product throughput/range report"
    # Positive evidence: section explicitly mentions a throughput/range report
    if "throughput" in low or "range report" in low or "range test" in low:
        return "Final-product RF evidence present"
    # Neither positive nor explicit denial — evidence is absent
    return "No final-product throughput/range report"


# -------------------------------------------------------------------
# Utility helpers
# -------------------------------------------------------------------

def _make_field(
    key: str, value: str,
    doc_ref: str, section: str, source_text: str,
) -> ExtractedField:
    return ExtractedField(
        key=key,
        value=value,
        source_document=doc_ref,
        source_section=section,
        source_text=source_text,
    )


def _extract_evidence_files(sections: dict[str, str]) -> list[str]:
    """Extract evidence-file references from the Submitted Evidence section."""
    evidence = sections.get("Submitted Evidence", "")
    return sorted(set(re.findall(r"(\w+(?:_\w+)*\.(?:md|json))", evidence)))


def _extract_referenced_facts(text: str) -> list[str]:
    """Extract REF-xxx IDs from the full document text."""
    return sorted(set(re.findall(r"REF-\d{3}", text)))


# ===================================================================
# CSV / JSON parsers
# ===================================================================

def parse_facts(filepath: Path) -> list[ReferenceFact]:
    """Parse facts.csv."""
    facts: list[ReferenceFact] = []
    with open(filepath, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            facts.append(ReferenceFact(
                fact_id=row["fact_id"],
                source_file=row["source_file"],
                section=row["section"],
                page=row["page"],
                statement=row["statement"],
                type=row["type"],
                scope=row["scope"],
                condition=row["condition"],
            ))
    return facts


def parse_findings(filepath: Path) -> list[Finding]:
    """Parse review_findings.json."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    findings: list[Finding] = []
    for item in data:
        findings.append(Finding(
            finding_id=item["finding_id"],
            product_id=item["product_id"],
            reviewed_version=item["reviewed_version"],
            assessment_id=item["assessment_id"],
            status=item["status"],
            category=item["category"],
            description=item["description"],
            source_fact=item["source_fact"],
            supporting_fact_ids=item.get("supporting_fact_ids", []),
            reference=item.get("reference", {}),
            location=item.get("location", ""),
            evidence_locations=item.get("evidence_locations", []),
            closure_criteria=item.get("closure_criteria", ""),
            review_policy_note=item.get("review_policy_note", ""),
        ))
    return findings


def parse_dependencies(filepath: Path) -> list[AssessmentDependency]:
    """Parse assessment_dependencies.csv."""
    deps: list[AssessmentDependency] = []
    with open(filepath, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            deps.append(AssessmentDependency(
                field=row["field"],
                assessment_id=row["assessment_id"],
                assessment_name=row["assessment_name"],
                reason=row["reason"],
            ))
    return deps


def parse_registry(filepath: Path) -> list[AssessmentRecord]:
    """Parse assessment_registry.csv."""
    records: list[AssessmentRecord] = []
    with open(filepath, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            records.append(AssessmentRecord(
                assessment_id=row["assessment_id"],
                assessment_name=row["assessment_name"],
                record_type=row["record_type"],
                submission_filename=row.get("submission_filename", ""),
                reviewed_document_version=row.get("reviewed_document_version", ""),
                reviewed_hardware_revision=row.get("reviewed_hardware_revision", ""),
                note=row.get("note", ""),
            ))
    return records
