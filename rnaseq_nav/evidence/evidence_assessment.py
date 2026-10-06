"""
Evidence assessment layer.

This module does not infer biological meaning and does not modify Scout's
existing intelligence layers. It provides a small, machine-readable
representation of the evidentiary status of an already-generated result.

The purpose is evaluation, benchmarking, provenance reporting, and
distinguishing:

    observed repository evidence
    repository evidence not established
    publication-resolved information
    unresolved information

Absence of repository evidence is never interpreted as biological absence.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class EvidenceStatus(str, Enum):
    OBSERVED = "observed"
    NOT_ESTABLISHED = "not_established"
    PUBLICATION_RESOLVED = "publication_resolved"
    LINKED_RECORD_RESOLVED = "linked_record_resolved"
    UNRESOLVED = "unresolved"


class EvidenceSource(str, Enum):
    REPOSITORY = "repository"
    LINKED_RECORD = "linked_record"
    PUBLICATION = "publication"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceAssessment:
    field: str
    value: Any = None
    status: EvidenceStatus = EvidenceStatus.UNRESOLVED
    source: EvidenceSource = EvidenceSource.UNKNOWN
    reason_code: str = ""
    provenance: list[str] = field(default_factory=list)

    @property
    def established(self) -> bool:
        return self.status in {
            EvidenceStatus.OBSERVED,
            EvidenceStatus.PUBLICATION_RESOLVED,
            EvidenceStatus.LINKED_RECORD_RESOLVED,
        }


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)

    return True


def _contains_not_established(value: Any) -> bool:
    text = _clean(value).lower()

    markers = (
        "could not be established",
        "not established",
        "insufficient information",
        "insufficient evidence",
        "unknown",
        "not available",
        "unresolved",
    )

    return any(marker in text for marker in markers)


def assess_field(
    field: str,
    value: Any,
    *,
    source: EvidenceSource = EvidenceSource.REPOSITORY,
    provenance: Iterable[str] = (),
) -> EvidenceAssessment:
    """
    Assess an already-generated field without changing its interpretation.

    This function deliberately does not attempt semantic inference.
    """
    provenance = list(provenance)

    if _contains_not_established(value):
        return EvidenceAssessment(
            field=field,
            value=value,
            status=EvidenceStatus.NOT_ESTABLISHED,
            source=source,
            reason_code="EXPLICITLY_NOT_ESTABLISHED",
            provenance=provenance,
        )

    if _has_value(value):
        return EvidenceAssessment(
            field=field,
            value=value,
            status=EvidenceStatus.OBSERVED,
            source=source,
            reason_code="VALUE_PRESENT",
            provenance=provenance,
        )

    return EvidenceAssessment(
        field=field,
        value=value,
        status=EvidenceStatus.UNRESOLVED,
        source=EvidenceSource.UNKNOWN,
        reason_code="NO_ESTABLISHED_VALUE",
        provenance=provenance,
    )


def assess_design_insight(design_insight: Any) -> list[EvidenceAssessment]:
    """
    Convert the existing ExperimentalDesignInsight into field-level
    evidence assessments.

    No new biological inference is performed.
    """
    if design_insight is None:
        return []

    fields = (
        "condition",
        "control",
        "treatment",
        "time_point",
        "replicate_information",
        "design_description",
    )

    assessments = []

    for name in fields:
        value = getattr(design_insight, name, None)

        if _contains_not_established(value):
            reason = "EXPLICITLY_NOT_ESTABLISHED"
            status = EvidenceStatus.NOT_ESTABLISHED
            source = EvidenceSource.REPOSITORY
        elif _has_value(value):
            reason = "DESIGN_INTELLIGENCE_VALUE"
            status = EvidenceStatus.OBSERVED
            source = EvidenceSource.REPOSITORY
        else:
            reason = "NO_ESTABLISHED_VALUE"
            status = EvidenceStatus.UNRESOLVED
            source = EvidenceSource.UNKNOWN

        assessments.append(
            EvidenceAssessment(
                field=name,
                value=value,
                status=status,
                source=source,
                reason_code=reason,
                provenance=["design_intelligence"],
            )
        )

    return assessments


def assess_reanalysis_readiness(readiness: Any) -> list[EvidenceAssessment]:
    """
    Preserve the existing reanalysis-readiness evidence categories
    as benchmarkable evidence records.
    """
    if readiness is None:
        return []

    assessments = []

    observed = getattr(readiness, "observed_evidence", []) or []
    not_established = getattr(readiness, "not_established", []) or []
    missing = getattr(readiness, "missing_information", []) or []

    for item in observed:
        assessments.append(
            EvidenceAssessment(
                field="reanalysis",
                value=item,
                status=EvidenceStatus.OBSERVED,
                source=EvidenceSource.REPOSITORY,
                reason_code="OBSERVED_EVIDENCE",
                provenance=["reanalysis_readiness"],
            )
        )

    for item in not_established:
        assessments.append(
            EvidenceAssessment(
                field="reanalysis",
                value=item,
                status=EvidenceStatus.NOT_ESTABLISHED,
                source=EvidenceSource.REPOSITORY,
                reason_code="NOT_ESTABLISHED",
                provenance=["reanalysis_readiness"],
            )
        )

    for item in missing:
        assessments.append(
            EvidenceAssessment(
                field="reanalysis",
                value=item,
                status=EvidenceStatus.NOT_ESTABLISHED,
                source=EvidenceSource.REPOSITORY,
                reason_code="MISSING_INFORMATION",
                provenance=["reanalysis_readiness"],
            )
        )

    return assessments


def summarize_assessments(
    assessments: Iterable[EvidenceAssessment],
) -> dict[str, int]:
    """
    Return machine-readable counts suitable for benchmark tables.
    """
    summary = {
        status.value: 0
        for status in EvidenceStatus
    }

    for assessment in assessments:
        summary[assessment.status.value] += 1

    summary["total"] = len(list(assessments)) if not isinstance(
        assessments, list
    ) else len(assessments)

    return summary


def assess_inspection_result(result: Any) -> list[EvidenceAssessment]:
    """
    Build a non-invasive evidence assessment from an InspectionResult.

    The original result is never modified.
    """
    if result is None:
        return []

    assessments = []

    design = getattr(result, "design_insight", None)
    assessments.extend(assess_design_insight(design))

    readiness = getattr(result, "reanalysis_readiness", None)
    assessments.extend(assess_reanalysis_readiness(readiness))

    return assessments
