"""
RNASeq Scout

Layer 2: Experimental Design Intelligence
==========================================

This module interprets experimental-design information from publicly
available sequencing metadata.

Evidence sources
----------------
1. Experiment title
2. Library construction protocol
3. Run metadata, only for identifying the presence of a sequencing run

Scientific policy
-----------------
The module distinguishes:

1. Observed information
   Explicitly documented in available metadata.

2. Inferred information
   Reasonably suggested by metadata but not explicitly established.

3. Not-established information
   Relevant information was examined but cannot be established.

4. Missing information
   The relevant field is not represented in the available metadata.

The module must not invent:

- biological replicates
- control groups
- treatment assignments
- time points
- statistical contrasts
- DESeq2 design formulas

A sequencing run is never treated as a biological replicate.

A contextual word such as "stress", "infection", "iron", or "detergent"
does not by itself establish a treatment assignment.

Protocol statements are treated as observed evidence only when the
language explicitly supports the interpretation.
"""

from dataclasses import dataclass, field
import re


# ==========================================================
# Data model
# ==========================================================

@dataclass
class ExperimentalDesignInsight:
    """
    Structured interpretation of experimental design metadata.
    """

    condition: str = ""

    control: str = ""

    treatment: str = ""

    time_point: str = ""

    replicate_information: str = ""

    design_description: str = ""

    design_confidence: str = "Insufficient information"

    observed_features: list[str] = field(
        default_factory=list
    )

    inferred_features: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    missing_information: list[str] = field(
        default_factory=list
    )


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


def _append_unique(items, value):
    """
    Append a value only once.
    """

    value = _clean(value)

    if value and value not in items:
        items.append(value)


def _get_experiment(metadata):
    """
    Retrieve experiment metadata safely.
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
    Retrieve sample metadata safely.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "sample",
        None,
    )


def _get_run(metadata):
    """
    Retrieve run metadata safely.
    """

    if metadata is None:
        return None

    return getattr(
        metadata,
        "run",
        None,
    )


def _collect_observed_metadata(metadata):
    """
    Collect directly observed experiment/sample metadata.

    Construction protocol is preserved as a separate evidence source.
    """

    observed = {}

    experiment = _get_experiment(metadata)
    sample = _get_sample(metadata)

    if experiment is not None:

        fields = [
            "title",
            "library_strategy",
            "layout",
            "platform",
            "library_source",
            "library_selection",
            "instrument",
            "construction_protocol",
        ]

        for field_name in fields:

            observed[field_name] = _clean(
                getattr(
                    experiment,
                    field_name,
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
# Evidence helpers
# ==========================================================

def _protocol(metadata):
    """
    Return the deposited library construction protocol, if available.
    """

    experiment = _get_experiment(metadata)

    if experiment is None:
        return ""

    return _clean(
        getattr(
            experiment,
            "construction_protocol",
            "",
        )
    )


def _evidence_source_label(source):
    """
    Human-readable evidence source.
    """

    if source == "protocol":
        return "library construction protocol"

    if source == "title":
        return "experiment title"

    return "available metadata"


# ==========================================================
# Condition / Experimental Context
# ==========================================================

def _detect_condition(title, protocol=""):
    """
    Identify an experimental condition or biological context.

    Context does not automatically establish a treatment assignment.

    Returns a concise phrase rather than an entire title/protocol.
    """

    # ------------------------------------------------------
    # Title-level contextual phrases
    # ------------------------------------------------------

    if title:

        # "infected with ... pathogens" establishes a concise
        # pathogen-infection context. Do not use the pathogen
        # descriptor itself as the condition value.
        if re.search(
            r"\binfected\s+with\b.*\bpathogen(?:s)?\b",
            title,
            flags=re.IGNORECASE,
        ):
            return "pathogen infection"

        title_patterns = [
            r"\b([A-Za-z0-9_-]+\s+stress)\b",
            r"\b(stress\s+(?:condition|response))\b",
            r"\b([A-Za-z0-9_-]+\s+starvation)\b",
            r"\b(starvation)\b",
            r"\b(hypoxia)\b",
            r"\b([A-Za-z0-9_-]+\s+hypoxia)\b",
            r"\b([A-Za-z0-9_-]+\s+limitation)\b",
            r"\b(nutrient\s+(?:limitation|deprivation|restriction))\b",
            r"\b(iron\s+(?:stress|limitation|depletion|exposure))\b",
            r"\b(detergent\s+stress)\b",
            r"\b(antibiotic\s+(?:stress|exposure))\b",

            # Prefer explicit infection context over the generic
            # adjective "infected".
            r"\binfected\s+with\s+(?:a\s+)?"
            r"(?:combination\s+of\s+)?"
            r"([A-Za-z0-9_.,\-+\s]+?)(?:\s*$)",

            r"\b(infection)\b",
        ]

        for pattern in title_patterns:

            match = re.search(
                pattern,
                title,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

    # ------------------------------------------------------
    # Protocol-level explicit contexts
    # ------------------------------------------------------

    if protocol:

        # Explicit pathogen/infection context.
        if re.search(
            r"\b(?:pathogen|pathogens)\b.*\b(?:infect|infection)\b|"
            r"\b(?:infect|infection)\b.*\b(?:pathogen|pathogens)\b",
            protocol,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            return "pathogen infection"

        protocol_patterns = [
            r"\bfirst\s+stressor\b",
            r"\bsecond\s+stressor\b",
            r"\bnematode\s+treatment\b",
            r"\bpathogen\s+(?:infection|treatment)\b",
            r"\bmock\s+treatment\b",
            r"\bexperimental\s+treatment\b",
        ]

        for pattern in protocol_patterns:

            match = re.search(
                pattern,
                protocol,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0).strip()

    return ""


# ==========================================================
# Control Detection
# ==========================================================

def _detect_control(title, protocol=""):
    """
    Detect explicitly documented control information.

    The existence of a treatment/stressor does not imply a control.

    Control information is returned only when explicit control or mock
    language is present.
    """

    texts = []

    if title:
        texts.append(("title", title))

    if protocol:
        texts.append(("protocol", protocol))

    patterns = [
        # Mock treatment / mock control
        (
            r"\bmock\s+(?:treatment|control|treated|treatment\s+group)\b",
            "mock treatment",
        ),
        (
            r"\bmock[-\s]?treated\b",
            "mock-treated",
        ),
        (
            r"\bvehicle\s+control\b",
            "vehicle control",
        ),
        (
            r"\buntreated\s+(?:control|samples?|cells?|plants?|groups?)\b",
            "untreated control",
        ),
        (
            r"\bcontrol\s+(?:group|sample|cells?|plants?|condition)\b",
            "control",
        ),
    ]

    for source, text in texts:

        for pattern, label in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                if source == "protocol":

                    return label

                return match.group(0).strip()

    return ""


# ==========================================================
# Treatment Detection
# ==========================================================

def _extract_treatment_agent(value):
    """
    Clean an explicitly captured treatment phrase.
    """

    value = _clean(value)

    if not value:
        return ""

    value = re.sub(
        r"\s+for\s+(?:\d+(?:\.\d+)?\s*)?(?:h|hours?|days?)\b.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s+at\s+day\s+\d+.*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # "stressor" describes the role of the intervention; it is
    # not part of the treatment agent itself.
    value = re.sub(
        r"^stressor\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value.strip(" ,.;:-")


def _detect_treatment(title, protocol=""):
    """
    Detect an explicit treatment relationship.

    A treatment keyword alone is insufficient.

    The function recognizes treatment only when language establishes
    that experimental material received, was exposed to, was treated
    with, was inoculated with, or otherwise underwent an intervention.

    Protocol evidence has priority over title evidence.
    """

    texts = []

    if protocol:
        texts.append(("protocol", protocol))

    if title:
        texts.append(("title", title))

    patterns = [
        # treated with X
        r"\btreated\s+with\s+([^,.;:\n]+)",

        # treatment with X
        r"\btreatment\s+with\s+([^,.;:\n]+)",

        # exposed to X
        r"\bexposed\s+to\s+([^,.;:\n]+)",

        # exposure to X
        r"\bexposure\s+to\s+([^,.;:\n]+)",

        # received X
        r"\breceived\s+([^,.;:\n]+)",

        # X treatment was performed
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"\s+treatment\s+was\s+(?:performed|applied|administered)\b",

        # treatment was performed with X
        r"\btreatment\s+was\s+(?:performed|applied|administered)"
        r"\s+(?:with|using)\s+([^,.;:\n]+)",

        # X treatment was given
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"\s+treatment\s+was\s+given\b",

        # inoculated with X
        r"\binoculated\s+with\s+([^,.;:\n]+)",

        # inoculation with X
        r"\binoculation\s+with\s+([^,.;:\n]+)",

        # X-treated cells/samples/plants/etc.
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"[-\s]treated\s+"
        r"(?:cells?|samples?|cultures?|organisms?|plants?|seedlings?)\b",

        # X-inoculated
        r"\b([A-Za-z0-9_/-]+(?:\s+[A-Za-z0-9_/-]+)?)"
        r"[-\s]inoculated\s+"
        r"(?:cells?|samples?|cultures?|organisms?|plants?|seedlings?)\b",

        # X-inoculated as an experiment label
        r"\b([A-Za-z0-9_/-]+)-inoculated\b",
    ]

    for source, text in texts:

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            if match.lastindex:

                value = _extract_treatment_agent(
                    match.group(match.lastindex)
                )

                if value:

                    # Explicit inoculation relationship
                    if re.search(
                        r"inoculat",
                        match.group(0),
                        flags=re.IGNORECASE,
                    ):
                        return value + " inoculation"

                    return value

            matched = match.group(0).strip()

            if matched:
                return matched

    return ""


# ==========================================================
# Time Point Detection
# ==========================================================

def _detect_time_point(title, protocol=""):
    """
    Detect explicitly documented sampling time information.

    Unlike title-only detection, protocol evidence can establish
    day-based sampling schedules.

    Examples:

        6h
        24 hours
        day 3
        days 1, 2, 3
        post 1, 2, 3, 4, 5 day
        time point
    """

    texts = []

    if protocol:
        texts.append(("protocol", protocol))

    if title:
        texts.append(("title", title))

    # ------------------------------------------------------
    # Protocol: sampling after X days
    # ------------------------------------------------------

    for source, text in texts:

        match = re.search(
            r"\bpost\s+"
            r"((?:\d+(?:\s*,\s*|\s+and\s+|\s*-\s*)?)+)"
            r"\s*day(?:s)?\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:

            values = _clean(
                match.group(1)
            )

            if values:
                return "Post-treatment days " + values

        match = re.search(
            r"\bsampling\s+(?:at|on)\s+"
            r"((?:day|days)\s+[^.;\n]+)",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return _clean(match.group(1))

        match = re.search(
            r"\b(?:at|on)\s+day\s+(\d+(?:\s*[-,]\s*\d+)*)\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return "Day " + _clean(match.group(1))

        # --------------------------------------------------
        # Hour-based time points
        # --------------------------------------------------

        match = re.search(
            r"\b(\d+(?:\.\d+)?\s*h)\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        match = re.search(
            r"\b(\d+(?:\.\d+)?\s+hours?)\b",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        if re.search(
            r"\btime\s+point\b",
            text,
            flags=re.IGNORECASE,
        ):
            return "Time point mentioned"

    return ""


# ==========================================================
# Replicate Assessment
# ==========================================================

def _assess_replicates(metadata):
    """
    Assess explicit replicate information.

    Priority:

    1. Construction protocol
    2. Experiment title
    3. Run metadata

    A sequencing run is never interpreted as a biological replicate.
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

    protocol = _protocol(metadata)

    # ------------------------------------------------------
    # Protocol: explicit biological replicates
    # ------------------------------------------------------

    if protocol:

        patterns = [
            r"\b(\d+)\s+biological\s+replicates?\b",
            r"\bthree\s+biological\s+replicates?\b",
            r"\btwo\s+biological\s+replicates?\b",
            r"\bfour\s+biological\s+replicates?\b",
            r"\bfive\s+biological\s+replicates?\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                protocol,
                flags=re.IGNORECASE,
            )

            if match:

                phrase = match.group(0).strip()

                # Normalize common textual number variants.
                number_map = {
                    "two": "2",
                    "three": "3",
                    "four": "4",
                    "five": "5",
                }

                for word, number in number_map.items():

                    phrase = re.sub(
                        rf"\b{word}\b",
                        number,
                        phrase,
                        flags=re.IGNORECASE,
                    )

                return (
                    phrase.capitalize()
                    + " are explicitly documented in the "
                    "library construction protocol."
                )

        # Biological replicate + individual biological material
        if re.search(
            r"\bbiological\s+replicate\b",
            protocol,
            flags=re.IGNORECASE,
        ):
            return (
                "Biological replicate information is explicitly "
                "documented in the library construction protocol."
            )

    # ------------------------------------------------------
    # Title: explicit biological replicate
    # ------------------------------------------------------

    if title:

        match = re.search(
            r"\bbiological\s+replicate\s+([A-Za-z0-9_-]+)",
            title,
            flags=re.IGNORECASE,
        )

        if match:

            return (
                f"Biological replicate {match.group(1)} is explicitly "
                "identified in the experiment title."
            )

        match = re.search(
            r"\breplicate\s+([A-Za-z0-9_-]+)",
            title,
            flags=re.IGNORECASE,
        )

        if match:

            return (
                f"Replicate {match.group(1)} is explicitly identified "
                "in the experiment title; biological or technical "
                "replicate status is not established."
            )

    # ------------------------------------------------------
    # Run: never infer biological replication
    # ------------------------------------------------------

    run = _get_run(metadata)

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
# Design complexity assessment
# ==========================================================

def _has_complex_design(metadata):
    """
    Identify protocol language indicating a multifactorial or
    sequential experimental design.

    This does not determine the experimental groups. It only prevents
    Scout from assigning the strongest confidence level when the
    available evidence indicates that the design is more complex than
    a simple single-factor treatment/control experiment.
    """

    protocol = _protocol(metadata)

    if not protocol:
        return False

    complexity_patterns = [
        r"\bfirst\s+stressor\b",
        r"\bsecond\s+stressor\b",
        r"\bmultiple\s+(?:stressors?|treatments?|pathogens?)\b",
        r"\bcombination\s+of\s+[^.\n]*pathogens?\b",
        r"\b(?:above|below)[-\s]ground\s+pathogens?\b",
        r"\bmock\s+treatment\b",
    ]

    for pattern in complexity_patterns:

        if re.search(
            pattern,
            protocol,
            flags=re.IGNORECASE,
        ):
            return True

    return False


# ==========================================================
# Design description
# ==========================================================

def _build_design_description(
    condition,
    control,
    treatment,
    time_point,
    replicate_information,
):
    """
    Build a conservative natural-language description.
    """

    established = []

    if condition:
        established.append("experimental context")

    if control:
        established.append("control information")

    if treatment:
        established.append("treatment information")

    if time_point:
        established.append("time-point information")

    if (
        replicate_information
        and "could not be established"
        not in replicate_information.lower()
        and "not established"
        not in replicate_information.lower()
    ):
        established.append("replicate information")

    if (
        condition
        and control
        and treatment
        and replicate_information
        and "could not be established"
        not in replicate_information.lower()
        and "not established"
        not in replicate_information.lower()
    ):
        return (
            "The available metadata explicitly document key elements "
            "of the experimental design, including experimental "
            "context, treatment/control information, and replicate "
            "structure."
        )

    if established:

        return (
            "The available metadata contain explicit experimental "
            "design information, but the complete experimental group "
            "structure cannot be established from the inspected "
            "accession alone."
        )

    return (
        "The available metadata do not provide enough information "
        "to establish the experimental design."
    )


# ==========================================================
# Main Layer 2 Function
# ==========================================================

def generate_design_insight(metadata):
    """
    Generate an evidence-based experimental design interpretation.

    Construction protocol information is treated as observed evidence
    when it explicitly documents a design feature.
    """

    insight = ExperimentalDesignInsight()

    observed = _collect_observed_metadata(
        metadata
    )

    title = observed.get(
        "title",
        "",
    )

    protocol = observed.get(
        "construction_protocol",
        "",
    )

    # ------------------------------------------------------
    # Record basic observed metadata
    # ------------------------------------------------------

    if title:

        _append_unique(
            insight.observed_features,
            f"Experiment title: {title}",
        )

    if observed.get("library_strategy"):

        _append_unique(
            insight.observed_features,
            "Library strategy: "
            + observed["library_strategy"],
        )

    if observed.get("layout"):

        _append_unique(
            insight.observed_features,
            "Sequencing layout: "
            + observed["layout"],
        )

    if observed.get("platform"):

        _append_unique(
            insight.observed_features,
            "Sequencing platform: "
            + observed["platform"],
        )

    if observed.get("organism"):

        _append_unique(
            insight.observed_features,
            "Organism: "
            + observed["organism"],
        )

    if protocol:

        _append_unique(
            insight.observed_features,
            "Library construction protocol is available as an "
            "experimental-design evidence source.",
        )

    # ------------------------------------------------------
    # Condition
    # ------------------------------------------------------

    condition = _detect_condition(
        title,
        protocol,
    )

    if condition:

        insight.condition = condition

        # If the protocol independently supports the biological
        # context, record the resulting interpretation as observed
        # evidence rather than treating it as title-only inference.
        protocol_support = False

        if protocol:

            if condition.lower() == "pathogen infection":

                protocol_support = bool(
                    re.search(
                        r"\b(?:pathogen|pathogens)\b|"
                        r"\binfect(?:ed|ion|ious)?\b|"
                        r"\bstressor\b",
                        protocol,
                        flags=re.IGNORECASE,
                    )
                )

            else:

                protocol_support = bool(
                    re.search(
                        re.escape(condition),
                        protocol,
                        flags=re.IGNORECASE,
                    )
                )

        if protocol_support:

            _append_unique(
                insight.observed_features,
                "Experimental context explicitly supported by "
                "the library construction protocol: "
                + condition,
            )

        else:

            _append_unique(
                insight.inferred_features,
                "The experiment title suggests an experimental "
                "condition or context: "
                + condition
                + ".",
            )

    # ------------------------------------------------------
    # Control
    # ------------------------------------------------------

    control = _detect_control(
        title,
        protocol,
    )

    if control:

        insight.control = control

        if protocol and re.search(
            r"\bmock\s+(?:treatment|control)\b|"
            r"\bvehicle\s+control\b|"
            r"\buntreated\s+(?:control|samples?|cells?|plants?)\b",
            protocol,
            flags=re.IGNORECASE,
        ):
            _append_unique(
                insight.observed_features,
                "Control information explicitly documented in the "
                "library construction protocol: "
                + control,
            )

        else:

            _append_unique(
                insight.observed_features,
                "Control terminology explicitly present in the "
                "experiment title: "
                + control,
            )

    else:

        _append_unique(
            insight.warnings,
            "No explicit control group was identified from the "
            "available metadata.",
        )

        _append_unique(
            insight.missing_information,
            "Control-group annotation",
        )

    # ------------------------------------------------------
    # Treatment
    # ------------------------------------------------------

    treatment = _detect_treatment(
        title,
        protocol,
    )

    if treatment:

        insight.treatment = treatment

        if protocol:

            _append_unique(
                insight.observed_features,
                "Treatment/intervention relationship explicitly "
                "documented in the library construction protocol: "
                + treatment,
            )

        else:

            _append_unique(
                insight.observed_features,
                "Treatment relationship explicitly present in the "
                "experiment title: "
                + treatment,
            )

    else:

        _append_unique(
            insight.warnings,
            "No unambiguous treatment assignment was identified "
            "from the available metadata.",
        )

        _append_unique(
            insight.missing_information,
            "Treatment-group annotation, if applicable",
        )

    # ------------------------------------------------------
    # Time point
    # ------------------------------------------------------

    time_point = _detect_time_point(
        title,
        protocol,
    )

    if time_point:

        insight.time_point = time_point

        if protocol:

            _append_unique(
                insight.observed_features,
                "Sampling time information explicitly documented "
                "in the library construction protocol: "
                + time_point,
            )

        else:

            _append_unique(
                insight.observed_features,
                "Time-point information explicitly present in the "
                "experiment title: "
                + time_point,
            )

    else:

        _append_unique(
            insight.missing_information,
            "Time-point information, if applicable",
        )

    # ------------------------------------------------------
    # Replicates
    # ------------------------------------------------------

    insight.replicate_information = _assess_replicates(
        metadata
    )

    if (
        "could not be established"
        not in insight.replicate_information.lower()
        and "not established"
        not in insight.replicate_information.lower()
    ):

        if protocol and (
            "protocol"
            in insight.replicate_information.lower()
        ):

            _append_unique(
                insight.observed_features,
                "Biological replicate information explicitly "
                "documented in the library construction protocol.",
            )

        else:

            _append_unique(
                insight.observed_features,
                "Replicate information explicitly documented in "
                "available metadata.",
            )

    else:

        _append_unique(
            insight.missing_information,
            "Biological replicate annotation",
        )

    # ------------------------------------------------------
    # Conservative warning
    # ------------------------------------------------------

    if _has_complex_design(metadata):

        _append_unique(
            insight.warnings,
            "The available protocol indicates a multifactorial or "
            "sequential experimental design; complete sample-level "
            "group assignments are not established by this accession "
            "alone.",
        )

    if (
        condition
        or control
        or treatment
        or time_point
    ):

        _append_unique(
            insight.warnings,
            "Experimental relationships are interpreted from "
            "explicitly documented metadata; sample-level group "
            "assignments should be confirmed before downstream "
            "statistical analysis.",
        )

    # ------------------------------------------------------
    # Design confidence
    # ------------------------------------------------------

    established_count = 0

    if condition:
        established_count += 1

    if control:
        established_count += 1

    if treatment:
        established_count += 1

    if time_point:
        established_count += 1

    if (
        insight.replicate_information
        and "could not be established"
        not in insight.replicate_information.lower()
        and "not established"
        not in insight.replicate_information.lower()
    ):
        established_count += 1

    if protocol:

        # Rich protocol evidence is not equivalent to a completely
        # resolved sample-level experimental design. In particular,
        # unresolved treatment/control relationships should prevent
        # the strongest confidence label.

        complete_group_structure = (
            bool(treatment)
            and bool(control)
            and (
                insight.replicate_information
                and "could not be established"
                not in insight.replicate_information.lower()
                and "not established"
                not in insight.replicate_information.lower()
            )
        )

        complex_design = _has_complex_design(metadata)

        # A multifactorial/sequential protocol can contain strong
        # evidence while still lacking sample-level group mapping.
        # Do not call such a design "Well characterized" merely
        # because several metadata fields were detected.
        if (
            established_count >= 4
            and complete_group_structure
            and not complex_design
        ):

            insight.design_confidence = (
                "Well characterized"
            )

        elif established_count >= 2:

            insight.design_confidence = (
                "Substantially characterized"
            )

        elif established_count >= 1:

            insight.design_confidence = (
                "Partially characterized"
            )

        else:

            insight.design_confidence = (
                "Insufficient information"
            )

    else:

        if established_count >= 3:

            insight.design_confidence = (
                "Substantially characterized"
            )

        elif established_count >= 1:

            insight.design_confidence = (
                "Partially characterized"
            )

        else:

            insight.design_confidence = (
                "Insufficient information"
            )

    # ------------------------------------------------------
    # Description
    # ------------------------------------------------------

    insight.design_description = _build_design_description(
        condition,
        control,
        treatment,
        time_point,
        insight.replicate_information,
    )

    return insight
