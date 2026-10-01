from rnaseq_nav.evidence.source_enrichment import enrich_source_evidence


def test_source_enrichment(monkeypatch):
    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    def fake_get(url, params=None, **kwargs):
        if url.endswith("esearch.fcgi"):
            return Response({"esearchresult": {"idlist": ["12345"]}})
        if url.endswith("esummary.fcgi"):
            return Response({
                "result": {
                    "12345": {
                        "uid": "12345",
                        "title": "Example RNA-seq study",
                        "fulljournalname": "Example Journal",
                        "pubdate": "2025",
                        "authors": [{"name": "Doe J"}],
                    }
                }
            })
        if url.endswith("elink.fcgi"):
            return Response({
                "linksets": [{
                    "linksetdbs": [{
                        "dbto": "pmc",
                        "links": ["99999"],
                    }]
                }]
            })
        raise AssertionError(url)

    monkeypatch.setattr(
        "rnaseq_nav.evidence.source_enrichment.requests.get",
        fake_get,
    )

    result = enrich_source_evidence("GSE135553")

    assert result.publication_count == 1
    assert result.pmc_count == 1
    assert any(
        item.source_name == "NCBI GEO"
        for item in result.items
    )
    assert any(
        item.identifier == "12345"
        for item in result.items
    )
    assert any(
        item.identifier == "PMC99999"
        for item in result.items
    )


def test_run_accession_does_not_query_pubmed(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("PubMed must not be queried")

    monkeypatch.setattr(
        "rnaseq_nav.evidence.source_enrichment.requests.get",
        fail,
    )

    result = enrich_source_evidence("SRR17730393")

    assert result.retrieval_status == "Repository evidence only"
    assert result.items[0].source_name == "NCBI SRA"
