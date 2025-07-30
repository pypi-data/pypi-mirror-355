"""
Functions to preprocess articles.
"""
from __future__ import annotations

import nltk
from nltk.tokenize import sent_tokenize

# Download tokenizer if needed
nltk.download('punkt_tab')


def get_sentences(text: str) -> list:
    """Get the sentences from the text.

    Args:
        text (str): Text.

    Returns:
        list: A list of sentences.
    """
    return sent_tokenize(text)
