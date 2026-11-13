"""Score five design fields per experiment using frozen summaries and submitted sample attributes."""
import argparse
import csv
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from rnaseq_nav.navigator import RNASeqNavigator
from rnaseq_nav.evidence import source_enrichment
from evaluate_v6 import canonical

FIELDS = ("condition", "control", "treatment", "time_point", "replicate_status")

def read_tsv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))

def attributes_xml(sample_id, attrs):
    root = ET.Element("BioSampleSet")
    sample = ET.SubElement(root, "BioSample", accession=sample_id)
    attributes = ET.SubElement(sample, "Attributes")
    for name, value in attrs.items():
        ET.SubElement(attributes, "Attribute", attribute_name=name).text = str(value)
    return ET.tostring(root)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("sources", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.snapshot) as archive:
        cases = {c["accession"]: c for c in json.loads(archive.read("cases.json"))}
    sources = read_tsv(args.sources)
    refs = read_tsv(args.reference)
    keyed = {(r["accession"], r["field"]): r for r in refs}
    accessions = {s["accession"] for s in sources}
    if (len(sources) != 50 or len(accessions) != 50 or len(refs) != 250 or
            set(keyed) != {(a, f) for a in accessions for f in FIELDS}):
        raise ValueError("Expected exactly five reference fields on each of 50 distinct accessions.")
    nav = RNASeqNavigator(email=None)
    results = []
    for s in sources:
        acc = s["accession"]
        case = cases[acc]
        record = case["record"]
        sample_id = ET.fromstring("<root>"+record["ExpXml"]+"</root>").findtext("Biosample")
        biosamples = {sample_id: attributes_xml(sample_id,json.loads(s["sample_attributes"]))}
        evidence = dict(case["publication_evidence"])
        evidence["items"] = [source_enrichment.SourceEvidenceItem(**it) for it in evidence["items"]]
        with patch.object(nav.discovery.client, "fetch", side_effect={acc:[record]}.__getitem__), patch.object(
            nav.discovery.client, "fetch_biosample", side_effect=biosamples.__getitem__
        ), patch.object(source_enrichment, "enrich_source_evidence", return_value=source_enrichment.SourceAwareEvidence(**evidence)):
            result = nav.inspect(acc, enrich_biosample=True)
        design = result.design_insight
        for field in FIELDS:
            ref = keyed[acc,field]
            sample_value = getattr(design, "sample_"+field, "") if design else ""
            fallback = "replicate_information" if field=="replicate_status" else field
            prediction = sample_value or getattr(design, fallback, "")
            expected = ref["expected"]
            matches = (not prediction if expected=="[absent]" else
                       canonical("experimental_design",field,expected)==canonical("experimental_design",field,prediction))
            results.append(dict(**ref,observed=prediction,origin="sample" if sample_value else "design",
                                match=int(result.success and matches),error=result.error or ""))
    with args.output.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=results[0],delimiter="\t")
        writer.writeheader()
        writer.writerows(results)
    print({f:sum(r["match"] for r in results if r["field"]==f) for f in FIELDS})

if __name__=="__main__":
    main()
