"""
RNASeq Scout

Usage Tracker Tests
===================
"""

from pathlib import Path

from rnaseq_nav.usage.tracker import (
    UsageTracker,
    classify_accession,
)


def test_classify_run_accession():
    assert classify_accession(
        "SRR17730393"
    ) == "run"


def test_classify_experiment_accession():
    assert classify_accession(
        "ERX9504298"
    ) == "experiment"


def test_classify_study_accession():
    assert classify_accession(
        "SRP356545"
    ) == "study"


def test_classify_project_accession():
    assert classify_accession(
        "PRJNA799829"
    ) == "project"


def test_classify_sample_accession():
    assert classify_accession(
        "ERS12470078"
    ) == "sample"


def test_unknown_accession():
    assert classify_accession(
        "UNKNOWN123"
    ) == "other"


def test_record_success(tmp_path: Path):
    tracker = UsageTracker(
        tmp_path / "usage.sqlite3"
    )

    tracker.record_success(
        "SRX33892298"
    )

    assert tracker.total_checks() == 1
    assert tracker.unique_accessions() == 1


def test_repeated_accession_counts_as_two_checks_but_one_unique(
    tmp_path: Path,
):
    tracker = UsageTracker(
        tmp_path / "usage.sqlite3"
    )

    tracker.record_success(
        "SRX33892298"
    )

    tracker.record_success(
        "SRX33892298"
    )

    assert tracker.total_checks() == 2
    assert tracker.unique_accessions() == 1


def test_different_accessions_count_as_unique(
    tmp_path: Path,
):
    tracker = UsageTracker(
        tmp_path / "usage.sqlite3"
    )

    tracker.record_success(
        "SRX33892298"
    )

    tracker.record_success(
        "ERX9504298"
    )

    assert tracker.total_checks() == 2
    assert tracker.unique_accessions() == 2


def test_accession_is_normalized(
    tmp_path: Path,
):
    tracker = UsageTracker(
        tmp_path / "usage.sqlite3"
    )

    tracker.record_success(
        "  erx9504298  "
    )

    tracker.record_success(
        "ERX9504298"
    )

    assert tracker.total_checks() == 2
    assert tracker.unique_accessions() == 1


def test_empty_accession_rejected(
    tmp_path: Path,
):
    tracker = UsageTracker(
        tmp_path / "usage.sqlite3"
    )

    try:
        tracker.record_success("")
    except ValueError as error:
        assert "Accession cannot be empty" in str(error)
    else:
        raise AssertionError(
            "Empty accession should raise ValueError"
        )


def test_summary(
    tmp_path: Path,
):
    tracker = UsageTracker(
        tmp_path / "usage.sqlite3"
    )

    tracker.record_success(
        "SRX33892298"
    )

    tracker.record_success(
        "ERX9504298"
    )

    tracker.record_success(
        "SRX33892298"
    )

    assert tracker.summary() == {
        "total_checks": 3,
        "unique_accessions": 2,
    }
