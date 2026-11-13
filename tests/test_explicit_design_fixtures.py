"""Synthetic design-field regression fixtures: five fields, four cue types, five variants."""
import pytest
from rnaseq_nav.intelligence.design_intelligence import generate_design_insight
from tests.test_intelligence_layers import make_metadata


def fixtures():
    cases = []
    def add(field, title, expected, protocol=""):
        cases.append(pytest.param(field, title, protocol, expected, id=f"{field}-{len(cases)+1:03}"))

    for gene, group, stress, age in zip(
        ("Actb","Clock","Cry1","Per1","Arntl"), ("baseline","recovery","sham","washout","replete"),
        ("oxygen","salt","thermal","osmotic","water"), ("young","aged","adult","old","young"),
    ):
        add("condition", f"{gene}_KO_rep1", gene+" knockout")
        add("condition", f"{gene} library; experimental group: {group}", group)
        add("condition", f"{gene} under {stress} stress", stress+" stress")
        add("condition", f"{gene}_{age}_WT", age+" wild type")

    for i, label in enumerate(("cultures","plants","cells","organoids","explants"),1):
        add("control", f"vehicle control; {label}", "vehicle control")
        add("control", f"control-{i}; {label}", "control")
        add("control", f"mock-treated {label}", "mock-treated")
        add("control", f"Sequencing quality control metrics for {label}", "")

    for agent in ("insulin","dexamethasone","caffeine","saline","estradiol"):
        add("treatment", f"Cells treated with {agent}", agent)
        add("treatment", f"Cells exposed to {agent}", agent)
        add("treatment", f"Expression after treatment with {agent}", agent)
        add("treatment", f"Library aliquot ({agent} study)", "", "Extracted RNA was treated with DNase.")

    for i in (2,3,4,6,8):
        add("time_point", f"Sample at {i} h", f"{i} h")
        add("time_point", f"Collection on day {i}", f"Day {i}")
        add("time_point", f"Embryo at {i}-cell stage", f"{i}-cell stage")
        add("time_point", f"Adapter ligation for {i} hours", "")

    for i in (1,2,3,4,5):
        add("replicate_information", f"Sample_A_rep{i}", f"Replicate {i}; type unspecified")
        add("replicate_information", f"Sample_A_biological_rep{i}", f"Biological replicate {i} is explicitly identified in the experiment title.")
        add("replicate_information", f"Sample_A_technical_rep{i}", f"Technical replicate {i}; biological replicate status is not established.")
        add("replicate_information", f"Pooled tissue preparation {i}", "One pooled biological replicate per sample",
            "Tissues from each specimen were pooled as one biological replicate.")
    return cases


@pytest.mark.parametrize("field,title,protocol,expected", fixtures())
def test_synthetic_design_field(field, title, protocol, expected):
    metadata = make_metadata(organism="Mus musculus", title=title)
    metadata.experiment.construction_protocol = protocol
    result = generate_design_insight(metadata)
    assert getattr(result, field) == expected
