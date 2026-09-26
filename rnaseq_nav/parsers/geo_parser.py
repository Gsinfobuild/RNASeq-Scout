"""
RNASeq Scout

GEO Parser
==========

Parse the text representation returned by the NCBI GEO accession
display endpoint into the existing RNASeq Scout Metadata model.

The parser preserves deposited GEO evidence and does not infer
experimental design.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from rnaseq_nav.models import Metadata, SampleAttribute


class GEOParser:
    """Parser for NCBI GEO Series and Sample text records."""

    _FIELD_RE = re.compile(r"^!(?P<field>[^=]+?)\s*=\s?(?P<value>.*)$")

    def _parse_fields(self, text: str) -> dict[str, list[str]]:
        """Parse GEO !Field = value records while preserving repeats."""
        fields: dict[str, list[str]] = {}

        for line in text.splitlines():
            match = self._FIELD_RE.match(line.strip())

            if not match:
                continue

            field = match.group("field").strip()
            value = match.group("value").strip()

            fields.setdefault(field, []).append(value)

        return fields

    @staticmethod
    def _first(fields: dict[str, list[str]], name: str) -> str:
        """Return the first value for a GEO field."""
        values = fields.get(name, [])
        return values[0] if values else ""

    @staticmethod
    def _last_accession_from_relation(
        values: list[str],
        prefix: str,
    ) -> str:
        """Extract an accession from a GEO relation URL."""
        for value in values:
            match = re.search(
                rf"(?:term=|/){re.escape(prefix)}(\d+)",
                value,
                flags=re.IGNORECASE,
            )

            if match:
                return f"{prefix}{match.group(1)}"

        return ""

    @staticmethod
    def _relation_accession(
        values: list[str],
        label: str,
    ) -> str:
        """Extract an accession from a labelled GEO relation."""
        for value in values:
            if not value.lower().startswith(label.lower() + ":"):
                continue

            match = re.search(
                r"(?:term=|/|:\s*)([A-Z]{2,}\d+)",
                value,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1)

        return ""

    @staticmethod
    def _attribute_name(field: str) -> str:
        """Convert a GEO field name into a deposited attribute name."""
        return field.replace("Sample_", "", 1)

    def _add_attribute(
        self,
        metadata: Metadata,
        name: str,
        value: str,
    ) -> None:
        """Preserve a GEO field as a raw SampleAttribute."""
        if not value:
            return

        metadata.sample.attributes.append(
            SampleAttribute(
                name=name,
                value=value,
                harmonized_name="",
                display_name=name,
            )
        )

    def sample_accessions(self, text: str) -> list[str]:
        """
        Extract GSM sample accessions explicitly listed by a GEO Series.

        This method only extracts deposited Series_sample_id values.
        It does not retrieve or interpret the corresponding samples.
        """
        fields = self._parse_fields(text)

        accessions = []

        for value in fields.get("Series_sample_id", []):
            accession = value.strip().upper()

            if accession.startswith("GSM") and accession not in accessions:
                accessions.append(accession)

        return accessions

    def parse(self, text: str) -> Metadata:
        """
        Parse a GEO Series or Sample text record.

        Parameters
        ----------
        text:
            Text returned by the GEO accession display endpoint.

        Returns
        -------
        Metadata
            Existing RNASeq Scout metadata model populated with
            source-faithful GEO evidence.
        """
        metadata = Metadata()

        if not text:
            return metadata

        fields = self._parse_fields(text)

        # ==========================================================
        # Determine record type
        # ==========================================================

        series_accession = self._first(
            fields,
            "Series_geo_accession",
        )

        sample_accession = self._first(
            fields,
            "Sample_geo_accession",
        )

        # ==========================================================
        # Series
        # ==========================================================

        if series_accession:
            metadata.study.accession = series_accession

            title = self._first(fields, "Series_title")

            if title:
                metadata.experiment.title = title

        # ==========================================================
        # Sample
        # ==========================================================

        if sample_accession:
            metadata.sample.accession = sample_accession

        sample_title = self._first(fields, "Sample_title")

        if sample_title:
            metadata.sample.name = sample_title
            metadata.experiment.title = sample_title

        organism = self._first(
            fields,
            "Sample_organism_ch1",
        )

        if organism:
            metadata.sample.organism = organism

        # ==========================================================
        # Sequencing metadata
        # ==========================================================

        metadata.experiment.library_strategy = self._first(
            fields,
            "Sample_library_strategy",
        )

        metadata.experiment.library_source = self._first(
            fields,
            "Sample_library_source",
        )

        metadata.experiment.library_selection = self._first(
            fields,
            "Sample_library_selection",
        )

        metadata.experiment.instrument = self._first(
            fields,
            "Sample_instrument_model",
        )

        platform_ids = fields.get("Sample_platform_id", [])

        if platform_ids:
            metadata.experiment.platform = "; ".join(
                dict.fromkeys(platform_ids)
            )

        # ==========================================================
        # Relationships
        # ==========================================================

        biosample = self._relation_accession(
            fields.get("Sample_relation", []),
            "BioSample",
        )

        if biosample:
            metadata.sample.biosample = biosample

        sra_accession = self._relation_accession(
            fields.get("Sample_relation", []),
            "SRA",
        )

        if sra_accession:
            metadata.experiment.accession = sra_accession

        if not metadata.study.accession:
            metadata.study.accession = self._first(
                fields,
                "Sample_series_id",
            )

        # ==========================================================
        # Preserve deposited sample evidence
        # ==========================================================

        attribute_fields = (
            "Sample_source_name_ch1",
            "Sample_taxid_ch1",
            "Sample_molecule_ch1",
            "Sample_description",
        )

        for field in attribute_fields:
            for value in fields.get(field, []):
                self._add_attribute(
                    metadata,
                    self._attribute_name(field),
                    value,
                )

        for value in fields.get(
            "Sample_characteristics_ch1",
            [],
        ):
            if ":" in value:
                name, attribute_value = value.split(
                    ":",
                    1,
                )

                self._add_attribute(
                    metadata,
                    name.strip(),
                    attribute_value.strip(),
                )
            else:
                self._add_attribute(
                    metadata,
                    "characteristics",
                    value,
                )

        # ==========================================================
        # Preserve protocol evidence as attributes
        # ==========================================================

        protocol_fields = (
            "Sample_treatment_protocol_ch1",
            "Sample_growth_protocol_ch1",
            "Sample_extract_protocol_ch1",
            "Sample_data_processing",
        )

        for field in protocol_fields:
            for value in fields.get(field, []):
                self._add_attribute(
                    metadata,
                    self._attribute_name(field),
                    value,
                )

        return metadata
