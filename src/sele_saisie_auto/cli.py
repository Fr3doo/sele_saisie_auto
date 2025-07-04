"""Command-line interface utilities."""

from __future__ import annotations

import argparse

from sele_saisie_auto.logger_utils import LOG_LEVELS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Launch PSA Time automation")
    parser.add_argument(
        "-l",
        "--log-level",
        choices=list(LOG_LEVELS.keys()),
        help="Override log level",
    )
    return parser.parse_args(argv)
