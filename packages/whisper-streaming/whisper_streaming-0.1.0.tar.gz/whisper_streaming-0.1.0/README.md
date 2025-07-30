# whisper-streaming

[![audit.yml](https://github.com/nkaaf/ufal-whisper_streaming/actions/workflows/audit.yml/badge.svg)](https://github.com/nkaaf/ufal-whisper_streaming/actions/workflows/audit.yml)

Providing easy-to-use and extensible STT (Speech-To-Text) implementation with Whisper-like ASR (
Automatic Speech Recognition) models.

> [!WARNING]  
> This project is currently in Alpha State. It is probably not stable over a long time and can have
> unexpected errors. You could help to push this project out of Alpha and Beta state by testing and
> reviewing it. Thanks!

## Index

* [Appreciation](#appreciation)
* [Components](#components)
    * [Backend](#backend)
    * [Receiver](#receiver)
    * [Sender](#sender)
* [Installation](#installation)
* [Development](#development)
    * [Installation of Prerequisites](#installation-of-prerequisites)
    * [Build executables](#build-executables)
* [Documentation](#documentation)
    * [Installation of Prerequisites](#installation-of-prerequisites-1)
    * [Build](#build)
* [License](#license)
* [Appendix](#appendix)
    * [Python venv](#python-venv)
    * [Links](#links)

## Appreciation

This project is the result of a rework of the ideas and prototype implementation created
by [Dominik Macháček](https://ufal.mff.cuni.cz/dominik-machacek), [Raj Dabre](https://prajdabre.github.io/), [Ondřej Bojar](https://ufal.mff.cuni.cz/ondrej-bojar) ([Original Repository](https://github.com/ufal/whisper_streaming)).
It is neither official nor fully API- and function-compatible with its original implementation.

Please have a look at their publication:
[ACL Anthology](https://aclanthology.org/2023.ijcnlp-demo.3/)
[Bibtex citation](https://aclanthology.org/2023.ijcnlp-demo.3.bib)

```
@inproceedings{machacek-etal-2023-turning,
    title = "Turning Whisper into Real-Time Transcription System",
    author = "Mach{\'a}{\v{c}}ek, Dominik  and
      Dabre, Raj  and
      Bojar, Ond{\v{r}}ej",
    editor = "Saha, Sriparna  and
      Sujaini, Herry",
    booktitle = "Proceedings of the 13th International Joint Conference on Natural Language Processing and the 3rd Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics: System Demonstrations",
    month = nov,
    year = "2023",
    address = "Bali, Indonesia",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.ijcnlp-demo.3",
    pages = "17--24",
}
```

With the usage of this project, you agree to the license terms, found in the [License](#license)
chapter.
This project is not affiliated with the paper, original implementation or their authors. It is just
reimplementing their ideas in a more modern und easier to use and adapt way, respecting the license
agreement.

## Components

### Backend

Currently following backends are implemented:

* [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)

### Receiver

"Receiver" are mechanisms to input data into the ASR model. Out-of-the-box support for:

* ALSA (Advanced Linux Sound Architecture)
* File - Audio file

### Sender

"Sender" are mechanisms to output data out of the ASR mode. Out-of-the-box support for:

* Print - Simple console output via "print"
* WebSocket (Client) - Output via network protocol

## Installation

This library can be easily installed with pip:

```bash
pip install whisper-streaming
```

The integration of different backends are installed via following extras:
* [all] - installs all backends
* [faster-whisper] - [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)

## Development

### Installation of Prerequisites

* Python 3 (latest) (https://www.python.org/downloads)
* Python venv (optional, recommended) <sub>[GoTo Installation](#python-venv)</sub>
* Installation of development requirements:

```bash
pip install -r requirements/dev/requirements.txt
```

* Installation of requirements:

```bash
pip install -r requirements/library/requirements.txt
```

* backend requirements:

```bash
pip install -r requirements/library/requirements_faster_whisper.txt
```

### Build executables

```bash
python3 -m build
```

## Documentation

### Installation of Prerequisites

* Python 3 (latest) (https://www.python.org/downloads)
* Python venv (optional, recommended) <sub>[GoTo Installation](#python-venv)</sub>
* Installation of requirements:

```bash
pip install -r requirements/docs/requirements.txt
```

### Build

```bash
rm -rf docs/_build
sphinx-build -M html docs/ docs/_build
```

If the developer documentation should be built, the following script can be used:

```bash
rm -rf docs/_build
sphinx-build -M html docs/ docs/_build -t Internal
```

## License

This project is published
under [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0) - please comply
with it, if you use/modify/distribute it. The license can be found in "LICENSE". The original
implementation is published under [MIT](https://mit-license.org/) and is mentioned at places in this
project where it still applies. The license can be found in "LICENSE-MIT". You have to distribute at
least these both licenses - in addition to your compliant license.

## Appendix

## Python venv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools
```

## Links

* [Project Home](https://github.com/nkaaf/ufal-whisper_streaming)
* [Original Implementation](https://github.com/ufal/whisper_streaming)
* [Original Paper](https://aclanthology.org/2023.ijcnlp-demo.3.pdf)
