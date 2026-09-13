"""
RNASeq Scout

NCBI BioSample Client Tests
===========================

Tests BioSample retrieval behavior without network access.
"""

from io import BytesIO

import pytest

from rnaseq_nav.clients.ncbi import NCBIClient


class FakeHandle:
    """Minimal Entrez handle replacement."""

    def __init__(self, payload):
        self.payload = payload
        self.closed = False

    def read(self):
        return self.payload

    def close(self):
        self.closed = True


def test_fetch_biosample_returns_raw_xml(monkeypatch):
    client = NCBIClient(email="test@example.org")

    esearch_handle = FakeHandle(None)
    efetch_handle = FakeHandle(b"<BioSampleSet><BioSample accession='SAMEA123'/></BioSampleSet>")

    def fake_esearch(**kwargs):
        assert kwargs["db"] == "biosample"
        assert kwargs["term"] == "SAMEA123"
        assert kwargs["retmode"] == "xml"
        return esearch_handle

    def fake_read(handle):
        assert handle is esearch_handle
        return {"IdList": ["12345"]}

    def fake_efetch(**kwargs):
        assert kwargs["db"] == "biosample"
        assert kwargs["id"] == "12345"
        assert kwargs["retmode"] == "xml"
        return efetch_handle

    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.esearch",
        fake_esearch,
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.read",
        fake_read,
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.efetch",
        fake_efetch,
    )

    result = client.fetch_biosample("SAMEA123")

    assert result == (
        b"<BioSampleSet><BioSample accession='SAMEA123'/></BioSampleSet>"
    )
    assert esearch_handle.closed
    assert efetch_handle.closed


def test_fetch_biosample_accepts_sra_sample_accession(monkeypatch):
    client = NCBIClient(email="test@example.org")

    esearch_handle = FakeHandle(None)
    efetch_handle = FakeHandle(b"<BioSampleSet/>")

    def fake_esearch(**kwargs):
        assert kwargs["db"] == "biosample"
        assert kwargs["term"] == "ERS12470078"
        return esearch_handle

    def fake_read(handle):
        return {"IdList": ["33208336"]}

    def fake_efetch(**kwargs):
        assert kwargs["db"] == "biosample"
        assert kwargs["id"] == "33208336"
        return efetch_handle

    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.esearch",
        fake_esearch,
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.read",
        fake_read,
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.efetch",
        fake_efetch,
    )

    result = client.fetch_biosample("ERS12470078")

    assert result == b"<BioSampleSet/>"


def test_fetch_biosample_raises_when_no_record_found(monkeypatch):
    client = NCBIClient(email="test@example.org")

    handle = FakeHandle(None)

    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.esearch",
        lambda **kwargs: handle,
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.read",
        lambda handle: {"IdList": []},
    )

    with pytest.raises(RuntimeError, match="No BioSample record found"):
        client.fetch_biosample("SAMEA999999")

    assert handle.closed


def test_fetch_biosample_wraps_entrez_errors(monkeypatch):
    client = NCBIClient(email="test@example.org")

    def fake_esearch(**kwargs):
        raise OSError("network failure")

    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.esearch",
        fake_esearch,
    )

    with pytest.raises(
        RuntimeError,
        match="Failed to retrieve BioSample",
    ):
        client.fetch_biosample("SAMEA123")


def test_fetch_biosample_preserves_binary_response(monkeypatch):
    client = NCBIClient(email="test@example.org")

    esearch_handle = FakeHandle(None)
    payload = BytesIO(
        b"<BioSampleSet><BioSample/></BioSampleSet>"
    ).getvalue()
    efetch_handle = FakeHandle(payload)

    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.esearch",
        lambda **kwargs: esearch_handle,
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.read",
        lambda handle: {"IdList": ["100"]},
    )
    monkeypatch.setattr(
        "rnaseq_nav.clients.ncbi.Entrez.efetch",
        lambda **kwargs: efetch_handle,
    )

    result = client.fetch_biosample("SAMEA123")

    assert isinstance(result, bytes)
    assert result == payload
