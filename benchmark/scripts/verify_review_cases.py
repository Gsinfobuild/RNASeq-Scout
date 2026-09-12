#!/usr/bin/env python3

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rnaseq_nav.clients.ncbi import NCBIClient


EMAIL = "gshankar.bbau@gmail.com"

TARGETS = [
    "ERP195344",
    "SRP686131",
]


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def text(parent, path):
    if parent is None:
        return ""

    node = parent.find(path)

    if node is None or node.text is None:
        return ""

    return clean(node.text)


def find_any(root, paths):
    for path in paths:
        node = root.find(path)

        if node is not None:
            return node

    return None


def parse_experiment_xml(expxml):
    """
    Extract repository-level experiment information directly from
    the SRA ExpXml returned by NCBI.

    This is verification only. It does not modify the production
    SRA parser or Scout.
    """

    result = {
        "experiment_accession": "",
        "study_accession": "",
        "sample_accession": "",
        "biosample_accession": "",
        "organism": "",
        "library_strategy": "",
        "library_source": "",
        "library_selection": "",
        "layout": "",
        "platform": "",
        "instrument": "",
        "title": "",
    }

    if not expxml:
        return result

    try:
        root = ET.fromstring(expxml)
    except ET.ParseError as exc:
        result["parse_error"] = str(exc)
        return result

    # Experiment accession
    result["experiment_accession"] = clean(
        root.attrib.get("accession", "")
    )

    # Study accession
    study = find_any(
        root,
        [
            ".//Study",
            ".//STUDY",
        ],
    )

    if study is not None:
        result["study_accession"] = clean(
            study.attrib.get("accession", "")
        )

    # Sample accession
    sample = find_any(
        root,
        [
            ".//Sample",
            ".//SAMPLE",
        ],
    )

    if sample is not None:
        result["sample_accession"] = clean(
            sample.attrib.get("accession", "")
        )

    # BioSample accession
    biosample = find_any(
        root,
        [
            ".//SAMPLE_ATTRIBUTE[@TAG='BioSample']",
            ".//SAMPLE_ATTRIBUTE[@TAG='biosample']",
        ],
    )

    if biosample is not None:
        result["biosample_accession"] = clean(
            biosample.findtext("VALUE", "")
        )

    # Organism
    organism = find_any(
        root,
        [
            ".//Organism",
            ".//ORGANISM",
        ],
    )

    if organism is not None:
        result["organism"] = clean(
            organism.attrib.get("ScientificName", "")
            or organism.attrib.get("CommonName", "")
        )

    # Library descriptor
    library = find_any(
        root,
        [
            ".//Library_descriptor",
            ".//LIBRARY_DESCRIPTOR",
        ],
    )

    if library is not None:
        result["library_strategy"] = text(
            library,
            "LIBRARY_STRATEGY",
        )

        result["library_source"] = text(
            library,
            "LIBRARY_SOURCE",
        )

        result["library_selection"] = text(
            library,
            "LIBRARY_SELECTION",
        )

        layout = library.find("LIBRARY_LAYOUT")

        if layout is not None:
            if layout.find("PAIRED") is not None:
                result["layout"] = "PAIRED"
            elif layout.find("SINGLE") is not None:
                result["layout"] = "SINGLE"

    # Platform
    platform = find_any(
        root,
        [
            ".//Platform",
            ".//PLATFORM",
        ],
    )

    if platform is not None:

        for child in list(platform):
            result["platform"] = child.tag
            result["instrument"] = clean(
                child.attrib.get("instrument_model", "")
            )

            if result["instrument"]:
                break

    # Title
    title = find_any(
        root,
        [
            ".//TITLE",
            ".//Title",
        ],
    )

    if title is not None and title.text:
        result["title"] = clean(title.text)

    return result


def unwrap(item):
    """
    NCBIClient.search() returns Biopython ListElement objects in
    this project. Convert the outer wrapper to the contained dict.
    """

    if isinstance(item, dict):
        return item

    if isinstance(item, list) and len(item) == 1:
        inner = item[0]

        if isinstance(inner, dict):
            return inner

    return {}


def print_record(label, record):
    print()
    print(f"  {label}")
    print("  " + "-" * 76)

    fields = [
        "experiment_accession",
        "study_accession",
        "sample_accession",
        "biosample_accession",
        "organism",
        "library_strategy",
        "library_source",
        "library_selection",
        "layout",
        "platform",
        "instrument",
        "title",
    ]

    for field in fields:
        print(
            f"  {field:25s}: {record.get(field, '')}"
        )


# ---------------------------------------------------------------------
# NCBI client
# ---------------------------------------------------------------------

client = NCBIClient(
    email=EMAIL,
)

print("=" * 80)
print("RNASeq Scout — REPOSITORY-LEVEL REVIEW CASE VERIFICATION")
print("=" * 80)

print()
print("Targets:")
for target in TARGETS:
    print(f"  {target}")

print()
print("Purpose:")
print(
    "Verify repository metadata only; no Scout prediction, "
    "publication evidence, or ground truth is used."
)

# ---------------------------------------------------------------------
# Search each study
# ---------------------------------------------------------------------

for accession in TARGETS:

    print()
    print("=" * 80)
    print(f"VERIFYING {accession}")
    print("=" * 80)

    try:
        results = client.search(
            f'"{accession}"',
            max_results=20,
        )
    except Exception as exc:
        print(f"NCBI retrieval failed: {exc}")
        continue

    print()
    print(f"Search results returned: {len(results)}")

    matched = False

    for i, item in enumerate(results, 1):

        record = unwrap(item)

        if not record:
            continue

        summary = record.get("summary", [])
        expxml = record.get("ExpXml", "")

        if not expxml:
            continue

        parsed = parse_experiment_xml(expxml)

        # Match the requested accession against any relevant field.
        accession_fields = {
            clean(record.get("accession", "")),
            clean(parsed.get("experiment_accession", "")),
            clean(parsed.get("study_accession", "")),
        }

        if accession not in accession_fields:
            continue

        matched = True

        print()
        print(f"Matched NCBI result #{i}")

        # Raw summary fields useful for verification.
        if isinstance(summary, list):
            print()
            print("  Summary:")
            for item2 in summary:
                if isinstance(item2, dict):
                    label = clean(item2.get("Item", ""))
                    value = clean(item2.get("Value", ""))

                    if label and value:
                        print(
                            f"    {label:24s}: {value}"
                        )

        print_record(
            "Parsed repository metadata",
            parsed,
        )

        # Runs XML is already supplied by NCBIClient.search().
        runs_xml = record.get("Runs", "")

        if runs_xml:
            try:
                runs_root = ET.fromstring(runs_xml)

                run_nodes = runs_root.findall(
                    ".//Run"
                )

                print()
                print(
                    f"  Run records in returned Runs XML: "
                    f"{len(run_nodes)}"
                )

                for run in run_nodes[:10]:
                    print(
                        "    "
                        f"{clean(run.attrib.get('accession', ''))}"
                    )

            except ET.ParseError:
                print()
                print("  Runs XML could not be parsed.")

        break

    if not matched:
        print()
        print(
            "WARNING: Requested accession was not directly "
            "matched in returned ExpXml records."
        )

print()
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print()
print(
    "No production code or benchmark selection was modified."
)
