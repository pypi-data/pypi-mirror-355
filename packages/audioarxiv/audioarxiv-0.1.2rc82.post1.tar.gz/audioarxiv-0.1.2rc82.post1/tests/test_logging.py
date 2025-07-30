from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

from audioarxiv import (env_package_list, get_version_information,
                        loaded_modules_dict, setup_logger)


def test_get_version_information():
    version = get_version_information()
    assert isinstance(version, str)
    assert len(version) > 0


def test_setup_logger_creates_handlers():
    logger = logging.getLogger("test_logger")
    logger.handlers = []  # Clear any existing handlers

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logger(logger, outdir=tmpdir, label="test", log_level="INFO", print_version=True)

        # Verify handlers
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

        # Verify log file content
        log_path = Path(tmpdir) / "test.log"
        assert log_path.exists()
        with open(log_path) as f:
            content = f.read()
        assert "audioarxiv version" in content.lower()


def test_loaded_modules_dict_structure():
    modules = loaded_modules_dict()
    assert isinstance(modules, dict)
    for k, v in modules.items():
        assert isinstance(k, str)
        assert isinstance(v, str)


@patch("audioarxiv.subprocess.check_output")
def test_env_package_list_conda(mock_sub_proc):
    mock_pkgs = [
        {"name": "numpy", "version": "1.24.0"},
        {"name": "pandas", "version": "2.0.0"},
    ]
    mock_sub_proc.return_value = json.dumps(mock_pkgs).encode("utf-8")

    with patch("pathlib.Path.is_dir", return_value=True):  # Simulate conda-meta directory
        result = env_package_list()
        assert isinstance(result, list)
        assert all("name" in pkg and "version" in pkg for pkg in result)


@patch("audioarxiv.subprocess.check_output")
def test_env_package_list_pip(mock_sub_proc):
    mock_pkgs = [
        {"name": "requests", "version": "2.31.0"},
        {"name": "flask", "version": "3.0.0"},
    ]
    mock_sub_proc.return_value = json.dumps(mock_pkgs).encode("utf-8")

    with patch("pathlib.Path.is_dir", return_value=False):  # Simulate no conda-meta
        result = env_package_list()
        assert isinstance(result, list)
        assert all("name" in pkg and "version" in pkg for pkg in result)


@patch("audioarxiv.subprocess.check_output")
def test_env_package_list_as_dataframe(mock_sub_proc):
    mock_pkgs = [
        {"name": "torch", "version": "2.1.0"},
        {"name": "scipy", "version": "1.11.0"},
    ]
    mock_sub_proc.return_value = json.dumps(mock_pkgs).encode("utf-8")

    with patch("pathlib.Path.is_dir", return_value=False):
        df = env_package_list(as_dataframe=True)
        assert df.shape[0] == 2  # type: ignore[attr-defined]
        assert "name" in df.columns  # type: ignore[attr-defined]
        assert "version" in df.columns  # type: ignore[attr-defined]
