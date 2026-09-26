from rnaseq_nav.parsers.geo_parser import GEOParser


GSM_TEXT = """\
^SAMPLE = GSM4134170
!Sample_title = DF1_0_07_Run_1
!Sample_geo_accession = GSM4134170
!Sample_source_name_ch1 = DF1 cells
!Sample_organism_ch1 = Gallus gallus
!Sample_taxid_ch1 = 9031
!Sample_characteristics_ch1 = cell line: DF-1
!Sample_characteristics_ch1 = virus: Wildtype A/Guinea Fowl/Hong Kong/WF10/99 (wtWF10)
!Sample_characteristics_ch1 = multiplicity of infection: 0.067
!Sample_molecule_ch1 = total RNA
!Sample_instrument_model = NextSeq 500
!Sample_library_selection = cDNA
!Sample_library_source = transcriptomic
!Sample_library_strategy = RNA-Seq
!Sample_relation = BioSample: https://www.ncbi.nlm.nih.gov/biosample/SAMN13072781
!Sample_relation = SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRX7032063
!Sample_series_id = GSE135553
"""


def test_parse_gsm_record():
    metadata = GEOParser().parse(GSM_TEXT)

    assert metadata.sample.accession == "GSM4134170"
    assert metadata.sample.organism == "Gallus gallus"
    assert metadata.sample.biosample == "SAMN13072781"

    assert metadata.study.accession == "GSE135553"
    assert metadata.experiment.accession == "SRX7032063"

    assert metadata.experiment.title == "DF1_0_07_Run_1"
    assert metadata.experiment.library_strategy == "RNA-Seq"
    assert metadata.experiment.library_source == "transcriptomic"
    assert metadata.experiment.library_selection == "cDNA"
    assert metadata.experiment.instrument == "NextSeq 500"

    attributes = {
        attribute.name: attribute.value
        for attribute in metadata.sample.attributes
    }

    assert attributes["cell line"] == "DF-1"
    assert attributes["virus"] == (
        "Wildtype A/Guinea Fowl/Hong Kong/WF10/99 (wtWF10)"
    )
    assert attributes["multiplicity of infection"] == "0.067"
    assert attributes["molecule_ch1"] == "total RNA"


def test_parser_preserves_repeated_characteristics():
    metadata = GEOParser().parse(
        """\
^SAMPLE = GSM1
!Sample_geo_accession = GSM1
!Sample_characteristics_ch1 = treatment: control
!Sample_characteristics_ch1 = time: 24 hours
"""
    )

    values = {
        attribute.name: attribute.value
        for attribute in metadata.sample.attributes
    }

    assert values["treatment"] == "control"
    assert values["time"] == "24 hours"


def test_empty_record_returns_empty_metadata():
    metadata = GEOParser().parse("")

    assert metadata.sample.accession == ""
    assert metadata.study.accession == ""
    assert metadata.experiment.accession == ""


def test_series_sample_accessions():
    text = """\
!Series_geo_accession = GSE135553
!Series_sample_id = GSM4134170
!Series_sample_id = GSM4134171
!Series_sample_id = GSM4134172
!Series_sample_id = GSM4134171
"""

    accessions = GEOParser().sample_accessions(text)

    assert accessions == [
        "GSM4134170",
        "GSM4134171",
        "GSM4134172",
    ]
