"""
audioarxiv
==========

audioarxiv is a Python package designed to make staying up to date with the latest research more accessible and
convenient.
It allows you to fetch research papers directly from `arXiv <https://arxiv.org>`_ and converts them into speech,
so you can listen to them on the go—whether you're commuting, working out, or simply prefer auditory learning.
With support for customizable text-to-speech settings and a streamlined interface, audioarxiv offers researchers,
students, and enthusiasts a hands-free way to engage with scientific literature.

**Please note**: the package is still in its early stages of development,
and some features may be limited or not fully mature yet.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from pandas import DataFrame

from . import audio, preprocess, resources

__version__ = "0.1.2""-rc78-post1"


def get_version_information() -> str:
    """Version information.

    Returns:
        str: Version information.
    """
    return __version__


def setup_logger(logger_: logging.Logger, outdir='.', label=None, log_level='INFO', print_version=False):
    """ Setup logging output: call at the start of the script to use

    Args:
        logger_ (logging.Logger): The logger instance to be configured.
        outdir (str): If supplied, write the logging output to outdir/label.log
        label (str): If supplied, write the logging output to outdir/label.log
        log_level (str, optional): ['debug', 'info', 'warning']
        Either a string from the list above, or an integer as specified
        in https://docs.python.org/2/library/logging.html#logging-levels
        print_version (bool): If true, print version information
    """
    if isinstance(log_level, str):
        try:
            level = getattr(logging, log_level.upper())
        except AttributeError as exc:
            raise ValueError(f'log_level {log_level} not understood') from exc
    else:
        level = int(log_level)

    logger_.propagate = False
    logger_.setLevel(level)

    if not any(isinstance(h, logging.StreamHandler) for h in logger_.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(name)s %(levelname)-8s: %(message)s', datefmt='%H:%M'))
        stream_handler.setLevel(level)
        logger_.addHandler(stream_handler)

    if not any(isinstance(h, logging.FileHandler) for h in logger_.handlers):
        if label:
            Path(outdir).mkdir(parents=True, exist_ok=True)
            log_file = f'{outdir}/{label}.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)-8s: %(message)s', datefmt='%H:%M'))

            file_handler.setLevel(level)
            logger_.addHandler(file_handler)

    for handler in logger_.handlers:
        handler.setLevel(level)

    if print_version:
        version = get_version_information()
        logger_.info('Running audioarxiv version: %s', version)


def loaded_modules_dict() -> dict:
    """Get the modules and the versions.

    Returns:
        dict: A dictionary of the modules and the versions.
    """
    module_names = list(sys.modules.keys())
    vdict = {}
    for key in module_names:
        if "." not in str(key):
            vdict[key] = str(getattr(sys.modules[key], "__version__", "N/A"))
    return vdict


def env_package_list(as_dataframe: bool = False) -> list | DataFrame:
    """Get the list of packages installed in the system prefix.

    If it is detected that the system prefix is part of a Conda environment,
    a call to ``conda list --prefix {sys.prefix}`` will be made, otherwise
    the call will be to ``{sys.executable} -m pip list installed``.

    Args:
        as_dataframe (bool): return output as a `pandas.DataFrame`

    Returns:
    Union[list, DataFrame]:
        If ``as_dataframe=False`` is given, the output is a `list` of `dict`,
        one for each package, at least with ``'name'`` and ``'version'`` keys
        (more if `conda` is used).
        If ``as_dataframe=True`` is given, the output is a `DataFrame`
        created from the `list` of `dicts`.
    """
    prefix = sys.prefix
    pkgs = []
    # if a conda-meta directory exists, this is a conda environment, so
    # use conda to print the package list
    conda_detected = (Path(prefix) / "conda-meta").is_dir()
    if conda_detected:
        try:
            pkgs = json.loads(subprocess.check_output([
                "conda",
                "list",
                "--prefix", prefix,
                "--json"
            ]))
        except (FileNotFoundError, subprocess.CalledProcessError):
            # When a conda env is in use but conda is unavailable
            conda_detected = False

    # otherwise try and use Pip
    if not conda_detected:
        try:
            import pip  # noqa: F401 # pylint: disable=unused-import, import-outside-toplevel
        except ModuleNotFoundError:  # no pip?
            # not a conda environment, and no pip, so just return
            # the list of loaded modules
            modules = loaded_modules_dict()
            pkgs = [{"name": x, "version": y} for x, y in modules.items()]
        else:
            pkgs = json.loads(subprocess.check_output([
                sys.executable,
                "-m", "pip",
                "list", "installed",
                "--format", "json",
            ]))

    # convert to recarray for storage
    if as_dataframe:
        return DataFrame(pkgs)
    return pkgs


logger = logging.getLogger('audioarxiv')
setup_logger(logger)

__all__ = [
    'audio',
    'preprocess',
    'resources',
    'logger',
    '__version__'
]
