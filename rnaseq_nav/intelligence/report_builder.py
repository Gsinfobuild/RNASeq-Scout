"""
RNASeq Navigator

Dataset Report Builder

Version 1.0

Purpose
-------
Combine metadata, normalization,
validation and interpretation into
one structured report.
"""

from dataclasses import dataclass, field


# ==========================================================
# Dataset Report
# ==========================================================

@dataclass
class DatasetReport:

    # Identity

    run: str = ""

    experiment: str = ""

    study: str = ""

    project: str = ""

    organism: str = ""

    # Experiment

    strategy: str = ""

    layout: str = ""

    platform: str = ""

    instrument: str = ""

    # Sequencing

    total_spots: int = 0

    total_bases: int = 0

    # Quality

    validation_score: float = 0

    normalization_changes: int = 0

    # Intelligence

    title: str = ""

    summary: str = ""

    sequencing: str = ""

    strengths: list[str] = field(default_factory=list)

    limitations: list[str] = field(default_factory=list)


# ==========================================================
# Builder
# ==========================================================

class DatasetReportBuilder:

    """
    Assemble one DatasetReport from all
    RNASeq Navigator modules.
    """

    def build(

        self,

        metadata,

        normalization,

        validation,

        description,

    ):

        report = DatasetReport()

        # ------------------------------------------
        # Identity
        # ------------------------------------------

        report.run = metadata.run.accession

        report.experiment = metadata.experiment.accession

        report.study = metadata.study.accession

        report.project = metadata.project.accession

        report.organism = metadata.sample.organism

        # ------------------------------------------
        # Experiment
        # ------------------------------------------

        report.strategy = metadata.experiment.library_strategy

        report.layout = metadata.experiment.layout

        report.platform = metadata.experiment.platform

        report.instrument = metadata.experiment.instrument

        # ------------------------------------------
        # Sequencing
        # ------------------------------------------

        report.total_spots = metadata.run.total_spots

        report.total_bases = metadata.run.total_bases

        # ------------------------------------------
        # Quality
        # ------------------------------------------

        report.validation_score = validation.quality_score

        report.normalization_changes = normalization.changes

        # ------------------------------------------
        # Intelligence
        # ------------------------------------------

        report.title = description.title

        report.summary = description.summary

        report.sequencing = description.sequencing

        report.strengths = list(description.strengths)

        report.limitations = list(description.limitations)

        return report
