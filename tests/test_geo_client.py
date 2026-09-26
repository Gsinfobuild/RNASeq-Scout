from rnaseq_nav.clients.geo import GEOClient


def test_geo_client_builds_series_url():
    client = GEOClient(email="test@example.org")

    url = client._build_url("gse135553")

    assert "acc=GSE135553" in url
    assert "targ=self" in url
    assert "view=brief" in url
    assert "form=text" in url


def test_geo_client_builds_sample_url():
    client = GEOClient(email="test@example.org")

    url = client._build_url("gsm123456")

    assert "acc=GSM123456" in url


def test_geo_client_rejects_unsupported_accession():
    client = GEOClient()

    try:
        client.fetch("SRR17730393")
    except ValueError as exc:
        assert "supports GSE and GSM" in str(exc)
    else:
        raise AssertionError(
            "Expected GEOClient to reject non-GEO accession."
        )


def test_geo_client_returns_response_text(monkeypatch):
    client = GEOClient(email="test@example.org")

    class FakeResponse:
        text = "!Sample_title = Example sample\n"

        def raise_for_status(self):
            return None

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "rnaseq_nav.clients.geo.requests.get",
        fake_get,
    )

    result = client.fetch("GSM123456")

    assert result == "!Sample_title = Example sample"


def test_geo_client_wraps_request_errors(monkeypatch):
    client = GEOClient()

    def fake_get(*args, **kwargs):
        import requests

        raise requests.RequestException("connection failed")

    monkeypatch.setattr(
        "rnaseq_nav.clients.geo.requests.get",
        fake_get,
    )

    try:
        client.fetch("GSE135553")
    except RuntimeError as exc:
        assert "GSE135553" in str(exc)
        assert "connection failed" in str(exc)
    else:
        raise AssertionError(
            "Expected GEO retrieval failure to raise RuntimeError."
        )
