from __future__ import annotations

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from audioarxiv.resources.paper import (  # Replace with actual module name
    Paper, validate_paper_arguments)


@pytest.fixture
def mock_paper_object():
    mock_paper = MagicMock()
    mock_paper.title = "Test Title"
    mock_paper.summary = "This is a test abstract."

    author1 = MagicMock()
    author1.name = "Alice"
    author2 = MagicMock()
    author2.name = "Bob"
    mock_paper.authors = [author1, author2]

    mock_paper.published = datetime(2022, 1, 1)
    mock_paper.updated = datetime(2022, 1, 2)
    return mock_paper


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_paper_init_and_client(mock_client_class):
    paper = Paper(page_size=200, delay_seconds=5.0, num_retries=2)
    client_instance = mock_client_class.return_value

    assert paper.client == client_instance
    mock_client_class.assert_called_with(page_size=200, delay_seconds=5.0, num_retries=2)


def test_validate_paper_arguments():
    args = validate_paper_arguments(page_size=150, delay_seconds=2.0, num_retries=5)
    assert args == {
        'page_size': 150,
        'delay_seconds': 2.0,
        'num_retries': 5
    }


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_search_by_arxiv_id_and_properties(mock_client_class, mock_paper_object):
    mock_client = MagicMock()
    mock_client.results.return_value = iter([mock_paper_object])
    mock_client_class.return_value = mock_client

    paper = Paper()
    paper.search_by_arxiv_id("1234.5678")

    assert paper.title == "Test Title"
    assert paper.abstract == "This is a test abstract."
    assert paper.authors == ["Alice", "Bob"]
    assert paper.published == datetime(2022, 1, 1)
    assert paper.updated == datetime(2022, 1, 2)


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_init_without_validation(mock_client_class):
    paper = Paper(validate_arguments=False)  # noqa: F841 # pylint: disable=unused-variable
    mock_client_class.assert_called_once()


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_paper_properties_when_paper_is_none(mock_client_class, caplog):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    logger = logging.getLogger('audioarxiv')  # Match the logger name
    logger.setLevel(logging.ERROR)  # Ensure ERROR logs are allowed
    logger.propagate = True

    paper = Paper()

    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        assert paper.title is None
        assert 'paper is None.' in caplog.text
    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        assert paper.abstract is None
        assert 'paper is None.' in caplog.text
    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        assert paper.authors is None
        assert 'paper is None.' in caplog.text
    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        assert paper.published is None
        assert 'paper is None.' in caplog.text
    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        assert paper.updated is None
        assert 'paper is None.' in caplog.text


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_download_pdf_with_valid_paper(mock_client_class, mock_paper_object):
    mock_client = MagicMock()
    mock_client.results.return_value = iter([mock_paper_object])
    mock_client_class.return_value = mock_client

    mock_paper_object.download_pdf.return_value = "path/to/pdf"

    # Create the Paper instance
    paper = Paper(validate_arguments=False)
    paper.search_by_arxiv_id('arxiv_id')

    # Call the `download_pdf` method
    pdf_path = paper.download_pdf(dirpath='./', filename='test_paper.pdf')

    # Assertions
    mock_paper_object.download_pdf.assert_called_once_with(dirpath='./', filename='test_paper.pdf')
    assert pdf_path == "path/to/pdf"


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_download_pdf_when_no_paper(mock_client_class, caplog):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    logger = logging.getLogger('audioarxiv')  # Match the logger name
    logger.setLevel(logging.ERROR)  # Ensure ERROR logs are allowed
    logger.propagate = True

    # Setup: Create Paper instance with no paper assigned
    paper = Paper(validate_arguments=False)

    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        # Call `download_pdf`
        pdf_path = paper.download_pdf(dirpath='./', filename='test_paper.pdf')

        # Assertions
        assert pdf_path is None
        assert 'Paper is None. Cannot download PDF.' in caplog.text


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_sections_with_valid_pdf(mock_client_class, mock_paper_object):
    mock_client = MagicMock()
    mock_client.results.return_value = iter([mock_paper_object])
    mock_client_class.return_value = mock_client

    # Setup: Create Paper instance with no paper assigned
    paper = Paper(validate_arguments=False)
    paper.search_by_arxiv_id('arxiv_id')

    # Mock the `download_pdf` and `fitz.open` methods
    with patch('fitz.open') as mock_fitz_open:
        mock_page = MagicMock()
        mock_page.get_text.return_value = [[None, None, None, None, "SECTION HEADER\n"],
                                           [None, None, None, None, "Section Content"]]
        mock_fitz_open.return_value = [mock_page]

        # Call the `sections` property
        sections = paper.sections

        # Assertions
        assert len(sections) > 0  # Should return at least one section
        assert sections[0]["header"] == "SECTION HEADER"
        assert "Section Content" in sections[0]["content"]


@patch("audioarxiv.resources.paper.arxiv.Client")
def test_sections_when_no_paper(mock_client_class, caplog):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    logger = logging.getLogger('audioarxiv')  # Match the logger name
    logger.setLevel(logging.ERROR)  # Ensure ERROR logs are allowed
    logger.propagate = True

    # Setup: Create Paper instance with no paper assigned
    paper = Paper(validate_arguments=False)

    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        # Call `sections` property
        sections = paper.sections

        # Assertions
        assert 'Paper is None. Cannot download PDF.' in caplog.text
        assert len(sections) == 0  # No sections should be found since paper is None


@patch("fitz.open")
@patch.object(Paper, "download_pdf")
def test_sections_extraction_logic(download_pdf_mock, fitz_open_mock):
    # Setup fake PDF text blocks
    mock_page = MagicMock()
    mock_page.get_text.return_value = [
        (0, 0, 100, 100, "1 Introduction", 0, 0, 0),
        (0, 0, 100, 100, "This is the first paragraph.", 0, 0, 0),
        (0, 0, 100, 100, "2 Related Work", 0, 0, 0),
        (0, 0, 100, 100, "Some related work goes here.", 0, 0, 0),
    ]

    mock_doc = [mock_page]
    fitz_open_mock.return_value = mock_doc

    paper = Paper()
    paper.paper = MagicMock()
    download_pdf_mock.return_value = "mock_path"

    sections = paper.sections

    assert len(sections) == 2  # ✅ tests `if len(self._sections) == 0`
    assert sections[0]["header"] == "1 Introduction"
    assert sections[0]["content"] == ["This is the first paragraph."]
    assert sections[1]["header"] == "2 Related Work"
    assert sections[1]["content"] == ["Some related work goes here."]


@patch("fitz.open")
@patch.object(Paper, "download_pdf")
def test_sections_only_appends_nonempty_sections(download_pdf_mock, fitz_open_mock):
    # Only content, no section header detected
    mock_page = MagicMock()
    mock_page.get_text.return_value = [
        (0, 0, 100, 100, "Just some content without a header", 0, 0, 0)
    ]

    mock_doc = [mock_page]
    fitz_open_mock.return_value = mock_doc

    paper = Paper()
    paper.paper = MagicMock()
    download_pdf_mock.return_value = "mock_path"

    sections = paper.sections

    # Tests `if current_section["header"] or current_section["content"]`
    assert len(sections) == 1
    assert sections[0]["header"] is None
    assert sections[0]["content"] == ["Just some content without a header"]


@patch("fitz.open")
@patch.object(Paper, "download_pdf")
def test_sections_empty_when_no_paper(download_pdf_mock, fitz_open_mock):
    paper = Paper()
    paper.paper = None  # simulate not setting a paper

    sections = paper.sections

    # Triggers early return due to missing paper
    assert sections == []
