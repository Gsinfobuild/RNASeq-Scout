"""
RNASeq Navigator
================

Public Navigator API

Version: 1.4

Purpose
-------
Provides the single public interface to the RNASeq Navigator
framework.

All user interfaces (CLI, GUI, Web, Python API) should interact
with this class.

Pipeline
--------
    Fetch
      ↓
    Normalize
      ↓
    Validate
      ↓
    Metadata Intelligence
      ↓
    Modality / Workflow Intelligence
      ↓
    Experimental Design Intelligence
      ↓
    Dataset Suitability
      ↓
    Reanalysis Readiness
      ↓
    Analysis Planning
      ↓
    Interpret
      ↓
    Build Report
      ↓
    InspectionResult

Author
------
RNASeq Navigator Project
"""

from rnaseq_nav.discovery.dataset_discovery import (
    DatasetDiscovery,
)

from rnaseq_nav.normalization.normalizer import (
    MetadataNormalizer,
)

from rnaseq_nav.validation.validator import (
    MetadataValidator,
)

from rnaseq_nav.intelligence.interpreter import (
    DatasetInterpreter,
)

from rnaseq_nav.intelligence.report_builder import (
    DatasetReportBuilder,
)

from rnaseq_nav.intelligence.metadata_intelligence import (
    generate_metadata_insight,
)

from rnaseq_nav.intelligence.study_landscape import (
    generate_study_experimental_landscape,
)

from rnaseq_nav.intelligence.modality_intelligence import (
    generate_modality_insight,
)

from rnaseq_nav.intelligence.design_intelligence import (
    generate_design_insight,
)

from rnaseq_nav.intelligence.suitability import (
    generate_suitability_insight,
)

from rnaseq_nav.intelligence.reanalysis_readiness import (
    generate_reanalysis_readiness,
)

from rnaseq_nav.intelligence.analysis_planner import (
    generate_analysis_plan,
)

from rnaseq_nav.intelligence.sample_enrichment import (
    enrich_sample_from_biosample,
)


from rnaseq_nav.core import (
    InspectionResult,
)


class RNASeqNavigator:
    """
    Public API for RNASeq Navigator.

    This class coordinates the complete metadata inspection
    pipeline.

    Public methods
    --------------

    fetch()
        Fetch metadata.

    normalize()
        Fetch and normalize metadata.

    validate()
        Fetch, normalize, and validate metadata.

    inspect()
        Execute the complete pipeline and return an
        InspectionResult.
    """

    # ======================================================
    # Initialization
    # ======================================================

    def __init__(
        self,
        email: str,
    ):
        """
        Initialize RNASeq Navigator.

        Parameters
        ----------
        email : str
            Email address used for NCBI Entrez requests.
        """

        self.discovery = DatasetDiscovery(
            email=email
        )

        self.normalizer = MetadataNormalizer()

        self.validator = MetadataValidator()

        self.interpreter = DatasetInterpreter()

        self.report_builder = DatasetReportBuilder()

    # ======================================================
    # Fetch
    # ======================================================

    def fetch(
        self,
        accession: str,
    ):
        """
        Fetch metadata for an accession.

        Parameters
        ----------
        accession : str
            SRA accession such as SRR17730393.

        Returns
        -------
        Metadata
            Metadata returned by the discovery layer.
        """

        return self.discovery.fetch(
            accession
        )

    # ======================================================
    # Normalize
    # ======================================================

    def normalize(
        self,
        accession: str,
    ):
        """
        Fetch and normalize metadata.

        Parameters
        ----------
        accession : str
            SRA accession.

        Returns
        -------
        NormalizationResult
            Structured normalization result.
        """

        metadata = self.fetch(
            accession
        )

        normalization = (
            self.normalizer.normalize(
                metadata
            )
        )

        return normalization

    # ======================================================
    # Validate
    # ======================================================

    def validate(
        self,
        accession: str,
    ):
        """
        Fetch, normalize, and validate metadata.

        Parameters
        ----------
        accession : str
            SRA accession.

        Returns
        -------
        ValidationResult
            Structured validation result.
        """

        metadata = self.fetch(
            accession
        )

        normalization = (
            self.normalizer.normalize(
                metadata
            )
        )

        normalized_metadata = (
            normalization.metadata
        )

        validation = (
            self.validator.validate(
                normalized_metadata
            )
        )

        return validation

    # ======================================================
    # Inspect
    # ======================================================

    def _build_experiment_at_a_glance(
        self,
        accession: str,
    ):
        """
        Build a study-level ExperimentAtGlance summary.

        Study-level retrieval is performed only for study accessions.
        """

        from rnaseq_nav.core.results import ExperimentAtGlance

        if not accession.startswith(("SRP", "ERP", "DRP")):
            return None

        context = self.discovery.fetch_experiment_at_a_glance(
            accession
        )

        study_experiments = context["study_experiments"]

        unique_samples = {
            item.sample_accession
            for item in study_experiments
            if item.sample_accession
        }

        unique_biosamples = {
            item.biosample_accession
            for item in study_experiments
            if item.biosample_accession
        }

        run_accessions = {
            run_accession
            for item in study_experiments
            for run_accession in item.run_accessions
            if run_accession
        }

        return ExperimentAtGlance(
            study_title=context["project_title"],
            study_description=context["project_description"],
            unique_sample_count=len(unique_samples),
            unique_biosample_count=len(unique_biosamples),
            experiment_count=len(study_experiments),
            run_count=len(run_accessions),
            study_experiments=study_experiments,
        )


    def inspect(
        self,
        accession: str,
        enrich_biosample: bool = False,
    ):
        """
        Execute the complete metadata inspection pipeline.

        Pipeline
        --------

        1. Fetch metadata
        2. Normalize metadata
        3. Validate normalized metadata
        4. Build study-level Experiment-at-a-Glance summary when applicable
        5. Generate metadata intelligence
        6. Classify sequencing modality and workflow compatibility
        7. Generate experimental design intelligence
        8. Generate dataset suitability assessment
        9. Generate evidence-based reanalysis readiness assessment
        10. Generate contextual analysis plan
        11. Interpret normalized metadata
        12. Build dataset report
        13. Return InspectionResult

        Parameters
        ----------
        accession : str
            SRA accession such as SRR17730393 or SRP356545.

        enrich_biosample : bool
            When True, explicitly retrieve and parse the
            associated NCBI BioSample record before
            normalization. Defaults to False.

        Returns
        -------
        InspectionResult
            Structured inspection result containing metadata,
            study-level context when applicable, intelligence
            layers, analysis planning, and dataset report.
        """

        try:

            # ------------------------------------------------
            # Step 1
            # Fetch metadata
            # ------------------------------------------------

            metadata = self.fetch(
                accession
            )

            # ------------------------------------------------
            # Step 1.5
            # Optional BioSample enrichment
            # ------------------------------------------------
            #
            # BioSample enrichment is deliberately opt-in.
            # The default inspection path remains unchanged.
            #
            # Enrichment happens before normalization so that
            # downstream intelligence layers can access the
            # richer sample metadata when explicitly requested.
            #
            # The enrichment layer performs retrieval and
            # metadata merging only. It does not infer
            # experimental groups, treatments, controls,
            # replicates, or statistical contrasts.

            if enrich_biosample:
                metadata = enrich_sample_from_biosample(
                    metadata,
                    self.discovery.client,
                )

            # ------------------------------------------------
            # Step 2
            # Normalize metadata
            # ------------------------------------------------

            normalization = (
                self.normalizer.normalize(
                    metadata
                )
            )

            normalized_metadata = (
                normalization.metadata
            )

            # ------------------------------------------------
            # Step 3
            # Validate metadata
            # ------------------------------------------------

            validation = (
                self.validator.validate(
                    normalized_metadata
                )
            )

            # ------------------------------------------------
            # Step 4
            # Experiment at a Glance
            # ------------------------------------------------
            #
            # Study-level enrichment is performed only for
            # study accessions. We deliberately do not retrieve
            # every experiment in a study when the user enters
            # an individual run or experiment accession.
            #
            # This keeps run-level inspection lightweight while
            # allowing study accessions to provide a broader
            # experimental context.

            experiment_at_glance = (
                self._build_experiment_at_a_glance(
                    accession
                )
            )

            # ------------------------------------------------
            # Step 5
            # Study Experimental Landscape
            # ------------------------------------------------
            #
            # Reuse the study-level experiment records already
            # retrieved for Experiment-at-a-Glance. No second
            # study-level NCBI retrieval is performed here.
            #
            # This layer describes observed assay families and
            # experimental context labels. It does not infer
            # controls, treatments, replicates, time points, or
            # statistical contrasts.

            study_experimental_landscape = None

            if experiment_at_glance is not None:
                study_experimental_landscape = (
                    generate_study_experimental_landscape(
                        experiment_at_glance.study_experiments
                    )
                )

            # ------------------------------------------------
            # Step 6
            # Modality / Workflow Intelligence
            # ------------------------------------------------
            #
            # Establish sequencing modality from structured
            # library metadata before generating higher-level
            # biological interpretation.

            modality_insight = (
                generate_modality_insight(
                    normalized_metadata,
                )
            )

            # ------------------------------------------------
            # Step 7
            # Metadata Intelligence
            # ------------------------------------------------
            #
            # Metadata interpretation can use the established
            # modality to avoid allowing contradictory free-text
            # titles to override structured sequencing evidence.

            metadata_insight = (
                generate_metadata_insight(
                    normalized_metadata,
                    modality_insight=modality_insight,
                )
            )

            # ------------------------------------------------
            # Step 8
            # Experimental Design Intelligence
            # ------------------------------------------------

            design_insight = (
                generate_design_insight(
                    normalized_metadata,
                )
            )

            # ------------------------------------------------
            # Step 9
            # Dataset Suitability
            # ------------------------------------------------

            suitability_insight = (
                generate_suitability_insight(
                    normalized_metadata,
                    design_insight,
                    modality_insight,
                )
            )

            # ------------------------------------------------
            # Step 10
            # Reanalysis Readiness
            # ------------------------------------------------
            #
            # This layer assesses whether the available public
            # metadata provide enough evidence for defensible
            # downstream reanalysis. It does not replace
            # dataset suitability and does not infer missing
            # experimental design information.
            #

            reanalysis_readiness = (
                generate_reanalysis_readiness(
                    normalized_metadata,
                    modality_insight,
                    design_insight,
                    suitability_insight,
                    experiment_at_glance,
                    study_experimental_landscape,
                )
            )

            # ------------------------------------------------
            # Step 11
            # Analysis Planning
            # ------------------------------------------------

            analysis_plan = (
                generate_analysis_plan(
                    normalized_metadata,
                    metadata_insight,
                    design_insight,
                    suitability_insight,
                    modality_insight,
                )
            )

            # ------------------------------------------------
            # Step 11
            # Interpret metadata
            # ------------------------------------------------

            description = (
                self.interpreter.describe(
                    normalized_metadata,
                    modality_insight=modality_insight,
                )
            )

            # ------------------------------------------------
            # Step 12
            # Build report
            # ------------------------------------------------

            report = (
                self.report_builder.build(
                    normalized_metadata,
                    normalization,
                    validation,
                    description,
                )
            )

            # ------------------------------------------------
            # Step 13
            # Return successful result
            # ------------------------------------------------

            return InspectionResult(

                success=True,

                accession=accession,

                metadata=normalized_metadata,

                experiment_at_glance=experiment_at_glance,

                study_experimental_landscape=(
                    study_experimental_landscape
                ),

                metadata_insight=metadata_insight,

                modality_insight=modality_insight,

                design_insight=design_insight,

                suitability_insight=suitability_insight,

                reanalysis_readiness=reanalysis_readiness,

                analysis_plan=analysis_plan,

                report=report,

                normalization=normalization,

                validation=validation,

                error=None,

            )

        except Exception as exc:

            # ------------------------------------------------
            # Controlled failure
            # ------------------------------------------------

            return InspectionResult(

                success=False,

                accession=accession,

                metadata=None,

                experiment_at_glance=None,

                study_experimental_landscape=None,

                metadata_insight=None,

                modality_insight=None,

                design_insight=None,

                suitability_insight=None,

                reanalysis_readiness=None,

                analysis_plan=None,

                report=None,

                normalization=None,

                validation=None,

                error=str(exc),

            )
