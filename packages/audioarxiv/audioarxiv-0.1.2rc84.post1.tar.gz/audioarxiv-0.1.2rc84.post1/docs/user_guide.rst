User Guide
===========

The audioarxiv command-line tool allows you to fetch research papers from `arXiv <https://arxiv.org/>`_ and read them aloud using a text-to-speech engine.

Basic Usage
-----------

.. code-block:: console

    $ audioarxiv --id 1602.03837

This will fetch the arXiv paper with ID 1602.03837, process its content, and read it aloud.

To save the audio to a file instead:

.. code-block:: console

    $ audioarxiv --id 1602.03837 --output audio.mp3

**Reminder**: It takes a long time to process a paper into an audio file.

Command-Line Options
--------------------

.. list-table:: Command-line Options for audioarxiv
   :widths: 25 75
   :header-rows: 1

   * - Option
     - Description
   * - ``-h``, ``--help``
     - Show the help message and exit.
   * - ``--id ID``
     - arXiv paper ID.
   * - ``--output OUTPUT``
     - Output to audio file if provided.
   * - ``--rate RATE``
     - Number of words per minute between 50 and 500.
   * - ``--volume VOLUME``
     - Volume between 0 and 1.
   * - ``--voice VOICE``
     - Voice to use for text-to-speech.
   * - ``--pause-seconds PAUSE_SECONDS``
     - Duration of pause between sentences in seconds.
   * - ``--page-size PAGE_SIZE``
     - Maximum number of results fetched in a single API request.
   * - ``--delay-seconds DELAY_SECONDS``
     - Number of seconds to wait between API requests.
   * - ``--num-retries NUM_RETRIES``
     - Number of times to retry a failing API request before raising an exception.
   * - ``--list-voices``
     - List the available voices.

List Available Voices
---------------------

To explore which voices are supported by your system:

.. code-block:: console

    $ audioarxiv --list-voices

Configuration File
------------------

All command-line options can be saved in a configuration file for reuse.
When the tool is run, it generates or loads settings from a config file stored locally.
The path to this file is printed in the logs when you run the tool with :code:`--id`.

This allows you to define and reuse your preferred settings (e.g. voice, volume, rate) without needing to type them every time.
