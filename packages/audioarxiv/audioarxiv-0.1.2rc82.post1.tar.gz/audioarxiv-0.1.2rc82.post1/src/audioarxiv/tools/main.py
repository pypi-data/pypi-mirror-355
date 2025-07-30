"""
A command line tool to fetch arXiv papers and read aloud.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time

import configargparse
from platformdirs import user_config_dir

from ..audio.base import Audio, validate_audio_arguments
from ..resources.paper import Paper, validate_paper_arguments

logger = logging.getLogger('audioarxiv')


def handle_exit(sig_num: int , frame: object):  # noqa: ARG001 # pylint: disable=unused-argument
    """Handle the exit.

    Args:
        sig_num (int): Signal number.
        frame (object): A frame object.
    """
    logger.info("\nReceived signal %s. Exiting cleanly.", sig_num)
    sys.exit(0)


def save_settings(config_path: str, settings: dict):
    """Save the settings to file.

    Args:
        config_path (str): Path to the configuration file.
        settings (dict): Dictionary of the settings.
    """
    try:
        with open(config_path, 'w', encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error('Error saving settings: %s', e)


def initialize_configuration(args: configargparse.Namespace) -> tuple:
    """Initialize the configuration.

    Args:
        args (configargparse.Namespace): Arguments.

    Returns:
        tuple: settings, config_path
    """
    config_dir = user_config_dir('audioarxiv')
    os.makedirs(config_dir, exist_ok=True)
    config_file = 'config.json'
    config_path = os.path.join(config_dir, config_file)
    # Default settings.
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

    # Validate the default settings.
    if os.path.exists(config_path):
        # Load the settings from the config file.
        try:
            with open(config_path, encoding="utf-8") as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
                settings['audio'] = validate_audio_arguments(**settings['audio'])
                settings['paper'] = validate_paper_arguments(**settings['paper'])
        except Exception as e:
            logger.error('Error loading settings: %s. Using defaults.', e)
    else:
        logger.info('Saving default settings to %s...', config_path)
        settings['audio'] = validate_audio_arguments(**settings['audio'])
        settings['paper'] = validate_paper_arguments(**settings['paper'])
        save_settings(config_path, settings)

    # Check audio properties
    audio_properties = list(settings['audio'].keys())
    audio_settings_changed = False
    for prop in audio_properties:
        value = getattr(args, prop)
        if value is not None:
            # Compare with the existing setting
            if value != settings['audio'][prop]:
                settings['audio'][prop] = value
                audio_settings_changed = True
    if audio_settings_changed:
        settings['audio'] = validate_audio_arguments(**settings['audio'])

    # Check paper properties
    paper_properties = list(settings['paper'].keys())
    paper_settings_changed = False
    for prop in paper_properties:
        value = getattr(args, prop)
        if value is not None:
            # Compare with the existing setting
            if value != settings['paper'][prop]:
                settings['paper'][prop] = value
                paper_settings_changed = True
    if paper_settings_changed:
        settings['paper'] = validate_paper_arguments(**settings['paper'])

    # Write the settings to file if there are changes.
    if audio_settings_changed or paper_settings_changed:
        logger.info('Saving updated settings to %s...', config_path)
        save_settings(config_path=config_path, settings=settings)
    return settings, config_path


def main():
    """Main function.
    """
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    parser = configargparse.ArgParser()
    parser.add_argument('--id', help='arXiv paper ID.')
    parser.add_argument('--output', type=str, help='Output to audio file if provided.')
    parser.add_argument('--rate', type=float, help='Number of words per minute between 50 and 500.')
    parser.add_argument('--volume', type=float, help='Volume between 0 and 1.')
    parser.add_argument('--voice', type=str, help='Voice.')
    parser.add_argument('--pause-seconds', type=float, help='Duration of pause between sentences in second.')
    parser.add_argument('--page-size', type=int, help='Maximum number of results fetched in a single API request.')
    parser.add_argument('--delay-seconds', type=float, help='Number of seconds to wait between API requests.')
    parser.add_argument('--num-retries', type=int, help=('Number of times to retry a failing API request before raising'
                                                         'an Exception.'))
    parser.add_argument('--list-voices', action='store_true', help='List the available voices.')

    args = parser.parse_args()

    if args.list_voices:
        audio = Audio()
        audio.list_voices()
        return

    # Get the settings
    settings, config_path = initialize_configuration(args)

    # The Audio instance.
    audio = Audio(**settings['audio'])

    # Load the paper.
    paper = Paper(**settings['paper'])

    # Search the paper.
    # Print the information
    logger.info('Configuration file: %s', config_path)
    logger.info('Audio settings')
    for key, value in settings['audio'].items():
        logger.info('%s: %s', key, value)

    logger.info('Paper settings')
    for key, value in settings['paper'].items():
        logger.info('%s: %s', key, value)

    logger.info('Searching arxiv: %s...', args.id)
    paper.search_by_arxiv_id(arxiv_id=args.id)
    # Get the sections
    sections = paper.sections
    if args.output is None:
        for section in sections:
            audio.read_article(section['header'])
            time.sleep(1)
            for content in section['content']:
                audio.read_article(content)
                time.sleep(1)
    else:
        article = []
        for section in sections:
            if section['header'] is not None:
                article.append(section['header'])
            if section['content'] is not None:
                article += section['content']
        article = " ".join(article)
        logger.info('Saving audio...')
        audio.save_article(filename=args.output, article=article)
        logger.info('Audio is saved to %s.', args.output)
