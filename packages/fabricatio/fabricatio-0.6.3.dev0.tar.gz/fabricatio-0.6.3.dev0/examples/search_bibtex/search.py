"""Example of using BibManager."""

from fabricatio import logger
from fabricatio_typst.rust import BibManager

b = BibManager("Exported Items.bib")
logger.success(
    b.get_cite_key_by_title(
        "A Negative Selection Immune System Inspired Methodology for Fault Diagnosis of Wind Turbines"
    )
)
logger.success(b.get_cite_key_fuzzy("System Inspired Methodology for Fault"))
