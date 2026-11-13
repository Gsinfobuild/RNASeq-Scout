from rnaseq_nav.intelligence.design_intelligence import generate_design_insight
from tests.test_intelligence_layers import make_metadata, SampleAttribute


def inspect_sample(attrs):
    sample = make_metadata(title="Library A")
    sample.sample.attributes = [SampleAttribute(name=k, value=v) for k,v in attrs]
    return generate_design_insight(sample)


def test_explicit_sample_group_takes_priority_over_treatment_and_genotype():
    result = inspect_sample([("experimental_group","Recovery"),("treatment","Saline"),("genotype","WT")])
    assert result.sample_condition == "Recovery"
    assert result.sample_treatment == "Saline"
    assert not result.condition


def test_control_is_not_an_active_treatment():
    result=inspect_sample([("treatment","No treatment (Control)")])
    assert result.sample_control == "control"
    assert not result.sample_treatment


def test_age_stage_and_exposure_have_separate_meanings():
    result=inspect_sample([("age","8 weeks"),("dev_stage","adult"),("treatment","DMSO 24hr")])
    assert result.sample_time_point == "24hr"
    assert result.sample_age == "8 weeks"
    assert result.sample_developmental_stage == "adult"
    assert not result.time_point


def test_opaque_replicate_code_is_preserved():
    result=inspect_sample([("replicate","donor_set_42")])
    assert result.sample_replicate_status=="Replicate label donor_set_42; type unspecified"


def test_genotype_in_title_and_treatment_in_sample_are_distinct():
    data = make_metadata(title="GSM123: Xyz1-KO, tissue B")
    data.sample.attributes = [SampleAttribute(name="genotype", value="Xyz1-KO"),
                              SampleAttribute(name="treatment", value="vehicle")]
    result = generate_design_insight(data)
    assert result.sample_condition == "Xyz1-KO"
    assert result.sample_treatment == "vehicle"


def test_post_injection_phase_does_not_invent_elapsed_time():
    result = inspect_sample([("pre_or_post_injection", "post"), ("treatment", "vehicle")])
    assert result.sample_time_point == "post-injection"
    assert result.sample_condition == "post-injection"
    assert result.sample_treatment == "vehicle"


def test_replicate_type_in_source_name_is_sample_scoped():
    result = inspect_sample([("source_name", "tissue B, biol rep 3")])
    assert result.sample_replicate_status == "Biological replicate 3"


def test_receiving_data_is_not_a_sample_intervention():
    data = make_metadata(title="Library B")
    data.experiment.construction_protocol = "Data was received in compressed files."
    assert generate_design_insight(data).treatment == ""
