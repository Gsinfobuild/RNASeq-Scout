"""
RNASeq Navigator

Accession Detection

Version: 1.0

Identifies the database and accession type
from a user-provided accession.
"""

import re


ACCESSION_PATTERNS = {
    # GEO
    "GSE": ("GEO", "Series"),
    "GSM": ("GEO", "Sample"),
    "GPL": ("GEO", "Platform"),
    "GDS": ("GEO", "Dataset"),

    # NCBI / ENA / DDBJ
    "PRJNA": ("NCBI", "BioProject"),
    "PRJEB": ("ENA", "BioProject"),
    "PRJDB": ("DDBJ", "BioProject"),

    "SRP": ("NCBI", "Study"),
    "ERP": ("ENA", "Study"),
    "DRP": ("DDBJ", "Study"),

    "SRX": ("NCBI", "Experiment"),
    "ERX": ("ENA", "Experiment"),
    "DRX": ("DDBJ", "Experiment"),

    "SRR": ("NCBI", "Run"),
    "ERR": ("ENA", "Run"),
    "DRR": ("DDBJ", "Run"),

    "SAMN": ("NCBI", "BioSample"),
    "SAMEA": ("ENA", "BioSample"),
    "SAMD": ("DDBJ", "BioSample"),
}


def detect_accession(accession: str):
    """
    Detect accession namespace and object type.

    Parameters
    ----------
    accession : str

    Returns
    -------
    dict
    """

    accession = accession.strip().upper()

    for prefix, (database, obj_type) in ACCESSION_PATTERNS.items():

        if accession.startswith(prefix):

            return {
                "accession": accession,
                "database": database,
                "type": obj_type,
                "prefix": prefix,
            }

    return {
        "accession": accession,
        "database": "Unknown",
        "type": "Unknown",
        "prefix": None,
    }


if __name__ == "__main__":

    tests = [
        "PRJNA1493258",
        "PRJEB12345",
        "PRJDB42722",
        "SRX34444857",
        "ERX16608090",
        "SRR123456",
        "ERR999999",
        "ABC123",
    ]

    for accession in tests:

        print(detect_accession(accession))
