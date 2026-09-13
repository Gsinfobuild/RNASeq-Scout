"""
RNASeq Scout

BioSample Parser Tests
======================

Tests raw parsing of NCBI BioSample XML without requiring
network access.
"""

from rnaseq_nav.parsers.biosample_parser import (
    BioSampleParser,
)


BIOSAMPLE_XML = """\
<?xml version="1.0" ?>
<BioSampleSet>
  <BioSample
      access="public"
      id="33208336"
      accession="SAMEA110371881">

    <Ids>
      <Id db="BioSample" is_primary="1">
        SAMEA110371881
      </Id>
      <Id db="SRA">
        ERS12470078
      </Id>
    </Ids>

    <Description>
      <Title>Sample 82</Title>

      <Organism
          taxonomy_id="4081"
          taxonomy_name="Solanum lycopersicum">
        <OrganismName>
          Solanum lycopersicum
        </OrganismName>
      </Organism>

      <Comment>
        <Paragraph>
          Three biological replicates were collected.
        </Paragraph>
      </Comment>
    </Description>

    <Attributes>

      <Attribute
          attribute_name="genotype"
          harmonized_name="genotype"
          display_name="genotype">
        wild type genotype
      </Attribute>

      <Attribute
          attribute_name="organism part"
          harmonized_name="tissue"
          display_name="tissue">
        terminal leaflet
      </Attribute>

      <Attribute
          attribute_name="infect">
        nematode Meloidogyne incognita
      </Attribute>

      <Attribute
          attribute_name="sample name"
          harmonized_name="sample_name"
          display_name="sample name">
        E-MTAB-11956:Sample 82
      </Attribute>

    </Attributes>

  </BioSample>
</BioSampleSet>
"""


def test_biosample_accession_is_parsed():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    assert metadata.biosample == (
        "SAMEA110371881"
    )


def test_biosample_title_is_parsed():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    assert metadata.title == "Sample 82"


def test_biosample_organism_is_parsed():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    assert metadata.organism == (
        "Solanum lycopersicum"
    )


def test_biosample_comment_is_preserved():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    assert (
        "Three biological replicates were collected."
        in metadata.description
    )


def test_structured_attributes_are_preserved():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    assert len(metadata.attributes) == 4


def test_attribute_fields_are_preserved():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    genotype = next(
        item
        for item in metadata.attributes
        if item.name == "genotype"
    )

    assert genotype.value == (
        "wild type genotype"
    )

    assert genotype.harmonized_name == (
        "genotype"
    )

    assert genotype.display_name == (
        "genotype"
    )


def test_harmonized_attribute_name_is_preserved():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    tissue = next(
        item
        for item in metadata.attributes
        if item.name == "organism part"
    )

    assert tissue.harmonized_name == "tissue"
    assert tissue.display_name == "tissue"
    assert tissue.value == "terminal leaflet"


def test_sample_name_is_extracted_only_when_explicitly_deposited():

    metadata = BioSampleParser().parse(
        BIOSAMPLE_XML
    )

    assert metadata.name == (
        "E-MTAB-11956:Sample 82"
    )


def test_empty_xml_returns_empty_metadata():

    metadata = BioSampleParser().parse("")

    assert metadata.biosample == ""
    assert metadata.organism == ""
    assert metadata.title == ""
    assert metadata.name == ""
    assert metadata.attributes == []


def test_missing_biosample_element_returns_empty_metadata():

    xml = """
    <BioSampleSet>
    </BioSampleSet>
    """

    metadata = BioSampleParser().parse(xml)

    assert metadata.biosample == ""
    assert metadata.attributes == []
