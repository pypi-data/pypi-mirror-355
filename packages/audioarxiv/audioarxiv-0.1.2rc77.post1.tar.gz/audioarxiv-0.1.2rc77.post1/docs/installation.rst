Installation
============

To install audioarxiv, you need Python 3.9 or higher. You can install the package using pip:

.. code-block:: console

      $ pip install audioarxiv

Requirements
------------

audioarxiv has a few dependencies that will be installed automatically with pip. These include:

- configargparse: for flexible command-line and config file parsing
- arxiv: to fetch paper metadata and content from `arXiv <https://arxiv.org>`_
- pyttsx3: a text-to-speech conversion library
- pymupdf: for parsing and extracting text from PDFs
- sympy: for handling mathematical expressions and symbols
- nltk: for natural language processing tasks like sentence tokenization
- pandas: for providing a data structure for handling tabular data
- platformdirs: for finding the right location to store configuration varies per platform.

Make sure you have an internet connection during installation to download all dependencies.

Development Version
-------------------

To install the latest development version directly from GitHub:

.. code-block:: console

   $ pip install git+https://github.com/isaac-cf-wong/audioarxiv.git
