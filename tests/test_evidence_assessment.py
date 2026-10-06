from dataclasses import dataclass

from rnaseq_nav.evidence.evidence_assessment import (
    EvidenceSource,
    EvidenceStatus,
    assess_design_insight,
    assess_field,
    assess_inspection_result,
    assess_reanalysis_readiness,
)


def test_empty_field_is_unresolved():
    result = assess_field("condition", "")

    assert result.status == EvidenceStatus.UNRESOLVED
    assert result.established is False


def test_observed_field_is_observed():
    result = assess_field(
        "organism",
        "Oncorhynchus mykiss",
    )

    assert result.status == EvidenceStatus.OBSERVED
    assert result.source == EvidenceSource.REPOSITORY
    assert result.established is True


def test_not_established_is_not_established():
    result = assess_field(
        "replicates",
        "Replicate structure could not be established from the available metadata.",
    )

    assert result.status == EvidenceStatus.NOT_ESTABLISHED
    assert result.established is False


def test_design_assessment_does_not_infer_empty_fields():
    @dataclass
    class Design:
        condition: str = ""
        control: str = ""
        treatment: str = ""
        time_point: str = ""
        replicate_information: str = (
            "Replicate structure could not be established from the available metadata."
        )
        design_description: str = (
            "The available metadata do not provide enough information "
            "to establish the experimental design."
        )

    assessments = assess_design_insight(Design())

    by_field = {item.field: item for item in assessments}

    assert by_field["condition"].status == EvidenceStatus.UNRESOLVED
    assert by_field["control"].status == EvidenceStatus.UNRESOLVED
    assert by_field["treatment"].status == EvidenceStatus.UNRESOLVED
    assert by_field["time_point"].status == EvidenceStatus.UNRESOLVED
    assert (
        by_field["replicate_information"].status
        == EvidenceStatus.NOT_ESTABLISHED
    )


def test_reanalysis_evidence_is_preserved():
    @dataclass
    class Readiness:
        observed_evidence: list[str]
        not_established: list[str]
        missing_information: list[str]

    readiness = Readiness(
        observed_evidence=["Representative experiment modality: RNA-seq."],
        not_established=["Control group could not be established."],
        missing_information=["Biological replicate structure."],
    )

    assessments = assess_reanalysis_readiness(readiness)

    assert len(assessments) == 3
    assert assessments[0].status == EvidenceStatus.OBSERVED
    assert assessments[1].status == EvidenceStatus.NOT_ESTABLISHED
    assert assessments[2].status == EvidenceStatus.NOT_ESTABLISHED


def test_inspection_result_is_not_modified():
    @dataclass
    class Design:
        condition: str = "hypoxia"

    @dataclass
    class Result:
        design_insight: object
        reanalysis_readiness: object = None

    result = Result(Design())

    assessments = assess_inspection_result(result)

    assert len(assessments) == 6
    assert result.design_insight.condition == "hypoxia"
