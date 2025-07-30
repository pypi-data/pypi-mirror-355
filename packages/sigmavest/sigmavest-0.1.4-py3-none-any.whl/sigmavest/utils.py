from pathlib import Path
import re


def split_at_capitals(input_str):
    """
    Splits a string into words at capital letters.

    Args:
        input_str (str): Input string to split (e.g., "StockholdersEquity")

    Returns:
        str: String with spaces inserted before capital letters (e.g., "Stockholders Equity")

    Example:
        >>> split_at_capitals("StockholdersEquity")
        "Stockholders Equity"

        >>> split_at_capitals("stockholdersEquity")
        "stockholders Equity"

        >>> split_at_capitals("EBIT")
        "EBIT"  # No split for acronyms

        >>> split_at_capitals("ReturnOnCapital")
        "Return On Capital"
    """
    return re.sub(r"(?<!^)(?=[A-Z])", " ", input_str)
