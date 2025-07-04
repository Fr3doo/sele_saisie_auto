import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto import __version__, cli  # noqa: E402


def test_help_displays_new_options(capsys):
    with pytest.raises(SystemExit):
        cli.parse_args(["--help"])
    out = capsys.readouterr().out
    assert "--version" in out
    assert "Automate PSA Time" in out


def test_version_option(capsys):
    with pytest.raises(SystemExit):
        cli.parse_args(["--version"])
    out = capsys.readouterr().out.strip()
    assert out.endswith(__version__)
