from unittest.mock import Mock

from rnaseq_nav.discovery.dataset_discovery import DatasetDiscovery


def test_fetch_geo_study_builds_study_experiments():
    series_text = """!Series_geo_accession = GSETEST123
!Series_sample_id = GSM100001
!Series_sample_id = GSM100002
"""

    sample_text = {
        "GSM100001": """!Sample_geo_accession = GSM100001
!Sample_title = Sample 1
!Sample_organism_ch1 = Homo sapiens
!Sample_relation = BioSample: SAMN000001
!Sample_relation = SRA: SRX000001
!Sample_library_strategy = RNA-Seq
""",
        "GSM100002": """!Sample_geo_accession = GSM100002
!Sample_title = Sample 2
!Sample_organism_ch1 = Homo sapiens
!Sample_relation = BioSample: SAMN000002
!Sample_relation = SRA: SRX000002
!Sample_library_strategy = RNA-Seq
""",
    }

    discovery = DatasetDiscovery(email="test@example.com")
    discovery.geo_client = Mock()

    def fake_fetch(accession):
        if accession == "GSETEST123":
            return series_text
        return sample_text[accession]

    discovery.geo_client.fetch.side_effect = fake_fetch

    result = discovery.fetch_geo_study(
        "GSETEST123",
        max_samples=10,
    )

    assert result["sample_accessions"] == [
        "GSM100001",
        "GSM100002",
    ]

    assert len(result["study_experiments"]) == 2

    first = result["study_experiments"][0]
    assert first.sample_accession == "GSM100001"
    assert first.biosample_accession == "SAMN000001"
    assert first.experiment_accession == "SRX000001"
    assert first.library_strategy == "RNA-Seq"

    second = result["study_experiments"][1]
    assert second.sample_accession == "GSM100002"
    assert second.biosample_accession == "SAMN000002"
    assert second.experiment_accession == "SRX000002"
    assert second.library_strategy == "RNA-Seq"

    assert discovery.geo_client.fetch.call_count == 3
