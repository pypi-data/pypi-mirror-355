"""
A base class for audio.
"""
from __future__ import annotations

import logging
import time

import pyttsx3

from ..preprocess import get_sentences

logger = logging.getLogger('audioarxiv')


def validate_audio_arguments(rate: float, volume: float, voice: int | str | None, pause_seconds: float) -> dict:
    """Validate the arguments for Audio.

    Args:
        rate (float): Number of words per minute.
        volume (float): Volume.
        voice (int | str | None): If it is int, it is interpreted as the index of the available voices.
            If it is str, it is interpreted as the ID of the voice.
            The available voice ids can be found with `list_voices()`.
        pause_seconds (float): Duration of pause between sentences.

    Returns:
        dict: rate, volume, voice, pause_seconds
    """
    engine = pyttsx3.init()
    available_voices = engine.getProperty('voices')
    rate = max(50, min(500, rate))
    volume = max(0.0, min(1.0, volume))
    if isinstance(voice, int):
        if 0 <= voice < len(available_voices):
            voice = available_voices[voice].id
        else:
            voice = None
            logger.error('Invalid voice index = %s. Keeping current voice.', voice)
    elif isinstance(voice, str):
        if voice not in [v.id for v in available_voices]:
            voice = None
            logger.error('Invalid voice ID = %s. Keeping current voice.', voice)
    elif voice is not None:
        logger.error('Unsupported datatype of voice = %s. It must be either int or str.', type(voice))
        voice = None
    if pause_seconds < 0:
        pause_seconds = 0.1
        logger.error('pause = %s must be non-negative. Keeping the current pause.', pause_seconds)
    return {'rate': rate,
            'volume': volume,
            'voice': voice,
            'pause_seconds': pause_seconds}


class Audio:
    """A class to generate audio from text.
    """
    def __init__(self, rate: float = 140,  # noqa: R0913,E1120,E501 # pylint: disable=too-many-arguments,too-many-positional-arguments,C0301
                 volume: float = 0.9,
                 voice: str | None = None,
                 pause_seconds: float = 0.1,
                 validate_arguments: bool = True):
        """A class to configure the audio.

        Args:
            rate (float, optional): Number of words per minute. Defaults to 140.
            volume (float, optional): Volume. Defaults to 0.9.
            voice (Optional[str], optional): Voice id.
                The available voice ids can be found with `list_voices()`.
                Defaults to None.
            pause_seconds (float, optional): Duration of pause between sentences. Defaults to 0.1.
            validate_arguments (bool): If True, validate the arguments.
        """
        if validate_arguments:
            arguments = validate_audio_arguments(rate=rate,
                                                 volume=volume,
                                                 voice=voice,
                                                 pause_seconds=pause_seconds)
            rate = arguments['rate']
            volume = arguments['volume']
            voice = arguments['voice']
            pause_seconds = arguments['pause_seconds']
        self.engine = pyttsx3.init()
        if rate is not None:
            self.engine.setProperty('rate', rate)
        if volume is not None:
            self.engine.setProperty('volume', volume)
        if voice is not None:
            self.engine.setProperty('voice', voice)
        self.pause_seconds = pause_seconds

    @property
    def available_voices(self) -> list:
        """Get the available voices.

        Returns:
            list: The available voices.
        """
        return self.engine.getProperty('voices')

    @property
    def pause_seconds(self) -> float:
        """The duration of pause between sentences.

        Returns:
            float: Duration of pause between sentences in second.
        """
        return self._pause_seconds

    @pause_seconds.setter
    def pause_seconds(self, value: float):
        """Set the duration of pause between sentences.

        Args:
            value (float): Duration of pause between sentences.
        """
        if value < 0:
            logger.error('pause = %s must be non-negative. Keeping the current pause.', value)
            return
        self._pause_seconds = value

    def list_voices(self):
        """Print available voices with their index and details."""
        for i, voice in enumerate(self.available_voices):
            logger.info("Index %s: %s (ID: %s)", i, voice.name, voice.id)

    def clean_text(self, text: str) -> str:
        """Clean the text for smoother reading.

        '\\n' is replaced with a white space.

        Args:
            text (str): Text.

        Returns:
            str: Cleaned text.
        """
        return " ".join(text.split()).replace('\n', ' ').strip()

    def read_article(self,
                     article: str):
        """Read the article aloud, splitting it into sentences.

        Args:
            article (str): Article.
        """
        if not isinstance(article, str):
            logger.warning('article = %s is not str. Skipping.', article)
            return
        cleaned_text = self.clean_text(article)
        sentences = get_sentences(cleaned_text)
        for sentence in sentences:
            self.engine.say(sentence)
            self.engine.runAndWait()
            time.sleep(self.pause_seconds)

    def save_article(self,
                     filename: str,
                     article: str):
        """Save the article to an audio file.

        Args:
            filename (str): File name.
            article (str): Article.
        """
        cleaned_text = self.clean_text(article)
        self.engine.save_to_file(cleaned_text, filename)
        self.engine.runAndWait()

    def stop(self):
        """Stop the current speech."""
        self.engine.stop()
