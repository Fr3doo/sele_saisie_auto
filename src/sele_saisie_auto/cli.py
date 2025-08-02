"""Command-line interface utilities."""

from __future__ import annotations

import argparse
import getpass
from typing import cast

import sele_saisie_auto.shared_utils as shared_utils
from sele_saisie_auto import __version__
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import service_configurator_factory
from sele_saisie_auto.interfaces import LoggerProtocol
from sele_saisie_auto.logger_utils import LOG_LEVEL_CHOICES
from sele_saisie_auto.logging_service import LoggingConfigurator, get_logger
from sele_saisie_auto.orchestration import AutomationOrchestrator
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
        choices=LOG_LEVEL_CHOICES,
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
        "--cleanup-mem",
        action="store_true",
        help="Remove leftover shared memory segments and exit",
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
    if args.cleanup_mem:
        from sele_saisie_auto.launcher import cleanup_memory_segments

        cleanup_memory_segments()
        return
    log_file = get_log_file()
    with get_logger(log_file) as logger:
        cfg = ConfigManager(log_file=log_file).load()
        LoggingConfigurator.setup(log_file, args.log_level, cfg.raw)

        service_configurator = service_configurator_factory(cfg)
        services = service_configurator.build_services(log_file)

        enc = services.encryption_service
        if not getattr(cfg, "encrypted_login", None) or not getattr(
            cfg, "encrypted_mdp", None
        ):
            login = input("Login: ")
            password = getpass.getpass("Password: ")
            cle_aes = getattr(enc, "cle_aes", None)
            if cle_aes is None:
                enc.__enter__()
                cle_aes = enc.cle_aes
            if cle_aes is None:  # pragma: no cover - defensive
                raise RuntimeError("AES key not initialized")
            data_login = enc.chiffrer_donnees(login, cle_aes)
            data_pwd = enc.chiffrer_donnees(password, cle_aes)
            enc.store_credentials(data_login, data_pwd)

        automation = PSATimeAutomation(
            log_file,
            cfg,
            logger=logger,
            services=services,
        )
        orchestrator = AutomationOrchestrator.from_components(
            automation.resource_manager,
            automation.page_navigator,
            service_configurator,
            automation.context,
            cast(LoggerProtocol, automation.logger),
        )
        orchestrator.run(headless=args.headless, no_sandbox=args.no_sandbox)


def cli_main(
    log_file: str | None = None,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Entry point used by the ``psatime-auto`` console script."""

    if log_file is not None:
        shared_utils._log_file = log_file

    argv: list[str] = []
    if headless:
        argv.append("--headless")
    if no_sandbox:
        argv.append("--no-sandbox")
    main(argv)


__all__ = ["parse_args", "main", "cli_main"]
