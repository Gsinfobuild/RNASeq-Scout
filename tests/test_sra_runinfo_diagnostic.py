#!/usr/bin/env python3
"""
RNASeq Navigator
Diagnostic script for SRA RunInfo retrieval.

Run directly when you want to query NCBI:
    python tests/test_sra_runinfo_diagnostic.py

Importing this module does not perform network requests.
"""

import csv
import io
import os
from pprint import pprint

import requests
from Bio import Entrez


BIOPROJECT = "PRJNA799829"


def main():
    """Search a BioProject, retrieve SRA RunInfo, and inspect its CSV."""
    Entrez.email = os.environ.get("NCBI_EMAIL", "YOUR_EMAIL@example.com")

    if Entrez.email == "YOUR_EMAIL@example.com":
        raise RuntimeError(
            "Set NCBI_EMAIL to your email address before running this diagnostic."
        )

    print("=" * 80)
    print("RNASeq Navigator - SRA RunInfo Diagnostic")
    print("=" * 80)

    print("\n[1] Searching BioProject...")
    with Entrez.esearch(db="bioproject", term=BIOPROJECT) as handle:
        result = Entrez.read(handle)

    if not result["IdList"]:
        raise RuntimeError(f"BioProject not found: {BIOPROJECT}")

    bioproject_uid = result["IdList"][0]
    print(f"BioProject UID: {bioproject_uid}")

    print("\n[2] Finding linked SRA record...")
    with Entrez.elink(
        dbfrom="bioproject",
        db="sra",
        id=bioproject_uid,
    ) as handle:
        links = Entrez.read(handle)

    linksets = links[0]["LinkSetDb"]
    if not linksets or not linksets[0]["Link"]:
        raise RuntimeError("No SRA links found for this BioProject.")

    sra_uid = linksets[0]["Link"][0]["Id"]
    print(f"SRA UID: {sra_uid}")

    print("\n[3] Downloading RunInfo...")
    url = f"https://trace.ncbi.nlm.nih.gov/Traces/sra/?runinfo={sra_uid}"
    print(f"URL:\n{url}")

    response = requests.get(url, timeout=60)
    print("\nHTTP Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    response.raise_for_status()

    outfile = "runinfo_raw_response.txt"
    with open(outfile, "w", encoding="utf-8") as output:
        output.write(response.text)

    print(f"\nRaw response saved to: {outfile}")
    print("\nFirst 500 characters:\n")
    print("-" * 80)
    print(response.text[:500])
    print("-" * 80)

    print("\n[4] Parsing CSV...")
    rows = list(csv.DictReader(io.StringIO(response.text)))
    print(f"Rows parsed: {len(rows)}")

    if not rows:
        print("No CSV data rows were returned.")
        return

    print("\nCSV Columns\n")
    print("=" * 80)
    for column in rows[0].keys():
        print(column)

    print("\nFirst Row\n")
    print("=" * 80)
    pprint(rows[0])
    print("\nDiagnostic complete.")


if __name__ == "__main__":
    main()
