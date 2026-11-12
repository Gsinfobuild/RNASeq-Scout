from types import SimpleNamespace

import pytest

from rnaseq_nav.intelligence.design_intelligence import _detect_control, _detect_time_point
from rnaseq_nav.intelligence.modality_intelligence import generate_modality_insight


def classify(title="", protocol="", strategy="RNA_SEQ"):
    experiment = SimpleNamespace(title=title, construction_protocol=protocol, library_strategy=strategy)
    return generate_modality_insight(SimpleNamespace(experiment=experiment))


@pytest.mark.parametrize("title,protocol,expected", [
    ("donor A", "snRNA-seq libraries were generated from nuclei.", "Single-nucleus RNA-seq"),
    ("donor B", "The system v2.0 was used for scRNA-seq.", "Single-cell RNA-seq"),
    ("Single-cell RNA-seq of donor C", "", "Single-cell RNA-seq"),
    ("bulk RNA-seq", "scRNA-seq libraries were prepared in the other arm.", "RNA-seq"),
    ("Sample A", "No scRNA-seq libraries were prepared.", "RNA-seq"),
    ("RNA-seq", "Cells were sorted into a single-cell suspension.", "RNA-seq"),
])
def test_library_resolution(title, protocol, expected):
    result = classify(title, protocol)
    assert result.modality == expected
    assert result.rna_seq_compatible is (expected == "RNA-seq")


def test_conflicting_amplicon_protocol_abstains():
    result = classify(protocol="DNA extraction was followed by preparation of an ASV feature table using SILVA.")
    assert result.rna_seq_compatible is None
    assert result.compatibility_status == "Uncertain"
    assert result.warnings


def test_pirna_title_refines_specialized_rna():
    result = classify(title="piRNA-seq of a sample", strategy="MIRNA_SEQ")
    assert result.modality == "piRNA sequencing"
    assert result.compatibility_status == "Specialized workflow"


def test_sampling_time_and_control_source():
    assert _detect_time_point("", "Cells were collected and then incubated for 4 hours.") == ""
    assert _detect_time_point("", "Cells were collected at 2.5 h.") == "2.5 h"
    assert _detect_time_point("sample at 24 h", "Cells were harvested at 1 h.") == "24 h"
    assert _detect_control("GSM123: control-1; mouse; RNA-Seq") == "control"
    assert _detect_control("Quality control-1; sequencing") == ""
