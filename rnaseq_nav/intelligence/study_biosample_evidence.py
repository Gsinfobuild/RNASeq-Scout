"""
RNASeq Scout

Study-level BioSample Evidence
==============================

Aggregate explicitly deposited BioSample metadata across the
samples belonging to a study.

This layer performs evidence aggregation only.

It does not infer:
- experimental groups
- controls
- treatments
- biological replicates
- statistical contrasts
- analysis formulas

Repeated attribute values are summarized as observed metadata
patterns, not interpreted as experimental design.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable

from rnaseq_nav.clients.ncbi import NCBIClient
from rnaseq_nav.models import SampleAttribute, StudyExperiment
from rnaseq_nav.parsers.biosample_parser import BioSampleParser


@dataclass
class StudyBioSampleRecord:
    """
    Raw BioSample evidence associated with one study sample.
    """

    biosample_accession: str = ""
    sample_accession: str = ""
    experiment_accession: str = ""

    organism: str = ""
    title: str = ""
    name: str = ""
    description: str = ""

    attributes: list[SampleAttribute] = field(
        default_factory=list
    )

    retrieval_status: str = "Not attempted"
    retrieval_error: str = ""


@dataclass
class StudyBioSampleEvidence:
    """
    Study-level aggregation of explicitly deposited BioSample
    metadata.

    Attribute frequencies describe observed repository
    metadata. They are not interpreted as experimental factors.
    """

    total_study_experiments: int = 0
    unique_biosample_count: int = 0

    retrieved_biosample_count: int = 0
    failed_biosample_count: int = 0
    missing_biosample_count: int = 0

    samples: list[StudyBioSampleRecord] = field(
        default_factory=list
    )

    attribute_values: dict[str, dict[str, int]] = field(
        default_factory=dict
    )

    observed_attribute_names: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )


def _attribute_key(attribute: SampleAttribute) -> str:
    """
    Select the most informative deposited attribute name.

    Preference:
    harmonized_name -> attribute name -> display name.
    """

    return (
        attribute.harmonized_name.strip()
        or attribute.name.strip()
        or attribute.display_name.strip()
    )


def _attribute_display_name(attribute: SampleAttribute) -> str:
    """
    Return a human-readable deposited attribute name.
    """

    return (
        attribute.display_name.strip()
        or attribute.name.strip()
        or attribute.harmonized_name.strip()
    )


def _build_study_sample_records(
    records: Iterable[StudyExperiment],
) -> list[tuple[str, str, str, str]]:
    """
    Build unique BioSample work items.

    Returns tuples of:
        (
            biosample_accession,
            sample_accession,
            experiment_accession,
            organism,
        )

    A BioSample is retrieved at most once even if multiple
    study experiment records reference it.
    """

    unique: dict[str, tuple[str, str, str, str]] = {}

    for record in records:

        biosample = (
            record.biosample_accession.strip()
            if record.biosample_accession
            else ""
        )

        if not biosample:
            continue

        if biosample in unique:
            continue

        unique[biosample] = (
            biosample,
            record.sample_accession.strip()
            if record.sample_accession
            else "",
            record.experiment_accession.strip()
            if record.experiment_accession
            else "",
            record.organism.strip()
            if record.organism
            else "",
        )

    return list(unique.values())


def generate_study_biosample_evidence(
    records: Iterable[StudyExperiment],
    client: NCBIClient,
    parser: BioSampleParser | None = None,
) -> StudyBioSampleEvidence:
    """
    Retrieve and aggregate BioSample metadata for a study.

    Parameters
    ----------
    records
        Study-level SRA experiment records.

    client
        NCBI client used to retrieve BioSample XML.

    parser
        Optional BioSampleParser.

    Returns
    -------
    StudyBioSampleEvidence
        Structured study-level repository evidence.

    Notes
    -----
    This function deliberately performs no biological inference.
    """

    records = list(records)

    evidence = StudyBioSampleEvidence(
        total_study_experiments=len(records)
    )

    if parser is None:
        parser = BioSampleParser()

    work_items = _build_study_sample_records(
        records
    )

    evidence.unique_biosample_count = len(
        work_items
    )

    if not work_items:
        evidence.warnings.append(
            "No BioSample accessions were available "
            "in the study experiment records."
        )
        evidence.missing_biosample_count = len(records)
        return evidence

    attribute_counters: dict[str, Counter[str]] = (
        defaultdict(Counter)
    )

    attribute_display_names: dict[str, str] = {}

    for (
        biosample_accession,
        sample_accession,
        experiment_accession,
        organism,
    ) in work_items:

        sample_record = StudyBioSampleRecord(
            biosample_accession=biosample_accession,
            sample_accession=sample_accession,
            experiment_accession=experiment_accession,
            organism=organism,
            retrieval_status="Not attempted",
        )

        try:

            xml = client.fetch_biosample(
                biosample_accession
            )

            biosample = parser.parse(xml)

            sample_record.organism = (
                biosample.organism
                or sample_record.organism
            )

            sample_record.title = biosample.title
            sample_record.name = biosample.name
            sample_record.description = (
                biosample.description
            )

            sample_record.attributes = list(
                biosample.attributes
            )

            sample_record.retrieval_status = (
                "Retrieved"
            )

            evidence.retrieved_biosample_count += 1

            for attribute in biosample.attributes:

                key = _attribute_key(attribute)
                value = attribute.value.strip()

                if not key or not value:
                    continue

                attribute_counters[key][value] += 1

                if key not in attribute_display_names:
                    attribute_display_names[key] = (
                        _attribute_display_name(
                            attribute
                        )
                    )

        except Exception as error:

            sample_record.retrieval_status = (
                "Failed"
            )

            sample_record.retrieval_error = (
                f"{type(error).__name__}: {error}"
            )

            evidence.failed_biosample_count += 1

        evidence.samples.append(
            sample_record
        )

    evidence.attribute_values = {
        key: dict(counter)
        for key, counter in attribute_counters.items()
    }

    evidence.observed_attribute_names = sorted(
        attribute_display_names.values(),
        key=str.lower,
    )

    if evidence.failed_biosample_count:
        evidence.warnings.append(
            f"{evidence.failed_biosample_count} BioSample "
            "record(s) could not be retrieved."
        )

    if evidence.retrieved_biosample_count < (
        evidence.unique_biosample_count
    ):
        evidence.warnings.append(
            "Study-level BioSample evidence is incomplete "
            "because one or more unique BioSample records "
            "could not be retrieved."
        )

    return evidence
