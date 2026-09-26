from rnaseq_nav.accession import detect_accession


def test_detect_geo_series():
    result = detect_accession("GSE135553")

    assert result["accession"] == "GSE135553"
    assert result["database"] == "GEO"
    assert result["type"] == "Series"
    assert result["prefix"] == "GSE"


def test_detect_geo_sample():
    result = detect_accession("gsm123456")

    assert result["accession"] == "GSM123456"
    assert result["database"] == "GEO"
    assert result["type"] == "Sample"
    assert result["prefix"] == "GSM"


def test_detect_geo_platform():
    result = detect_accession("GPL24676")

    assert result["accession"] == "GPL24676"
    assert result["database"] == "GEO"
    assert result["type"] == "Platform"
    assert result["prefix"] == "GPL"


def test_detect_geo_dataset():
    result = detect_accession("GDS1234")

    assert result["accession"] == "GDS1234"
    assert result["database"] == "GEO"
    assert result["type"] == "Dataset"
    assert result["prefix"] == "GDS"


def test_existing_sra_detection_is_unchanged():
    result = detect_accession("srr17730393")

    assert result["accession"] == "SRR17730393"
    assert result["database"] == "NCBI"
    assert result["type"] == "Run"
    assert result["prefix"] == "SRR"
