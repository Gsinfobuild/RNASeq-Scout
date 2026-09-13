"""
RNASeq Scout

BioSample Enrichment
====================

Explicit enrichment workflow for retrieving and parsing
NCBI BioSample metadata.

This module performs retrieval and metadata enrichment only.
It does not infer experimental groups, treatments, controls,
replicates, or biological relationships.
"""

from __future__ import annotations

from rnaseq_nav.clients.ncbi import NCBIClient
from rnaseq_nav.models import Metadata, SampleMetadata
from rnaseq_nav.parsers.biosample_parser import BioSampleParser


def _merge_sample_metadata(
    existing: SampleMetadata,
    biosample: SampleMetadata,
) -> SampleMetadata:
    """
    Merge BioSample metadata into an existing sample record.

    Existing non-empty information is preserved when the
    BioSample record does not provide a corresponding value.

    BioSample values are preferred for fields explicitly
    populated by the BioSample record.

    No biological interpretation or conflict resolution is
    performed here.
    """

    merged = SampleMetadata(
        accession=existing.accession,
        biosample=existing.biosample,
        organism=existing.organism,
        title=existing.title,
        name=existing.name,
        description=existing.description,
        attributes=list(existing.attributes),
    )

    if biosample.biosample:
        merged.biosample = biosample.biosample

    if biosample.organism:
        merged.organism = biosample.organism

    if biosample.title:
        merged.title = biosample.title

    if biosample.name:
        merged.name = biosample.name

    if biosample.description:
        merged.description = biosample.description

    if biosample.attributes:
        merged.attributes.extend(
            biosample.attributes
        )

    return merged


def enrich_sample_from_biosample(
    metadata: Metadata,
    client: NCBIClient,
    parser: BioSampleParser | None = None,
) -> Metadata:
    """
    Enrich sample metadata using its BioSample accession.

    Parameters
    ----------
    metadata : Metadata
        Existing SRA metadata object.

    client : NCBIClient
        NCBI client used to retrieve the BioSample XML.

    parser : BioSampleParser, optional
        Parser used to convert BioSample XML into SampleMetadata.
        A default parser is created when none is supplied.

    Returns
    -------
    Metadata
        The same metadata object with sample information
        enriched from the BioSample record.

    Notes
    -----
    BioSample enrichment is explicitly requested by calling
    this function. It is not part of NCBIClient.fetch().

    Existing SRA sample information is preserved when the
    BioSample record does not provide a corresponding field.

    No biological interpretation is performed here.
    """

    if metadata is None:
        raise ValueError(
            "metadata must be a Metadata object."
        )

    accession = (
        metadata.sample.biosample.strip()
        if metadata.sample.biosample
        else ""
    )

    if not accession:
        raise ValueError(
            "BioSample accession is not available in metadata.sample."
        )

    if parser is None:
        parser = BioSampleParser()

    biosample_xml = client.fetch_biosample(
        accession
    )

    biosample_sample = parser.parse(
        biosample_xml
    )

    metadata.sample = _merge_sample_metadata(
        metadata.sample,
        biosample_sample,
    )

    return metadata
