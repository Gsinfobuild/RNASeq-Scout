"""
RNASeq Navigator

Dataset Intelligence Engine

Version 1.0

Purpose
-------
Translate metadata into a human-readable description
of the dataset.
"""

from dataclasses import dataclass, field


# ==========================================================
# Dataset Description
# ==========================================================

@dataclass
class DatasetDescription:
    """
    Human-readable interpretation of one dataset.
    """

    title: str = ""

    summary: str = ""

    organism: str = ""

    sequencing: str = ""

    experiment: str = ""

    strengths: list[str] = field(default_factory=list)

    limitations: list[str] = field(default_factory=list)


# ==========================================================
# Dataset Interpreter
# ==========================================================

class DatasetInterpreter:
    """
    Converts normalized metadata into an
    easy-to-understand explanation.
    """

    # -----------------------------------------------------

    def describe(self, metadata, modality_insight=None):

        description = DatasetDescription()

        # -------------------------------------------------
        # Organism
        # -------------------------------------------------

        description.organism = metadata.sample.organism

        # -------------------------------------------------
        # Experiment type
        # -------------------------------------------------

        strategy = metadata.experiment.library_strategy

        strategy_map = {

            "RNA_SEQ":
                "Bulk RNA sequencing",

            "MRNA_SEQ":
                "Messenger RNA sequencing",

            "NCRNA_SEQ":
                "Non-coding RNA sequencing",

            "MIRNA_SEQ":
                "MicroRNA sequencing",

            "SMRNA_SEQ":
                "Small RNA sequencing",

            "ATAC_SEQ":
                "Chromatin accessibility sequencing",

            "CHIP_SEQ":
                "Protein-DNA interaction sequencing",

            "RAD_SEQ":
                "Restriction-site associated DNA sequencing",

            "WGS":
                "Whole genome sequencing",

            "WXS":
                "Whole exome sequencing",

        }

        description.experiment = strategy_map.get(

            strategy,

            strategy,

        )

        # -------------------------------------------------
        # Layout explanation
        # -------------------------------------------------

        if metadata.experiment.layout == "PAIRED":

            layout_text = (
                "paired-end sequencing, where both "
                "ends of each fragment were sequenced."
            )

            # Paired-end layout alone does not establish an
            # RNA-seq expression experiment. RNA-seq-specific
            # benefits must therefore only be reported when
            # modality intelligence explicitly identifies
            # conventional RNA-seq.

            rna_seq_compatible = None

            if modality_insight is not None:
                rna_seq_compatible = getattr(
                    modality_insight,
                    "rna_seq_compatible",
                    None,
                )

            if rna_seq_compatible is True:

                description.strengths.append(
                    "Improved alignment accuracy"
                )

                description.strengths.append(
                    "Better transcript quantification"
                )

        elif metadata.experiment.layout == "SINGLE":

            layout_text = (
                "single-end sequencing, where one "
                "end of each fragment was sequenced."
            )

            description.limitations.append(

                "Lower alignment information than paired-end data"

            )

        else:

            layout_text = (
                "sequencing layout could not be established "
                "from the available metadata."
            )

        # -------------------------------------------------
        # Platform
        # -------------------------------------------------

        platform_map = {

            "ILLUMINA":
                "Illumina",

            "ION_TORRENT":
                "Ion Torrent",

            "PACBIO_SMRT":
                "PacBio SMRT",

            "OXFORD_NANOPORE":
                "Oxford Nanopore",

            "BGISEQ":
                "BGI sequencing platform",

        }

        platform = platform_map.get(

            metadata.experiment.platform,

            metadata.experiment.platform,

        )

        platform_text = platform.strip() if platform else ""

        if metadata.experiment.layout in {"PAIRED", "SINGLE"}:

            if platform_text:

                description.sequencing = (
                    f"The dataset was generated using "
                    f"{layout_text} "
                    f"The sequencing platform was "
                    f"{platform_text}."
                )

            else:

                description.sequencing = (
                    f"The dataset was generated using "
                    f"{layout_text} "
                    f"The sequencing platform could not be "
                    f"established from the available metadata."
                )

        else:

            if platform_text:

                description.sequencing = (
                    "Sequencing layout could not be established "
                    "from the available metadata. "
                    f"The sequencing platform was {platform_text}."
                )

            else:

                description.sequencing = (
                    "Sequencing layout and platform could not "
                    "be established from the available metadata."
                )

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        experiment_title = (
            metadata.experiment.title.strip()
            if metadata.experiment.title
            else ""
        )

        experiment_text = description.experiment.strip()

        if experiment_text:

            description.title = (
                f"{experiment_text} dataset"
            )

        elif experiment_title:

            description.title = experiment_title

        else:

            description.title = "Dataset with incomplete metadata"

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        if metadata.experiment.layout == "PAIRED":

            layout_summary = "paired-end reads"

        elif metadata.experiment.layout == "SINGLE":

            layout_summary = "single-end reads"

        else:

            layout_summary = (
                "reads with an unestablished sequencing layout"
            )

        experiment_text = description.experiment.strip()
        organism_text = description.organism.strip()
        platform_text = platform.strip() if platform else ""

        summary_parts = []

        if experiment_text and organism_text:
            summary_parts.append(
                f"This dataset contains "
                f"{experiment_text.lower()} data generated from "
                f"{organism_text}."
            )

        elif experiment_text:
            summary_parts.append(
                f"This dataset contains "
                f"{experiment_text.lower()} data."
            )

        elif organism_text:
            summary_parts.append(
                f"This dataset contains data generated from "
                f"{organism_text}."
            )

        else:
            summary_parts.append(
                "The available metadata does not establish "
                "the experiment type or organism."
            )

        if platform_text:
            summary_parts.append(
                f"The sequencing experiment generated "
                f"{layout_summary} on the "
                f"{platform_text} platform."
            )

        else:
            summary_parts.append(
                f"The sequencing experiment generated "
                f"{layout_summary}; the sequencing platform "
                f"could not be established from the available metadata."
            )

        description.summary = " ".join(summary_parts)

        # -------------------------------------------------
        # Generic strengths
        # -------------------------------------------------

        if (
            metadata.run.total_spots is not None
            and metadata.run.total_spots > 10000000
        ):

            description.strengths.append(

                "High sequencing depth"

            )

        if metadata.run.public:

            description.strengths.append(

                "Publicly available dataset"

            )

        return description
