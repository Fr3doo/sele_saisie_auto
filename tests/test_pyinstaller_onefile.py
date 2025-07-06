import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow


def test_pyinstaller_build_onefile():
    root = Path(__file__).resolve().parents[1]
    dist_dir = root / "dist"
    build_dir = root / "build"
    spec_file = root / "main.spec"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()

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
    assert result.returncode == 0, result.stdout

    binary_name = "main.exe" if os.name == "nt" else "main"
    binary_path = dist_dir / binary_name
    assert binary_path.exists(), f"Missing {binary_path}"

    binary_path.unlink()
    if dist_dir.exists() and not any(dist_dir.iterdir()):
        dist_dir.rmdir()
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()
