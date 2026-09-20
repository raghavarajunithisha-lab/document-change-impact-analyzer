"""Domain data classes for the Seamflow prototype.

Evidence is defined before ReassessmentResult to avoid forward-reference
issues without requiring postponed annotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@dataclass
class ReferenceFact:
    """A structured technical fact extracted from an official reference PDF."""
    fact_id: str
    source_file: str
    section: str
    page: str
    statement: str
    type: str
    scope: str
    condition: str


@dataclass
class Finding:
    """A review finding raised against a submission."""
    finding_id: str
    product_id: str
    reviewed_version: str
    assessment_id: str
    status: str
    category: str
    description: str
    source_fact: str
    supporting_fact_ids: list[str] = field(default_factory=list)
    reference: dict = field(default_factory=dict)
    location: str = ""
    evidence_locations: list[str] = field(default_factory=list)
    closure_criteria: str = ""
    review_policy_note: str = ""


# ---------------------------------------------------------------------------
# Parsed product specification
# ---------------------------------------------------------------------------

@dataclass
class ExtractedField:
    """A field value extracted from a product specification, preserving the
    source document, section, and original section text for traceability."""
    key: str
    value: str
    source_document: str
    source_section: str
    source_text: str


@dataclass
class ProductSpec:
    """Parsed representation of a product specification markdown document."""
    document_id: str
    version: str
    hardware_revision: str
    supersedes: Optional[str]
    status: str
    product_id: str
    fields: dict[str, ExtractedField]
    sections: dict[str, str]
    evidence_files: list[str] = field(default_factory=list)
    referenced_facts: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

@dataclass
class DetectedChange:
    """A single atomic field change detected between V1 and V2 specs."""
    field: str
    old_value: str
    new_value: str
    change_kind: str   # design_change | evidence_added | unchanged_finding_check | applicability_change
    section: str
    related_finding_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Evidence and reassessment (Evidence defined first)
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    """A pointer to the document, section, field, and reference fact that
    supports a conclusion."""
    document_id: str
    section: str
    field: Optional[str] = None
    reference_fact: Optional[str] = None


@dataclass
class ReassessmentResult:
    """The outcome of reassessing a finding or evaluating a new issue."""
    finding_id: Optional[str]
    change_id: Optional[str]
    status: str   # potentially_resolved | remains_open | new_finding | review_required
    explanation: str
    affected_assessments: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Relationship data
# ---------------------------------------------------------------------------

@dataclass
class AssessmentDependency:
    """A mapping from a product-spec field to an assessment that depends on it."""
    field: str
    assessment_id: str
    assessment_name: str
    reason: str


@dataclass
class AssessmentRecord:
    """A row from the assessment registry."""
    assessment_id: str
    assessment_name: str
    record_type: str          # existing_document | placeholder
    submission_filename: str
    reviewed_document_version: str
    reviewed_hardware_revision: str
    note: str


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """The result of one structural validation check."""
    check_name: str
    passed: bool
    details: list[str] = field(default_factory=list)
    file_count: Optional[int] = None
    missing_files: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Pipeline aggregate
# ---------------------------------------------------------------------------

@dataclass
class PipelineOutput:
    """Complete output of the Seamflow pipeline."""
    validation_results: list[ValidationResult] = field(default_factory=list)
    detected_changes: list[DetectedChange] = field(default_factory=list)
    reassessment_results: list[ReassessmentResult] = field(default_factory=list)
    affected_assessments: dict[str, list[str]] = field(default_factory=dict)
    v1_spec: Optional[ProductSpec] = None
    v2_spec: Optional[ProductSpec] = None
