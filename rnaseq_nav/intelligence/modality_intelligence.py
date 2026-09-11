"""
RNASeq Navigator — Modality / Workflow Intelligence

Classifies sequencing experiments from explicit library metadata and
determines whether the dataset is compatible with a conventional
RNA-seq analysis workflow.

This layer is intentionally conservative:
- explicit library strategy is preferred;
- unsupported strategies are not silently converted to RNA-seq;
- RNA-derived strategies such as small RNA / ncRNA sequencing are
  distinguished from conventional RNA_SEQ;
- classification is based on metadata evidence, not biological guesswork.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ModalityInsight:
    """Interpretation of the sequencing modality."""

    modality: str = "Unknown"
    library_strategy: str = ""
    library_source: str = ""
    library_selection: str = ""

    workflow_family: str = "Unknown"

    rna_seq_compatible: bool = False
    compatibility_status: str = "Uncertain"

    classification_confidence: str = "Low"

    observed_evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rationale: str = ""


def _clean(value) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _get_experiment(metadata):
    if metadata is None:
        return None

    experiment = getattr(
        metadata,
        "experiment",
        None,
    )

    return experiment


def _strategy(metadata) -> str:
    experiment = _get_experiment(metadata)

    if experiment is None:
        return ""

    return _clean(
        getattr(
            experiment,
            "library_strategy",
            "",
        )
    ).upper()


def _source(metadata) -> str:
    experiment = _get_experiment(metadata)

    if experiment is None:
        return ""

    return _clean(
        getattr(
            experiment,
            "library_source",
            "",
        )
    ).upper()


def _selection(metadata) -> str:
    experiment = _get_experiment(metadata)

    if experiment is None:
        return ""

    return _clean(
        getattr(
            experiment,
            "library_selection",
            "",
        )
    ).upper()


def generate_modality_insight(metadata) -> ModalityInsight:
    """
    Classify the sequencing modality from explicit experiment metadata.

    Returns
    -------
    ModalityInsight
        Conservative modality and workflow-compatibility assessment.
    """

    strategy = _strategy(metadata)
    source = _source(metadata)
    selection = _selection(metadata)

    result = ModalityInsight(
        library_strategy=strategy,
        library_source=source,
        library_selection=selection,
    )

    if strategy:
        result.observed_evidence.append(
            f"Library strategy identified: {strategy}."
        )

    if source:
        result.observed_evidence.append(
            f"Library source identified: {source}."
        )

    if selection:
        result.observed_evidence.append(
            f"Library selection identified: {selection}."
        )

    # --------------------------------------------------------
    # Explicit RNA-seq
    # --------------------------------------------------------

    if strategy == "RNA_SEQ":

        result.modality = "RNA-seq"
        result.workflow_family = "bulk_rna_seq"
        result.rna_seq_compatible = True
        result.compatibility_status = "Compatible"
        result.classification_confidence = "High"

        result.rationale = (
            "The library strategy is explicitly RNA_SEQ, supporting "
            "classification as an RNA-seq dataset."
        )

        return result

    # --------------------------------------------------------
    # Small RNA / ncRNA
    # --------------------------------------------------------

    if strategy in {
        "SMALL_RNA",
        "MIRNA_SEQ",
        "NCRNA_SEQ",
    }:

        if strategy in {
            "SMALL_RNA",
            "MIRNA_SEQ",
        }:
            result.modality = (
                "miRNA sequencing"
                if strategy == "MIRNA_SEQ"
                else "Small RNA sequencing"
            )
        else:
            result.modality = "Non-coding RNA sequencing"

        result.workflow_family = "specialized_rna"
        result.rna_seq_compatible = False
        result.compatibility_status = "Specialized workflow"
        result.classification_confidence = "High"

        result.warnings.append(
            "This RNA-derived sequencing strategy should not "
            "automatically be processed as conventional bulk RNA-seq."
        )

        result.rationale = (
            "The library strategy indicates an RNA-derived sequencing "
            "experiment, but not conventional bulk RNA_SEQ. A specialized "
            "workflow should be selected."
        )

        return result

    # --------------------------------------------------------
    # Amplicon
    # --------------------------------------------------------

    if strategy == "AMPLICON":

        result.modality = "Amplicon sequencing"
        result.workflow_family = "amplicon"
        result.rna_seq_compatible = False
        result.compatibility_status = "Not compatible"
        result.classification_confidence = "High"

        result.warnings.append(
            "AMPLICON data should not be processed using a conventional "
            "RNA-seq expression workflow."
        )

        result.rationale = (
            "The library strategy is explicitly AMPLICON. The dataset "
            "therefore does not represent a conventional RNA-seq "
            "expression experiment."
        )

        return result

    # --------------------------------------------------------
    # Whole-genome sequencing
    # --------------------------------------------------------

    if strategy in {
        "WGS",
        "WGA",
    }:

        result.modality = "Whole-genome sequencing"
        result.workflow_family = "genome"
        result.rna_seq_compatible = False
        result.compatibility_status = "Not compatible"
        result.classification_confidence = "High"

        result.warnings.append(
            "Whole-genome sequencing data should not be processed using "
            "an RNA-seq expression workflow."
        )

        result.rationale = (
            "The library strategy indicates genome-level sequencing "
            "rather than transcriptome sequencing."
        )

        return result

    # --------------------------------------------------------
    # Whole-exome sequencing
    # --------------------------------------------------------

    if strategy in {
        "WXS",
        "EXOME",
    }:

        result.modality = "Whole-exome sequencing"
        result.workflow_family = "exome"
        result.rna_seq_compatible = False
        result.compatibility_status = "Not compatible"
        result.classification_confidence = "High"

        result.warnings.append(
            "Exome sequencing data should not be processed using an "
            "RNA-seq expression workflow."
        )

        result.rationale = (
            "The library strategy indicates targeted exome sequencing "
            "rather than transcriptome sequencing."
        )

        return result

    # --------------------------------------------------------
    # ChIP-seq
    # --------------------------------------------------------

    if strategy in {
        "CHIP_SEQ",
        "CHIP-SEQ",
    }:

        result.modality = "ChIP-seq"
        result.workflow_family = "chromatin"
        result.rna_seq_compatible = False
        result.compatibility_status = "Not compatible"
        result.classification_confidence = "High"

        result.warnings.append(
            "ChIP-seq data require a chromatin/immunoprecipitation "
            "analysis workflow rather than RNA-seq expression analysis."
        )

        result.rationale = (
            "The library strategy indicates ChIP-seq rather than "
            "transcriptome sequencing."
        )

        return result

    # --------------------------------------------------------
    # ATAC-seq
    # --------------------------------------------------------

    if strategy in {
        "ATAC_SEQ",
        "ATAC-SEQ",
    }:

        result.modality = "ATAC-seq"
        result.workflow_family = "chromatin_accessibility"
        result.rna_seq_compatible = False
        result.compatibility_status = "Not compatible"
        result.classification_confidence = "High"

        result.warnings.append(
            "ATAC-seq data require a chromatin-accessibility workflow "
            "rather than RNA-seq expression analysis."
        )

        result.rationale = (
            "The library strategy indicates ATAC-seq rather than "
            "transcriptome sequencing."
        )

        return result

    # --------------------------------------------------------
    # Bisulfite sequencing
    # --------------------------------------------------------

    if strategy in {
        "BISULFITE-SEQ",
        "BISULFITE_SEQ",
    }:

        result.modality = "Bisulfite sequencing"
        result.workflow_family = "methylation"
        result.rna_seq_compatible = False
        result.compatibility_status = "Not compatible"
        result.classification_confidence = "High"

        result.warnings.append(
            "Bisulfite sequencing requires a methylation-analysis "
            "workflow rather than RNA-seq expression analysis."
        )

        result.rationale = (
            "The library strategy indicates bisulfite sequencing."
        )

        return result

    # --------------------------------------------------------
    # Unknown strategy
    # --------------------------------------------------------

    result.modality = (
        "Sequencing modality not established"
        if not strategy
        else f"Unclassified sequencing strategy ({strategy})"
    )

    result.workflow_family = "Unknown"
    result.rna_seq_compatible = None
    result.compatibility_status = "Uncertain"
    result.classification_confidence = "Low"

    result.warnings.append(
        "The sequencing strategy does not provide sufficient evidence "
        "to establish compatibility with a conventional RNA-seq workflow."
    )

    result.rationale = (
        "The available library strategy does not match a supported "
        "RNA-seq modality classification."
    )

    return result
