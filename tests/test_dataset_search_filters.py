
from rnaseq_nav.discovery.dataset_discovery import DatasetDiscovery
from rnaseq_nav.models import Metadata


def make_metadata(
    project="PRJNA1",
    study="SRP1",
    run="SRR1",
    layout="PAIRED",
    platform="ILLUMINA",
    source="TRANSCRIPTOMIC",
    selection="POLY_A",
):
    metadata = Metadata()
    metadata.project.accession = project
    metadata.study.accession = study
    metadata.run.accession = run
    metadata.experiment.layout = layout
    metadata.experiment.platform = platform
    metadata.experiment.library_source = source
    metadata.experiment.library_selection = selection
    return metadata


def make_discovery(records):
    discovery = DatasetDiscovery(email="test@example.com")
    discovery.client.search = lambda **kwargs: records
    discovery.parser.parse = lambda record: record
    return discovery


def test_layout_filter_is_applied():
    paired = make_metadata(run="SRR1", layout="PAIRED")
    single = make_metadata(run="SRR2", layout="SINGLE")

    results = make_discovery([paired, single]).search(
        organism="test",
        layout="PAIRED",
        diversity="run",
    )

    assert [item.run.accession for item in results] == ["SRR1"]


def test_platform_filter_is_case_insensitive():
    illumina = make_metadata(run="SRR1", platform="ILLUMINA")
    other = make_metadata(run="SRR2", platform="OXFORD_NANOPORE")

    results = make_discovery([illumina, other]).search(
        organism="test",
        platform="illumina",
        diversity="run",
    )

    assert [item.run.accession for item in results] == ["SRR1"]


def test_source_and_selection_filters_are_applied():
    matching = make_metadata(
        run="SRR1",
        source="TRANSCRIPTOMIC",
        selection="POLY_A",
    )
    other = make_metadata(
        run="SRR2",
        source="GENOMIC",
        selection="RANDOM",
    )

    results = make_discovery([matching, other]).search(
        organism="test",
        source="TRANSCRIPTOMIC",
        selection="POLY_A",
        diversity="run",
    )

    assert [item.run.accession for item in results] == ["SRR1"]


def test_run_diversity_preserves_individual_records():
    first = make_metadata(project="PRJNA1", run="SRR1")
    second = make_metadata(project="PRJNA1", run="SRR2")

    results = make_discovery([first, second]).search(
        organism="test",
        diversity="run",
    )

    assert [item.run.accession for item in results] == ["SRR1", "SRR2"]


def test_unknown_diversity_is_rejected():
    discovery = make_discovery([])

    try:
        discovery.search(organism="test", diversity="unknown")
    except ValueError as exc:
        assert "diversity" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for unknown diversity")
