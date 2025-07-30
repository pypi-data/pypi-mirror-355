"""
Processes and cleans the extracted text from papers,
including sentence segmentation, symbol handling, and formatting for better audio output.
"""
from __future__ import annotations

from .article import get_sentences
from .math_equation import process_math_equations

__all__ = [
    'get_sentences',
    'process_math_equations',
]
