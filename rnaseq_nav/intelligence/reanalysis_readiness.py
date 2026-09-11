"""
RNASeq Scout

Reanalysis Readiness Intelligence

Assesses whether available public sequencing metadata provide
enough evidence for defensible downstream reanalysis.

This layer is deliberately conservative. It does not invent
controls, treatments, biological replicates, batch structure,
time points, or statistical contrasts.

For study accessions, the assessment uses the complete study-level
experiment collection and experimental landscape. Individual
experiment metadata are retained as context, but are never treated
as representative of the complete study unless the study structure
supports that interpretation.
"""

from rnaseq_nav.models import ReanalysisReadinessInsight


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_established(value: str) -> bool:
    value = _clean(value).lower()

    if not value:
        return False

    unavailable_terms = (
        "could not be established",
        "cannot be established",
        "not established",
        "not available",
        "unavailable",
        "unknown",
        "unspecified",
    )

    return not any(term in value for term in unavailable_terms)


def _append_unique(items: list[str], value: str) -> None:
    value = _clean(value)

    if value and value not in items:
        items.append(value)


def _get_experiment_metadata(metadata):
    return getattr(metadata, "experiment", None)


def _get_sample_metadata(metadata):
    return getattr(metadata, "sample", None)


def _is_study_context_available(
    experiment_at_glance,
    study_experimental_landscape,
) -> bool:
    return (
        experiment_at_glance is not None
        or study_experimental_landscape is not None
    )


def _add_study_evidence(
    observed_evidence: list[str],
    not_established: list[str],
    warnings: list[str],
    experiment_at_glance,
    study_experimental_landscape,
) -> None:
    if experiment_at_glance is not None:
        experiment_count = getattr(
            experiment_at_glance,
            "experiment_count",
            0,
        )
        sample_count = getattr(
            experiment_at_glance,
            "unique_sample_count",
            0,
        )
        biosample_count = getattr(
            experiment_at_glance,
            "unique_biosample_count",
            0,
        )
        run_count = getattr(
            experiment_at_glance,
            "run_count",
            0,
        )

        if experiment_count:
            _append_unique(
                observed_evidence,
                (
                    "Study-level experiment collection contains "
                    f"{experiment_count} experiment records."
                ),
            )

        if sample_count:
            _append_unique(
                observed_evidence,
                (
                    "Study-level metadata expose "
                    f"{sample_count} unique SRA sample identifier(s)."
                ),
            )

        if biosample_count:
            _append_unique(
                observed_evidence,
                (
                    "Study-level metadata expose "
                    f"{biosample_count} unique BioSample identifier(s)."
                ),
            )

        if run_count:
            _append_unique(
                observed_evidence,
                (
                    "Study-level metadata contain "
                    f"{run_count} unique run(s)."
                ),
            )

    if study_experimental_landscape is not None:
        assay_families = getattr(
            study_experimental_landscape,
            "observed_assay_families",
            [],
        )
        contexts = getattr(
            study_experimental_landscape,
            "observed_contexts",
            [],
        )
        assay_counts = getattr(
            study_experimental_landscape,
            "assay_family_counts",
            {},
        )

        if assay_families:
            _append_unique(
                observed_evidence,
                (
                    "Observed study assay families: "
                    + ", ".join(assay_families)
                    + "."
                ),
            )

        if contexts:
            _append_unique(
                observed_evidence,
                (
                    "Observed study contains "
                    f"{len(contexts)} experimental context label(s)."
                ),
            )

            if len(contexts) > 1:
                _append_unique(
                    observed_evidence,
                    "Multiple experimental contexts are observed at study level.",
                )

        non_rna_assay_families = [
            family
            for family in assay_families
            if family not in {"RNA-seq", "Unclassified"}
        ]

        if non_rna_assay_families:
            _append_unique(
                warnings,
                (
                    "The study contains multiple assay families; "
                    "the complete study should not automatically be "
                    "treated as one homogeneous RNA-seq reanalysis unit."
                ),
            )

        if len(assay_counts) > 1:
            _append_unique(
                not_established,
                (
                    "A single RNA-seq analysis unit cannot be established "
                    "from the complete study-level assay collection."
                ),
            )

        _append_unique(
            not_established,
            (
                "Biological replicate identity is not established solely "
                "from repeated study experiment records."
            ),
        )

        if contexts:
            _append_unique(
                not_established,
                (
                    "Study-level control and treatment assignments are "
                    "not established solely from context labels."
                ),
            )


def _add_individual_experiment_evidence(
    observed_evidence: list[str],
    experiment_metadata,
    sample_metadata,
    modality_insight,
) -> None:
    if experiment_metadata is None:
        return

    accession = _clean(
        getattr(experiment_metadata, "accession", "")
    )

    strategy = _clean(
        getattr(experiment_metadata, "library_strategy", "")
    )

    source = _clean(
        getattr(experiment_metadata, "library_source", "")
    )

    selection = _clean(
        getattr(experiment_metadata, "library_selection", "")
    )

    layout = _clean(
        getattr(experiment_metadata, "layout", "")
    )

    platform = _clean(
        getattr(experiment_metadata, "platform", "")
    )

    organism = ""
    if sample_metadata is not None:
        organism = _clean(
            getattr(sample_metadata, "organism", "")
        )

    if accession:
        _append_unique(
            observed_evidence,
            f"Representative experiment metadata are available for {accession}.",
        )

    if modality_insight is not None:
        modality = _clean(
            getattr(modality_insight, "modality", "")
        )

        if modality:
            _append_unique(
                observed_evidence,
                f"Representative experiment modality: {modality}.",
            )

        compatibility = _clean(
            getattr(modality_insight, "compatibility_status", "")
        )

        if compatibility:
            if compatibility.lower() == "compatible":
                _append_unique(
                    observed_evidence,
                    "The dataset is classified as compatible with RNA-seq analysis.",
                )
            else:
                _append_unique(
                    observed_evidence,
                    (
                        "Representative experiment RNA-seq compatibility: "
                        f"{compatibility}."
                    ),
                )

    if strategy:
        _append_unique(
            observed_evidence,
            f"Representative experiment library strategy: {strategy}.",
        )

    if source:
        _append_unique(
            observed_evidence,
            f"Representative experiment library source: {source}.",
        )

    if selection:
        _append_unique(
            observed_evidence,
            f"Representative experiment library selection: {selection}.",
        )

    if layout:
        _append_unique(
            observed_evidence,
            f"Representative experiment read layout: {layout}.",
        )

    if platform:
        _append_unique(
            observed_evidence,
            f"Representative experiment sequencing platform: {platform}.",
        )

    if organism:
        _append_unique(
            observed_evidence,
            f"Representative experiment organism: {organism}.",
        )


def _add_run_evidence(
    observed_evidence: list[str],
    not_established: list[str],
    metadata,
) -> None:
    """
    Propagate meaningful sequencing-run evidence into the
    reanalysis-readiness evidence model.

    Run availability is independent of biological replication.
    """

    run = getattr(
        metadata,
        "run",
        None,
    )

    if run is None:
        _append_unique(
            not_established,
            "Sequencing run availability could not be established.",
        )
        return

    accession = _clean(
        getattr(run, "accession", "")
    )

    total_spots = getattr(
        run,
        "total_spots",
        None,
    )

    total_bases = getattr(
        run,
        "total_bases",
        None,
    )

    public = getattr(
        run,
        "public",
        None,
    )

    if accession:

        _append_unique(
            observed_evidence,
            f"Sequencing run identified: {accession}.",
        )
        return

    if total_spots is not None:

        _append_unique(
            observed_evidence,
            (
                "Sequencing run information is available "
                f"with {total_spots} spots."
            ),
        )
        return

    if total_bases is not None:

        _append_unique(
            observed_evidence,
            (
                "Sequencing run information is available "
                f"with {total_bases} bases."
            ),
        )
        return

    if public is True:

        _append_unique(
            observed_evidence,
            "Sequencing run is identified as public.",
        )
        return

    _append_unique(
        not_established,
        "Sequencing run availability could not be established.",
    )


def _add_design_evidence(
    observed_evidence: list[str],
    not_established: list[str],
    missing_information: list[str],
    design_insight,
) -> None:
    if design_insight is None:
        _append_unique(
            missing_information,
            "Experimental design information was not available.",
        )
        return

    fields = (
        ("condition", "Experimental condition information"),
        ("control", "Control group information"),
        ("treatment", "Treatment information"),
        ("time_point", "Time-point information"),
        ("replicate_information", "Biological replicate information"),
    )

    for field_name, label in fields:
        value = _clean(
            getattr(design_insight, field_name, "")
        )

        if field_name == "replicate_information":

            replicate_lower = value.lower()

            if value and "could not be established" not in replicate_lower:

                _append_unique(
                    observed_evidence,
                    f"Replicate information is available: {value.rstrip('.')}.",
                )

                if (
                    "biological or technical replicate status "
                    "is not established"
                    in replicate_lower
                ):

                    _append_unique(
                        not_established,
                        "Biological versus technical replicate status "
                        "could not be established.",
                    )

            else:

                _append_unique(
                    not_established,
                    "Biological replicate structure could not be established.",
                )

        elif _is_established(value):

            _append_unique(
                observed_evidence,
                f"{label} is available: {value.rstrip('.')}.",
            )

        else:

            _append_unique(
                not_established,
                f"{label} could not be established.",
            )


def _add_suitability_evidence(
    observed_evidence: list[str],
    warnings: list[str],
    suitability_insight,
) -> None:
    if suitability_insight is None:
        return

    suitability = _clean(
        getattr(suitability_insight, "overall", "")
    )

    if suitability:
        _append_unique(
            observed_evidence,
            f"Dataset suitability assessment: {suitability}.",
        )

    for warning in getattr(
        suitability_insight,
        "warnings",
        [],
    ):
        _append_unique(
            warnings,
            f"Suitability warning: {warning}",
        )


def _is_rna_seq_compatible(modality_insight):
    """
    Resolve RNA-seq compatibility while remaining compatible with
    both the current ModalityInsight model and lightweight test
    doubles that expose only compatibility_status.
    """
    if modality_insight is None:
        return None

    explicit_value = getattr(
        modality_insight,
        "rna_seq_compatible",
        None,
    )

    if explicit_value is True:
        return True

    if explicit_value is False:
        return False

    compatibility_status = _clean(
        getattr(
            modality_insight,
            "compatibility_status",
            "",
        )
    ).lower()

    if compatibility_status == "compatible":
        return True

    if compatibility_status == "not compatible":
        return False

    return None


def _build_incompatible_result(
    observed_evidence,
    not_established,
    warnings,
):
    return ReanalysisReadinessInsight(
        verdict="Not suitable",
        observed_evidence=observed_evidence,
        inferred_evidence=[],
        not_established=not_established,
        missing_information=[],
        warnings=warnings,
        rationale=(
            "The available sequencing modality is not compatible with "
            "RNA-seq analysis. The dataset may be useful for another "
            "analysis workflow, but it should not be treated as an "
            "RNA-seq reanalysis dataset."
        ),
    )


def _build_uncertain_modality_result(
    observed_evidence,
    not_established,
    missing_information,
    warnings,
):
    return ReanalysisReadinessInsight(
        verdict="Insufficient evidence",
        observed_evidence=observed_evidence,
        inferred_evidence=[],
        not_established=not_established,
        missing_information=missing_information,
        warnings=warnings,
        rationale=(
            "The sequencing modality could not be established with "
            "sufficient confidence. RNA-seq reanalysis should not be "
            "assumed until the sequencing strategy is verified."
        ),
    )


def _build_study_result(
    observed_evidence,
    not_established,
    missing_information,
    warnings,
    design_insight,
    modality_insight,
):
    compatibility = _is_rna_seq_compatible(modality_insight)

    if compatibility is False:
        _append_unique(
            warnings,
            "The dataset is not compatible with RNA-seq analysis.",
        )

        return _build_incompatible_result(
            observed_evidence,
            not_established,
            warnings,
        )

    if compatibility is None:
        return _build_uncertain_modality_result(
            observed_evidence,
            not_established,
            missing_information,
            warnings,
        )

    has_multiple_assay_families = any(
        "multiple assay families" in warning.lower()
        for warning in warnings
    )

    condition = ""
    control = ""
    treatment = ""
    replicate = ""

    if design_insight is not None:
        condition = _clean(
            getattr(design_insight, "condition", "")
        )
        control = _clean(
            getattr(design_insight, "control", "")
        )
        treatment = _clean(
            getattr(design_insight, "treatment", "")
        )
        replicate = _clean(
            getattr(design_insight, "replicate_information", "")
        )

    design_complete = (
        _is_established(condition)
        and _is_established(control)
        and _is_established(replicate)
    )

    if has_multiple_assay_families:
        if design_complete:
            rationale = (
                "The study contains RNA-seq-compatible data but also "
                "contains multiple assay families. Individual RNA-seq "
                "subsets may be reusable when their experimental design "
                "and replicate structure are independently verified."
            )
        else:
            rationale = (
                "The study contains RNA-seq-compatible data but also "
                "contains multiple assay families. The complete study "
                "should not automatically be treated as one homogeneous "
                "RNA-seq reanalysis unit. Individual RNA-seq experiment "
                "subsets should be defined and their experimental design "
                "verified before formal reanalysis."
            )

        return ReanalysisReadinessInsight(
            verdict="Conditionally reusable",
            observed_evidence=observed_evidence,
            inferred_evidence=[],
            not_established=not_established,
            missing_information=missing_information,
            warnings=warnings,
            rationale=rationale,
        )

    if design_complete:
        return ReanalysisReadinessInsight(
            verdict="Ready for reanalysis",
            observed_evidence=observed_evidence,
            inferred_evidence=[],
            not_established=not_established,
            missing_information=missing_information,
            warnings=warnings,
            rationale=(
                "The available metadata establish RNA-seq compatibility "
                "and provide condition, control, and biological replicate "
                "information needed to define a defensible reanalysis."
            ),
        )

    if (
        _is_established(condition)
        or _is_established(control)
        or _is_established(treatment)
    ):
        rationale = (
            "The dataset is compatible with RNA-seq analysis and some "
            "experimental design information is available, but the "
            "available metadata do not establish the complete design "
            "required for formal reanalysis."
        )
    else:
        rationale = (
            "The dataset is compatible with RNA-seq analysis, but the "
            "available metadata do not establish enough experimental "
            "design information for formal reanalysis."
        )

    return ReanalysisReadinessInsight(
        verdict="Exploratory use only",
        observed_evidence=observed_evidence,
        inferred_evidence=[],
        not_established=not_established,
        missing_information=missing_information,
        warnings=warnings,
        rationale=rationale,
    )


def generate_reanalysis_readiness(
    metadata,
    modality_insight=None,
    design_insight=None,
    suitability_insight=None,
    experiment_at_glance=None,
    study_experimental_landscape=None,
):
    """
    Generate an evidence-based assessment of reanalysis readiness.

    Study accessions are assessed using the complete study-level
    experiment collection and experimental landscape.

    Individual experiment metadata are explicitly labeled as
    representative experiment evidence when study context exists.
    """

    observed_evidence = []
    inferred_evidence = []
    not_established = []
    missing_information = []
    warnings = []

    experiment_metadata = _get_experiment_metadata(metadata)
    sample_metadata = _get_sample_metadata(metadata)

    # Run availability is orthogonal to assay compatibility.
    # Record sequencing-run evidence before entering the
    # compatibility-specific readiness branches so that
    # incompatible, specialized, unknown, and compatible
    # datasets all retain documented run-level evidence.

    _add_run_evidence(
        observed_evidence,
        not_established,
        metadata,
    )

    compatibility = _is_rna_seq_compatible(modality_insight)

    if compatibility is False:
        _add_individual_experiment_evidence(
            observed_evidence,
            experiment_metadata,
            sample_metadata,
            modality_insight,
        )

        _add_study_evidence(
            observed_evidence,
            not_established,
            warnings,
            experiment_at_glance,
            study_experimental_landscape,
        )

        _add_design_evidence(
            observed_evidence,
            not_established,
            missing_information,
            design_insight,
        )

        _add_suitability_evidence(
            observed_evidence,
            warnings,
            suitability_insight,
        )

        _append_unique(
            warnings,
            "The dataset is not compatible with RNA-seq analysis.",
        )

        return _build_incompatible_result(
            observed_evidence,
            not_established,
            warnings,
        )

    if compatibility is None:
        _add_individual_experiment_evidence(
            observed_evidence,
            experiment_metadata,
            sample_metadata,
            modality_insight,
        )

        _add_study_evidence(
            observed_evidence,
            not_established,
            warnings,
            experiment_at_glance,
            study_experimental_landscape,
        )

        _add_design_evidence(
            observed_evidence,
            not_established,
            missing_information,
            design_insight,
        )

        _add_suitability_evidence(
            observed_evidence,
            warnings,
            suitability_insight,
        )

        _append_unique(
            not_established,
            "Sequencing modality could not be established.",
        )

        _append_unique(
            missing_information,
            "Sequencing modality must be verified before RNA-seq reanalysis.",
        )

        return _build_uncertain_modality_result(
            observed_evidence,
            not_established,
            missing_information,
            warnings,
        )

    is_study = _is_study_context_available(
        experiment_at_glance,
        study_experimental_landscape,
    )

    _add_study_evidence(
        observed_evidence,
        not_established,
        warnings,
        experiment_at_glance,
        study_experimental_landscape,
    )

    _add_individual_experiment_evidence(
        observed_evidence,
        experiment_metadata,
        sample_metadata,
        modality_insight,
    )

    _add_design_evidence(
        observed_evidence,
        not_established,
        missing_information,
        design_insight,
    )

    _add_suitability_evidence(
        observed_evidence,
        warnings,
        suitability_insight,
    )

    if is_study:
        return _build_study_result(
            observed_evidence,
            not_established,
            missing_information,
            warnings,
            design_insight,
            modality_insight,
        )

    return _build_study_result(
        observed_evidence,
        not_established,
        missing_information,
        warnings,
        design_insight,
        modality_insight,
    )
