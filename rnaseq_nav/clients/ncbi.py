"""
RNASeq Navigator

NCBI Entrez Client

Version 2.1

Purpose
-------
Provides a reusable interface for retrieving RNA-seq
metadata from the NCBI Sequence Read Archive (SRA).

Public API
----------
fetch(accession)
    Retrieve one dataset by accession.

search(query)
    Search SRA using an Entrez query.
"""

from __future__ import annotations

import time
from typing import List

from Bio import Entrez


class NCBIClient:
    """
    Client for retrieving RNA-seq metadata from NCBI.
    """

    # -----------------------------------------------------

    def __init__(
        self,
        email: str,
        api_key: str | None = None,
        verbose: bool = False,
    ):

        self.email = email
        self.api_key = api_key
        self.verbose = verbose

        Entrez.email = email
        Entrez.tool = "RNASeq-Navigator"

        if api_key:
            Entrez.api_key = api_key

    # -----------------------------------------------------
    # Logger
    # -----------------------------------------------------

    def _log(
        self,
        message: str,
        level: str = "INFO",
    ):

        if self.verbose:
            print(f"[{level}] {message}")

    # -----------------------------------------------------
    # Internal helper
    # -----------------------------------------------------

    def _fetch_summary(self, uid: str):
        """
        Retrieve one parsed ESummary record.
        """

        handle = Entrez.esummary(
            db="sra",
            id=uid,
            retmode="xml",
        )

        try:
            summary = Entrez.read(handle)
        finally:
            handle.close()

        return summary

    # -----------------------------------------------------
    # Fetch one accession
    # -----------------------------------------------------

    def fetch(self, accession: str):
        """
        Retrieve one SRA record by accession.

        Supports:
            SRR, SRX, SRP
            ERR, ERX, ERP
            DRR, DRX, DRP
            PRJNA, PRJEB, PRJDB
            SAMN, SAMEA, SAMD
        """

        self._log(f"Searching accession: {accession}")

        try:

            handle = Entrez.esearch(
                db="sra",
                term=accession,
                retmode="xml",
            )

            try:
                result = Entrez.read(handle)
            finally:
                handle.close()

            ids = result.get("IdList", [])

            if not ids:
                raise ValueError(
                    f"No SRA record found for '{accession}'."
                )

            uid = ids[0]

            self._log(f"UID = {uid}")

            return self._fetch_summary(uid)

        except Exception as error:

            raise RuntimeError(
                f"Failed to retrieve '{accession}'. "
                f"{type(error).__name__}: {error}"
            ) from error

    # -----------------------------------------------------
    # Fetch all records belonging to a study
    # -----------------------------------------------------

    def fetch_study(
        self,
        accession: str,
        max_results: int = 1000,
    ) -> List:

        """
        Retrieve all SRA records returned for a study-level
        accession.

        Unlike fetch(), which preserves the historical
        single-record behavior, this method retrieves the
        complete set of SRA records returned by Entrez.

        Parameters
        ----------
        accession : str
            Study-level accession such as SRP, ERP, or DRP.

        max_results : int
            Maximum number of SRA records to retrieve.

        Returns
        -------
        List
            Parsed ESummary records.
        """

        self._log(
            f"Searching study accession: {accession}"
        )

        try:

            handle = Entrez.esearch(
                db="sra",
                term=accession,
                retmax=max_results,
                retmode="xml",
            )

            try:
                result = Entrez.read(handle)
            finally:
                handle.close()

            ids = result.get("IdList", [])

            self._log(
                f"Study records found: {len(ids)}"
            )

            if not ids:
                raise ValueError(
                    f"No SRA records found for '{accession}'."
                )

            summaries = []

            for uid in ids:

                summaries.append(
                    self._fetch_summary(uid)
                )

                if not self.api_key:
                    time.sleep(0.34)
                else:
                    time.sleep(0.11)

            return summaries

        except Exception as error:

            raise RuntimeError(
                f"Failed to retrieve study '{accession}'. "
                f"{type(error).__name__}: {error}"
            ) from error

    # -----------------------------------------------------
    # Fetch BioProject record
    # -----------------------------------------------------

    def fetch_bioproject(
        self,
        accession: str,
    ):
        """
        Retrieve the BioProject XML record for an accession.
        """

        self._log(
            f"Fetching BioProject: {accession}"
        )

        try:

            handle = Entrez.esearch(
                db="bioproject",
                term=accession,
                retmode="xml",
            )

            try:
                result = Entrez.read(handle)
            finally:
                handle.close()

            ids = result.get("IdList", [])

            if not ids:
                raise ValueError(
                    f"No BioProject record found for '{accession}'."
                )

            uid = ids[0]

            handle = Entrez.efetch(
                db="bioproject",
                id=uid,
                retmode="xml",
            )

            try:
                return handle.read()
            finally:
                handle.close()

        except Exception as error:

            raise RuntimeError(
                f"Failed to retrieve BioProject '{accession}'. "
                f"{type(error).__name__}: {error}"
            ) from error

    # -----------------------------------------------------
    # Fetch BioSample record
    # -----------------------------------------------------

    def fetch_biosample(
        self,
        accession: str,
    ):
        """
        Retrieve a BioSample XML record for an accession.

        Supports BioSample accessions such as SAMEA, SAMN,
        and SAMD, as well as SRA sample accessions such as
        ERS, SRS, and DRS when NCBI resolves them to a
        BioSample record.

        Parameters
        ----------
        accession : str
            BioSample or SRA sample accession.

        Returns
        -------
        bytes
            Raw BioSample XML returned by NCBI.

        Notes
        -----
        This method performs retrieval only. XML interpretation
        is handled separately by BioSampleParser.
        """

        self._log(
            f"Fetching BioSample: {accession}"
        )

        try:

            handle = Entrez.esearch(
                db="biosample",
                term=accession,
                retmode="xml",
            )

            try:
                result = Entrez.read(handle)
            finally:
                handle.close()

            ids = result.get("IdList", [])

            if not ids:
                raise ValueError(
                    f"No BioSample record found for '{accession}'."
                )

            uid = ids[0]

            self._log(
                f"BioSample UID = {uid}"
            )

            handle = Entrez.efetch(
                db="biosample",
                id=uid,
                retmode="xml",
            )

            try:
                return handle.read()
            finally:
                handle.close()

        except Exception as error:

            raise RuntimeError(
                f"Failed to retrieve BioSample '{accession}'. "
                f"{type(error).__name__}: {error}"
            ) from error

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    def search(
        self,
        query: str,
        max_results: int = 20,
    ) -> List:

        self._log(f"Query: {query}")

        try:

            handle = Entrez.esearch(
                db="sra",
                term=query,
                retmax=max_results,
                retmode="xml",
            )

            try:
                result = Entrez.read(handle)
            finally:
                handle.close()

            ids = result.get("IdList", [])

            self._log(f"Candidates found: {len(ids)}")

            summaries = []

            for uid in ids:

                summaries.append(
                    self._fetch_summary(uid)
                )

                # Respect NCBI rate limits
                if not self.api_key:
                    time.sleep(0.34)
                else:
                    time.sleep(0.11)

            return summaries

        except Exception as error:

            raise RuntimeError(
                f"Search failed. "
                f"{type(error).__name__}: {error}"
            ) from error
