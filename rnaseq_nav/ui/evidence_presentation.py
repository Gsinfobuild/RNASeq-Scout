"""Evidence-aware presentation helpers for RNA-Seq Scout."""

from __future__ import annotations


def is_rna_seq_compatible(modality_insight):
    """Return backend RNA-seq compatibility without inference."""

    if modality_insight is None:
        return None

    value = getattr(
        modality_insight,
        "rna_seq_compatible",
        None,
    )

    if value is True:
        return True

    if value is False:
        return False

    return None


def experimental_design_display(modality_insight):
    """Return modality-aware experimental-design presentation state."""

    compatible = is_rna_seq_compatible(
        modality_insight
    )

    if compatible is False:
        return {
            "status": "Not applicable",
            "interpretation": (
                "Experimental-design fields used for conventional "
                "RNA-seq analysis are not assessed for this "
                "sequencing modality."
            ),
            "show_design_warnings": False,
            "show_missing_information": False,
        }

    if compatible is True:
        return {
            "status": "Assessing available metadata",
            "interpretation": "",
            "show_design_warnings": True,
            "show_missing_information": True,
        }

    return {
        "status": "Insufficient information",
        "interpretation": (
            "RNA-seq compatibility could not be established, "
            "so experimental-design assessment remains conservative."
        ),
        "show_design_warnings": True,
        "show_missing_information": True,
    }


def analysis_plan_display(
    analysis_plan,
    modality_insight,
):
    """Separate analysis-plan applicability from confidence."""

    compatible = is_rna_seq_compatible(
        modality_insight
    )

    workflow = str(
        getattr(
            analysis_plan,
            "workflow",
            "",
        ) or ""
    ).strip()

    if (
        compatible is False
        or "not applicable" in workflow.lower()
    ):
        return {
            "label": "Planning status",
            "value": "Not applicable",
            "explanation": (
                "No conventional RNA-seq analysis plan is "
                "applicable to the identified sequencing modality."
            ),
        }

    confidence = str(
        getattr(
            analysis_plan,
            "confidence",
            "",
        ) or ""
    ).strip()

    return {
        "label": "Planning confidence",
        "value": confidence or "Not established",
        "explanation": "",
    }


def inspection_summary_planning_value(
    analysis_plan,
    modality_insight,
):
    """Return compact planning value for Inspection Summary."""

    return analysis_plan_display(
        analysis_plan,
        modality_insight,
    )["value"]


def reanalysis_readiness_display(
    reanalysis_readiness,
    modality_insight,
):
    """Make RNA-seq-specific readiness gaps modality-aware."""

    compatible = is_rna_seq_compatible(
        modality_insight
    )

    if compatible is False:
        return {
            "show_design_gap_evidence": False,
            "explanation": (
                "RNA-seq experimental-design completeness is not assessed "
                "because the identified sequencing modality is not compatible "
                "with conventional RNA-seq analysis."
            ),
        }

    if compatible is True:
        return {
            "show_design_gap_evidence": True,
            "explanation": "",
        }

    return {
        "show_design_gap_evidence": True,
        "explanation": "",
    }
