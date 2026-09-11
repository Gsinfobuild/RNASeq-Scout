"""
RNASeq Scout

Metadata Models

Version 0.1.0

Defines the core metadata objects used throughout
RNASeq Scout.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ==========================================================
# Project Metadata
# ==========================================================

@dataclass
class ProjectMetadata:
    """
    BioProject-level metadata.
    """

    accession: str = ""


# ==========================================================
# Study Metadata
# ==========================================================

@dataclass
class StudyMetadata:
    """
    Study (SRP) metadata.
    """

    accession: str = ""


# ==========================================================
# Experiment Metadata
# ==========================================================

@dataclass
class ExperimentMetadata:
    """
    Experiment (SRX) metadata.
    """

    accession: str = ""

    # Experiment title
    title: str = ""

    # Sequencing information
    library_strategy: str = ""
    library_source: str = ""
    library_selection: str = ""

    # Layout
    layout: str = ""

    # Sequencing platform
    platform: str = ""

    # Instrument model
    instrument: str = ""


# ==========================================================
# Run Metadata
# ==========================================================

@dataclass
class RunMetadata:
    """
    Run (SRR) metadata.
    """

    accession: str = ""

    total_spots: Optional[int] = None

    total_bases: Optional[int] = None

    public: bool = False

    cluster: str = ""

    static_data: bool = False


# ==========================================================
# Sample Metadata
# ==========================================================

@dataclass
class SampleMetadata:
    """
    Sample (SRS/SAMN) metadata.
    """

    accession: str = ""

    biosample: str = ""

    organism: str = ""


# ==========================================================
# Study Sample Metadata
# ==========================================================

@dataclass
class StudyExperiment:
    """
    Sample-level metadata within a study.
    """

    sample_accession: str = ""
    biosample_accession: str = ""
    experiment_accession: str = ""
    experiment_title: str = ""
    library_strategy: str = ""
    run_accessions: List[str] = field(default_factory=list)
    organism: str = ""
    sample_name: str = ""


# ==========================================================
# Master Metadata Object
# ==========================================================

@dataclass
class ReanalysisReadinessInsight:
    """
    Evidence-based assessment of whether a public sequencing
    dataset contains enough information to support defensible
    downstream reanalysis.

    This layer does not score datasets and does not invent
    experimental design information. Evidence is explicitly
    classified as observed, inferred, not established, or missing.
    """
    verdict: str = "Insufficient evidence"
    observed_evidence: List[str] = field(default_factory=list)
    inferred_evidence: List[str] = field(default_factory=list)
    not_established: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rationale: str = ""

@dataclass
class StudyExperimentalLandscape:
    """
    Observed experimental structure across a study.

    This model records assay families and experimental context
    labels directly observed in study-level experiment metadata.
    It does not infer controls, treatments, replicates, time
    points, or statistical contrasts.
    """

    total_experiments: int = 0
    assay_family_counts: dict[str, int] = field(default_factory=dict)
    context_counts: dict[str, int] = field(default_factory=dict)
    assay_context_counts: dict[str, dict[str, int]] = field(
        default_factory=dict
    )
    observed_assay_families: List[str] = field(default_factory=list)
    observed_contexts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class Metadata:
    """
    Master metadata object used throughout RNASeq Scout.
    """

    project: ProjectMetadata = field(
        default_factory=ProjectMetadata
    )

    study: StudyMetadata = field(
        default_factory=StudyMetadata
    )

    experiment: ExperimentMetadata = field(
        default_factory=ExperimentMetadata
    )

    run: RunMetadata = field(
        default_factory=RunMetadata
    )

    sample: SampleMetadata = field(
        default_factory=SampleMetadata
    )

    study_experiments: List[StudyExperiment] = field(
        default_factory=list
    )
