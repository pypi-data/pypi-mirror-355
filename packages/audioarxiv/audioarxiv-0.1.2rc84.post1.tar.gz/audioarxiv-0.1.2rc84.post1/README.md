# 🎧 audioarxiv

[![PyPI version](https://badge.fury.io/py/audioarxiv.svg)](https://pypi.org/project/audioarxiv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/isaac-cf-wong/audioarxiv/CI.yml?branch=main)](https://github.com/isaac-cf-wong/audioarxiv/actions)
[![codecov](https://codecov.io/gh/isaac-cf-wong/audioarxiv/branch/main/graph/badge.svg)](https://codecov.io/gh/isaac-cf-wong/audioarxiv)
[![Python Version](https://img.shields.io/pypi/pyversions/audioarxiv)](https://pypi.org/project/audioarxiv/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Documentation Status](https://img.shields.io/badge/documentation-online-brightgreen)](https://isaac-cf-wong.github.io/audioarxiv/)
[![DOI](https://zenodo.org/badge/956387048.svg)](https://doi.org/10.5281/zenodo.15251111)

📚 **Documentation**: [https://isaac-cf-wong.github.io/audioarxiv/](https://isaac-cf-wong.github.io/audioarxiv/)

**Turn arXiv papers into audio.**
`audioarxiv` lets you fetch the research papers from arXiv and read them aloud.

---

## 🚀 Features

- 🔍 Search and retrieve papers using the arXiv API
- 📄 Extract and parse the content from PDF (excluding title/abstract)
- 🗣️ Convert text to speech with natural voice output
- 🧠 Great for passive learning while commuting or doing chores

---

## 📦 Installation

Install from [PyPI](https://pypi.org/project/audioarxiv/):

```bash
pip install audioarxiv
```

---

## 🛠 Usage

```bash
audioarxiv --id "<arxiv id>"
```

### 🎙️ Text-to-Speech Options

You can customize the voice engine using `pyttsx3` by specifying the speaking rate, volume, voice, and pause between sentences.

```bash
audioarxiv --id "<arxiv id>" --rate <rate> --volume <volume> --voice "<voice>" --pause-seconds <pause-seconds>
```

- `rate`: Number of words per minutes. Defaults to 140.
- `volume`: Volume of the audio. Defaults to 0.9.
- `voice`: Voice of the audio. Defaults to the pyttsx3 default voice.
- `pause-seconds`: Number of seconds to pause between sentences.

The settings are saved, so you only need to provide your preferred settings once.

## Contributing

Contributions and suggestions are welcome! Whether it's fixing bugs, improving documentation, or adding new features, your help is appreciated.

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

To get started:

- Fork the repository
- Create a new branch for your changes
- Submit a pull request

If you're unsure where to begin, feel free to open an issue or ask for guidance!
