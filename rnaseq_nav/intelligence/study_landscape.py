"""
RNASeq Scout

Study Experimental Landscape Intelligence

Summarizes the observed assay families and experimental
context labels across a study.

This layer is deliberately descriptive. It does not infer
controls, treatments, biological replicates, time points,
or statistical contrasts.
"""

from collections import Counter
from typing import Iterable

from rnaseq_nav.models import (
    StudyExperiment,
    StudyExperimentalLandscape,
)


def _clean(value: str) -> str:
    """Normalize a metadata string for comparison."""
    return (value or "").strip()


def _classify_assay_family(
    library_strategy: str,
    title: str,
) -> str:
    """
    Classify an experiment into an observed assay family.

    Classification hierarchy
    -------------------------
    1. Explicit LibraryStrategy provides the primary
       repository-level modality evidence.
    2. Experiment title provides finer assay-family
       resolution when the strategy is broad.
    3. Title is used as a fallback when LibraryStrategy
       is unavailable.

    This function intentionally does not infer experimental
    design such as controls, treatments, or replicates.
    """

    strategy = _clean(library_strategy)
    title = _clean(title)

    strategy_upper = strategy.upper()
    title_lower = title.lower()

    # ------------------------------------------------------
    # Explicit specialized RNA strategies
    # ------------------------------------------------------

    if strategy_upper in {
        "SMALL_RNA",
        "SMALL-RNA",
    }:
        return "Small RNA sequencing"

    if strategy_upper in {
        "NCRNA_SEQ",
        "NCRNA-SEQ",
    }:
        # ncRNA-Seq may be represented in SRA titles as
        # sRNA-seq. Preserve the observed title label when
        # available; otherwise retain the repository strategy.
        if "srna-seq" in title_lower:
            return "sRNA-seq"
        return "ncRNA-Seq"

    # ------------------------------------------------------
    # Explicit non-RNA sequencing strategies
    # ------------------------------------------------------

    if strategy_upper in {
        "AMPLICON",
    }:
        return "Amplicon sequencing"

    if strategy_upper in {
        "WGS",
        "WGA",
    }:
        return "Whole-genome sequencing"

    if strategy_upper in {
        "WXS",
        "EXOME",
    }:
        return "Exome sequencing"

    if strategy_upper in {
        "CHIP_SEQ",
        "CHIP-SEQ",
    }:
        return "ChIP-seq"

    if strategy_upper in {
        "ATAC_SEQ",
        "ATAC-SEQ",
    }:
        return "ATAC-seq"

    if strategy_upper in {
        "HI-C",
        "HIC",
    }:
        return "Hi-C"

    if "BISULFITE" in strategy_upper:
        return "Bisulfite sequencing"

    # ------------------------------------------------------
    # RNA-Seq strategy
    # ------------------------------------------------------

    if strategy_upper in {
        "RNA_SEQ",
        "RNA-SEQ",
    }:
        # Preserve explicit assay-family terminology from
        # the title when present.
        if "tex+ rna-seq" in title_lower:
            return "TEX+ RNA-seq"

        if "srna-seq" in title_lower:
            return "sRNA-seq"

        if "small rna-seq" in title_lower:
            return "Small RNA sequencing"

        if "ncrna-seq" in title_lower:
            return "ncRNA-Seq"

        if "rna-seq" in title_lower:
            return "RNA-seq"

        return "RNA-seq"

    # ------------------------------------------------------
    # Title-based fallback
    # ------------------------------------------------------

    if "tex+ rna-seq" in title_lower:
        return "TEX+ RNA-seq"

    if "srna-seq" in title_lower:
        return "sRNA-seq"

    if "small rna-seq" in title_lower:
        return "Small RNA sequencing"

    if "ncrna-seq" in title_lower:
        return "ncRNA-Seq"

    if "atac-seq" in title_lower:
        return "ATAC-seq"

    if "amplicon" in title_lower:
        return "Amplicon sequencing"

    if "wgs" in title_lower:
        return "Whole-genome sequencing"

    if "rna-seq" in title_lower:
        return "RNA-seq"

    return "Unclassified"


def _extract_context(title: str) -> str:
    """
    Extract the observed context label from an experiment title.

    The context is the text following the final colon.
    No normalization or semantic merging is performed.
    """

    title = _clean(title)

    if ":" not in title:
        return "Unspecified"

    context = title.rsplit(":", 1)[1].strip()

    return context or "Unspecified"


def generate_study_experimental_landscape(
    records: Iterable[StudyExperiment],
) -> StudyExperimentalLandscape:
    """
    Generate a descriptive study-level experimental landscape.

    Parameters
    ----------
    records : Iterable[StudyExperiment]
        Study-level experiment records retrieved from SRA.

    Returns
    -------
    StudyExperimentalLandscape
        Counts and observed labels describing the study.

    Notes
    -----
    This function intentionally does not infer:

    - controls
    - treatments
    - biological replicates
    - time points
    - statistical contrasts
    """

    records = list(records)

    assay_family_counts = Counter()
    context_counts = Counter()
    assay_context_counts = {}

    warnings = []

    for record in records:

        title = (
            record.experiment_title
            if record.experiment_title
            else ""
        )

        library_strategy = (
            record.library_strategy
            if record.library_strategy
            else ""
        )

        assay_family = _classify_assay_family(
            library_strategy,
            title,
        )

        context = _extract_context(title)

        assay_family_counts[assay_family] += 1
        context_counts[context] += 1

        if assay_family not in assay_context_counts:
            assay_context_counts[assay_family] = {}

        assay_context_counts[assay_family][context] = (
            assay_context_counts[assay_family].get(
                context,
                0,
            )
            + 1
        )

    if not records:
        warnings.append(
            "No study experiment records were available."
        )

    if "Unclassified" in assay_family_counts:
        warnings.append(
            "One or more experiment records could not be "
            "assigned to a recognized assay family from "
            "available repository metadata."
        )

    landscape = StudyExperimentalLandscape(
        total_experiments=len(records),
        assay_family_counts=dict(
            assay_family_counts
        ),
        context_counts=dict(
            context_counts
        ),
        assay_context_counts=assay_context_counts,
        observed_assay_families=sorted(
            assay_family_counts.keys()
        ),
        observed_contexts=sorted(
            context_counts.keys()
        ),
        warnings=warnings,
    )

    return landscape
