import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


@pytest.fixture(scope="session")
def pyinstaller_env(tmp_path_factory):
    """Construit le binaire PyInstaller et fournit le chemin du binaire."""
    pytest.importorskip("PyInstaller")

    root = Path(__file__).resolve().parents[1]
    dist_dir = tmp_path_factory.mktemp("dist")
    build_dir = tmp_path_factory.mktemp("build")
    spec_dir = tmp_path_factory.mktemp("spec")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--name",
            "main",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            "--specpath",
            str(spec_dir),
            "src/sele_saisie_auto/main.py",
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    binary = {"nt": "main.exe"}.get(os.name, "main")
    yield result, dist_dir / binary


def test_pyinstaller_return_code(pyinstaller_env):
    result, _ = pyinstaller_env
    assert result.returncode == 0, f"{result.stdout}\n{result.args}"


def test_pyinstaller_creates_binary(pyinstaller_env):
    _, binary_path = pyinstaller_env
    assert binary_path.exists(), f"Missing {binary_path}"
