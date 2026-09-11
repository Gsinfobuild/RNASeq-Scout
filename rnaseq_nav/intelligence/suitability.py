"""
RNASeq Navigator

Layer 3 — Dataset Suitability Intelligence

Evaluates whether the available metadata provides enough
information to consider a dataset suitable for downstream
RNA-seq analysis.

Scientific policy
-----------------

This module evaluates metadata availability, consistency,
and compatibility with the intended RNA-seq workflow.

It does NOT claim that a dataset is biologically valid for
a specific research question unless the available metadata
supports that conclusion.

It distinguishes:

    Observed evidence
    Warnings
    Missing information
    Workflow compatibility
    Overall suitability

Version: 1.1
"""

from dataclasses import dataclass, field
from typing import List


# ==========================================================
# Suitability Result
# ==========================================================

@dataclass
class SuitabilityInsight:
    """
    Structured assessment of dataset suitability.
    """

    overall: str = "Insufficient information"

    score: int = 0

    observed_evidence: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )

    missing_information: List[str] = field(
        default_factory=list
    )

    rationale: str = ""


# ==========================================================
# Utility Functions
# ==========================================================

def _clean(value):
    """
    Convert a metadata value into a clean string.
    """

    if value is None:
        return ""

    return str(value).strip()


def _get_experiment(metadata):
    """
    Safely retrieve experiment metadata.
    """

    return getattr(
        metadata,
        "experiment",
        None,
    )


def _get_sample(metadata):
    """
    Safely retrieve sample metadata.
    """

    return getattr(
        metadata,
        "sample",
        None,
    )


def _get_run(metadata):
    """
    Safely retrieve run metadata.
    """

    return getattr(
        metadata,
        "run",
        None,
    )


# ==========================================================
# Evidence Assessment
# ==========================================================

def _assess_library_strategy(metadata):
    """
    Assess whether sequencing/library strategy is available.
    """

    experiment = _get_experiment(
        metadata
    )

    strategy = _clean(
        getattr(
            experiment,
            "library_strategy",
            "",
        )
    )

    if strategy:

        return (
            True,
            f"Library strategy identified: {strategy}.",
        )

    return (
        False,
        "",
    )


def _assess_layout(metadata):
    """
    Assess whether sequencing layout is available.
    """

    experiment = _get_experiment(
        metadata
    )

    layout = _clean(
        getattr(
            experiment,
            "layout",
            "",
        )
    )

    if layout:

        return (
            True,
            f"Sequencing layout identified: {layout}.",
        )

    return (
        False,
        "",
    )


def _assess_platform(metadata):
    """
    Assess whether sequencing platform is available.
    """

    experiment = _get_experiment(
        metadata
    )

    platform = _clean(
        getattr(
            experiment,
            "platform",
            "",
        )
    )

    if platform:

        return (
            True,
            f"Sequencing platform identified: {platform}.",
        )

    return (
        False,
        "",
    )


def _assess_organism(metadata):
    """
    Assess whether organism information is available.
    """

    sample = _get_sample(
        metadata
    )

    organism = _clean(
        getattr(
            sample,
            "organism",
            "",
        )
    )

    if organism:

        return (
            True,
            f"Organism identified: {organism}.",
        )

    return (
        False,
        "",
    )


def _assess_experiment_title(metadata):
    """
    Assess whether an experiment title is available.
    """

    experiment = _get_experiment(
        metadata
    )

    title = _clean(
        getattr(
            experiment,
            "title",
            "",
        )
    )

    if title:

        return (
            True,
            f"Experiment description available: {title}.",
        )

    return (
        False,
        "",
    )


def _assess_run(metadata):
    """
    Assess whether meaningful sequencing-run evidence exists.

    Run-level evidence may be represented by a run accession,
    total spot count, total base count, or public-status
    information.

    Run existence must not be interpreted as evidence of
    biological replication.
    """

    run = _get_run(
        metadata
    )

    accession = _clean(
        getattr(
            run,
            "accession",
            "",
        )
    )

    total_spots = getattr(
        run,
        "total_spots",
        None,
    )

    total_bases = getattr(
        run,
        "total_bases",
        None,
    )

    public = getattr(
        run,
        "public",
        None,
    )

    if accession:

        return (
            True,
            f"Sequencing run identified: {accession}.",
        )

    if total_spots is not None:

        return (
            True,
            "Sequencing run information available "
            f"with {total_spots} spots.",
        )

    if total_bases is not None:

        return (
            True,
            "Sequencing run information available "
            f"with {total_bases} bases.",
        )

    if public is True:

        return (
            True,
            "Sequencing run is identified as public.",
        )

    return (
        False,
        "",
    )


# ==========================================================
# Modality Compatibility
# ==========================================================

def _assess_rna_seq_compatibility(
    modality_insight,
):
    """
    Assess compatibility with conventional RNA-seq analysis.

    The modality intelligence layer is treated as the primary
    source for this decision.

    Returns
    -------
    tuple
        status, evidence, warning
    """

    if modality_insight is None:

        return (
            "unknown",
            "",
            "RNA-seq workflow compatibility has not "
            "been established.",
        )

    compatible = getattr(
        modality_insight,
        "rna_seq_compatible",
        None,
    )

    modality = _clean(
        getattr(
            modality_insight,
            "modality",
            "",
        )
    )

    status = _clean(
        getattr(
            modality_insight,
            "compatibility_status",
            "",
        )
    )

    strategy = _clean(
        getattr(
            modality_insight,
            "library_strategy",
            "",
        )
    )

    if compatible is True:

        evidence = (
            f"Dataset classified as {modality or 'RNA-seq'} "
            "and compatible with the conventional RNA-seq "
            "workflow."
        )

        return (
            "compatible",
            evidence,
            "",
        )

    if compatible is False:

        warning = (
            f"Dataset classified as "
            f"{modality or 'a non-RNA-seq modality'}"
        )

        if strategy:

            warning += (
                f" based on library strategy {strategy}."
            )

        else:

            warning += "."

        return (
            "incompatible",
            "",
            warning,
        )

    return (
        "unknown",
        "",
        (
            "RNA-seq workflow compatibility could not "
            "be established from the available metadata."
        ),
    )


# ==========================================================
# Main Suitability Function
# ==========================================================

def generate_suitability_insight(
    metadata,
    design_insight=None,
    modality_insight=None,
):
    """
    Generate a dataset suitability assessment.

    Parameters
    ----------
    metadata
        Normalized sequencing metadata.

    design_insight
        Optional Layer 2 experimental design interpretation.

    modality_insight
        Optional Layer 1.5 modality/workflow interpretation.

    Returns
    -------
    SuitabilityInsight
        Structured suitability assessment.

    Scientific policy
    -----------------

    This function evaluates the information available in
    metadata. It does not fabricate biological replicates,
    controls, treatment groups, or statistical designs.

    An explicitly incompatible sequencing modality takes
    precedence over generic metadata completeness when the
    intended workflow is conventional RNA-seq.
    """

    insight = SuitabilityInsight()

    evidence_count = 0

    # ======================================================
    # Modality compatibility
    # ======================================================

    compatibility, compatibility_evidence, compatibility_warning = (
        _assess_rna_seq_compatibility(
            modality_insight,
        )
    )

    if compatibility_evidence:

        insight.observed_evidence.append(
            compatibility_evidence
        )

    if compatibility_warning:

        insight.warnings.append(
            compatibility_warning
        )


    # ======================================================
    # Library strategy
    # ======================================================

    available, evidence = _assess_library_strategy(
        metadata
    )

    if available:

        evidence_count += 1

        insight.observed_evidence.append(
            evidence
        )

    else:

        insight.missing_information.append(
            "Library strategy"
        )


    # ======================================================
    # Sequencing layout
    # ======================================================

    available, evidence = _assess_layout(
        metadata
    )

    if available:

        evidence_count += 1

        insight.observed_evidence.append(
            evidence
        )

    else:

        insight.missing_information.append(
            "Sequencing layout"
        )


    # ======================================================
    # Sequencing platform
    # ======================================================

    available, evidence = _assess_platform(
        metadata
    )

    if available:

        evidence_count += 1

        insight.observed_evidence.append(
            evidence
        )

    else:

        insight.missing_information.append(
            "Sequencing platform"
        )


    # ======================================================
    # Organism
    # ======================================================

    available, evidence = _assess_organism(
        metadata
    )

    if available:

        evidence_count += 1

        insight.observed_evidence.append(
            evidence
        )

    else:

        insight.missing_information.append(
            "Organism identification"
        )


    # ======================================================
    # Experiment description
    # ======================================================

    available, evidence = _assess_experiment_title(
        metadata
    )

    if available:

        evidence_count += 1

        insight.observed_evidence.append(
            evidence
        )

    else:

        insight.missing_information.append(
            "Experiment description"
        )


    # ======================================================
    # Sequencing run
    # ======================================================

    available, evidence = _assess_run(
        metadata
    )

    if available:

        evidence_count += 1

        insight.observed_evidence.append(
            evidence
        )

    else:

        insight.missing_information.append(
            "Sequencing run information"
        )


    # ======================================================
    # Layer 2 integration
    # ======================================================

    if design_insight is not None:

        # --------------------------------------------------
        # Experimental condition
        # --------------------------------------------------

        condition = _clean(
            getattr(
                design_insight,
                "condition",
                "",
            )
        )

        if condition:

            insight.observed_evidence.append(
                "An experimental condition is suggested "
                "by the available metadata."
            )

        else:

            insight.warnings.append(
                "Experimental condition could not be "
                "clearly established from the metadata."
            )


        # --------------------------------------------------
        # Control
        # --------------------------------------------------

        control = _clean(
            getattr(
                design_insight,
                "control",
                "",
            )
        )

        if not control:

            insight.warnings.append(
                "A control group could not be established "
                "from the available metadata."
            )

            if "Control-group annotation" not in (
                insight.missing_information
            ):

                insight.missing_information.append(
                    "Control-group annotation"
                )


        # --------------------------------------------------
        # Treatment
        # --------------------------------------------------

        treatment = _clean(
            getattr(
                design_insight,
                "treatment",
                "",
            )
        )

        if not treatment:

            insight.warnings.append(
                "A treatment group could not be "
                "unambiguously established."
            )

            if (
                "Treatment-group annotation, if applicable"
                not in insight.missing_information
            ):

                insight.missing_information.append(
                    "Treatment-group annotation, if applicable"
                )


        # --------------------------------------------------
        # Replicates
        # --------------------------------------------------

        replicate_information = _clean(
            getattr(
                design_insight,
                "replicate_information",
                "",
            )
        )

        replicate_lower = replicate_information.lower()

        if replicate_information:

            if (
                "could not be established"
                in replicate_lower
            ):

                insight.warnings.append(
                    "Replicate structure could not be "
                    "established from the available metadata."
                )

                if (
                    "Biological replicate annotation"
                    not in insight.missing_information
                ):

                    insight.missing_information.append(
                        "Biological replicate annotation"
                    )

            else:

                insight.observed_evidence.append(
                    "Replicate information established: "
                    f"{replicate_information}"
                )

                if (
                    "biological or technical replicate status "
                    "is not established"
                    in replicate_lower
                ):

                    insight.warnings.append(
                        "Biological versus technical replicate "
                        "status could not be established from "
                        "the available metadata."
                    )

                    if (
                        "Biological versus technical "
                        "replicate status"
                        not in insight.missing_information
                    ):

                        insight.missing_information.append(
                            "Biological versus technical "
                            "replicate status"
                        )

        else:

            insight.warnings.append(
                "Replicate structure could not be established "
                "from the available metadata."
            )

            if (
                "Biological replicate annotation"
                not in insight.missing_information
            ):

                insight.missing_information.append(
                    "Biological replicate annotation"
                )

    else:

        insight.warnings.append(
            "Experimental design information has not "
            "been evaluated."
        )

        insight.missing_information.append(
            "Experimental design assessment"
        )


    # ======================================================
    # Explicit modality gate
    # ======================================================

    if compatibility == "incompatible":

        insight.score = 0

        insight.overall = (
            "Not suitable for RNA-seq analysis"
        )

        modality = _clean(
            getattr(
                modality_insight,
                "modality",
                "",
            )
        )

        strategy = _clean(
            getattr(
                modality_insight,
                "library_strategy",
                "",
            )
        )

        if modality and strategy:

            insight.rationale = (
                f"The dataset is classified as {modality} "
                f"from the explicit library strategy "
                f"{strategy}. It should not be processed "
                "using a conventional RNA-seq expression "
                "workflow."
            )

        elif modality:

            insight.rationale = (
                f"The dataset is classified as {modality}, "
                "which is not compatible with a conventional "
                "RNA-seq expression workflow."
            )

        else:

            insight.rationale = (
                "The available sequencing metadata indicate "
                "a modality that is not compatible with a "
                "conventional RNA-seq expression workflow."
            )

        return insight


    # ======================================================
    # Unknown modality gate
    # ======================================================

    if compatibility == "unknown":

        insight.score = 0

        insight.overall = (
            "RNA-seq compatibility uncertain"
        )

        insight.rationale = (
            "The available metadata do not establish that "
            "the dataset is compatible with a conventional "
            "RNA-seq workflow. Additional sequencing "
            "strategy information should be inspected before "
            "planning downstream RNA-seq analysis."
        )

        return insight


    # ======================================================
    # Suitability classification for RNA-seq-compatible data
    # ======================================================

    # ------------------------------------------------------
    # Strong metadata foundation
    # ------------------------------------------------------

    if evidence_count >= 5:

        insight.score = 3

    elif evidence_count >= 3:

        insight.score = 2

    elif evidence_count >= 1:

        insight.score = 1

    else:

        insight.score = 0


    # ======================================================
    # Design limitations affect suitability
    # ======================================================

    design_has_major_gap = False

    if design_insight is not None:

        control = _clean(
            getattr(
                design_insight,
                "control",
                "",
            )
        )

        replicate_information = _clean(
            getattr(
                design_insight,
                "replicate_information",
                "",
            )
        )

        if not control:

            design_has_major_gap = True

        if (
            "could not be established"
            in replicate_information.lower()
        ):

            design_has_major_gap = True


    # ======================================================
    # Final classification
    # ======================================================

    if evidence_count >= 5 and not design_has_major_gap:

        insight.overall = (
            "Suitable"
        )

        insight.rationale = (
            "The available metadata provides a strong "
            "basic foundation for downstream RNA-seq "
            "analysis. Experimental design should still "
            "be confirmed before statistical testing."
        )


    elif evidence_count >= 3:

        insight.overall = (
            "Potentially suitable"
        )

        insight.rationale = (
            "Core sequencing and biological metadata are "
            "available, but important aspects of the "
            "experimental design remain incomplete or "
            "uncertain."
        )


    else:

        insight.overall = (
            "Insufficient information"
        )

        insight.rationale = (
            "The available metadata do not provide enough "
            "information to establish strong suitability "
            "for downstream RNA-seq analysis."
        )


    return insight
