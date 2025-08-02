"""Launcher module handling configuration and Selenium startup."""

from __future__ import annotations

import configparser
import multiprocessing
import tkinter as tk
from multiprocessing import shared_memory
from tkinter import messagebox, ttk
from typing import Callable, cast

from sele_saisie_auto import cli, messages, saisie_automatiser_psatime
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import Services, service_configurator_factory
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.enums import LogLevel
from sele_saisie_auto.gui_builder import (
    create_a_frame,
    create_button_with_style,
    create_combobox_with_pack,
    create_modern_entry_with_pack,
    create_modern_label_with_pack,
    create_tab,
)
from sele_saisie_auto.interfaces import LoggerProtocol
from sele_saisie_auto.logger_utils import LOG_LEVEL_CHOICES
from sele_saisie_auto.logging_service import Logger, LoggingConfigurator, get_logger
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.read_or_write_file_config_ini_utils import (
    read_config_ini,
    write_config_ini,
)
from sele_saisie_auto.resources.resource_manager import ResourceManager
from sele_saisie_auto.shared_utils import get_log_file

DEFAULT_SETTINGS = {"date_cible": "", "debug_mode": "INFO"}


def cleanup_memory_segments(memory_config: MemoryConfig | None = None) -> None:
    """Remove leftover shared memory segments.

    Parameters
    ----------
    memory_config:
        Names of the segments to remove. Defaults to :class:`MemoryConfig`.
    """

    cfg = memory_config or MemoryConfig()
    for name in (
        cfg.cle_name,
        cfg.data_name,
        cfg.login_name,
        cfg.password_name,
    ):
        try:
            mem = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            continue
        else:
            try:
                mem.close()
            finally:
                try:
                    mem.unlink()
                except FileNotFoundError:
                    pass


def run_psatime(
    log_file: str,
    menu: tk.Tk,
    logger: Logger | None = None,
    *,
    encryption_service: EncryptionService | Services | None = None,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Launch the Selenium automation after closing the menu."""
    menu.destroy()
    if logger is None:
        with get_logger(log_file) as log:
            _run_psa_time(
                log_file,
                cfg_loader=lambda: ConfigManager(log_file=log_file).load(),
                logger=log,
                encryption_service=encryption_service,
                headless=headless,
                no_sandbox=no_sandbox,
            )
    else:
        _run_psa_time(
            log_file,
            cfg_loader=lambda: ConfigManager(log_file=log_file).load(),
            logger=logger,
            encryption_service=encryption_service,
            headless=headless,
            no_sandbox=no_sandbox,
        )


def _run_psa_time(
    log_file: str,
    *,
    cfg_loader: Callable[[], AppConfig],
    logger: Logger,
    encryption_service: EncryptionService | Services | None,
    headless: bool,
    no_sandbox: bool,
) -> None:
    """Internal helper to initialize automation."""
    logger.info("Launching PSA time")
    cfg: AppConfig = cfg_loader()
    services: Services | None = None
    memory_config = None
    if isinstance(encryption_service, Services):
        services = encryption_service
        memory_config = services.encryption_service.memory_config
        service_configurator = service_configurator_factory(
            cfg, memory_config=memory_config
        )
    elif encryption_service is not None:
        memory_config = encryption_service.memory_config  # type: ignore[attr-defined]
        service_configurator = service_configurator_factory(
            cfg, memory_config=memory_config
        )
        waiter = service_configurator.create_waiter()
        browser_session = BrowserSession(log_file, cfg, waiter=waiter)
        login_handler = service_configurator.create_login_handler(
            log_file, encryption_service, browser_session  # type: ignore[arg-type]
        )
        services = Services(
            encryption_service,  # type: ignore[arg-type]
            browser_session,
            waiter,
            login_handler,
        )
    else:
        service_configurator = service_configurator_factory(cfg)

    automation = saisie_automatiser_psatime.PSATimeAutomation(
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
    orchestrator.run(headless=headless, no_sandbox=no_sandbox)


def run_psatime_with_credentials(
    encryption_service: EncryptionService,
    login_var: tk.StringVar,
    mdp_var: tk.StringVar,
    log_file: str,
    menu: tk.Tk,
    logger: Logger | None = None,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Encrypt credentials and start PSA time after closing the menu."""
    login = login_var.get()
    password = mdp_var.get()
    if not login or not password:
        messagebox.showerror("Erreur", messages.ASK_CREDENTIALS)
        return

    cle_aes = encryption_service.cle_aes
    if cle_aes is None:
        messagebox.showerror("Erreur", messages.MISSING_AES_KEY)
        return

    data_login = encryption_service.chiffrer_donnees(login, cle_aes)
    data_pwd = encryption_service.chiffrer_donnees(password, cle_aes)
    encryption_service.store_credentials(data_login, data_pwd)

    run_psatime(
        log_file,
        menu,
        logger=logger,
        encryption_service=encryption_service,
        headless=headless,
        no_sandbox=no_sandbox,
    )


def start_configuration(
    cle_aes: bytes,
    log_file: str,
    encryption_service: EncryptionService,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Minimal configuration window."""

    raw_cfg = read_config_ini(log_file)
    if isinstance(raw_cfg, configparser.ConfigParser):
        config: dict[str, dict[str, str]] = {
            section: dict(raw_cfg.items(section)) for section in raw_cfg.sections()
        }
    else:
        config = raw_cfg
    for key, val in DEFAULT_SETTINGS.items():
        config.setdefault("settings", {}).setdefault(key, val)

    root = tk.Tk()
    root.title("Configuration")
    root.geometry("400x200")

    style = ttk.Style(root)
    style.theme_use("clam")

    notebook: ttk.Notebook | tk.Tk
    if hasattr(root, "tk"):
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)
    else:  # fallback for DummyRoot in tests
        notebook = root
    frame = create_tab(cast(ttk.Notebook, notebook), title="Paramètres")

    date_var = tk.StringVar(value=config["settings"].get("date_cible", ""))
    debug_var = tk.StringVar(value=config["settings"].get("debug_mode", "INFO"))

    date_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_modern_label_with_pack(date_row, "Date cible:", side="left")
    create_modern_entry_with_pack(date_row, date_var, side="left")

    debug_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_modern_label_with_pack(debug_row, "Log Level:", side="left")
    create_combobox_with_pack(debug_row, debug_var, values=LOG_LEVEL_CHOICES)

    def save() -> None:
        """Enregistre la configuration saisie."""
        config["settings"]["date_cible"] = date_var.get()
        debug_val: str | LogLevel = debug_var.get()
        if isinstance(debug_val, LogLevel):
            debug_val = debug_val.value
        config["settings"]["debug_mode"] = debug_val
        if isinstance(raw_cfg, configparser.ConfigParser):
            if not raw_cfg.has_section("settings"):
                raw_cfg.add_section("settings")
            raw_cfg.set("settings", "date_cible", config["settings"]["date_cible"])
            raw_cfg.set("settings", "debug_mode", debug_val)
            write_config_ini(raw_cfg, log_file)
        else:
            write_config_ini(config, log_file)
        messagebox.showinfo("Info", messages.CONFIGURATION_SAVED)
        root.destroy()
        from sele_saisie_auto.main_menu import main_menu

        main_menu(
            cle_aes,
            log_file,
            encryption_service,
            headless=headless,
            no_sandbox=no_sandbox,
        )

    btn_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_button_with_style(btn_row, "Sauvegarder", command=save)

    root.mainloop()


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = cli.parse_args(argv)

    log_file = get_log_file()
    with get_logger(log_file) as logger:
        logger.info("Initialisation")

        config = read_config_ini(log_file)
        LoggingConfigurator.setup(log_file, args.log_level, config)

        multiprocessing.freeze_support()
        cleanup_memory_segments()
        with EncryptionService(log_file) as encryption_service:
            cle_aes = cast(bytes, encryption_service.cle_aes)
            from sele_saisie_auto.main_menu import main_menu

            main_menu(
                cle_aes,
                log_file,
                encryption_service,
                headless=args.headless,
                no_sandbox=args.no_sandbox,
            )


if __name__ == "__main__":
    main()
