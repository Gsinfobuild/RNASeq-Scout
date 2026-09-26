"""
RNASeq Scout

NCBI GEO Client
===============

Retrieves GEO metadata for GEO accession identifiers.

Supported accessions
--------------------
GSE : GEO Series
GSM : GEO Sample

This client retrieves deposited GEO metadata only.
Biological interpretation is performed elsewhere.
"""

from __future__ import annotations

from urllib.parse import urlencode

import requests


class GEOClient:
    """
    Client for retrieving metadata from NCBI GEO.
    """

    BASE_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

    def __init__(
        self,
        email: str | None = None,
        timeout: int = 30,
    ):
        self.email = email
        self.timeout = timeout

    def _build_url(
        self,
        accession: str,
    ) -> str:
        """
        Construct the NCBI GEO accession-display URL.
        """

        params = {
            "acc": accession.strip().upper(),
            "targ": "self",
            "view": "brief",
            "form": "text",
        }

        return f"{self.BASE_URL}?{urlencode(params)}"

    def fetch(
        self,
        accession: str,
    ) -> str:
        """
        Retrieve a GEO accession as text.

        Parameters
        ----------
        accession : str
            GEO accession such as GSE135553 or GSM123456.

        Returns
        -------
        str
            Deposited GEO metadata in text form.

        Raises
        ------
        ValueError
            If the accession is not a supported GEO accession.
        RuntimeError
            If GEO retrieval fails.
        """

        accession = accession.strip().upper()

        if not accession.startswith(("GSE", "GSM")):
            raise ValueError(
                f"GEOClient currently supports GSE and GSM accessions, "
                f"not '{accession}'."
            )

        url = self._build_url(accession)

        headers = {
            "User-Agent": (
                "RNASeq-Scout/1.0 "
                "(metadata retrieval; "
                f"contact={self.email or 'not-specified'})"
            )
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to retrieve GEO accession '{accession}': {exc}"
            ) from exc

        text = response.text.strip()

        if not text:
            raise RuntimeError(
                f"GEO returned an empty response for '{accession}'."
            )

        return text
