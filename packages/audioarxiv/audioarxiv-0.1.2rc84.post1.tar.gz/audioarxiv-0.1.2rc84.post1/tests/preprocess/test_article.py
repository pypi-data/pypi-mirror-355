from __future__ import annotations

from audioarxiv.preprocess import get_sentences


def test_get_sentences_basic():
    text = "This is the first sentence. This is the second one."
    sentences = get_sentences(text)
    assert sentences == ["This is the first sentence.", "This is the second one."]


def test_get_sentences_with_newlines():
    text = "This is the first sentence.\nThis is the second one."
    sentences = get_sentences(text)
    assert sentences == ["This is the first sentence.", "This is the second one."]


def test_get_sentences_single_sentence():
    text = "Just one sentence here!"
    sentences = get_sentences(text)
    assert sentences == ["Just one sentence here!"]


def test_get_sentences_empty_string():
    text = ""
    sentences = get_sentences(text)
    assert sentences == []


def test_get_sentences_with_abbreviations():
    text = "Dr. Smith went to Washington. He arrived at 10 a.m. on Tuesday."
    sentences = get_sentences(text)
    # Expecting 2 sentences, not breaking on "Dr." or "a.m."
    assert sentences == ["Dr. Smith went to Washington.", "He arrived at 10 a.m. on Tuesday."]


def test_get_sentences_unicode_and_emojis():
    text = "I love Python! 🐍 Do you? 🤔"
    sentences = get_sentences(text)
    assert sentences == ["I love Python!", "🐍 Do you?", "🤔"]


def test_get_sentences_multiple_spaces():
    text = "This is a sentence.     This is another."
    sentences = get_sentences(text)
    assert sentences == ["This is a sentence.", "This is another."]
