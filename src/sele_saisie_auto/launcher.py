"""Launcher module handling configuration and Selenium startup."""

from __future__ import annotations

import configparser
import multiprocessing
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, cast

from sele_saisie_auto import cli, messages, saisie_automatiser_psatime
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.gui_builder import (
    create_a_frame,
    create_button_with_style,
    create_combobox_with_pack,
    create_modern_entry_with_pack,
    create_modern_label_with_pack,
    create_tab,
)
from sele_saisie_auto.logger_utils import LOG_LEVELS
from sele_saisie_auto.logging_service import Logger, LoggingConfigurator, get_logger
from sele_saisie_auto.read_or_write_file_config_ini_utils import (
    read_config_ini,
    write_config_ini,
)
from sele_saisie_auto.shared_utils import get_log_file

DEFAULT_SETTINGS = {"date_cible": "", "debug_mode": "INFO"}


def run_psatime(
    log_file: str,
    menu: tk.Tk,
    logger: Logger | None = None,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Launch the Selenium automation after closing the menu."""
    menu.destroy()
    if logger is None:
        with get_logger(log_file) as log:
            log.info("Launching PSA time")
            cfg = ConfigManager(log_file=log_file).load()
            automation = saisie_automatiser_psatime.PSATimeAutomation(
                log_file,
                cfg,
                logger=log,
            )
            automation.run(headless=headless, no_sandbox=no_sandbox)
    else:
        logger.info("Launching PSA time")
        cfg = ConfigManager(log_file=log_file).load()
        automation = saisie_automatiser_psatime.PSATimeAutomation(
            log_file,
            cfg,
            logger=logger,
        )
        automation.run(headless=headless, no_sandbox=no_sandbox)


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

    if hasattr(root, "tk"):
        notebook: Any = ttk.Notebook(root)  # pragma: no cover - UI init
        notebook.pack(fill="both", expand=True)  # pragma: no cover - UI init
    else:  # fallback for DummyRoot in tests
        notebook: Any = root
    frame = create_tab(notebook, title="Paramètres")
    date_var = tk.StringVar(value=config["settings"].get("date_cible", ""))
    debug_var = tk.StringVar(value=config["settings"].get("debug_mode", "INFO"))

    date_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_modern_label_with_pack(date_row, "Date cible:", side="left")
    create_modern_entry_with_pack(date_row, date_var, side="left")

    debug_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_modern_label_with_pack(debug_row, "Log Level:", side="left")
    create_combobox_with_pack(debug_row, debug_var, values=list(LOG_LEVELS.keys()))

    def save() -> None:
        """Enregistre la configuration saisie."""
        config["settings"]["date_cible"] = date_var.get()
        config["settings"]["debug_mode"] = debug_var.get()
        if isinstance(raw_cfg, configparser.ConfigParser):
            if not raw_cfg.has_section("settings"):
                raw_cfg.add_section("settings")
            raw_cfg.set("settings", "date_cible", config["settings"]["date_cible"])
            raw_cfg.set("settings", "debug_mode", config["settings"]["debug_mode"])
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


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
