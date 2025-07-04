"""Export dependencies from Poetry into requirements.txt."""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path


def main() -> int:
    """Run ``poetry export`` to generate requirements.txt."""
    root = Path(__file__).resolve().parents[1]
    output = root / "requirements.txt"
    cmd = [
        "poetry",
        "export",
        "-f",
        "requirements.txt",
        "--output",
        str(output),
        "--without-hashes",
    ]
    result = subprocess.run(cmd, check=False, shell=False)  # nosec B603
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
