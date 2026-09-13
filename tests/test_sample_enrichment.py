"""
RNASeq Scout

BioSample Enrichment Tests
==========================

Tests explicit BioSample enrichment without network access.
"""

import pytest

from rnaseq_nav.intelligence.sample_enrichment import (
    enrich_sample_from_biosample,
)
from rnaseq_nav.models import (
    Metadata,
    SampleAttribute,
    SampleMetadata,
)


BIOSAMPLE_XML = """\
<?xml version="1.0" ?>
<BioSampleSet>
  <BioSample accession="SAMEA123456">

    <Description>
      <Title>Example BioSample</Title>

      <Organism taxonomy_id="4081"
                taxonomy_name="Solanum lycopersicum">
        <OrganismName>Solanum lycopersicum</OrganismName>
      </Organism>

      <Comment>
        <Paragraph>BioSample description.</Paragraph>
      </Comment>
    </Description>

    <Attributes>
      <Attribute
          attribute_name="genotype"
          harmonized_name="genotype"
          display_name="genotype">wild type</Attribute>

      <Attribute
          attribute_name="organism part"
          harmonized_name="tissue"
          display_name="tissue">leaf</Attribute>

      <Attribute
          attribute_name="sample name"
          harmonized_name="sample_name"
          display_name="sample name">Sample 1</Attribute>
    </Attributes>

  </BioSample>
</BioSampleSet>
"""


class FakeClient:
    """Minimal fake NCBI client."""

    def __init__(self):
        self.requested_accessions = []

    def fetch_biosample(self, accession):
        self.requested_accessions.append(accession)
        return BIOSAMPLE_XML.encode("utf-8")


def make_metadata():
    """Create metadata containing existing SRA sample information."""

    metadata = Metadata()

    metadata.sample = SampleMetadata(
        accession="ERS123456",
        biosample="SAMEA123456",
        organism="Solanum lycopersicum",
    )

    return metadata


def test_enrichment_retrieves_and_parses_biosample():
    metadata = make_metadata()
    client = FakeClient()

    result = enrich_sample_from_biosample(
        metadata,
        client,
    )

    assert result is metadata
    assert result.sample.biosample == "SAMEA123456"
    assert result.sample.organism == "Solanum lycopersicum"
    assert result.sample.title == "Example BioSample"
    assert result.sample.name == "Sample 1"
    assert result.sample.description == (
        "BioSample description."
    )
    assert len(result.sample.attributes) == 3

    assert client.requested_accessions == [
        "SAMEA123456"
    ]


def test_enrichment_preserves_existing_sra_fields():
    metadata = make_metadata()

    metadata.sample.title = "SRA title"
    metadata.sample.name = "SRA sample"
    metadata.sample.description = "SRA description"

    existing_attribute = SampleAttribute(
        name="source",
        value="SRA-deposited value",
    )

    metadata.sample.attributes.append(
        existing_attribute
    )

    client = FakeClient()

    result = enrich_sample_from_biosample(
        metadata,
        client,
    )

    # BioSample explicitly provides these fields,
    # so its values are preferred.
    assert result.sample.title == "Example BioSample"
    assert result.sample.name == "Sample 1"
    assert result.sample.description == (
        "BioSample description."
    )

    # Existing attributes are preserved.
    assert existing_attribute in result.sample.attributes

    # BioSample attributes are added.
    assert len(result.sample.attributes) == 4


def test_enrichment_preserves_existing_field_when_biosample_is_empty():
    metadata = make_metadata()

    metadata.sample.title = "Existing SRA title"
    metadata.sample.name = "Existing SRA name"
    metadata.sample.description = "Existing description"

    class EmptyFieldParser:
        def parse(self, xml):
            return SampleMetadata(
                biosample="SAMEA123456",
            )

    client = FakeClient()

    result = enrich_sample_from_biosample(
        metadata,
        client,
        parser=EmptyFieldParser(),
    )

    assert result.sample.title == "Existing SRA title"
    assert result.sample.name == "Existing SRA name"
    assert result.sample.description == (
        "Existing description"
    )


def test_enrichment_preserves_existing_metadata_object():
    metadata = make_metadata()
    client = FakeClient()

    result = enrich_sample_from_biosample(
        metadata,
        client,
    )

    assert id(result) == id(metadata)


def test_enrichment_requires_biosample_accession():
    metadata = Metadata()
    metadata.sample = SampleMetadata()

    client = FakeClient()

    with pytest.raises(
        ValueError,
        match="BioSample accession is not available",
    ):
        enrich_sample_from_biosample(
            metadata,
            client,
        )

    assert client.requested_accessions == []


def test_enrichment_rejects_none_metadata():
    client = FakeClient()

    with pytest.raises(
        ValueError,
        match="metadata must be a Metadata object",
    ):
        enrich_sample_from_biosample(
            None,
            client,
        )


def test_enrichment_accepts_explicit_parser():
    metadata = make_metadata()
    client = FakeClient()

    class TrackingParser:
        def __init__(self):
            self.called = False

        def parse(self, xml):
            self.called = True

            return SampleMetadata(
                biosample="SAMEA123456",
                organism="Solanum lycopersicum",
                title="Parsed explicitly",
            )

    parser = TrackingParser()

    result = enrich_sample_from_biosample(
        metadata,
        client,
        parser=parser,
    )

    assert parser.called
    assert result.sample.title == "Parsed explicitly"
