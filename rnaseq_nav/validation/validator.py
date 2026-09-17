"""
RNASeq Navigator

Metadata Validation Engine

Version 1.0

Purpose
-------
Validate normalized metadata and generate a structured
quality assessment.
"""

from dataclasses import dataclass, field
from collections import Counter


# ==========================================================
# Validation Issue
# ==========================================================

@dataclass
class ValidationIssue:
    """
    Represents one validation finding.
    """

    severity: str

    section: str

    field: str

    message: str


# ==========================================================
# Validation Result
# ==========================================================

@dataclass
class ValidationResult:
    """
    Result returned by MetadataValidator.
    """

    metadata: object

    issues: list[ValidationIssue] = field(default_factory=list)

    summary: dict = field(default_factory=dict)

    quality_score: float = 100.0


# ==========================================================
# Validator
# ==========================================================

class MetadataValidator:

    def __init__(self):

        self.allowed_layout = {

            "PAIRED",

            "SINGLE",

        }

        self.allowed_strategy = {

            "RNA_SEQ",

            "MRNA_SEQ",

            "NCRNA_SEQ",

            "MIRNA_SEQ",

            "SMRNA_SEQ",

            "AMPLICON",

            "RAD_SEQ",

            "WGS",

            "WXS",

            "ATAC_SEQ",

            "CHIP_SEQ",

        }

    # ------------------------------------------------------

    def validate(self, metadata):

        issues = []

        # --------------------------------------------------
        # Required identifiers
        # --------------------------------------------------

        self._required(

            issues,

            metadata.project.accession,

            "Project",

            "accession",

        )

        self._required(

            issues,

            metadata.study.accession,

            "Study",

            "accession",

        )

        self._required(

            issues,

            metadata.experiment.accession,

            "Experiment",

            "accession",

        )

        self._required(

            issues,

            metadata.run.accession,

            "Run",

            "accession",

        )

        self._required(

            issues,

            metadata.sample.organism,

            "Sample",

            "organism",

        )

        # --------------------------------------------------
        # Strategy
        # --------------------------------------------------

        if metadata.experiment.library_strategy not in self.allowed_strategy:

            issues.append(

                ValidationIssue(

                    severity="WARNING",

                    section="Experiment",

                    field="library_strategy",

                    message=f"Unknown strategy: {metadata.experiment.library_strategy}",

                )

            )

        # --------------------------------------------------
        # Layout
        # --------------------------------------------------

        if metadata.experiment.layout not in self.allowed_layout:

            issues.append(

                ValidationIssue(

                    severity="WARNING",

                    section="Experiment",

                    field="layout",

                    message=f"Unknown layout: {metadata.experiment.layout}",

                )

            )

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        if (
            metadata.run.total_spots is None
            or metadata.run.total_spots <= 0
        ):

            issues.append(

                ValidationIssue(

                    severity="WARNING",

                    section="Run",

                    field="total_spots",

                    message="Sequencing depth unavailable.",

                )

            )

        if (
            metadata.run.total_bases is None
            or metadata.run.total_bases <= 0
        ):

            issues.append(

                ValidationIssue(

                    severity="WARNING",

                    section="Run",

                    field="total_bases",

                    message="Total bases unavailable.",

                )

            )

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------

        summary = self._summary(issues)

        score = self._score(issues)

        return ValidationResult(

            metadata=metadata,

            issues=issues,

            summary=summary,

            quality_score=score,

        )

    # ------------------------------------------------------

    def _required(

        self,

        issues,

        value,

        section,

        field,

    ):

        if value is None:

            value = ""

        if str(value).strip() == "":

            issues.append(

                ValidationIssue(

                    severity="ERROR",

                    section=section,

                    field=field,

                    message="Required field missing.",

                )

            )

    # ------------------------------------------------------

    def _summary(self, issues):

        severity = Counter()

        section = Counter()

        for issue in issues:

            severity[issue.severity] += 1

            section[issue.section] += 1

        return {

            "total_issues": len(issues),

            "by_severity": dict(severity),

            "by_section": dict(section),

        }

    # ------------------------------------------------------

    def _score(self, issues):

        score = 100

        for issue in issues:

            if issue.severity == "ERROR":

                score -= 10

            elif issue.severity == "WARNING":

                score -= 2

            else:

                score -= 1

        return max(score, 0)
