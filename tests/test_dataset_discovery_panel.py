from types import SimpleNamespace

from rnaseq_nav.ui.dataset_discovery_panel import _metadata_to_row


def test_metadata_to_row_uses_run_and_nested_experiment_fields():
    metadata = SimpleNamespace(
        run=SimpleNamespace(accession="SRR123"),
        study=SimpleNamespace(accession="SRP123", organism="Homo sapiens"),
        project=SimpleNamespace(accession="PRJNA123"),
        organism="Homo sapiens",
        experiment=SimpleNamespace(
            accession="SRX123",
            title="Example RNA sequencing study",
            layout="PAIRED",
            platform="ILLUMINA",
            library_source="TRANSCRIPTOMIC",
            library_selection="cDNA",
        ),
    )

    row = _metadata_to_row(metadata)

    assert row["Run accession"] == "SRR123"
    assert row["Study accession"] == "SRP123"
    assert row["Project accession"] == "PRJNA123"
    assert row["Organism"] == "Homo sapiens"
    assert row["Title"] == "Example RNA sequencing study"
    assert row["Layout"] == "PAIRED"
    assert row["Platform"] == "ILLUMINA"
    assert row["Library source"] == "TRANSCRIPTOMIC"
    assert row["Library selection"] == "cDNA"


def test_metadata_to_row_falls_back_to_experiment_accession():
    metadata = SimpleNamespace(
        run=SimpleNamespace(accession=""),
        study=SimpleNamespace(accession=""),
        project=SimpleNamespace(accession=""),
        organism="",
        title="Fallback title",
        experiment=SimpleNamespace(
            accession="SRX456",
            title="",
            layout="",
            platform="",
            library_source="",
            library_selection="",
        ),
    )

    row = _metadata_to_row(metadata)

    assert row["Run accession"] == "SRX456"
    assert row["Title"] == "Fallback title"
    assert row["Organism"] == ""
