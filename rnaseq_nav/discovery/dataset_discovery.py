"""
RNASeq Navigator

Dataset Discovery Engine

Version 3.0
API STATUS: STABLE

Public API
----------
fetch(accession)

search(
    organism,
    strategy="RNA-Seq",
    layout=None,
    platform=None,
    source=None,
    selection=None,
    max_results=20,
    diversity="project",
)

NOTE
----
The search() signature is frozen for backward compatibility.
New filters should only be added as OPTIONAL keyword arguments.
Existing parameters must never be removed.
"""

from __future__ import annotations

from typing import Optional

from rnaseq_nav.clients.ncbi import NCBIClient
from rnaseq_nav.clients.geo import GEOClient
from rnaseq_nav.parsers.sra_parser import SRAParser
from rnaseq_nav.parsers.geo_parser import GEOParser
from rnaseq_nav.models import StudyExperiment
from rnaseq_nav.accession import detect_accession
from rnaseq_nav.discovery.diversity import DatasetDiversity
from rnaseq_nav.discovery.ranker import DatasetRanker


class DatasetDiscovery:
    """
    Stable public interface for dataset discovery.
    """

    API_VERSION = "1.0"

    def __init__(
        self,
        email: str,
        api_key: Optional[str] = None,
        verbose: bool = False,
    ):

        self.client = NCBIClient(
            email=email,
            api_key=api_key,
            verbose=verbose,
        )

        self.parser = SRAParser()

        self.geo_client = GEOClient(
            email=email,
        )

        self.geo_parser = GEOParser()

    # ---------------------------------------------------------
    # PUBLIC API (STABLE)
    # ---------------------------------------------------------

    def fetch(self, accession: str):
        """
        Retrieve one accession.

        Parameters
        ----------
        accession
            SRR / ERR / DRR / SRX / SRP / PRJNA ...

        Returns
        -------
        Metadata
        """

        detected = detect_accession(accession)

        if (
            detected["database"] == "GEO"
            and detected["type"] in {"Series", "Sample"}
        ):
            text = self.geo_client.fetch(
                detected["accession"]
            )

            return self.geo_parser.parse(text)

        summary = self.client.fetch(accession)

        record = summary[0]

        return self.parser.parse(
            record["ExpXml"],
            record["Runs"],
        )

    # ---------------------------------------------------------
    # Study-level retrieval
    # ---------------------------------------------------------

    # GEO study-level retrieval

    def fetch_geo_study(
        self,
        accession: str,
        max_samples: int = 100,
    ):
        """
        Retrieve a GEO Series and its explicitly listed GSM samples.
        """
        detected = detect_accession(accession)

        if not (
            detected["database"] == "GEO"
            and detected["type"] == "Series"
        ):
            raise ValueError(
                "fetch_geo_study() requires a GEO Series "
                f"accession (GSE), not '{accession}'."
            )

        if max_samples < 1:
            raise ValueError(
                "max_samples must be at least 1."
            )

        series_text = self.geo_client.fetch(
            detected["accession"]
        )

        series_metadata = self.geo_parser.parse(
            series_text
        )

        sample_accessions = self.geo_parser.sample_accessions(
            series_text
        )[:max_samples]

        study_experiments = []

        for sample_accession in sample_accessions:
            sample_text = self.geo_client.fetch(
                sample_accession
            )

            metadata = self.geo_parser.parse(
                sample_text
            )

            study_experiments.append(
                StudyExperiment(
                    sample_accession=metadata.sample.accession,
                    biosample_accession=metadata.sample.biosample,
                    experiment_accession=metadata.experiment.accession,
                    experiment_title=metadata.experiment.title,
                    library_strategy=metadata.experiment.library_strategy,
                    organism=metadata.sample.organism,
                    sample_name=metadata.sample.name,
                )
            )

        series_metadata.study_experiments = study_experiments

        return {
            "metadata": series_metadata,
            "sample_accessions": sample_accessions,
            "study_experiments": study_experiments,
        }

    def fetch_study(
        self,
        accession: str,
        max_results: int = 1000,
    ):
        """
        Retrieve all experiment records belonging to a study.

        Parameters
        ----------
        accession : str
            Study-level accession such as SRP, ERP, or DRP.

        Returns
        -------
        list[StudyExperiment]
            Experiment-level records associated with the study.
        """

        if max_results <= 0:
            raise ValueError(
                "max_results must be greater than zero."
            )

        summaries = self.client.fetch_study(
            accession,
            max_results=max_results,
        )

        return self.parser.parse_study_experiments(
            summaries
        )

    # ---------------------------------------------------------
    # PUBLIC API (STABLE)
    # ---------------------------------------------------------

    def fetch_linked_sra_records(
        self,
        accession: str,
        max_records: int = 100,
    ) -> dict:
        """
        Discover experiment/run records through the accession's parent study.

        This method uses the study relationship reported by the existing
        metadata parser. It does not guarantee that every link shown on
        an NCBI webpage has been retrieved.

        Parameters
        ----------
        accession : str
            Starting SRA accession, such as SRX, SRR, or SRP.
        max_records : int
            Maximum number of experiment records returned to the caller.

        Returns
        -------
        dict
            Starting accession, parent study accession, experiment records,
            unique experiment/run counts, and a truncation indicator.
        """
        accession = accession.strip().upper()

        if max_records <= 0:
            raise ValueError(
                "max_records must be greater than zero."
            )

        if not accession:
            raise ValueError(
                "A starting accession is required."
            )

        metadata = self.fetch(accession)
        study = getattr(metadata, "study", None)
        study_accession = (
            getattr(study, "accession", "") or ""
        ).strip().upper()

        if not study_accession:
            raise ValueError(
                f"No parent study accession could be resolved for "
                f"'{accession}'. Linked-record discovery requires a "
                "parent study."
            )

        retrieval_limit = 1000
        records = self.fetch_study(
            study_accession,
            max_results=retrieval_limit,
        )
        records = list(records or [])

        # Remove duplicate experiment records while preserving order.
        unique_records = []
        seen_experiments = set()

        for record in records:
            experiment_accession = (
                getattr(record, "experiment_accession", "") or ""
            ).strip().upper()

            # Retain records with no accession, but do not deduplicate
            # them by an empty identifier.
            if experiment_accession:
                if experiment_accession in seen_experiments:
                    continue
                seen_experiments.add(experiment_accession)

            unique_records.append(record)

        truncated = len(unique_records) > max_records
        selected_records = unique_records[:max_records]

        unique_runs = {
            run.strip().upper()
            for record in selected_records
            for run in (getattr(record, "run_accessions", []) or [])
            if isinstance(run, str) and run.strip()
        }

        return {
            "starting_accession": accession,
            "study_accession": study_accession,
            "experiments": selected_records,
            "experiment_count": len(selected_records),
            "run_count": len(unique_runs),
            "truncated": truncated,
            "max_records": max_records,
            "study_records_retrieved": len(records),
            "study_retrieval_limit": retrieval_limit,
            "study_retrieval_cap_reached": len(records) >= retrieval_limit,
            "retrieval_scope": "parent_study",
            "complete_link_coverage_verified": False,
        }

    def fetch_experiment_at_a_glance(
        self,
        accession: str,
    ):
        """
        Retrieve the study-level information required to build
        an Experiment-at-a-Glance summary.

        Returns
        -------
        dict
            Contains study experiments and associated BioProject
            title/description.
        """

        study_experiments = self.fetch_study(accession)

        project_accession = ""

        if study_experiments:
            first = study_experiments[0]

            # BioProject accession is not currently stored in
            # StudyExperiment, so obtain it from the canonical
            # single-record metadata retrieval.
            metadata = self.fetch(accession)

            project_accession = (
                metadata.project.accession
            )

        project_title = ""
        project_description = ""

        if project_accession:
            bioproject_xml = (
                self.client.fetch_bioproject(
                    project_accession
                )
            )

            (
                project_title,
                project_description,
            ) = self.parser.parse_bioproject(
                bioproject_xml
            )

        return {
            "study_experiments": study_experiments,
            "project_accession": project_accession,
            "project_title": project_title,
            "project_description": project_description,
        }


    def search(
        self,
        organism: str,
        strategy: str = "RNA-Seq",
        layout: Optional[str] = None,
        platform: Optional[str] = None,
        source: Optional[str] = None,
        selection: Optional[str] = None,
        max_results: int = 20,
        diversity: str = "project",
    ):
        """
        Search public sequencing datasets.

        Optional metadata filters use case-insensitive
        exact matching and are applied after retrieval.

        diversity:
            "project": best-scoring record per project
            "study": one record per study
            "run": preserve individual records

        Filtering occurs after retrieval, so fewer than
        max_results records may be returned.
        """


        allowed_diversity = {"project", "study", "run"}
        if diversity not in allowed_diversity:
            raise ValueError(
                f"Unsupported diversity '{diversity}'. "
                f"Choose one of: {', '.join(sorted(allowed_diversity))}."
            )

        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        query = (
            f'"{organism}"[Organism] '
            f'AND "{strategy}" '
            f'AND public[Access]'
        )

        summaries = self.client.search(
            query=query,
            max_results=max_results,
        )

        metadata_list = []

        for summary in summaries:
            try:
                metadata = self.parser.parse(summary)
                metadata_list.append(metadata)
            except Exception:
                continue

        filters = (
            ("layout", layout),
            ("platform", platform),
            ("library_source", source),
            ("library_selection", selection),
        )

        for field_name, expected in filters:
            if expected is None:
                continue

            expected_value = str(expected).strip().casefold()

            metadata_list = [
                metadata
                for metadata in metadata_list
                if str(
                    getattr(
                        metadata.experiment,
                        field_name,
                        "",
                    ) or ""
                ).strip().casefold() == expected_value
            ]

        if diversity == "project":
            metadata_list = DatasetRanker.best_per_project(
                metadata_list
            )
        elif diversity == "study":
            metadata_list = DatasetDiversity.unique_studies(
                metadata_list
            )

        return metadata_list
