"""Source-aware evidence enrichment.

Explicit repository-to-publication links are preferred. Accession-based
PubMed search is a fallback and is labelled as an association rather than
a confirmed source link.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import os
import re

import requests

NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "RNASeq-Scout/1.0"
STUDY_PREFIXES = (
    "GSE", "GSM", "SRP", "SRS", "SRX", "ERP", "ERS", "DRP", "DRS",
    "PRJNA", "PRJNB", "PRJEB", "PRJDB",
)


@dataclass
class SourceEvidenceItem:
    source_type: str = ""
    source_name: str = ""
    identifier: str = ""
    title: str = ""
    status: str = "Observed"
    confidence: str = "Direct"
    url: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceAwareEvidence:
    accession: str = ""
    attempted: bool = False
    retrieval_status: str = "Not attempted"
    publication_count: int = 0
    pmc_count: int = 0
    items: list[SourceEvidenceItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _headers() -> dict[str, str]:
    email = os.getenv("NCBI_EMAIL", "").strip()
    value = USER_AGENT
    if email:
        value += f" (mailto:{email})"
    return {"User-Agent": value}


def _get(url: str, params: dict[str, Any]) -> requests.Response:
    response = requests.get(url, params=params, headers=_headers(), timeout=15)
    response.raise_for_status()
    return response


def _repository_for(accession: str) -> str:
    value = accession.strip().upper()
    if value.startswith(("GSE", "GSM")):
        return "NCBI GEO"
    if value.startswith(("SRP", "SRS", "SRX", "SRR", "ERP", "ERS", "DRP", "DRS")):
        return "NCBI SRA"
    if value.startswith(("PRJNA", "PRJNB", "PRJEB", "PRJDB")):
        return "NCBI BioProject"
    return "Unknown"


def _pubmed_ids_for_accession(accession: str) -> list[str]:
    response = _get(
        f"{NCBI_EUTILS}/esearch.fcgi",
        {"db": "pubmed", "term": f"{accession}[All Fields]", "retmode": "json", "retmax": 20},
    )
    payload = response.json()
    return [
        str(item).strip()
        for item in payload.get("esearchresult", {}).get("idlist", [])
        if str(item).strip()
    ]


def _geo_explicit_pubmed_ids(accession: str) -> list[str]:
    """Read explicit PubMed identifiers deposited in a GEO record."""
    if not accession.upper().startswith(("GSE", "GSM")):
        return []
    try:
        from rnaseq_nav.clients.geo import GEOClient
        text = GEOClient().fetch(accession.upper())
    except Exception:
        return []

    ids: list[str] = []
    for line in str(text).splitlines():
        if "pubmed_id" not in line.lower():
            continue
        match = re.search(r"(\d{5,9})\s*$", line.strip())
        if match and match.group(1) not in ids:
            ids.append(match.group(1))
    return ids


def _pubmed_summaries(ids: list[str]) -> list[dict[str, Any]]:
    if not ids:
        return []
    response = _get(
        f"{NCBI_EUTILS}/esummary.fcgi",
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
    )
    payload = response.json().get("result", {})
    summaries = []
    for identifier in ids:
        item = payload.get(str(identifier))
        if not isinstance(item, dict):
            continue
        summaries.append({
            "pmid": str(identifier),
            "title": str(item.get("title", "")).strip(),
            "journal": str(item.get("fulljournalname", "")).strip(),
            "pubdate": str(item.get("pubdate", "")).strip(),
            "authors": [
                str(author.get("name", "")).strip()
                for author in item.get("authors", [])
                if isinstance(author, dict) and str(author.get("name", "")).strip()
            ],
        })
    return summaries


def _pmc_ids_for_pubmed(ids: list[str]) -> dict[str, str]:
    """
    Resolve PubMed IDs to PMC IDs using NCBI ELink.

    NCBI ELink responses may identify the source PubMed record
    explicitly through ``ids`` or may omit that identifier from
    individual linksets. Handle both forms while preserving the
    requested PubMed-to-PMC relationship.
    """
    if not ids:
        return {}

    response = requests.get(
        f"{NCBI_EUTILS}/elink.fcgi",
        {
            "dbfrom": "pubmed",
            "db": "pmc",
            "id": ",".join(ids),
            "retmode": "json",
        },
        timeout=15,
    )

    response.raise_for_status()
    payload = response.json()

    requested_ids = [
        str(value).strip()
        for value in ids
        if str(value).strip()
    ]

    result = {}

    for block_index, block in enumerate(
        payload.get("linksets", []) or []
    ):
        if not isinstance(block, dict):
            continue

        pubmed_id = ""

        # Normal NCBI ELink form:
        # {"ids": ["12345"], ...}
        block_ids = block.get("ids")

        if isinstance(block_ids, list):
            for value in block_ids:
                candidate = str(value).strip()
                if candidate in requested_ids:
                    pubmed_id = candidate
                    break

        # Be tolerant of alternate key capitalization.
        if not pubmed_id:
            for key in ("Id", "id", "IdList"):
                value = block.get(key)

                if isinstance(value, list):
                    for candidate in value:
                        candidate = str(candidate).strip()
                        if candidate in requested_ids:
                            pubmed_id = candidate
                            break
                    if pubmed_id:
                        break

                elif value not in (None, ""):
                    candidate = str(value).strip()
                    if candidate in requested_ids:
                        pubmed_id = candidate
                        break

        # The compact response used by the regression test does not
        # include the PubMed ID inside the linkset. If only one
        # PubMed ID was requested, the mapping is unambiguous.
        if not pubmed_id and len(requested_ids) == 1:
            pubmed_id = requested_ids[0]

        # For multiple IDs, use linkset order only when the response
        # omitted source IDs entirely.
        if not pubmed_id and block_index < len(requested_ids):
            pubmed_id = requested_ids[block_index]

        if pubmed_id not in requested_ids:
            continue

        for linkset in block.get("linksetdbs", []) or []:
            if not isinstance(linkset, dict):
                continue

            dbto = str(
                linkset.get("dbto", "")
            ).strip().lower()

            if dbto != "pmc":
                continue

            links = linkset.get("links", []) or []

            if not isinstance(links, list):
                continue

            for target in links:
                target = str(target).strip()

                if target:
                    result[pubmed_id] = target
                    break

            if pubmed_id in result:
                break

    return result


def _extract_pmc_ids(payload) -> list[str]:
    """Extract PMC IDs from an NCBI ELink JSON payload."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            dbto = str(node.get("dbto", "")).strip().lower()
            if dbto == "pmc":
                links = node.get("links", [])
                if isinstance(links, list):
                    for value in links:
                        value = str(value).strip()
                        if value:
                            found.add(value)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return sorted(found)


def enrich_source_evidence(accession: str) -> SourceAwareEvidence:

    _normalized_accession = str(accession or "").strip().upper()

    if re.match(r"^(SRR|ERR|DRR)\d+$", _normalized_accession):
        return SourceAwareEvidence(
            accession=_normalized_accession,
            attempted=True,
            retrieval_status="Repository evidence only",
            publication_count=0,
            pmc_count=0,
            items=[
                SourceEvidenceItem(
                    source_type="Repository",
                    source_name="NCBI SRA",
                    identifier=_normalized_accession,
                    status="Observed",
                    confidence="Direct",
                    details={"scope": "run-level accession"},
                )
            ],
            warnings=[],
        )

    accession = str(accession or "").strip().upper()
    result = SourceAwareEvidence(accession=accession, attempted=True, retrieval_status="Completed")
    if not accession:
        result.retrieval_status = "Skipped — empty accession"
        return result

    repository = _repository_for(accession)
    repository_url = ""
    if repository == "NCBI GEO":
        repository_url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"
    elif repository == "NCBI SRA":
        repository_url = f"https://www.ncbi.nlm.nih.gov/sra/?term={accession}"
    elif repository == "NCBI BioProject":
        repository_url = f"https://www.ncbi.nlm.nih.gov/bioproject/?term={accession}"

    result.items.append(SourceEvidenceItem(
        source_type="Repository", source_name=repository, identifier=accession,
        status="Observed", confidence="Direct", url=repository_url,
    ))

    if not accession.startswith(STUDY_PREFIXES):
        return result

    try:
        explicit_ids = _geo_explicit_pubmed_ids(accession)
        ids = explicit_ids
        link_basis = "Explicit GEO publication field"
        if not ids:
            ids = _pubmed_ids_for_accession(accession)
            link_basis = "Accession-associated PubMed search"

        summaries = _pubmed_summaries(ids)
        pmc_map = _pmc_ids_for_pubmed(ids)

        for item in summaries:
            pmid = item["pmid"]
            direct = pmid in explicit_ids
            result.items.append(SourceEvidenceItem(
                source_type="Publication", source_name="PubMed", identifier=pmid,
                title=item["title"], status="Observed",
                confidence="Direct" if direct else "Indirect",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                details={
                    "journal": item["journal"], "pubdate": item["pubdate"],
                    "authors": item["authors"],
                    "link_basis": "Explicit GEO publication field" if direct else link_basis,
                },
            ))

        result.publication_count = len(summaries)
        for pmid, pmc_id in pmc_map.items():
            result.items.append(SourceEvidenceItem(
                source_type="Full text", source_name="PubMed Central",
                identifier=f"PMC{pmc_id}", status="Observed", confidence="Direct",
                url=f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/",
                details={"pmid": pmid},
            ))

        result.pmc_count = len({
            item.identifier for item in result.items if item.source_type == "Full text"
        })

        if not summaries:
            result.retrieval_status = (
                "Completed — no directly linked or accession-associated PubMed record found"
            )
        elif explicit_ids:
            result.retrieval_status = "Completed — explicit repository publication link resolved"
        else:
            result.retrieval_status = (
                "Completed — accession-associated PubMed record(s) found; "
                "no explicit repository publication link was available"
            )
    except Exception as exc:
        result.warnings.append(f"Publication enrichment failed: {type(exc).__name__}: {exc}")
        result.retrieval_status = "Completed with warnings"

    return result
