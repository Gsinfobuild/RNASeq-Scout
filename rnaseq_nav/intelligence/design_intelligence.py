"""
Layer 2: Experimental Design Intelligence

This module interprets experimental-design information from publicly
available sequencing metadata.

Scientific policy
-----------------
The module distinguishes:

1. Observed metadata
2. Cautious inference
3. Information that is not established

The module must not invent:

- biological replicates
- control groups
- treatment groups
- time points
- statistical contrasts

An experimental context such as "detergent stress", "starvation", or
"hypoxia" is not automatically treated as a formal treatment assignment.

Treatment inference requires explicit treatment-related language or
an explicit relationship in the available experiment metadata.
"""

from dataclasses import dataclass, field
import re


# ==========================================================
# Data model
# ==========================================================

@dataclass
class ExperimentalDesignInsight:
    condition: str = ""
    control: str = ""
    treatment: str = ""
    time_point: str = ""
    replicate_information: str = ""
    design_description: str = ""
    design_confidence: str = "Insufficient information"
    observed_features: list[str] = field(default_factory=list)
    inferred_features: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)


# ==========================================================
# Utility functions
# ==========================================================

def _clean(value):
    """
    Normalize a metadata value to a clean string.
    """

    if value is None:
        return ""

    value = str(value).strip()

    if value.lower() in {
        "",
        "none",
        "null",
        "nan",
        "n/a",
        "na",
        "unknown",
        "not available",
        "not specified",
    }:
        return ""

    return value


def _get_experiment(metadata):
    """
    Retrieve experiment metadata from the normalized Metadata object.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "experiment",
        None,
    )


def _get_sample(metadata):
    """
    Retrieve sample metadata from the normalized Metadata object.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "sample",
        None,
    )


def _collect_observed_metadata(metadata):
    """
    Collect directly observed experiment/sample metadata.
    """

    observed = {}

    experiment = _get_experiment(metadata)
    sample = _get_sample(metadata)

    if experiment is not None:

        observed["title"] = _clean(
            getattr(
                experiment,
                "title",
                "",
            )
        )

        observed["library_strategy"] = _clean(
            getattr(
                experiment,
                "library_strategy",
                "",
            )
        )

        observed["layout"] = _clean(
            getattr(
                experiment,
                "layout",
                "",
            )
        )

        observed["platform"] = _clean(
            getattr(
                experiment,
                "platform",
                "",
            )
        )

        observed["library_source"] = _clean(
            getattr(
                experiment,
                "library_source",
                "",
            )
        )

        observed["library_selection"] = _clean(
            getattr(
                experiment,
                "library_selection",
                "",
            )
        )

        observed["instrument"] = _clean(
            getattr(
                experiment,
                "instrument",
                "",
            )
        )

    if sample is not None:

        observed["organism"] = _clean(
            getattr(
                sample,
                "organism",
                "",
            )
        )

        observed["biosample"] = _clean(
            getattr(
                sample,
                "biosample",
                "",
            )
        )

    return observed


# ==========================================================
# Condition / Experimental Context Detection
# ==========================================================

def _detect_condition(title):
    """
    Identify an experimental condition or context.

    Scientific policy
    -----------------
    Contextual terms such as:

        stress
        starvation
        hypoxia
        nutrient limitation
        iron stress
        detergent stress
        infection
        antibiotic exposure

    may establish an experimental context.

    They do NOT automatically establish a formal treatment assignment.

    The function attempts to return the relevant contextual phrase rather
    than the entire experiment title.
    """

    if not title:
        return ""

    title_lower = title.lower()

    # ------------------------------------------------------
    # Explicit contextual phrases
    # ------------------------------------------------------

    context_patterns = [
        r"\b([a-z0-9_-]+\s+stress)\b",
        r"\b(stress\s+(?:condition|response))\b",
        r"\b([a-z0-9_-]+\s+starvation)\b",
        r"\b(starvation)\b",
        r"\b(hypoxia)\b",
        r"\b([a-z0-9_-]+\s+hypoxia)\b",
        r"\b([a-z0-9_-]+\s+limitation)\b",
        r"\b(nutrient\s+(?:limitation|deprivation|restriction))\b",
        r"\b(iron\s+(?:stress|limitation|depletion|exposure))\b",
        r"\b(detergent\s+stress)\b",
        r"\b(antibiotic\s+(?:stress|exposure))\b",
        r"\b(infection)\b",
        r"\b(infected)\b",
    ]

    for pattern in context_patterns:

        match = re.search(
            pattern,
            title_lower,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    # ------------------------------------------------------
    # Explicit named experimental contexts
    # ------------------------------------------------------

    context_terms = [
        "stress",
        "starvation",
        "hypoxia",
        "nutrient",
        "iron",
        "infection",
        "infected",
    ]

    for term in context_terms:

        if term in title_lower:

            # Return a short phrase around the contextual term.
            words = title.split()

            for index, word in enumerate(words):

                if term in word.lower():

                    start = max(
                        0,
                        index - 1,
                    )

                    end = min(
                        len(words),
                        index + 2,
                    )

                    return " ".join(
                        words[start:end]
                    ).strip(
                        " ,;:-"
                    )

    return ""


# ==========================================================
# Control Detection
# ==========================================================

def _detect_control(title):
    """
    Detect explicit control terminology.

    A control is returned only when control-related language is explicitly
    present in the title.

    The existence of another condition does not imply a control group.
    """

    if not title:
        return ""

    title_lower = title.lower()

    control_patterns = [
        r"\bvehicle\s+control\b",
        r"\bmock[-\s]?control\b",
        r"\bmock[-\s]?treated\b",
        r"\buntreated\b",
        r"\bcontrol\s+cells?\b",
        r"\bcontrol\s+sample\b",
        r"\bcontrol\s+group\b",
        r"\bcontrol\b",
    ]

    for pattern in control_patterns:

        match = re.search(
            pattern,
            title_lower,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(0)

    return ""


# ==========================================================
# Treatment Detection
# ==========================================================

def _detect_treatment(title):
    """
    Detect an explicit treatment relationship.

    Scientific policy
    -----------------
    A treatment keyword alone is insufficient.

    For example:

        "detergent stress"

    establishes experimental context but does not necessarily establish
    that detergent was assigned as a formal treatment.

    Stronger evidence includes constructions such as:

        treated with isoniazid
        treatment with drug X
        exposed to antibiotic Y
        cells received drug X
        drug-treated cells

    Named agents such as isoniazid or kanamycin are therefore interpreted
    as treatment only when an explicit treatment relationship is present.
    """

    if not title:
        return ""

    # ------------------------------------------------------
    # Explicit treatment relationships
    # ------------------------------------------------------

    treatment_patterns = [

        # treated with X
        r"\btreated\s+with\s+([^,;:]+)",

        # treatment with X
        r"\btreatment\s+with\s+([^,;:]+)",

        # exposed to X
        r"\bexposed\s+to\s+([^,;:]+)",

        # exposure to X
        r"\bexposure\s+to\s+([^,;:]+)",

        # received X
        r"\breceived\s+([^,;:]+)",

        # X-treated cells/samples/etc.
        r"\b([a-z0-9_-]+(?:\s+[a-z0-9_-]+)?)"
        r"[-\s]treated\s+"
        r"(?:cells?|samples?|cultures?|organisms?|bacteria)\b",

        # drug treatment
        r"\bdrug\s+treatment\b",

        # antibiotic treatment
        r"\bantibiotic\s+treatment\b",

        # treatment group
        r"\btreatment\s+group\b",
    ]

    for pattern in treatment_patterns:

        match = re.search(
            pattern,
            title,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        # For phrases such as "treated with isoniazid", return the
        # treatment agent rather than the whole title.
        if match.lastindex:
            value = _clean(
                match.group(
                    match.lastindex
                )
            )

            if value:
                return value

        return match.group(0).strip()

    return ""


# ==========================================================
# Time Point Detection
# ==========================================================

def _detect_time_point(title):
    """
    Detect simple explicit time-point terminology.

    Examples potentially recognized:

        6h
        12h
        24h
        6 hours
        24 hours
        time point

    The function does not invent a time point.
    """

    if not title:
        return ""

    title_lower = title.lower()

    # ------------------------------------------------------
    # Compact forms such as 6h, 12h, 24h
    # ------------------------------------------------------

    match = re.search(
        r"\b(\d+(?:\.\d+)?\s*h)\b",
        title_lower,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    # ------------------------------------------------------
    # Explicit hour duration
    # ------------------------------------------------------

    match = re.search(
        r"\b(\d+(?:\.\d+)?\s+hours?)\b",
        title_lower,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    if "time point" in title_lower:
        return "Time point mentioned"

    return ""


# ==========================================================
# Replicate Assessment
# ==========================================================

def _assess_replicates(metadata):
    """
    Assess whether explicit replicate information is available.

    Scientific policy
    -----------------
    A single sequencing run must NOT be interpreted as a biological
    replicate.

    However, an explicit replicate annotation in the experiment title
    is observed metadata and should be preserved.

    The function distinguishes:

    - explicit biological replicate labels
    - explicit replicate labels whose biological/technical nature
      is not established
    - absence of explicit replicate information
    """

    experiment = _get_experiment(metadata)

    title = ""

    if experiment is not None:
        title = _clean(
            getattr(
                experiment,
                "title",
                "",
            )
        )

    if title:

        biological_match = re.search(
            r"\bbiological\s+replicate\s+([A-Za-z0-9_-]+)",
            title,
            flags=re.IGNORECASE,
        )

        if biological_match:

            label = biological_match.group(1)

            return (
                f"Biological replicate {label} is explicitly "
                "identified in the experiment title."
            )

        replicate_match = re.search(
            r"\breplicate\s+([A-Za-z0-9_-]+)",
            title,
            flags=re.IGNORECASE,
        )

        if replicate_match:

            label = replicate_match.group(1)

            return (
                f"Replicate {label} is explicitly identified "
                "in the experiment title; biological or technical "
                "replicate status is not established."
            )

    run = getattr(
        metadata,
        "run",
        None,
    )

    accession = ""

    if run is not None:
        accession = _clean(
            getattr(
                run,
                "accession",
                "",
            )
        )

    if accession:

        return (
            "One sequencing run is represented by the inspected "
            "accession; biological replicate status is not "
            "established by this information alone."
        )

    return (
        "Replicate structure could not be established "
        "from the available metadata."
    )


# ==========================================================
# Main Layer 2 Function
# ==========================================================

def generate_design_insight(metadata):
    """
    Generate an experimental design interpretation.

    Scientific policy
    -----------------
    The function distinguishes explicit observations from cautious
    inference.

    It does not claim:

    - biological replicates
    - experimental controls
    - treatment groups
    - statistical design formulas

    unless sufficient metadata supports those claims.

    Explicit metadata labels are recorded as observed evidence.
    """

    insight = ExperimentalDesignInsight()

    observed = _collect_observed_metadata(
        metadata
    )

    title = observed.get(
        "title",
        "",
    )

    # ------------------------------------------------------
    # Record observed metadata
    # ------------------------------------------------------

    if title:

        insight.observed_features.append(
            f"Experiment title: {title}"
        )

    if observed.get("library_strategy"):

        insight.observed_features.append(
            "Library strategy: "
            + observed["library_strategy"]
        )

    if observed.get("layout"):

        insight.observed_features.append(
            "Sequencing layout: "
            + observed["layout"]
        )

    if observed.get("platform"):

        insight.observed_features.append(
            "Sequencing platform: "
            + observed["platform"]
        )

    if observed.get("organism"):

        insight.observed_features.append(
            "Organism: "
            + observed["organism"]
        )

    # ------------------------------------------------------
    # Condition / experimental context
    # ------------------------------------------------------

    condition = _detect_condition(
        title
    )

    if condition:

        insight.condition = condition

        insight.inferred_features.append(
            "The experiment title suggests an experimental "
            "condition or context: "
            + condition
            + "."
        )

    # ------------------------------------------------------
    # Control
    # ------------------------------------------------------

    control = _detect_control(
        title
    )

    if control:

        insight.control = control

        insight.inferred_features.append(
            "Control terminology is explicitly present "
            "in the experiment title."
        )

    else:

        insight.warnings.append(
            "No explicit control group was identified "
            "from the available metadata."
        )

        insight.missing_information.append(
            "Control-group annotation"
        )

    # ------------------------------------------------------
    # Treatment
    # ------------------------------------------------------

    treatment = _detect_treatment(
        title
    )

    if treatment:

        insight.treatment = treatment

        insight.inferred_features.append(
            "An explicit treatment relationship is present "
            "in the experiment title."
        )

    else:

        insight.missing_information.append(
            "Treatment-group annotation, if applicable"
        )

    # ------------------------------------------------------
    # Time point
    # ------------------------------------------------------

    time_point = _detect_time_point(
        title
    )

    if time_point:

        insight.time_point = time_point

        insight.inferred_features.append(
            "Explicit time-related information is present "
            "in the experiment metadata."
        )

    else:

        insight.missing_information.append(
            "Time-point information, if applicable"
        )

    # ------------------------------------------------------
    # Replicates
    # ------------------------------------------------------

    insight.replicate_information = (
        _assess_replicates(
            metadata
        )
    )

    replicate_text = (
        insight.replicate_information.lower()
    )

    if (
        "biological replicate" in replicate_text
        and "explicitly identified" in replicate_text
    ):

        insight.observed_features.append(
            "Biological replicate information is explicitly "
            "documented in the experiment title."
        )

    elif (
        "replicate " in replicate_text
        and "explicitly identified" in replicate_text
    ):

        insight.observed_features.append(
            "Replicate information is explicitly documented "
            "in the experiment title."
        )

        insight.missing_information.append(
            "Biological versus technical replicate status"
        )

    else:

        insight.missing_information.append(
            "Biological replicate annotation"
        )

    # ------------------------------------------------------
    # Design description
    # ------------------------------------------------------

    design_features_present = any(
        [
            condition,
            control,
            treatment,
            time_point,
            "explicitly identified" in replicate_text,
        ]
    )

    if design_features_present:

        insight.design_description = (
            "The available metadata contains explicit or "
            "suggestive experimental design information, "
            "but the complete experimental group structure "
            "cannot be established from the inspected "
            "accession alone."
        )

    else:

        insight.design_description = (
            "The available metadata does not provide "
            "enough information to establish the "
            "experimental design."
        )

    # ------------------------------------------------------
    # Confidence
    # ------------------------------------------------------

    if (
        condition
        and control
        and treatment
        and time_point
    ):

        insight.design_confidence = (
            "Partially characterized"
        )

    elif (
        condition
        or control
        or treatment
        or time_point
        or "explicitly identified" in replicate_text
    ):

        insight.design_confidence = (
            "Partially characterized"
        )

    else:

        insight.design_confidence = (
            "Insufficient information"
        )

    # ------------------------------------------------------
    # Final warning
    # ------------------------------------------------------

    insight.warnings.append(
        "Experimental relationships are interpreted "
        "conservatively and should be confirmed using "
        "sample-level metadata before downstream "
        "statistical analysis."
    )

    return insight
