"""Command-line interface utilities."""

from __future__ import annotations

import argparse

from sele_saisie_auto import __version__
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import ServiceConfigurator
from sele_saisie_auto.logger_utils import LOG_LEVELS, initialize_logger
from sele_saisie_auto.logging_service import get_logger
from sele_saisie_auto.saisie_automatiser_psatime import PSATimeAutomation
from sele_saisie_auto.shared_utils import get_log_file


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


def main(argv: list[str] | None = None) -> None:
    """Run the automation from the command line."""

    args = parse_args(argv)
    log_file = get_log_file()
    with get_logger(log_file) as logger:
        cfg = ConfigManager(log_file=log_file).load()
        initialize_logger(cfg.raw, log_level_override=args.log_level)

        service_configurator = ServiceConfigurator(cfg)
        services = service_configurator.build_services(log_file)

        automation = PSATimeAutomation(
            log_file,
            cfg,
            logger=logger,
            services=services,
        )
        automation.run(headless=args.headless, no_sandbox=args.no_sandbox)


__all__ = ["parse_args", "main"]
