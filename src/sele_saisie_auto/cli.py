"""Command-line interface utilities."""

from __future__ import annotations

import argparse

from sele_saisie_auto import __version__
from sele_saisie_auto.logger_utils import LOG_LEVELS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=("Automate PSA Time timesheet entry via Selenium and a minimal GUI")
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=list(LOG_LEVELS.keys()),
        help="Override log level",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the browser in headless mode",
    )
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Disable the browser sandbox",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program version and exit",
    )
    return parser.parse_args(argv)
