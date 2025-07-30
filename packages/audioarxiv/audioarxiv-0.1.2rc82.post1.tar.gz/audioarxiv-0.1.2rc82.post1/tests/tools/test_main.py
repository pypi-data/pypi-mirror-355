from __future__ import annotations

import json
import logging
import os
import signal
import tempfile
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
import pyttsx3

from audioarxiv.tools.main import (handle_exit, initialize_configuration, main,
                                   save_settings)


@pytest.fixture
def mock_pyttsx3_init(monkeypatch):
    mock_engine = MagicMock()
    monkeypatch.setattr(pyttsx3, "init", lambda: mock_engine)
    return mock_engine


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


# Patch where classes/functions are used, not defined
@pytest.mark.integration
@patch("audioarxiv.tools.main.Audio")
@patch("audioarxiv.tools.main.Paper")
@patch("audioarxiv.tools.main.configargparse.ArgParser.parse_args")
def test_main_with_id_and_output(mock_parse_args, mock_Paper, mock_Audio):
    mock_args = MagicMock()
    mock_args.id = "1234.5678"
    mock_args.output = "output.mp3"
    mock_args.list_voices = False
    mock_args.rate = None
    mock_args.volume = None
    mock_args.voice = None
    mock_args.pause_seconds = None
    mock_args.page_size = None
    mock_args.delay_seconds = None
    mock_args.num_retries = None
    mock_parse_args.return_value = mock_args

    mock_audio = mock_Audio.return_value
    mock_paper = mock_Paper.return_value
    mock_paper.sections = [
        {'header': "Introduction", 'content': ["This is content."]},
        {'header': None, 'content': ["More content."]}
    ]

    with patch("audioarxiv.tools.main.initialize_configuration") as mock_init_config:
        mock_init_config.return_value = ({"audio": {}, "paper": {}}, "mock/config/path")

        main()

    mock_audio.save_article.assert_called_once()
    assert mock_audio.save_article.call_args[1]["filename"] == "output.mp3"


@pytest.mark.integration
@patch("audioarxiv.tools.main.Audio")
@patch("audioarxiv.tools.main.configargparse.ArgParser.parse_args")
def test_main_list_voices(mock_parse_args, mock_Audio):
    mock_args = MagicMock()
    mock_args.list_voices = True
    mock_parse_args.return_value = mock_args

    mock_audio = mock_Audio.return_value

    main()

    mock_audio.list_voices.assert_called_once()


@pytest.mark.integration
@patch("audioarxiv.tools.main.validate_audio_arguments")
@patch("audioarxiv.tools.main.validate_paper_arguments")
def test_initialize_configuration_defaults(mock_validate_paper, mock_validate_audio):
    mock_validate_audio.return_value = {'rate': 140, 'volume': 0.9, 'voice': None, 'pause_seconds': 0.1}
    mock_validate_paper.return_value = {'page_size': 100, 'delay_seconds': 3.0, 'num_retries': 3}

    dummy_args = MagicMock()
    for attr in ['rate', 'volume', 'voice', 'pause_seconds', 'page_size', 'delay_seconds', 'num_retries']:
        setattr(dummy_args, attr, None)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        config_path = os.path.join(tmp_dir_name, 'config.json')  # noqa: F841 # pylint: disable=unused-variable

        with patch("audioarxiv.tools.main.user_config_dir", return_value=tmp_dir_name):
            settings, path = initialize_configuration(dummy_args)
            assert settings['audio']['rate'] == 140
            assert os.path.exists(path)


@pytest.mark.integration
@patch("builtins.open", new_callable=mock.mock_open)
def test_save_settings(mock_open_func):
    settings = {"audio": {"rate": 150}, "paper": {"page_size": 50}}
    save_settings("config.json", settings)
    mock_open_func.assert_called_once_with("config.json", 'w', encoding='utf-8')
    handle = mock_open_func()
    handle.write.assert_called()


@pytest.mark.integration
@patch("audioarxiv.tools.main.sys.exit")
def test_handle_exit(mock_exit):
    with patch("audioarxiv.tools.main.logger.info") as mock_logger:
        handle_exit(signal.SIGINT, None)
        mock_logger.assert_called_once()
        mock_exit.assert_called_once_with(0)


@patch('builtins.open', side_effect=IOError('Mocked IOError during file open'))
def test_save_settings_throws_exception(mock_open, caplog):
    config_path = "test_config.json"
    settings = {
        'audio': {
            'rate': 140,
            'volume': 0.9,
            'voice': None,
            'pause_seconds': 0.1
        },
        'paper': {
            'page_size': 100,
            'delay_seconds': 3.0,
            'num_retries': 3
        }
    }

    logger = logging.getLogger('audioarxiv')
    logger.setLevel(logging.ERROR)
    logger.propagate = True

    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        # Call save_settings, which should raise an exception
        save_settings(config_path, settings)

        # Assert that the open function was called (even though it will raise an exception)
        mock_open.assert_called_once_with(config_path, 'w', encoding="utf-8")

        assert 'Error saving settings: Mocked IOError during file open' in caplog.text


@patch('audioarxiv.tools.main.user_config_dir', return_value='.')  # Mock user_config_dir
@patch('os.path.exists')
@patch('builtins.open', new_callable=MagicMock)  # Mock the open function to read the file
@patch('json.load')  # Mock json.load to simulate loading settings
@patch('audioarxiv.audio.base.validate_audio_arguments')  # Mock the validate_audio_arguments function
@patch('audioarxiv.resources.paper.validate_paper_arguments')  # Mock the validate_paper_arguments function
@patch("audioarxiv.resources.paper.arxiv.Client")
@patch("configargparse.ArgParser.parse_args")
def test_load_settings(mock_parse_args,
                       mock_client_class,
                       mock_validate_paper,
                       mock_validate_audio,
                       mock_json_load,
                       mock_open,
                       mock_exists,
                       mock_user_config_dir,
                       mock_pyttsx3_init,
                       mock_paper_object,
                       caplog):
    # Set up mock arguments
    mock_args = MagicMock()
    mock_args.id = "1234.5678"
    mock_args.output = None
    mock_args.list_voices = False
    mock_args.rate = None
    mock_args.volume = None
    mock_args.voice = None
    mock_args.pause_seconds = None
    mock_args.page_size = None
    mock_args.delay_seconds = None
    mock_args.num_retries = None
    mock_parse_args.return_value = mock_args

    mock_engine = mock_pyttsx3_init()  # noqa: F841

    mock_client = MagicMock()
    mock_client.results.return_value = iter([mock_paper_object])
    mock_client_class.return_value = mock_client

    mock_paper_object.download_pdf.return_value = "path/to/pdf"

    # Set up the logger
    logger = logging.getLogger('audioarxiv')
    logger.setLevel(logging.DEBUG)
    logger.propagate = True

    # Sample settings to be loaded
    config_dir = mock_user_config_dir('audioarxiv')  # Assuming this function is defined correctly
    config_file = 'config.json'
    config_path = os.path.join(config_dir, config_file)
    settings_from_file = {
        'audio': {
            'rate': 150,
            'volume': 1.0,
            'voice': None,
            'pause_seconds': 0.2
        },
        'paper': {
            'page_size': 50,
            'delay_seconds': 2.0,
            'num_retries': 5
        }
    }

    # Mock file reading
    mock_file = MagicMock()
    mock_file.read.return_value = b'mocked file content'
    mock_open.return_value.__enter__.return_value = mock_file
    mock_json_load.return_value = settings_from_file

    # Mock validation functions
    mock_validate_audio.return_value = settings_from_file['audio']
    mock_validate_paper.return_value = settings_from_file['paper']

    # Mock file existence
    mock_exists.return_value = True

    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        # Mock the `download_pdf` and `fitz.open` methods
        with patch('fitz.open') as mock_fitz_open:
            mock_page = MagicMock()
            mock_page.get_text.return_value = [[None, None, None, None, "SECTION HEADER\n"],
                                               [None, None, None, None, "Section Content"]]
            mock_fitz_open.return_value = [mock_page]
            main()

    # Verify config_path was checked
    mock_exists.assert_any_call(config_path)
    mock_json_load.assert_called_once_with(mock_file)


@patch('audioarxiv.tools.main.user_config_dir', return_value='.')  # Mock user_config_dir
@patch('os.path.exists')
@patch('builtins.open', new_callable=MagicMock)  # Mock the open function to read the file
@patch('json.load')  # Mock json.load to simulate loading settings
@patch('audioarxiv.audio.base.validate_audio_arguments')  # Mock the validate_audio_arguments function
@patch('audioarxiv.resources.paper.validate_paper_arguments')  # Mock the validate_paper_arguments function
@patch("audioarxiv.resources.paper.arxiv.Client")
@patch("configargparse.ArgParser.parse_args")
def test_load_settings_error(mock_parse_args,
                             mock_client_class,
                             mock_validate_paper,
                             mock_validate_audio,
                             mock_json_load,
                             mock_open,
                             mock_exists,
                             mock_user_config_dir,
                             mock_pyttsx3_init,
                             mock_paper_object,
                             caplog):
    # Set up mock arguments
    mock_args = MagicMock()
    mock_args.id = "1234.5678"
    mock_args.output = None
    mock_args.list_voices = False
    mock_args.rate = None
    mock_args.volume = None
    mock_args.voice = None
    mock_args.pause_seconds = None
    mock_args.page_size = None
    mock_args.delay_seconds = None
    mock_args.num_retries = None
    mock_parse_args.return_value = mock_args

    mock_engine = mock_pyttsx3_init()  # noqa: F841

    mock_client = MagicMock()
    mock_client.results.return_value = iter([mock_paper_object])
    mock_client_class.return_value = mock_client

    mock_paper_object.download_pdf.return_value = "path/to/pdf"

    # Set up the logger
    logger = logging.getLogger('audioarxiv')
    logger.setLevel(logging.DEBUG)
    logger.propagate = True

    # Sample settings to be loaded
    config_dir = mock_user_config_dir('audioarxiv')  # Assuming this function is defined correctly
    config_file = 'config.json'
    config_path = os.path.join(config_dir, config_file)

    settings_from_file = {
        'audio': {
            'rate': 150,
            'volume': 1.0,
            'voice': None,
            'pause_seconds': 0.2
        },
        'paper': {
            'page_size': 50,
            'delay_seconds': 2.0,
            'num_retries': 5
        }
    }

    # Mock validation functions
    mock_validate_audio.return_value = settings_from_file['audio']
    mock_validate_paper.return_value = settings_from_file['paper']

    # Set up the mock to simulate file reading failure (File not found error)
    mock_exists.return_value = False  # Simulate that the file doesn't exist
    with caplog.at_level(logging.INFO, logger='audioarxiv'):
        with patch('fitz.open') as mock_fitz_open:
            mock_page = MagicMock()
            mock_page.get_text.return_value = [[None, None, None, None, "SECTION HEADER\n"],
                                               [None, None, None, None, "Section Content"]]
            mock_fitz_open.return_value = [mock_page]
            main()

    # Ensure the file existence check was called and failed
    mock_exists.assert_any_call(config_path)
    # Check for the error in logs
    assert 'Saving default settings to ./config.json...' in caplog.text

    # Now simulate an invalid JSON error
    mock_exists.return_value = True
    mock_file = MagicMock()
    mock_file.read.return_value = b'mocked file content'
    mock_open.return_value.__enter__.return_value = mock_file
    mock_json_load.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)  # Simulate JSONDecodeError
    mock_client.results.return_value = iter([mock_paper_object])

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger='audioarxiv'):
        with patch('fitz.open') as mock_fitz_open:
            mock_page = MagicMock()
            mock_page.get_text.return_value = [[None, None, None, None, "SECTION HEADER\n"],
                                               [None, None, None, None, "Section Content"]]
            mock_fitz_open.return_value = [mock_page]
            main()

    # Ensure json.load was called
    mock_json_load.assert_called_once_with(mock_file)
    # Check for the JSON error in logs
    assert 'Error loading settings: Expecting value' in caplog.text
