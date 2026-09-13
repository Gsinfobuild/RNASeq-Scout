"""
RNASeq Scout

BioSample Parser
================

Parse NCBI BioSample XML into SampleMetadata objects.

The parser preserves deposited BioSample information as raw
repository evidence. It does not infer biological factors,
experimental groups, treatments, controls, or replicates.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from rnaseq_nav.models import (
    SampleAttribute,
    SampleMetadata,
)


class BioSampleParser:
    """
    Parser for NCBI BioSample XML.
    """

    def parse(
        self,
        biosample_xml: str | bytes,
    ) -> SampleMetadata:
        """
        Parse a BioSample XML record.

        Parameters
        ----------
        biosample_xml : str | bytes
            XML returned by the NCBI BioSample endpoint.

        Returns
        -------
        SampleMetadata
            Sample metadata containing raw BioSample evidence.
        """

        if not biosample_xml:
            return SampleMetadata()

        if isinstance(biosample_xml, bytes):
            biosample_xml = biosample_xml.decode(
                "utf-8",
                errors="replace",
            )

        root = ET.fromstring(biosample_xml)

        biosample = root.find(".//BioSample")

        if biosample is None:
            return SampleMetadata()

        metadata = SampleMetadata()

        # ------------------------------------------------------
        # BioSample accession
        # ------------------------------------------------------

        metadata.biosample = biosample.attrib.get(
            "accession",
            "",
        )

        # ------------------------------------------------------
        # Description
        # ------------------------------------------------------

        description = biosample.find("Description")

        if description is not None:

            # BioSample title
            title = description.find("Title")

            if title is not None and title.text:
                metadata.title = title.text.strip()

            # Organism
            organism = description.find("Organism")

            if organism is not None:

                organism_name = organism.find(
                    "OrganismName"
                )

                if (
                    organism_name is not None
                    and organism_name.text
                ):
                    metadata.organism = (
                        organism_name.text.strip()
                    )

                elif organism.attrib.get(
                    "taxonomy_name"
                ):
                    metadata.organism = (
                        organism.attrib[
                            "taxonomy_name"
                        ].strip()
                    )

            # Comment / description
            comment = description.find("Comment")

            if comment is not None:

                paragraphs = []

                for paragraph in comment.findall(
                    "Paragraph"
                ):

                    if (
                        paragraph.text
                        and paragraph.text.strip()
                    ):
                        paragraphs.append(
                            paragraph.text.strip()
                        )

                metadata.description = "\n".join(
                    paragraphs
                )

        # ------------------------------------------------------
        # Structured attributes
        # ------------------------------------------------------

        attributes = biosample.find("Attributes")

        if attributes is not None:

            for attribute in attributes.findall(
                "Attribute"
            ):

                value = (
                    attribute.text.strip()
                    if attribute.text
                    else ""
                )

                name = attribute.attrib.get(
                    "attribute_name",
                    "",
                ).strip()

                harmonized_name = attribute.attrib.get(
                    "harmonized_name",
                    "",
                ).strip()

                display_name = attribute.attrib.get(
                    "display_name",
                    "",
                ).strip()

                # Ignore completely empty records.
                if not any(
                    (
                        name,
                        value,
                        harmonized_name,
                        display_name,
                    )
                ):
                    continue

                metadata.attributes.append(
                    SampleAttribute(
                        name=name,
                        value=value,
                        harmonized_name=harmonized_name,
                        display_name=display_name,
                    )
                )

                # BioSample's "sample name" is useful as
                # the raw sample name, but only populate
                # metadata.name when explicitly deposited
                # under that attribute.
                if (
                    not metadata.name
                    and harmonized_name == "sample_name"
                    and value
                ):
                    metadata.name = value

        return metadata
