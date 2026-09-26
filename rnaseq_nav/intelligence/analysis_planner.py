"""
RNASeq Navigator

Layer 4 — Analysis Planning

Converts the available metadata, modality interpretation,
experimental design interpretation, and dataset suitability
assessment into a cautious analysis plan.

Scientific policy
-----------------

This module distinguishes:

    observed information
    inferred information
    recommended analysis

It must not invent:

    - biological replicates
    - control groups
    - treatment groups
    - statistical design formulas

when these cannot be established from the available metadata.

Modality policy
---------------

The analysis planner must first determine whether the dataset
is compatible with a conventional RNA-seq workflow.

A dataset explicitly classified as another sequencing modality
must not receive RNA-seq-specific recommendations such as:

    - STAR
    - featureCounts
    - DESeq2

Suitability is interpreted relative to RNA-seq analysis. A
dataset that is valid for another purpose may therefore be
classified as not applicable for RNA-seq planning.
"""

from dataclasses import dataclass, field
from typing import List


# ==========================================================
# Analysis Plan
# ==========================================================

@dataclass
class AnalysisPlan:
    """
    Structured analysis recommendation.

    The plan is deliberately conservative. Recommendations
    describe an appropriate workflow while clearly identifying
    information that still needs confirmation.
    """

    workflow: str = ""

    alignment: str = ""

    quantification: str = ""

    differential_analysis: str = ""

    design_formula: str = ""

    replicate_status: str = ""

    confidence: str = "Provisional"

    rationale: str = ""

    recommendations: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )


# ==========================================================
# Utility
# ==========================================================

def _clean(value):
    """
    Convert a value into a clean string.
    """

    if value is None:
        return ""

    return str(value).strip()


# ==========================================================
# Modality / Applicability Gate
# ==========================================================

def _is_rna_seq_compatible(modality_insight):
    """
    Determine whether the dataset is compatible with a
    conventional RNA-seq analysis workflow.

    Layer 1.5 is the authoritative source for this decision.

    Returns
    -------
    bool or None

        True
            Explicitly compatible with RNA-seq.

        False
            Explicitly incompatible with RNA-seq.

        None
            Compatibility could not be established.
    """

    if modality_insight is None:
        return None

    value = getattr(
        modality_insight,
        "rna_seq_compatible",
        None,
    )

    if value is None:
        return None

    return bool(value)


# ==========================================================
# Workflow Selection
# ==========================================================

def _select_workflow(metadata_insight):
    """
    Select the broad analysis workflow from the interpreted
    study type and sequencing strategy.
    """

    study_type = _clean(
        getattr(
            metadata_insight,
            "study_type",
            "",
        )
    )

    if "small" in study_type.lower():
        return "Small RNA-seq analysis"

    if "bulk" in study_type.lower():
        return "Bulk RNA-seq differential expression"

    if "rna" in study_type.lower():
        return "RNA-seq analysis"

    return "RNA-seq analysis"


# ==========================================================
# Alignment
# ==========================================================

def _select_aligner(metadata_insight):
    """
    Select an alignment strategy.

    STAR is used as the default recommendation for conventional
    RNA-seq when the metadata indicate an RNA-seq experiment.

    This is a planning recommendation, not a claim that STAR
    has already been run.
    """

    study_type = _clean(
        getattr(
            metadata_insight,
            "study_type",
            "",
        )
    ).lower()

    if "small" in study_type:
        return "Bowtie"

    if "rna" in study_type:
        return "STAR"

    return "STAR"


# ==========================================================
# Quantification
# ==========================================================

def _select_quantification(metadata_insight):
    """
    Select a transcript/gene quantification approach.
    """

    study_type = _clean(
        getattr(
            metadata_insight,
            "study_type",
            "",
        )
    ).lower()

    if "small" in study_type:
        return "miRDeep2"

    if "rna" in study_type:
        return "featureCounts"

    return "featureCounts"


# ==========================================================
# Differential Analysis
# ==========================================================

def _select_differential_analysis(metadata_insight):
    """
    Select a statistical analysis framework.

    DESeq2 is recommended for count-based RNA-seq differential
    expression when the dataset is appropriate for such analysis.
    """

    study_type = _clean(
        getattr(
            metadata_insight,
            "study_type",
            "",
        )
    ).lower()

    if "rna" in study_type:
        return "DESeq2"

    return "DESeq2"


# ==========================================================
# Design Formula
# ==========================================================

def _determine_design_formula(design_insight):
    """
    Determine whether a statistical design formula can be
    proposed safely.

    Scientific policy:

    Never generate '~ condition' merely because a condition
    word appears in an experiment title.

    A design formula is only proposed when the available
    interpretation provides enough evidence.
    """

    if design_insight is None:
        return "Not established"

    condition = _clean(
        getattr(
            design_insight,
            "condition",
            "",
        )
    )

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

    if (
        condition
        and control
        and replicate_information
        and "could not be established"
        not in replicate_information.lower()
        and "not established"
        not in replicate_information.lower()
    ):
        return "~ condition"

    return (
        "Not established from available metadata"
    )


# ==========================================================
# Replicate Status
# ==========================================================

def _replicate_status(design_insight):
    """
    Extract the replicate assessment generated by Layer 2.
    """

    if design_insight is None:
        return (
            "Replicate structure unavailable."
        )

    value = _clean(
        getattr(
            design_insight,
            "replicate_information",
            "",
        )
    )

    if value:
        return value

    return (
        "Replicate structure could not be established "
        "from the available metadata."
    )


# ==========================================================
# Confidence
# ==========================================================

def _determine_confidence(
    design_insight,
    suitability_insight,
):
    """
    Determine the confidence of the analysis plan.

    This is deliberately conservative.
    """

    design_confidence = _clean(
        getattr(
            design_insight,
            "design_confidence",
            "",
        )
        if design_insight is not None
        else ""
    )

    suitability = _clean(
        getattr(
            suitability_insight,
            "overall",
            "",
        )
        if suitability_insight is not None
        else ""
    )

    # Use the vocabulary produced by the experimental-design
    # and suitability intelligence layers explicitly. Do not rely
    # on substring matching because the design layer uses
    # "Well characterized", not "Fully characterized".
    if (
        design_confidence == "Well characterized"
        and suitability == "Suitable"
    ):
        return "High"

    if (
        design_confidence in {
            "Well characterized",
            "Substantially characterized",
            "Partially characterized",
        }
        and suitability in {
            "Suitable",
            "Potentially suitable",
        }
    ):
        return "Moderate"

    return "Provisional"


# ==========================================================
# Non-RNA-seq Plan
# ==========================================================

def _build_incompatible_plan(
    modality_insight,
    suitability_insight,
):
    """
    Build an analysis plan when the dataset is explicitly
    incompatible with conventional RNA-seq analysis.
    """

    plan = AnalysisPlan()

    modality = _clean(
        getattr(
            modality_insight,
            "modality",
            "",
        )
    )

    library_strategy = _clean(
        getattr(
            modality_insight,
            "library_strategy",
            "",
        )
    )

    workflow_family = _clean(
        getattr(
            modality_insight,
            "workflow_family",
            "",
        )
    )

    plan.workflow = (
        "RNA-seq workflow not applicable"
    )

    plan.alignment = "Not applicable"

    plan.quantification = "Not applicable"

    plan.differential_analysis = "Not applicable"

    plan.design_formula = "Not applicable"

    plan.replicate_status = (
        "Not assessed because the dataset is "
        "not compatible with conventional RNA-seq analysis."
    )

    plan.confidence = "High"

    if modality and library_strategy:
        plan.rationale = (
            f"The dataset is classified as {modality} "
            f"based on the library strategy {library_strategy}. "
            "This modality is not compatible with a conventional "
            "RNA-seq expression workflow. RNA-seq alignment, "
            "gene-level quantification, and DESeq2-based "
            "differential expression planning are therefore "
            "not applicable."
        )

    elif modality:
        plan.rationale = (
            f"The dataset is classified as {modality} "
            "and is not compatible with a conventional "
            "RNA-seq expression workflow. RNA-seq-specific "
            "analysis planning is therefore not applicable."
        )

    else:
        plan.rationale = (
            "The available modality assessment indicates that "
            "the dataset is not compatible with a conventional "
            "RNA-seq expression workflow."
        )

    if workflow_family:
        plan.recommendations.append(
            "Use an analysis workflow appropriate to the "
            f"identified modality ({workflow_family})."
        )
    else:
        plan.recommendations.append(
            "Determine the appropriate analysis workflow "
            "from the identified sequencing modality."
        )

    plan.recommendations.append(
        "Do not apply a conventional RNA-seq workflow "
        "until modality compatibility has been established."
    )

    modality_warnings = getattr(
        modality_insight,
        "warnings",
        [],
    )

    for warning in modality_warnings:

        warning = _clean(warning)

        if warning and warning not in plan.warnings:
            plan.warnings.append(warning)

    suitability_warnings = getattr(
        suitability_insight,
        "warnings",
        []
    ) if suitability_insight is not None else []

    for warning in suitability_warnings:

        warning = _clean(warning)

        if warning and warning not in plan.warnings:
            plan.warnings.append(warning)

    return plan


# ==========================================================
# Uncertain Modality Plan
# ==========================================================

def _build_uncertain_modality_plan(
    modality_insight,
):
    """
    Build a conservative plan when RNA-seq compatibility
    cannot be established.
    """

    plan = AnalysisPlan()

    modality = _clean(
        getattr(
            modality_insight,
            "modality",
            "",
        )
    )

    library_strategy = _clean(
        getattr(
            modality_insight,
            "library_strategy",
            "",
        )
    )

    plan.workflow = (
        "RNA-seq workflow applicability uncertain"
    )

    plan.alignment = "Not established"

    plan.quantification = "Not established"

    plan.differential_analysis = "Not established"

    plan.design_formula = "Not established"

    plan.replicate_status = (
        "Not assessed because RNA-seq compatibility "
        "could not be established."
    )

    plan.confidence = "Provisional"

    if library_strategy:
        plan.rationale = (
            f"The library strategy is {library_strategy}, "
            "but the available modality information does "
            "not establish compatibility with a conventional "
            "RNA-seq workflow. RNA-seq-specific tools should "
            "not be selected until the sequencing modality "
            "is clarified."
        )
    elif modality:
        plan.rationale = (
            f"The dataset modality is reported as {modality}, "
            "but RNA-seq compatibility could not be established "
            "from the available metadata."
        )
    else:
        plan.rationale = (
            "RNA-seq compatibility could not be established "
            "from the available metadata."
        )

    plan.recommendations.append(
        "Inspect the library strategy and experiment metadata "
        "before selecting an analysis workflow."
    )

    plan.recommendations.append(
        "Do not finalize RNA-seq-specific tools until "
        "modality compatibility is confirmed."
    )

    return plan


# ==========================================================
# Main Analysis Planner
# ==========================================================

def generate_analysis_plan(
    metadata,
    metadata_insight,
    design_insight,
    suitability_insight,
    modality_insight=None,
):
    """
    Generate a contextual analysis plan.

    Parameters
    ----------
    metadata
        Normalized dataset metadata.

    metadata_insight
        Layer 1 metadata interpretation.

    design_insight
        Layer 2 experimental design interpretation.

    suitability_insight
        Layer 3 dataset suitability assessment.

    modality_insight
        Layer 1.5 modality / workflow interpretation.

    Returns
    -------
    AnalysisPlan
        Structured analysis recommendation.
    """

    # ------------------------------------------------------
    # Modality / applicability gate
    # ------------------------------------------------------

    compatibility = _is_rna_seq_compatible(
        modality_insight
    )

    if compatibility is False:

        return _build_incompatible_plan(
            modality_insight,
            suitability_insight,
        )

    if compatibility is None:

        return _build_uncertain_modality_plan(
            modality_insight,
        )

    # ------------------------------------------------------
    # Conventional RNA-seq planning
    # ------------------------------------------------------

    plan = AnalysisPlan()

    # ------------------------------------------------------
    # Workflow
    # ------------------------------------------------------

    plan.workflow = _select_workflow(
        metadata_insight
    )

    # ------------------------------------------------------
    # Core tools
    # ------------------------------------------------------

    plan.alignment = _select_aligner(
        metadata_insight
    )

    plan.quantification = _select_quantification(
        metadata_insight
    )

    plan.differential_analysis = (
        _select_differential_analysis(
            metadata_insight
        )
    )

    # ------------------------------------------------------
    # Experimental design
    # ------------------------------------------------------

    plan.design_formula = (
        _determine_design_formula(
            design_insight
        )
    )

    plan.replicate_status = (
        _replicate_status(
            design_insight
        )
    )

    # ------------------------------------------------------
    # Confidence
    # ------------------------------------------------------

    plan.confidence = _determine_confidence(
        design_insight,
        suitability_insight,
    )

    # ------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------

    plan.recommendations.append(
        "Inspect sample-level metadata before "
        "constructing the final statistical design."
    )

    if (
        plan.design_formula
        == "Not established from available metadata"
    ):

        plan.recommendations.append(
            "Do not finalize a DESeq2 design formula "
            "until experimental groups and biological "
            "replicates are confirmed."
        )

    else:

        plan.recommendations.append(
            "Confirm the proposed design formula against "
            "the complete sample annotation before analysis."
        )

    # ------------------------------------------------------
    # Warnings
    # ------------------------------------------------------

    if design_insight is not None:

        warnings = getattr(
            design_insight,
            "warnings",
            [],
        )

        for warning in warnings:

            warning = _clean(
                warning
            )

            if (
                warning
                and warning not in plan.warnings
            ):

                plan.warnings.append(
                    warning
                )

    if suitability_insight is not None:

        suitability_warnings = getattr(
            suitability_insight,
            "warnings",
            [],
        )

        for warning in suitability_warnings:

            warning = _clean(
                warning
            )

            if (
                warning
                and warning not in plan.warnings
            ):

                plan.warnings.append(
                    warning
                )

    # ------------------------------------------------------
    # Rationale
    # ------------------------------------------------------

    if (
        plan.design_formula
        == "Not established from available metadata"
    ):

        plan.rationale = (
            "The available metadata support planning a "
            "RNA-seq analysis workflow, but the experimental "
            "group structure and replicate organization are "
            "not sufficiently established to define the "
            "final statistical model."
        )

    else:

        plan.rationale = (
            "The available metadata provide sufficient "
            "evidence for a provisional analysis design. "
            "Sample-level annotations should still be "
            "checked before downstream statistical analysis."
        )

    return plan
