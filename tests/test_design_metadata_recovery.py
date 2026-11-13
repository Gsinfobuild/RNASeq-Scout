from rnaseq_nav.intelligence.design_intelligence import generate_design_insight
from tests.test_intelligence_layers import SampleAttribute, make_metadata


def test_sample_condition_is_scoped_and_conflicts_do_not_select_a_group():
    metadata = make_metadata(strategy="ATAC_SEQ", title="Library A")
    metadata.sample.attributes = [SampleAttribute(name="experimental_group", value="Recovery")]
    insight = generate_design_insight(metadata)
    assert insight.sample_condition == "Recovery"
    assert insight.condition == ""
    metadata.sample.attributes.append(SampleAttribute(name="condition", value="Baseline"))
    assert generate_design_insight(metadata).sample_condition == ""


def test_technical_replicate_stays_technical():
    data = make_metadata(strategy="CHIP_SEQ", title="Sample_A_technical_rep2")
    result = generate_design_insight(data)
    assert "Technical replicate 2" in result.replicate_information
    assert "not established" in result.replicate_information


def test_generic_attribute_preserves_submitted_replicate_identifier():
    data = make_metadata(strategy="WGS", title="Library A")
    data.sample.attributes = [SampleAttribute(name="Replication", value="donor-pair B")]
    result = generate_design_insight(data)
    assert result.replicate_information == "Replicate label donor-pair B; type unspecified"


def test_title_condition_with_explicit_assignment():
    data = make_metadata(strategy="RNA_SEQ", title="Sample B; condition: recovery")
    assert generate_design_insight(data).condition == "recovery"
