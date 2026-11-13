from rnaseq_nav.intelligence.design_intelligence import _detect_time_point, _detect_treatment


def test_ligation_duration_is_technical():
    assert _detect_time_point("ATP 18H ligation Rep 1") == ""
    assert _detect_time_point("18 h adapter ligation; samples at 6 h") == "6 h"
    assert _detect_time_point("adapter ligation for 2 hours") == ""


def test_treatment_of_extracted_material():
    assert _detect_treatment("", "Small RNAs were treated with phosphatase.") == ""
    assert _detect_treatment("", "RNA was treated with enzyme. Cells were treated with vehicle.") == "vehicle"
