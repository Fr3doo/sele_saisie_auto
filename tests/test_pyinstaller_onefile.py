import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def _safe_rm(path: Path) -> None:
    """Supprime un fichier ou un dossier si présent, sans branches."""
    try:
        path.unlink(missing_ok=True)
    except IsADirectoryError:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(scope="session")
def pyinstaller_env():
    """Construit le binaire PyInstaller puis nettoie l'environnement."""
    root = Path(__file__).resolve().parents[1]
    dist_dir = root / "dist"
    build_dir = root / "build"
    spec_file = root / "main.spec"

    for p in (dist_dir, build_dir, spec_file):
        _safe_rm(p)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "src/sele_saisie_auto/main.py",
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        yield result, dist_dir, build_dir, spec_file
    finally:
        for p in (dist_dir, build_dir, spec_file):
            _safe_rm(p)


def test_pyinstaller_return_code(pyinstaller_env):
    result, *_ = pyinstaller_env
    assert result.returncode == 0, result.stdout


def test_pyinstaller_creates_binary(pyinstaller_env):
    _, dist_dir, *_ = pyinstaller_env
    binary = {"nt": "main.exe"}.get(os.name, "main")
    binary_path = dist_dir / binary
    assert binary_path.exists(), f"Missing {binary_path}"
