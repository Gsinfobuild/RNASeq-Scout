from rnaseq_nav.intelligence.study_biosample_evidence import (
    generate_study_biosample_evidence,
)
from rnaseq_nav.models import StudyExperiment


class FakeClient:
    def __init__(self, xml_by_accession):
        self.xml_by_accession = xml_by_accession
        self.calls = []

    def fetch_biosample(self, accession):
        self.calls.append(accession)

        if accession not in self.xml_by_accession:
            raise RuntimeError(
                f"BioSample not found: {accession}"
            )

        return self.xml_by_accession[accession]


BIOSAMPLE_XML_1 = """
<BioSampleSet>
  <BioSample accession="SAMN000001">
    <Description>
      <Title>Sample 1</Title>
      <Comment>Test sample one</Comment>
    </Description>
    <Organism>
      <OrganismName>Homo sapiens</OrganismName>
    </Organism>
    <Attributes>
      <Attribute attribute_name="condition">control</Attribute>
      <Attribute attribute_name="replicate">biological replicate 1</Attribute>
    </Attributes>
  </BioSample>
</BioSampleSet>
"""


BIOSAMPLE_XML_2 = """
<BioSampleSet>
  <BioSample accession="SAMN000002">
    <Description>
      <Title>Sample 2</Title>
      <Comment>Test sample two</Comment>
    </Description>
    <Organism>
      <OrganismName>Homo sapiens</OrganismName>
    </Organism>
    <Attributes>
      <Attribute attribute_name="condition">treated</Attribute>
      <Attribute attribute_name="replicate">biological replicate 2</Attribute>
    </Attributes>
  </BioSample>
</BioSampleSet>
"""


def test_duplicate_biosample_is_retrieved_only_once():
    records = [
        StudyExperiment(
            sample_accession="SRS001",
            biosample_accession="SAMN000001",
            experiment_accession="SRX001",
            organism="Homo sapiens",
        ),
        StudyExperiment(
            sample_accession="SRS002",
            biosample_accession="SAMN000001",
            experiment_accession="SRX002",
            organism="Homo sapiens",
        ),
    ]

    client = FakeClient(
        {"SAMN000001": BIOSAMPLE_XML_1}
    )

    evidence = generate_study_biosample_evidence(
        records,
        client,
    )

    assert client.calls == ["SAMN000001"]
    assert evidence.total_study_experiments == 2
    assert evidence.unique_biosample_count == 1
    assert evidence.retrieved_biosample_count == 1
    assert evidence.failed_biosample_count == 0
    assert len(evidence.samples) == 1


def test_raw_biosample_attributes_are_preserved():
    records = [
        StudyExperiment(
            sample_accession="SRS001",
            biosample_accession="SAMN000001",
            experiment_accession="SRX001",
            organism="Homo sapiens",
        )
    ]

    client = FakeClient(
        {"SAMN000001": BIOSAMPLE_XML_1}
    )

    evidence = generate_study_biosample_evidence(
        records,
        client,
    )

    sample = evidence.samples[0]

    assert sample.biosample_accession == "SAMN000001"
    assert sample.sample_accession == "SRS001"
    assert sample.experiment_accession == "SRX001"
    assert sample.organism == "Homo sapiens"
    assert sample.title == "Sample 1"
    assert sample.retrieval_status == "Retrieved"

    attribute_values = {
        attribute.name: attribute.value
        for attribute in sample.attributes
    }

    assert attribute_values["condition"] == "control"
    assert (
        attribute_values["replicate"]
        == "biological replicate 1"
    )


def test_attribute_values_are_aggregated_as_observed_metadata():
    records = [
        StudyExperiment(
            sample_accession="SRS001",
            biosample_accession="SAMN000001",
            experiment_accession="SRX001",
            organism="Homo sapiens",
        ),
        StudyExperiment(
            sample_accession="SRS002",
            biosample_accession="SAMN000002",
            experiment_accession="SRX002",
            organism="Homo sapiens",
        ),
    ]

    client = FakeClient(
        {
            "SAMN000001": BIOSAMPLE_XML_1,
            "SAMN000002": BIOSAMPLE_XML_2,
        }
    )

    evidence = generate_study_biosample_evidence(
        records,
        client,
    )

    assert evidence.attribute_values["condition"] == {
        "control": 1,
        "treated": 1,
    }

    assert evidence.attribute_values["replicate"] == {
        "biological replicate 1": 1,
        "biological replicate 2": 1,
    }

    assert "condition" in evidence.observed_attribute_names
    assert "replicate" in evidence.observed_attribute_names


def test_missing_biosample_accessions_are_reported():
    records = [
        StudyExperiment(
            sample_accession="SRS001",
            biosample_accession="",
            experiment_accession="SRX001",
            organism="Homo sapiens",
        ),
        StudyExperiment(
            sample_accession="SRS002",
            biosample_accession="",
            experiment_accession="SRX002",
            organism="Homo sapiens",
        ),
    ]

    client = FakeClient({})

    evidence = generate_study_biosample_evidence(
        records,
        client,
    )

    assert evidence.total_study_experiments == 2
    assert evidence.unique_biosample_count == 0
    assert evidence.retrieved_biosample_count == 0
    assert evidence.failed_biosample_count == 0
    assert evidence.missing_biosample_count == 2
    assert evidence.samples == []

    assert len(evidence.warnings) == 1
    assert (
        "No BioSample accessions"
        in evidence.warnings[0]
    )


def test_failed_biosample_does_not_stop_other_samples():
    records = [
        StudyExperiment(
            sample_accession="SRS001",
            biosample_accession="SAMN000001",
            experiment_accession="SRX001",
            organism="Homo sapiens",
        ),
        StudyExperiment(
            sample_accession="SRS002",
            biosample_accession="SAMN000002",
            experiment_accession="SRX002",
            organism="Homo sapiens",
        ),
    ]

    client = FakeClient(
        {"SAMN000001": BIOSAMPLE_XML_1}
    )

    evidence = generate_study_biosample_evidence(
        records,
        client,
    )

    assert evidence.unique_biosample_count == 2
    assert evidence.retrieved_biosample_count == 1
    assert evidence.failed_biosample_count == 1

    assert len(evidence.samples) == 2

    retrieved = next(
        sample
        for sample in evidence.samples
        if sample.biosample_accession == "SAMN000001"
    )

    failed = next(
        sample
        for sample in evidence.samples
        if sample.biosample_accession == "SAMN000002"
    )

    assert retrieved.retrieval_status == "Retrieved"
    assert failed.retrieval_status == "Failed"
    assert "RuntimeError" in failed.retrieval_error

    assert any(
        "could not be retrieved" in warning
        for warning in evidence.warnings
    )
