"""
RNASeq Navigator

Core Result Objects

Version: 1.3

Defines the standard result objects returned by the
public RNASeqNavigator API.
"""

from dataclasses import dataclass, field
from typing import Optional

from rnaseq_nav.models import (
    Metadata,
    StudyExperiment,
    StudyExperimentalLandscape,
)

from rnaseq_nav.intelligence.report import (
    DatasetReport,
)

from rnaseq_nav.intelligence.metadata_intelligence import (
    MetadataInsight,
)

from rnaseq_nav.intelligence.modality_intelligence import (
    ModalityInsight,
)

from rnaseq_nav.intelligence.design_intelligence import (
    ExperimentalDesignInsight,
)

from rnaseq_nav.intelligence.study_biosample_evidence import (
    StudyBioSampleEvidence,
)

from rnaseq_nav.intelligence.suitability import (
    SuitabilityInsight,
)

from rnaseq_nav.intelligence.reanalysis_readiness import (
    ReanalysisReadinessInsight,
)

from rnaseq_nav.intelligence.analysis_planner import (
    AnalysisPlan,
)

from rnaseq_nav.normalization.normalizer import (
    NormalizationResult,
)

from rnaseq_nav.validation.validator import (
    ValidationResult,
)


# ==========================================================
# Experiment at a Glance
# ==========================================================

@dataclass
class ExperimentAtGlance:
    """
    Study-level summary for rapid understanding of an
    SRA experiment collection.

    This object describes retrieved study information.
    Experimental control/treatment interpretation remains
    the responsibility of ExperimentalDesignInsight.
    """

    study_title: str = ""
    study_description: str = ""

    unique_sample_count: int = 0
    unique_biosample_count: int = 0
    experiment_count: int = 0
    run_count: int = 0

    study_experiments: list[StudyExperiment] = field(default_factory=list)


# ==========================================================
# Inspection Result
# ==========================================================

@dataclass
class InspectionResult:
    """
    Complete result returned by
    RNASeqNavigator.inspect().
    """

    # ------------------------------------------------------
    # Basic inspection status
    # ------------------------------------------------------

    success: bool = True

    accession: str = ""

    # ------------------------------------------------------
    # Core metadata
    # ------------------------------------------------------

    metadata: Optional[Metadata] = None

    # ------------------------------------------------------
    # Experiment at a Glance
    # ------------------------------------------------------

    experiment_at_glance: Optional[
        ExperimentAtGlance
    ] = None

    # ------------------------------------------------------
    # Study Experimental Landscape
    # ------------------------------------------------------

    study_experimental_landscape: Optional[
        StudyExperimentalLandscape
    ] = None

    # ------------------------------------------------------
    # Study BioSample Evidence
    # ------------------------------------------------------

    study_biosample_evidence: Optional[
        StudyBioSampleEvidence
    ] = None

    # ------------------------------------------------------
    # Layer 1 — Metadata Intelligence
    # ------------------------------------------------------

    metadata_insight: Optional[
        MetadataInsight
    ] = None

    # ------------------------------------------------------
    # Layer 1.5 — Modality / Workflow Intelligence
    # ------------------------------------------------------

    modality_insight: Optional[
        ModalityInsight
    ] = None

    # ------------------------------------------------------
    # Layer 2 — Experimental Design Intelligence
    # ------------------------------------------------------

    design_insight: Optional[
        ExperimentalDesignInsight
    ] = None

    # ------------------------------------------------------
    # Layer 3 — Dataset Suitability
    # ------------------------------------------------------

    suitability_insight: Optional[
        SuitabilityInsight
    ] = None

    # ------------------------------------------------------
    # Layer 3.5 — Reanalysis Readiness
    # ------------------------------------------------------

    reanalysis_readiness: Optional[
        ReanalysisReadinessInsight
    ] = None

    # ------------------------------------------------------
    # Layer 4 — Analysis Planning
    # ------------------------------------------------------

    analysis_plan: Optional[
        AnalysisPlan
    ] = None

    # ------------------------------------------------------
    # Existing dataset report
    # ------------------------------------------------------

    report: Optional[
        DatasetReport
    ] = None

    # ------------------------------------------------------
    # Normalization
    # ------------------------------------------------------

    normalization: Optional[
        NormalizationResult
    ] = None

    # ------------------------------------------------------
    # Validation
    # ------------------------------------------------------

    validation: Optional[
        ValidationResult
    ] = None

    # ------------------------------------------------------
    # Error information
    # ------------------------------------------------------

    error: Optional[str] = None

    # ======================================================
    # Error helper
    # ======================================================

    @property
    def has_error(self):
        """
        Return True when the inspection contains an error.
        """

        return self.error is not None
