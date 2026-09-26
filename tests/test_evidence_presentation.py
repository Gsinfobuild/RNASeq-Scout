from types import SimpleNamespace


from rnaseq_nav.ui.evidence_presentation import (
    analysis_plan_display,
    experimental_design_display,
    inspection_summary_planning_value,
)


def modality(compatible):
    return SimpleNamespace(
        rna_seq_compatible=compatible
    )


def plan(
    workflow="RNA-seq analysis",
    confidence="Moderate",
):
    return SimpleNamespace(
        workflow=workflow,
        confidence=confidence,
    )


def test_non_rna_seq_design_is_not_applicable():

    result = experimental_design_display(
        modality(False)
    )

    assert result["status"] == "Not applicable"
    assert result["show_design_warnings"] is False
    assert result["show_missing_information"] is False


def test_rna_seq_design_remains_assessable():

    result = experimental_design_display(
        modality(True)
    )

    assert result["status"] == (
        "Assessing available metadata"
    )
    assert result["show_design_warnings"] is True
    assert result["show_missing_information"] is True


def test_unknown_modality_is_conservative():

    result = experimental_design_display(
        modality(None)
    )

    assert result["status"] == "Insufficient information"
    assert result["show_design_warnings"] is True
    assert result["show_missing_information"] is True


def test_non_rna_seq_plan_is_not_applicable():

    result = analysis_plan_display(
        plan(
            workflow="RNA-seq workflow not applicable",
            confidence="High",
        ),
        modality(False),
    )

    assert result["label"] == "Planning status"
    assert result["value"] == "Not applicable"


def test_rna_seq_plan_retains_confidence():

    result = analysis_plan_display(
        plan(),
        modality(True),
    )

    assert result["label"] == "Planning confidence"
    assert result["value"] == "Moderate"


def test_inspection_summary_uses_applicability():

    result = inspection_summary_planning_value(
        plan(
            workflow="RNA-seq workflow not applicable",
            confidence="High",
        ),
        modality(False),
    )

    assert result == "Not applicable"


def test_non_rna_seq_readiness_hides_design_gaps():

    from rnaseq_nav.ui.evidence_presentation import (
        reanalysis_readiness_display,
    )

    result = reanalysis_readiness_display(
        None,
        modality(False),
    )

    assert result["show_design_gap_evidence"] is False
    assert "not compatible" in result["explanation"]


def test_rna_seq_readiness_keeps_design_gaps():

    from rnaseq_nav.ui.evidence_presentation import (
        reanalysis_readiness_display,
    )

    result = reanalysis_readiness_display(
        None,
        modality(True),
    )

    assert result["show_design_gap_evidence"] is True
    assert result["explanation"] == ""


def test_unknown_modality_keeps_readiness_gaps():

    from rnaseq_nav.ui.evidence_presentation import (
        reanalysis_readiness_display,
    )

    result = reanalysis_readiness_display(
        None,
        modality(None),
    )

    assert result["show_design_gap_evidence"] is True
    assert result["explanation"] == ""
