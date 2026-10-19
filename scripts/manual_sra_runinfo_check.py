"""
RNASeq Navigator

Test SRA RunInfo retrieval

This script:

1. Searches for the BioProject
2. Finds the linked SRA Study
3. Downloads RunInfo CSV
4. Prints important RNA-seq metadata
"""

from Bio import Entrez
import requests
import csv
import io

# --------------------------------------------------
# Configure Entrez
# --------------------------------------------------

Entrez.email = "YOUR_EMAIL@example.com"

BIOPROJECT = "PRJNA799829"

print("=" * 80)
print("Testing SRA RunInfo Retrieval")
print("=" * 80)

# --------------------------------------------------
# Step 1: BioProject UID
# --------------------------------------------------

search = Entrez.esearch(
    db="bioproject",
    term=BIOPROJECT
)

search_result = Entrez.read(search)
search.close()

uid = search_result["IdList"][0]

print(f"\nBioProject UID : {uid}")

# --------------------------------------------------
# Step 2: Link BioProject -> SRA
# --------------------------------------------------

links = Entrez.elink(
    dbfrom="bioproject",
    db="sra",
    id=uid
)

link_result = Entrez.read(links)
links.close()

linksets = link_result[0]["LinkSetDb"]

if not linksets:
    raise RuntimeError("No linked SRA study found.")

sra_uid = linksets[0]["Link"][0]["Id"]

print(f"SRA UID        : {sra_uid}")

# --------------------------------------------------
# Step 3: Download RunInfo CSV
# --------------------------------------------------

url = (
    "https://trace.ncbi.nlm.nih.gov/Traces/sra/"
    f"?runinfo={sra_uid}"
)

print("\nDownloading RunInfo...")

response = requests.get(url, timeout=30)

response.raise_for_status()

reader = csv.DictReader(io.StringIO(response.text))

rows = list(reader)

print(f"\nRuns found : {len(rows)}")

print("\nFirst run metadata:\n")

if rows:

    first = rows[0]

    fields = [

        "Run",
        "Experiment",
        "BioSample",
        "LibraryStrategy",
        "LibrarySource",
        "LibrarySelection",
        "Platform",
        "Model",
        "ScientificName"

    ]

    for field in fields:

        print(f"{field:20}: {first.get(field)}")
