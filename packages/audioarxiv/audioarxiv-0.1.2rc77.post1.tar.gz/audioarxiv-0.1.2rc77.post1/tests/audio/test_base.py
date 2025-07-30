from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
import pyttsx3

from audioarxiv.audio.base import Audio, validate_audio_arguments


# Mock pyttsx3.init to avoid actual engine initialization during testing
@pytest.fixture
def mock_pyttsx3_init(monkeypatch):
    mock_engine = MagicMock()
    monkeypatch.setattr(pyttsx3, "init", lambda: mock_engine)
    return mock_engine


def test_validate_audio_arguments_valid(mock_pyttsx3_init):
    # Mocking valid parameters
    mock_engine = mock_pyttsx3_init()  # noqa: F841
    result = validate_audio_arguments(150, 0.8, "voice_id", 0.5)
    assert result['rate'] == 150
    assert result['volume'] == 0.8
    assert result['voice'] is None
    assert result['pause_seconds'] == 0.5


def test_validate_audio_arguments_invalid_voice_index(mock_pyttsx3_init):
    mock_engine = mock_pyttsx3_init()  # noqa: F841
    result = validate_audio_arguments(150, 0.8, 99, 0.5)  # Invalid voice index  # noqa: F841
    assert result['voice'] is None  # Voice should be set to None for invalid index


def test_validate_audio_arguments_invalid_voice_id(mock_pyttsx3_init):
    mock_engine = mock_pyttsx3_init()  # noqa: F841
    result = validate_audio_arguments(150, 0.8, "invalid_voice_id", 0.5)  # Invalid voice ID
    assert result['voice'] is None  # Voice should be set to None for invalid voice ID


def test_validate_audio_arguments_invalid_voice_type(mock_pyttsx3_init):
    mock_engine = mock_pyttsx3_init()  # noqa: F841
    result = validate_audio_arguments(150, 0.8, 12345, 0.5)  # Invalid voice type
    assert result['voice'] is None  # Voice should be set to None for invalid type


def test_validate_audio_arguments_invalid_pause_seconds(mock_pyttsx3_init):
    mock_engine = mock_pyttsx3_init()  # noqa: F841
    result = validate_audio_arguments(150, 0.8, "voice_id", -1)  # Invalid pause seconds (negative)
    assert result['pause_seconds'] == 0.1  # Pause seconds should be set to the default value 0.1


@pytest.fixture
def audio_instance(mock_pyttsx3_init):
    mock_engine = mock_pyttsx3_init()  # noqa: F841
    return Audio(rate=150, volume=0.8, voice="voice_id", pause_seconds=0.5, validate_arguments=True)


def test_audio_initialization(audio_instance):
    assert audio_instance.engine is not None  # Ensure engine is initialized
    assert audio_instance.pause_seconds == 0.5  # Check if pause_seconds is set correctly


@patch('audioarxiv.audio.base.time.sleep')  # prevent actual sleeping
@patch('audioarxiv.audio.base.get_sentences')  # control sentence splitting
@patch('audioarxiv.audio.base.pyttsx3.init')  # control TTS engine
def test_read_article(mock_init, mock_get_sentences, mock_sleep):
    # Create a mock engine with say() and runAndWait()
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine

    # Mock get_sentences to return predictable output
    mock_get_sentences.return_value = ['Sentence 1', 'Sentence 2']

    # Create Audio instance and run test
    audio = Audio()
    audio.read_article("Some article.")

    # Verify say() was called with the expected sentence
    mock_engine.say.assert_any_call('Sentence 1')
    mock_engine.say.assert_any_call('Sentence 2')
    assert mock_engine.runAndWait.call_count == 2
    assert mock_sleep.call_count == 2


def test_save_article(audio_instance, monkeypatch):
    # Mocking pyttsx3 save_to_file method
    mock_save = MagicMock()
    monkeypatch.setattr(audio_instance.engine, "save_to_file", mock_save)

    article = "This is an article."
    filename = "test_audio.mp3"
    audio_instance.save_article(filename, article)

    # Ensure the save_to_file method was called once with the cleaned text and filename
    mock_save.assert_called_once_with("This is an article.", filename)


def test_pause_seconds_setter(audio_instance):
    audio_instance.pause_seconds = 1.0  # Setting a valid value
    assert audio_instance.pause_seconds == 1.0  # Check if the setter works correctly

    audio_instance.pause_seconds = -1.0  # Setting an invalid value (negative)
    assert audio_instance.pause_seconds == 1.0  # The value should remain 1.0


@patch('audioarxiv.audio.base.logger')
@patch('audioarxiv.audio.base.pyttsx3.init')
def test_list_voices(mock_init, mock_logger):
    mock_engine = MagicMock()
    mock_voice = MagicMock()
    mock_voice.name = "Voice 1"
    mock_voice.id = "voice1"
    mock_engine.getProperty.return_value = [mock_voice]
    mock_init.return_value = mock_engine

    audio = Audio()
    audio.list_voices()

    mock_logger.info.assert_any_call("Index %s: %s (ID: %s)", 0, "Voice 1", "voice1")


def test_validate_audio_arguments_with_voice_index():
    mock_voice = MagicMock()
    mock_voice.id = "mock_voice_id"
    with patch("pyttsx3.init") as mock_init:
        mock_engine = MagicMock()
        mock_engine.getProperty.return_value = [mock_voice]
        mock_init.return_value = mock_engine

        result = validate_audio_arguments(rate=140, volume=0.9, voice=0, pause_seconds=0.1)
        assert result["voice"] == "mock_voice_id"


def test_validate_audio_arguments_with_invalid_voice_type(caplog):
    with patch("pyttsx3.init") as mock_init:
        mock_engine = MagicMock()
        mock_engine.getProperty.return_value = None
        mock_init.return_value = mock_engine

        logger = logging.getLogger('audioarxiv')  # Match the logger name
        logger.setLevel(logging.ERROR)  # Ensure ERROR logs are allowed
        logger.propagate = True

        # Capture logs at ERROR level
        with caplog.at_level(logging.ERROR, logger='audioarxiv'):
            result = validate_audio_arguments(rate=140,
                                              volume=0.9,
                                              voice=[],  # type: ignore[argument]
                                              pause_seconds=0.1)
            print(caplog.text)
            # Check if the log contains the expected error message
            assert "Unsupported datatype of voice" in caplog.text
            assert "<class 'list'>" in caplog.text  # Optionally check for the actual type in the log message

            # Ensure the result['voice'] is None
            assert result['voice'] is None


def test_audio_sets_voice_property():
    mock_voice = MagicMock()
    mock_voice.id = "mock_voice_id"
    with patch("pyttsx3.init") as mock_init:
        mock_engine = MagicMock()
        mock_engine.getProperty.return_value = [mock_voice]
        mock_init.return_value = mock_engine

        audio = Audio(voice="mock_voice_id")  # noqa: F841
        # Ensure setProperty was called with the correct voice ID
        mock_engine.setProperty.assert_any_call("voice", "mock_voice_id")


@patch('audioarxiv.audio.base.pyttsx3.init')  # control TTS engine
def test_read_article_with_non_string_input(mock_init, caplog):
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine

    logger = logging.getLogger('audioarxiv')  # Match the logger name
    logger.setLevel(logging.WARNING)  # Ensure ERROR logs are allowed
    logger.propagate = True

    audio = Audio()
    with caplog.at_level("WARNING"):
        audio.read_article(article=12345)  # type: ignore[argument]
        assert "is not str. Skipping." in caplog.text


@patch("audioarxiv.audio.base.pyttsx3.init")
def test_audio_stop(mock_init):
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine

    # Create the Audio instance, which should use the mocked engine
    audio = Audio()

    # Call the stop method
    audio.stop()

    # Verify that the stop method was called on the mocked engine
    mock_engine.stop.assert_called_once()


@patch("audioarxiv.audio.base.pyttsx3.init")
def test_validate_arguments_enabled(mock_init):
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine

    # Arrange
    with patch("audioarxiv.audio.base.validate_audio_arguments") as mock_validate:
        mock_validate.return_value = {
            "rate": 150,
            "volume": 0.8,
            "voice": "voice_id",
            "pause_seconds": 0.2
        }

        # Act
        audio = Audio(rate=150,  # noqa: F841 # pylint: disable=unused-variable
                      volume=0.8,
                      voice="voice_id",
                      pause_seconds=0.2,
                      validate_arguments=True)

        # Assert
        mock_validate.assert_called_once()
        mock_engine.setProperty.assert_any_call('rate', 150)
        mock_engine.setProperty.assert_any_call('volume', 0.8)
        mock_engine.setProperty.assert_any_call('voice', 'voice_id')


@patch("audioarxiv.audio.base.pyttsx3.init")
def test_validate_arguments_disabled(mock_init):
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine
    # Should not call `validate_audio_arguments`
    with patch("audioarxiv.audio.base.validate_audio_arguments") as mock_validate:
        audio = Audio(rate=150,  # noqa: F841 # pylint: disable=unused-variable
                      volume=0.8,
                      voice="voice_id",
                      pause_seconds=0.2,
                      validate_arguments=False)

        mock_validate.assert_not_called()
        mock_engine.setProperty.assert_any_call('rate', 150)
        mock_engine.setProperty.assert_any_call('volume', 0.8)
        mock_engine.setProperty.assert_any_call('voice', 'voice_id')


@pytest.mark.parametrize("rate", [100, None])
@patch("audioarxiv.audio.base.pyttsx3.init")
def test_rate_handling(mock_init, rate):
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine
    audio = Audio(rate=rate, volume=0.8, validate_arguments=False)  # noqa: F841 # pylint: disable=unused-variable
    if rate is not None:
        mock_engine.setProperty.assert_any_call('rate', rate)
    else:
        for call in mock_engine.setProperty.call_args_list:
            assert call[0][0] != 'rate'


@pytest.mark.parametrize("volume", [0.5, None])
@patch("audioarxiv.audio.base.pyttsx3.init")
def test_volume_handling(mock_init, volume):
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine
    audio = Audio(rate=140, volume=volume, validate_arguments=False)  # noqa: F841 # pylint: disable=unused-variable
    if volume is not None:
        mock_engine.setProperty.assert_any_call('volume', volume)
    else:
        for call in mock_engine.setProperty.call_args_list:
            assert call[0][0] != 'volume'
