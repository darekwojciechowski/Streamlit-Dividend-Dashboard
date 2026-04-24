"""Parsing helpers shared across POMs."""

import re


def parse_currency(text: str) -> float:
    """Strip currency symbols and parse a numeric value from *text*.

    Handles values like ``"$5.25"``, ``"€10.00"``, ``"PLN 3.14"``,
    ``"$1,234.56"``. Returns ``0.0`` when no digits are present so the
    caller can decide how to treat empty cells (rather than raising).
    """
    numeric = re.sub(r"[^\d.]", "", text.strip())
    if not numeric or numeric == ".":
        return 0.0
    return float(numeric)
