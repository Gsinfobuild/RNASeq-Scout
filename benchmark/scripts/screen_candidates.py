"""
RNASeq Scout
============

Benchmark Candidate Screening v2

Purpose
-------
Retrieve repository-level SRA evidence for benchmark candidates.

Important
---------
This script does NOT establish experimental truth.

It separates:

1. experiment-level repository evidence
2. study-level repository context

Publication and experimental-design claims from the candidate registry
are retained only as preliminary candidate claims and are not treated
as validated ground truth.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from rnaseq_nav.discovery.dataset_discovery import DatasetDiscovery
from rnaseq_nav.intelligence.study_landscape import (
    generate_study_experimental_landscape,
)


INPUT_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "candidate_accessions.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "results"
    / "candidate_screening.csv"
)

EMAIL = "gshankar.bbau@gmail.com"


def clean(value) -> str:
    if value is None:
        return ""

    return " ".join(str(value).split())


def unique_count(values) -> int:
    return len(
        {
            clean(value)
            for value in values
            if clean(value)
        }
    )


def benchmark_unit(accession_type: str) -> str:

    accession_type = clean(
        accession_type
    ).upper()

    if accession_type in {
        "SRP",
        "ERP",
        "DRP",
    }:
        return "study"

    if accession_type in {
        "SRX",
        "ERX",
        "DRX",
    }:
        return "experiment"

    if accession_type in {
        "SRR",
        "ERR",
        "DRR",
    }:
        return "run"

    return "unknown"


def extract_context(title: str) -> str:

    title = clean(title)

    if ":" not in title:
        return "Unspecified"

    context = title.rsplit(
        ":",
        1,
    )[1].strip()

    return context or "Unspecified"


def retrieve_metadata(
    discovery,
    accession: str,
):
    """
    Retrieve metadata while explicitly preserving both
    ExpXml and Runs XML.
    """

    summary_wrapper = discovery.client.fetch(
        accession
    )

    if not summary_wrapper:
        raise ValueError(
            f"Empty SRA response for {accession}"
        )

    record = summary_wrapper[0]

    expxml = record.get(
        "ExpXml",
        "",
    )

    runs_xml = record.get(
        "Runs",
        "",
    )

    if not expxml:
        raise ValueError(
            f"No ExpXml available for {accession}"
        )

    metadata = discovery.parser.parse(
        expxml,
        runs_xml,
    )

    return metadata


def retrieve_study_context(
    discovery,
    study_accession: str,
) -> dict:

    context = {
        "study_title": "",
        "study_description": "",
        "study_experiment_count": 0,
        "study_sample_count": 0,
        "study_biosample_count": 0,
        "study_run_count": 0,
        "study_assay_families": "",
        "study_context_count": 0,
        "study_contexts": "",
        "study_context_warning": "",
    }

    if not study_accession:
        return context

    study_experiments = (
        discovery.fetch_study(
            study_accession
        )
    )

    context["study_experiment_count"] = (
        len(study_experiments)
    )

    context["study_sample_count"] = unique_count(
        record.sample_accession
        for record in study_experiments
    )

    context["study_biosample_count"] = unique_count(
        record.biosample_accession
        for record in study_experiments
    )

    context["study_run_count"] = unique_count(
        run
        for record in study_experiments
        for run in record.run_accessions
    )

    landscape = generate_study_experimental_landscape(
        study_experiments
    )

    context["study_assay_families"] = (
        "; ".join(
            landscape.observed_assay_families
        )
    )

    contexts = {
        extract_context(
            record.experiment_title
        )
        for record in study_experiments
    }

    context["study_context_count"] = (
        len(contexts)
    )

    context["study_contexts"] = (
        "; ".join(
            sorted(contexts)
        )
    )

    if landscape.warnings:
        context["study_context_warning"] = " ".join(
            landscape.warnings
        )

    # Retrieve BioProject through the canonical
    # single-record metadata pathway.
    try:

        metadata = retrieve_metadata(
            discovery,
            study_accession,
        )

        bioproject = clean(
            metadata.project.accession
        )

        if bioproject:

            xml = discovery.client.fetch_bioproject(
                bioproject
            )

            (
                context["study_title"],
                context["study_description"],
            ) = discovery.parser.parse_bioproject(
                xml
            )

    except Exception as error:

        context["study_context_warning"] = (
            "Study BioProject enrichment failed: "
            f"{type(error).__name__}: {error}"
        )

    return context


def screen_candidate(
    discovery,
    candidate: dict,
) -> dict:

    accession = clean(
        candidate.get("accession")
    )

    accession_type = clean(
        candidate.get("accession_type")
    ).upper()

    result = {
        "accession": accession,
        "accession_type": accession_type,
        "benchmark_unit": benchmark_unit(
            accession_type
        ),

        "candidate_category": clean(
            candidate.get("category")
        ),

        "candidate_organism": clean(
            candidate.get("organism")
        ),

        "candidate_strategy": clean(
            candidate.get("library_strategy")
        ),

        "candidate_reason": clean(
            candidate.get("candidate_reason")
        ),

        "retrieval_status": "not_attempted",

        "study_accession": "",
        "bioproject_accession": "",

        "experiment_accession": "",
        "experiment_title": "",

        "library_strategy": "",
        "library_source": "",
        "library_selection": "",
        "layout": "",
        "platform": "",
        "instrument": "",

        "organism": "",
        "sample_accession": "",
        "run_accession": "",

        "total_spots": "",
        "total_bases": "",

        "study_title": "",
        "study_description": "",
        "study_experiment_count": "",
        "study_sample_count": "",
        "study_biosample_count": "",
        "study_run_count": "",
        "study_assay_families": "",
        "study_context_count": "",
        "study_contexts": "",
        "study_context_warning": "",

        "publication_identifier_claim": clean(
            candidate.get(
                "publication_identifier"
            )
        ),

        "publication_available_claim": clean(
            candidate.get(
                "publication_available"
            )
        ),

        "experimental_design_documented_claim": clean(
            candidate.get(
                "experimental_design_documented"
            )
        ),

        "screening_status": "needs_review",
        "screening_notes": "",
        "error": "",
    }

    try:

        metadata = retrieve_metadata(
            discovery,
            accession,
        )

        result["retrieval_status"] = "success"

        result["study_accession"] = clean(
            metadata.study.accession
        )

        result["bioproject_accession"] = clean(
            metadata.project.accession
        )

        result["experiment_accession"] = clean(
            metadata.experiment.accession
        )

        result["experiment_title"] = clean(
            metadata.experiment.title
        )

        result["library_strategy"] = clean(
            metadata.experiment.library_strategy
        )

        result["library_source"] = clean(
            metadata.experiment.library_source
        )

        result["library_selection"] = clean(
            metadata.experiment.library_selection
        )

        result["layout"] = clean(
            metadata.experiment.layout
        )

        result["platform"] = clean(
            metadata.experiment.platform
        )

        result["instrument"] = clean(
            metadata.experiment.instrument
        )

        result["organism"] = clean(
            metadata.sample.organism
        )

        result["sample_accession"] = clean(
            metadata.sample.accession
        )

        result["run_accession"] = clean(
            metadata.run.accession
        )

        if metadata.run.total_spots is not None:
            result["total_spots"] = (
                metadata.run.total_spots
            )

        if metadata.run.total_bases is not None:
            result["total_bases"] = (
                metadata.run.total_bases
            )

        # -----------------------------------------------------
        # Study context
        # -----------------------------------------------------

        study_context = retrieve_study_context(
            discovery,
            result["study_accession"],
        )

        result.update(
            study_context
        )

        # -----------------------------------------------------
        # Preliminary status
        # -----------------------------------------------------

        # Everything remains needs_review until an independent
        # benchmark curator verifies the scientific evidence.
        result["screening_status"] = (
            "needs_review"
        )

        notes = []

        if result["library_strategy"]:
            notes.append(
                "Library strategy retrieved from SRA."
            )
        else:
            notes.append(
                "Library strategy not established."
            )

        if result["run_accession"]:
            notes.append(
                "Run metadata retrieved."
            )

        if result["study_experiment_count"]:
            notes.append(
                "Study-level experiment context retrieved."
            )

        if (
            result["study_assay_families"]
        ):
            notes.append(
                "Study assay-family composition retrieved."
            )

        if (
            result["publication_identifier_claim"]
        ):
            notes.append(
                "Publication identifier is a preliminary "
                "candidate-registry claim and requires verification."
            )
        else:
            notes.append(
                "Publication identifier has not yet been independently verified."
            )

        notes.append(
            "Experimental truth has not yet been established."
        )

        result["screening_notes"] = " ".join(
            notes
        )

    except Exception as error:

        result["retrieval_status"] = "failed"

        result["screening_status"] = (
            "exclude_pending_review"
        )

        result["error"] = (
            f"{type(error).__name__}: {error}"
        )

        result["screening_notes"] = (
            "Candidate could not be resolved through "
            "the current SRA retrieval pipeline."
        )

    return result


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {INPUT_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        candidates = list(
            csv.DictReader(handle)
        )

    print(
        f"Loaded {len(candidates)} candidates."
    )

    discovery = DatasetDiscovery(
        email=EMAIL,
        verbose=False,
    )

    results = []

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        accession = clean(
            candidate.get("accession")
        )

        print(
            f"[{index}/{len(candidates)}] "
            f"Screening {accession} ..."
        )

        result = screen_candidate(
            discovery,
            candidate,
        )

        results.append(
            result
        )

        print(
            "    "
            f"status={result['retrieval_status']} "
            f"unit={result['benchmark_unit']} "
            f"strategy={result['library_strategy'] or 'NA'} "
            f"study={result['study_accession'] or 'NA'} "
            f"runs={result['study_run_count'] or result['run_accession'] or 'NA'}"
        )

    if not results:
        print(
            "No candidates found."
        )
        return

    fieldnames = list(
        results[0].keys()
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    successful = sum(
        result["retrieval_status"]
        == "success"
        for result in results
    )

    failed = (
        len(results)
        - successful
    )

    print()
    print(
        "Candidate screening complete."
    )
    print(
        f"Candidates: {len(results)}"
    )
    print(
        f"Retrieved successfully: {successful}"
    )
    print(
        f"Retrieval failures: {failed}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
