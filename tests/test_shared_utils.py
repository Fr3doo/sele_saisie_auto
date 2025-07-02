import sys
from pathlib import Path

import pytest

# add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from shared_utils import get_log_file, setup_logs  # noqa: E402


def test_setup_logs_creates_path(tmp_path):
    log_dir = tmp_path / "logs"
    path = setup_logs(log_dir=str(log_dir), log_format="txt")
    assert str(log_dir) in path
    assert path.endswith(".txt")


def test_get_log_file_creates_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    file1 = get_log_file()
    file2 = get_log_file()
    assert file1 == file2
    assert file1.endswith(".html")


def test_setup_logs_invalid_format(tmp_path):
    log_dir = tmp_path / "logs"
    path = setup_logs(log_dir=str(log_dir), log_format="invalid")
    assert path.endswith(".txt")


def test_setup_logs_oserror(monkeypatch):
    def raise_oserror(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr("shared_utils.os.makedirs", raise_oserror)
    with pytest.raises(RuntimeError):
        setup_logs()


def test_setup_logs_generic_error(monkeypatch):
    def raise_value(*args, **kwargs):
        raise ValueError("nope")

    monkeypatch.setattr("shared_utils.os.makedirs", raise_value)
    with pytest.raises(RuntimeError):
        setup_logs()


def test_get_log_file_initializes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("shared_utils._log_file", None)
    log_file = get_log_file()
    assert log_file.endswith(".html")
