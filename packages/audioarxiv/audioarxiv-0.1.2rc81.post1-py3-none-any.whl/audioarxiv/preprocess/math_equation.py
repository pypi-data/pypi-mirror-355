"""
Functions to preprocess math equations.
"""
from __future__ import annotations

import re

from sympy import srepr
from sympy.parsing.sympy_parser import parse_expr


def process_math_equations(text: str) -> str:
    """Detects LaTeX-style math symbols and converts them to a readable format.

    Args:
        text (str): Text.

    Returns:
        str: Text with the processed math equations.
    """

    def replace_math(match: re.Match) -> str:
        raw_expr = match.group(1)
        try:
            parsed = parse_expr(raw_expr)
            return f"Math: {srepr(parsed)}"
        except Exception:
            return f"Equation: {raw_expr}"

    # First replace block math ($$...$$)
    text = re.sub(r"\$\$(.+?)\$\$", replace_math, text)

    # Then replace inline math, match $...$ only if it's surrounded by non-digit characters (to avoid $5)
    text = re.sub(r"(?<!\w)\$(.+?)\$(?!\w)", replace_math, text)

    return text
