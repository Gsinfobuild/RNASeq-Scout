"""Run the public inspection API against the frozen v6 panel without network calls."""
import argparse
import json
import hashlib
import zipfile
from pathlib import Path
from rnaseq_nav.evidence import source_enrichment
from rnaseq_nav.navigator import RNASeqNavigator
from run_benchmark import build_observation, write_results
from unittest.mock import patch

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with zipfile.ZipFile(args.snapshot) as archive:
        cases=json.loads(archive.read("cases.json"))
    navigator=RNASeqNavigator(email=None)
    records={case["accession"]:[case["record"]] for case in cases}
    evidence={}
    for case in cases:
        data=dict(case["publication_evidence"])
        data["items"]=[source_enrichment.SourceEvidenceItem(**i) for i in data["items"]]
        evidence[case["accession"]]=source_enrichment.SourceAwareEvidence(**data)
    package=Path(__file__).resolve().parents[2]/"rnaseq_nav"
    digest=hashlib.sha256()
    for path in sorted(package.rglob("*.py")):
        digest.update(path.relative_to(package).as_posix().encode()+b"\0")
        digest.update(path.read_bytes().replace(b"\r\n",b"\n")+b"\0")
    rows=[]
    with patch.object(navigator.discovery.client,"fetch",side_effect=records.__getitem__), patch.object(
        source_enrichment,"enrich_source_evidence",side_effect=evidence.__getitem__
    ):
        for accession in records:
            result=navigator.inspect(accession)
            rows.append(build_observation(accession,result,"","source-sha256:"+digest.hexdigest()))
    write_results(args.output,rows)

if __name__=="__main__":
    main()
