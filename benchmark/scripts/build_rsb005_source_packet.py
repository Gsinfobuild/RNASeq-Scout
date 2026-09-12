#!/usr/bin/env python3

from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "benchmark/annotations/source_packets/RSB005"


REPOSITORY_ROWS = [
    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "library_strategy", "RNA-Seq", "ENA portal API",
     "library_strategy=RNA-Seq"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "library_source", "TRANSCRIPTOMIC", "ENA portal API",
     "library_source=TRANSCRIPTOMIC"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "library_selection", "cDNA_randomPriming", "ENA portal API",
     "library_selection=cDNA_randomPriming"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "library_layout", "PAIRED", "ENA portal API",
     "library_layout=PAIRED"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "instrument_platform", "ILLUMINA", "ENA portal API",
     "instrument_platform=ILLUMINA"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "instrument_model", "Illumina NovaSeq 6000", "ENA portal API",
     "instrument_model=Illumina NovaSeq 6000"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "scientific_name", "Arabidopsis thaliana", "ENA portal API",
     "scientific_name=Arabidopsis thaliana"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "run_accession", "ERR15811000", "ENA portal API",
     "run_accession=ERR15811000"],

    ["RSB005", "ERX15210614", "ENA File Report", "ERX15210614",
     "sample_accession", "SAMEA120469952", "ENA portal API",
     "sample_accession=SAMEA120469952"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "sra_accession", "ERS27170638", "BioSamples record",
     "sraAccession=ERS27170638"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "sample_name", "36", "BioSamples record",
     "name=36"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "title", "RNAseq_ago1-27.3", "BioSamples record",
     "title=RNAseq_ago1-27.3"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "description", "RNAseq, ago1-27, biological replica 3",
     "BioSamples record",
     "description=RNAseq, ago1-27, biological replica 3"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "ecotype", "Col-0", "BioSamples record",
     "ecotype=Col-0"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "tissue_type", "Inflorescences", "BioSamples record",
     "tissue_type=Inflorescences"],

    ["RSB005", "ERX15210614", "BioSamples", "SAMEA120469952",
     "organism", "Arabidopsis thaliana", "BioSamples record",
     "organism=Arabidopsis thaliana"],
]


REPOSITORY_HEADER = [
    "benchmark_id",
    "accession",
    "source_type",
    "source_identifier",
    "field",
    "source_value",
    "evidence_location",
    "evidence_excerpt",
]


README = """# RSB005 — ERX15210614

## Benchmark unit

- Benchmark ID: RSB005
- Accession: ERX15210614
- Accession type: experiment
- Study: ERP183101
- Project: PRJEB101698
- Organism group: Arabidopsis

## Source packet

This directory contains source evidence for independent experimental-truth
annotation.

The packet is evidence-oriented and must not be treated as a Scout answer key.

## Source files

1. `repository_evidence.csv`
2. `publication_evidence.md`
3. `supplementary_evidence.md`

## Reviewer independence

Reviewer 1 and Reviewer 2 must work independently.

A reviewer must not inspect:

- the other reviewer's annotation
- Scout output
- the internal evidence register
- an adjudicated answer

before completing their own annotation.

## Important distinction

Source evidence is not itself the final annotation.

For example, the BioSamples source contains:

`title=RNAseq_ago1-27.3`

and:

`description=RNAseq, ago1-27, biological replica 3`

The reviewer must independently determine what experimental-truth fields
these observations establish and what evidence state is appropriate.

## Evidence hierarchy

Use the benchmark annotation guidelines:

1. Primary research publication
2. Publication supplementary material
3. Study-specific experimental metadata
4. SRA / BioProject / BioSample repository records
5. Other authoritative repository-linked records

## Supplementary accession mapping

The inspected supplementary tables did not directly contain:

- ERX15210614
- ERS27170638
- ERR15811000

Therefore, reviewers must not infer an accession-to-sample mapping merely
from the presence of sample names such as `ago1-27` in Table S1.

## Annotation boundary

Do not construct:

- treatment assignments
- control assignments
- design formulas
- experimental groups

unless the source explicitly establishes them.

Unsupported inference is a primary benchmark error category.
"""


PUBLICATION = """# RSB005 — Publication Evidence

## Primary source

Title:

A single NLS directs AGO1 nuclear import and shapes spatial small RNA loading
and silencing outputs in Arabidopsis

DOI:

10.21203/rs.3.rs-8166011/v1

Dataset project:

PRJEB101698

## Source-level information

The publication describes transcriptomic experiments involving Arabidopsis
thaliana material and discusses experimental material including:

- Col-0
- ago1-27
- wtAGO1
- nucAGO1
- cytAGO1

The study describes total RNA sequencing / transcriptomic analysis of
Arabidopsis inflorescence material.

## Reviewer instruction

Use the publication as primary scientific evidence where it establishes
experimental truth.

In particular, independently determine whether the publication establishes
for the specific benchmark accession:

- biological condition
- genotype
- treatment
- control
- time point
- biological replicate identity
- technical replicate identity
- experimental group
- batch information

Do not assume that a study-level statement automatically applies to the
specific accession ERX15210614.

The source summary in this file is not an answer key.
"""


SUPPLEMENT = """# RSB005 — Supplementary Evidence

## Supplementary package

`SuppTablesMoroetal19.08.zip`

## Inspection

The supplementary package contains Tables S1-S7.

Table S1 contains RNA-seq expression/count information with sample columns
including:

- Col-0
- ago1-27
- wtAGO1
- nucAGO1
- cytAGO1

The inspected supplementary tables did not contain the accession identifiers:

- ERX15210614
- ERS27170638
- ERR15811000

Therefore, the supplementary package was not used to establish the
accession-specific mapping between ERX15210614 and a particular sample
column.

## Reviewer instruction

The supplementary material may be used to establish experimental context
when the source explicitly supports the claim.

Do not infer that ERX15210614 corresponds to a particular supplementary
sample column unless the source explicitly establishes that relationship.

The presence of a sample name in Table S1 is not by itself an accession
mapping.

The reviewer must independently annotate experimental truth according to the
benchmark guidelines.
"""


def write_text(path: Path, text: str):
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main():
    PACKET.mkdir(parents=True, exist_ok=True)

    with (PACKET / "repository_evidence.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(REPOSITORY_HEADER)
        writer.writerows(REPOSITORY_ROWS)

    write_text(PACKET / "README.md", README)
    write_text(PACKET / "publication_evidence.md", PUBLICATION)
    write_text(PACKET / "supplementary_evidence.md", SUPPLEMENT)

    print("Built RSB005 source packet:")
    for path in sorted(PACKET.iterdir()):
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
