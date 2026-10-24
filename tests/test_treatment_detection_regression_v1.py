import pytest

from rnaseq_nav.intelligence.design_intelligence import (
    _detect_treatment,
)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Cells were treated with drug X at 10 uM", "drug X"),
        ("Cells were treated with drug X at 2.5 mg/ml", "drug X"),
        ("Cells were treated with drug X for 24 hours at 10 uM", "drug X"),
        ("Cells were treated with drug X for 24 hours", "drug X"),
        ("Cells were exposed to drug X for 6 hours", "drug X"),
        ("Cells were treated with drug X", "drug X"),
        ("Cells were exposed to drug X", "drug X"),
        ("Treatment with drug X was performed", "drug X"),
        ("Drug X exposure in cultured cells", "Drug X"),
        ("Drug X treatment", ""),
        ("RNA-seq of untreated cells", ""),
    ],
)
def test_treatment_detection_regression(title, expected):
    assert _detect_treatment(title) == expected


def test_protocol_treatment_evidence_has_priority():
    assert (
        _detect_treatment(
            "Cells were treated with drug A",
            protocol="Cells were exposed to drug B",
        )
        == "drug B"
    )
