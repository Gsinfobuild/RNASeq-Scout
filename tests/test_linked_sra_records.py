from types import SimpleNamespace

import pytest

from rnaseq_nav.discovery.dataset_discovery import DatasetDiscovery
from rnaseq_nav.models import StudyExperiment


def make_discovery():
    """Create a discovery instance without initializing network clients."""
    discovery = DatasetDiscovery.__new__(DatasetDiscovery)
    return discovery


def test_linked_record_discovery_from_experiment_uses_parent_study():
    discovery = make_discovery()

    discovery.fetch = lambda accession: SimpleNamespace(
        study=SimpleNamespace(accession="SRP013565")
    )

    expected = [
        StudyExperiment(
            sample_accession="SRS30071355",
            biosample_accession="SAMN61851618",
            experiment_accession="SRX34493783",
            experiment_title="Example RNA-seq experiment",
            run_accessions=["SRR39819551"],
            organism="Homo sapiens",
        )
    ]

    calls = []

    def fake_fetch_study(accession, max_results=1000):
        calls.append(accession)
        return expected

    discovery.fetch_study = fake_fetch_study

    result = discovery.fetch_linked_sra_records(
        "SRX34493783",
        max_records=100,
    )

    assert calls == ["SRP013565"]
    assert result["starting_accession"] == "SRX34493783"
    assert result["study_accession"] == "SRP013565"
    assert result["experiments"] == expected
    assert result["experiment_count"] == 1
    assert result["run_count"] == 1
    assert result["truncated"] is False
    assert result["study_retrieval_limit"] == 1000
    assert result["study_retrieval_cap_reached"] is False
    assert result["complete_link_coverage_verified"] is False


def test_linked_record_discovery_reports_record_limit():
    discovery = make_discovery()

    discovery.fetch = lambda accession: SimpleNamespace(
        study=SimpleNamespace(accession="SRP013565")
    )

    discovery.fetch_study = lambda accession, max_results=1000: [
        StudyExperiment(
            experiment_accession=f"SRX{i}",
            run_accessions=[f"SRR{i}"],
        )
        for i in range(3)
    ]

    result = discovery.fetch_linked_sra_records(
        "SRX123",
        max_records=2,
    )

    assert result["experiment_count"] == 2
    assert result["run_count"] == 2
    assert result["truncated"] is True
    assert result["study_retrieval_cap_reached"] is False


def test_linked_record_discovery_requires_parent_study():
    discovery = make_discovery()

    discovery.fetch = lambda accession: SimpleNamespace(
        study=SimpleNamespace(accession="")
    )

    with pytest.raises(ValueError, match="parent study"):
        discovery.fetch_linked_sra_records("SRX123")


def test_linked_record_discovery_rejects_invalid_limit():
    discovery = make_discovery()

    with pytest.raises(ValueError, match="max_records"):
        discovery.fetch_linked_sra_records(
            "SRX123",
            max_records=0,
        )
