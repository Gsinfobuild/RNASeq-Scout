"""
Tests for GEO routing in DatasetDiscovery.fetch().
"""

from unittest.mock import Mock

from rnaseq_nav.discovery.dataset_discovery import DatasetDiscovery
from rnaseq_nav.models import Metadata


def test_gse_routes_to_geo_client_and_parser():
    discovery = DatasetDiscovery(
        email="test@example.com"
    )

    expected = Metadata()

    discovery.geo_client.fetch = Mock(
        return_value="GSE_TEST_RECORD"
    )
    discovery.geo_parser.parse = Mock(
        return_value=expected
    )
    discovery.client.fetch = Mock()

    result = discovery.fetch("GSE135553")

    discovery.geo_client.fetch.assert_called_once_with(
        "GSE135553"
    )
    discovery.geo_parser.parse.assert_called_once_with(
        "GSE_TEST_RECORD"
    )
    discovery.client.fetch.assert_not_called()

    assert result is expected


def test_gsm_routes_to_geo_client_and_parser():
    discovery = DatasetDiscovery(
        email="test@example.com"
    )

    expected = Metadata()

    discovery.geo_client.fetch = Mock(
        return_value="GSM_TEST_RECORD"
    )
    discovery.geo_parser.parse = Mock(
        return_value=expected
    )
    discovery.client.fetch = Mock()

    result = discovery.fetch("GSM4134170")

    discovery.geo_client.fetch.assert_called_once_with(
        "GSM4134170"
    )
    discovery.geo_parser.parse.assert_called_once_with(
        "GSM_TEST_RECORD"
    )
    discovery.client.fetch.assert_not_called()

    assert result is expected


def test_srr_keeps_existing_ncbi_sra_route():
    discovery = DatasetDiscovery(
        email="test@example.com"
    )

    expected = Metadata()

    discovery.client.fetch = Mock(
        return_value=[
            {
                "ExpXml": "<EXPERIMENT/>",
                "Runs": "<RUN_SET/>",
            }
        ]
    )
    discovery.parser.parse = Mock(
        return_value=expected
    )
    discovery.geo_client.fetch = Mock()

    result = discovery.fetch("SRR17730393")

    discovery.client.fetch.assert_called_once_with(
        "SRR17730393"
    )
    discovery.parser.parse.assert_called_once_with(
        "<EXPERIMENT/>",
        "<RUN_SET/>",
    )
    discovery.geo_client.fetch.assert_not_called()

    assert result is expected
