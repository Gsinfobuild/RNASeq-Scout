from rnaseq_nav.intelligence.design_intelligence import (
    generate_design_insight,
)
from tests.test_intelligence_layers import (
    SampleAttribute,
    make_metadata,
)


def test_explicit_biosample_treatment_is_available_as_sample_evidence():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Thalassia hemprichii sediment sample",
    )
    metadata.sample.attributes = [
        SampleAttribute(
            name="Treatment",
            harmonized_name="treatment",
            display_name="treatment",
            value="Acidification",
        )
    ]

    insight = generate_design_insight(metadata)

    assert any(
        "treatment: Acidification" in feature
        for feature in insight.observed_features
    )
    assert insight.treatment == ""


def test_explicit_biosample_timepoint_is_available_as_sample_evidence():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Thalassia hemprichii sediment sample",
    )
    metadata.sample.attributes = [
        SampleAttribute(name="Time", value="Day30")
    ]

    insight = generate_design_insight(metadata)

    assert any(
        "time: Day30" in feature
        for feature in insight.observed_features
    )
    assert insight.time_point == ""


def test_control_like_treatment_value_is_not_promoted():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="HCT116 parental cells",
    )
    metadata.sample.attributes = [
        SampleAttribute(
            name="Treatment",
            harmonized_name="treatment",
            value="none (parental control)",
        )
    ]

    insight = generate_design_insight(metadata)

    assert insight.treatment == ""


def test_treatment_value_control_is_not_promoted():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Rainbow trout liver",
    )
    metadata.sample.attributes = [
        SampleAttribute(
            name="Treatment",
            harmonized_name="treatment",
            value="control",
        )
    ]

    insight = generate_design_insight(metadata)

    assert insight.treatment == ""
    assert insight.control == ""


def test_paired_sample_annotations_support_partial_confidence_only():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Thalassia hemprichii sediment sample",
    )
    metadata.sample.attributes = [
        SampleAttribute(
            name="Treatment",
            harmonized_name="treatment",
            display_name="treatment",
            value="Acidification",
        ),
        SampleAttribute(
            name="Time",
            harmonized_name="time",
            display_name="time",
            value="Day30",
        ),
    ]

    insight = generate_design_insight(metadata)

    assert insight.sample_treatment == "Acidification"
    assert insight.sample_time_point == "Day30"

    # Sample annotations must not be promoted to study-level assignments.
    assert insight.treatment == ""
    assert insight.time_point == ""

    # Both explicit sample-level annotations support partial confidence.
    assert insight.design_confidence == "Partially characterized"


def test_paired_sample_annotations_support_partial_confidence_with_protocol():
    metadata = make_metadata(
        strategy="RNA_SEQ",
        title="Thalassia hemprichii sediment sample",
    )
    metadata.experiment.construction_protocol = (
        "RNA sequencing library prepared from sediment samples."
    )
    metadata.sample.attributes = [
        SampleAttribute(
            name="Treatment",
            harmonized_name="treatment",
            display_name="treatment",
            value="Acidification",
        ),
        SampleAttribute(
            name="Time",
            harmonized_name="time",
            display_name="time",
            value="Day30",
        ),
    ]

    insight = generate_design_insight(metadata)

    assert insight.sample_treatment == "Acidification"
    assert insight.sample_time_point == "Day30"
    assert insight.treatment == ""
    assert insight.time_point == ""
    assert insight.design_confidence == "Partially characterized"
