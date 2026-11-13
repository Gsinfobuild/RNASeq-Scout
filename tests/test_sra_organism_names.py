import pytest
from rnaseq_nav.parsers.sra_parser import SRAParser


@pytest.mark.parametrize("attrs, expected", [
    ('ScientificName="Mus musculus" CommonName="house mouse"', "Mus musculus"),
    ('ScientificName=" " CommonName="house mouse"', "house mouse"),
    ('CommonName="house mouse"', "house mouse"),
    ('taxid="10090"', ""),
])
def test_reported_organism_names_at_experiment_and_study_level(attrs, expected):
    xml = f'<Experiment acc="SRX1"/><Organism {attrs}/>'
    parser = SRAParser()
    assert parser.parse(xml, "").sample.organism == expected
    study, = parser.parse_study_experiments([{"ExpXml": xml, "Runs": ""}])
    assert study.organism == expected
