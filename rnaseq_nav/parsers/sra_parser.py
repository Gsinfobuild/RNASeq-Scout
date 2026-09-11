"""
RNASeq Navigator

SRA Parser
==========

Version: 2.0

Purpose
-------
Parse the ExpXml and Runs XML returned by the NCBI
SRA ESummary API into RNASeq Navigator Metadata objects.

Author:
RNASeq Navigator Project
"""

import xml.etree.ElementTree as ET

from rnaseq_nav.models import Metadata, StudyExperiment


class SRAParser:
    """
    Parser for NCBI SRA metadata.
    """

    def parse_bioproject(
        self,
        bioproject_xml,
    ) -> tuple[str, str]:
        """
        Parse BioProject XML and return the project title
        and description.

        Returns
        -------
        tuple[str, str]
            (title, description)
        """

        if not bioproject_xml:
            return "", ""

        if isinstance(bioproject_xml, bytes):
            bioproject_xml = bioproject_xml.decode(
                "utf-8",
                errors="replace",
            )

        root = ET.fromstring(bioproject_xml)

        title = ""
        description = ""

        title_node = root.find(
            ".//ProjectDescr/Title"
        )

        if title_node is not None and title_node.text:
            title = title_node.text.strip()

        description_node = root.find(
            ".//ProjectDescr/Description"
        )

        if (
            description_node is not None
            and description_node.text
        ):
            description = description_node.text.strip()

        return title, description


    def parse_study_experiments(self, summaries) -> list[StudyExperiment]:
        """
        Parse study-level ESummary records into StudyExperiment objects.

        Each ESummary record represents an SRA experiment and may
        contain one or more associated runs.
        """

        study_experiments = []

        for summary_wrapper in summaries:

            if not summary_wrapper:
                continue

            record = summary_wrapper[0]

            expxml = record.get("ExpXml", "")
            runs_xml = record.get("Runs", "")

            if not expxml:
                continue

            root = ET.fromstring(
                f"<ROOT>{expxml}</ROOT>"
            )

            sample = root.find("Sample")
            biosample = root.find("Biosample")
            experiment = root.find("Experiment")
            organism = root.find("Organism")

            sample_accession = ""
            biosample_accession = ""
            experiment_accession = ""
            experiment_title = ""
            library_strategy = ""
            organism_name = ""
            sample_name = ""

            if sample is not None:
                sample_accession = sample.attrib.get(
                    "acc", ""
                )
                sample_name = sample.attrib.get(
                    "name", ""
                )

            if biosample is not None and biosample.text:
                biosample_accession = (
                    biosample.text.strip()
                )

            if experiment is not None:
                experiment_accession = experiment.attrib.get(
                    "acc", ""
                )
                experiment_title = experiment.attrib.get(
                    "name", ""
                )

            library_descriptor = root.find(
                "Library_descriptor"
            )

            if library_descriptor is not None:
                strategy = library_descriptor.find(
                    "LIBRARY_STRATEGY"
                )

                if strategy is not None and strategy.text:
                    library_strategy = strategy.text.strip()

            if organism is not None:
                organism_name = organism.attrib.get(
                    "ScientificName", ""
                )

            run_accessions = []

            if runs_xml:
                run_root = ET.fromstring(
                    f"<ROOT>{runs_xml}</ROOT>"
                )

                for run in run_root.findall("Run"):
                    accession = run.attrib.get(
                        "acc", ""
                    )

                    if accession:
                        run_accessions.append(
                            accession
                        )

            study_experiments.append(
                StudyExperiment(
                    sample_accession=sample_accession,
                    biosample_accession=biosample_accession,
                    experiment_accession=experiment_accession,
                    experiment_title=experiment_title,
                    library_strategy=library_strategy,
                    run_accessions=run_accessions,
                    organism=organism_name,
                    sample_name=sample_name,
                )
            )

        return study_experiments


    def parse(self, expxml: str, runs_xml: str = "") -> Metadata:
        """
        Parse ExpXml and Runs XML into a Metadata object.

        Parameters
        ----------
        expxml : str
            XML stored in the ExpXml field.

        runs_xml : str
            XML stored in the Runs field.

        Returns
        -------
        Metadata
        """

        metadata = Metadata()

        # ==========================================================
        # Parse ExpXml
        # ==========================================================

        root = ET.fromstring(f"<ROOT>{expxml}</ROOT>")

        # ----------------------------------------------------------
        # Summary
        # ----------------------------------------------------------

        summary = root.find("Summary")

        if summary is not None:

            title = summary.find("Title")

            if title is not None and title.text:
                metadata.experiment.title = title.text.strip()

            platform = summary.find("Platform")

            if platform is not None:

                if platform.text:
                    metadata.experiment.platform = (
                        platform.text.strip()
                    )

                instrument_model = platform.attrib.get(
                    "instrument_model"
                )

                if instrument_model:
                    metadata.experiment.instrument = (
                        instrument_model
                    )

            statistics = summary.find("Statistics")

            if statistics is not None:

                total_spots = statistics.attrib.get(
                    "total_spots"
                )

                total_bases = statistics.attrib.get(
                    "total_bases"
                )

                if total_spots:
                    metadata.run.total_spots = int(
                        total_spots
                    )

                if total_bases:
                    metadata.run.total_bases = int(
                        total_bases
                    )

        # ----------------------------------------------------------
        # Study
        # ----------------------------------------------------------

        study = root.find("Study")

        if study is not None:
            metadata.study.accession = (
                study.attrib.get("acc", "")
            )

        # ----------------------------------------------------------
        # Experiment
        # ----------------------------------------------------------

        experiment = root.find("Experiment")

        if experiment is not None:
            metadata.experiment.accession = (
                experiment.attrib.get("acc", "")
            )

        # ----------------------------------------------------------
        # Organism
        # ----------------------------------------------------------

        organism = root.find("Organism")

        if organism is not None:
            metadata.sample.organism = (
                organism.attrib.get(
                    "ScientificName",
                    ""
                )
            )

        # ----------------------------------------------------------
        # Sample
        # ----------------------------------------------------------

        sample = root.find("Sample")

        if sample is not None:
            metadata.sample.accession = (
                sample.attrib.get("acc", "")
            )

        # ----------------------------------------------------------
        # Instrument
        # ----------------------------------------------------------

        instrument = root.find("Instrument")

        if (
            instrument is not None
            and not metadata.experiment.instrument
        ):

            if instrument.attrib:

                first_key = next(
                    iter(instrument.attrib)
                )

                metadata.experiment.instrument = (
                    instrument.attrib[first_key]
                )

        # ----------------------------------------------------------
        # Library Descriptor
        # ----------------------------------------------------------

        library = root.find("Library_descriptor")

        if library is not None:

            strategy = library.find(
                "LIBRARY_STRATEGY"
            )

            if (
                strategy is not None
                and strategy.text
            ):
                metadata.experiment.library_strategy = (
                    strategy.text.strip()
                )

            source = library.find(
                "LIBRARY_SOURCE"
            )

            if (
                source is not None
                and source.text
            ):
                metadata.experiment.library_source = (
                    source.text.strip()
                )

            selection = library.find(
                "LIBRARY_SELECTION"
            )

            if (
                selection is not None
                and selection.text
            ):
                metadata.experiment.library_selection = (
                    selection.text.strip()
                )

            layout = library.find(
                "LIBRARY_LAYOUT"
            )

            if layout is not None:

                if layout.find("PAIRED") is not None:
                    metadata.experiment.layout = (
                        "PAIRED"
                    )

                elif layout.find("SINGLE") is not None:
                    metadata.experiment.layout = (
                        "SINGLE"
                    )

        # ----------------------------------------------------------
        # BioProject
        # ----------------------------------------------------------

        bioproject = root.find("Bioproject")

        if (
            bioproject is not None
            and bioproject.text
        ):
            metadata.project.accession = (
                bioproject.text.strip()
            )

        # ----------------------------------------------------------
        # BioSample
        # ----------------------------------------------------------

        biosample = root.find("Biosample")

        if (
            biosample is not None
            and biosample.text
        ):
            metadata.sample.biosample = (
                biosample.text.strip()
            )

        # ==========================================================
        # Parse Runs XML
        # ==========================================================

        if runs_xml:

            run_root = ET.fromstring(
                f"<ROOT>{runs_xml}</ROOT>"
            )

            run = run_root.find("Run")

            if run is not None:

                metadata.run.accession = (
                    run.attrib.get("acc", "")
                )

                spots = run.attrib.get(
                    "total_spots"
                )

                if spots:
                    metadata.run.total_spots = int(
                        spots
                    )

                bases = run.attrib.get(
                    "total_bases"
                )

                if bases:
                    metadata.run.total_bases = int(
                        bases
                    )

                metadata.run.public = (
                    run.attrib.get(
                        "is_public",
                        "false"
                    ).lower()
                    == "true"
                )

                metadata.run.cluster = (
                    run.attrib.get(
                        "cluster_name",
                        ""
                    )
                )

                metadata.run.static_data = (
                    run.attrib.get(
                        "static_data_available",
                        "false"
                    ).lower()
                    == "true"
                )

        return metadata
