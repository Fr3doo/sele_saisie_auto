"""Launcher module handling configuration and Selenium startup."""

from __future__ import annotations

import multiprocessing
import tkinter as tk
from tkinter import messagebox, ttk

from sele_saisie_auto import cli, messages, saisie_automatiser_psatime
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.gui_builder import (
    create_a_frame,
    create_button_with_style,
    create_combobox_with_pack,
    create_modern_entry_with_pack,
    create_modern_label_with_pack,
    create_tab,
)
from sele_saisie_auto.logger_utils import LOG_LEVELS, initialize_logger
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.read_or_write_file_config_ini_utils import (
    read_config_ini,
    write_config_ini,
)
from sele_saisie_auto.shared_utils import get_log_file

DEFAULT_SETTINGS = {"date_cible": "", "debug_mode": "INFO"}


def run_psatime(log_file: str, menu: tk.Tk, logger: Logger | None = None) -> None:
    """Launch the Selenium automation after closing the menu."""
    menu.destroy()
    if logger is None:
        with Logger(log_file) as log:
            log.info("Launching PSA time")
            saisie_automatiser_psatime.main(log_file)
    else:
        logger.info("Launching PSA time")
        saisie_automatiser_psatime.main(log_file)


def run_psatime_with_credentials(
    encryption_service: EncryptionService,
    login_var: tk.StringVar,
    mdp_var: tk.StringVar,
    log_file: str,
    menu: tk.Tk,
    logger: Logger | None = None,
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

    run_psatime(log_file, menu, logger=logger)


def start_configuration(
    cle_aes: bytes, log_file: str, encryption_service: EncryptionService
) -> None:
    """Minimal configuration window."""

    config = read_config_ini(log_file)
    for key, val in DEFAULT_SETTINGS.items():
        config.setdefault("settings", {}).setdefault(key, val)

    root = tk.Tk()
    root.title("Configuration")
    root.geometry("400x200")
    style = ttk.Style(root)
    style.theme_use("clam")

    frame = create_tab(root, title="Paramètres")
    date_var = tk.StringVar(value=config["settings"].get("date_cible", ""))
    debug_var = tk.StringVar(value=config["settings"].get("debug_mode", "INFO"))

    date_row = create_a_frame(frame, padding=(10, 10))
    create_modern_label_with_pack(date_row, "Date cible:", side="left")
    create_modern_entry_with_pack(date_row, date_var, side="left")

    debug_row = create_a_frame(frame, padding=(10, 10))
    create_modern_label_with_pack(debug_row, "Log Level:", side="left")
    create_combobox_with_pack(debug_row, debug_var, values=list(LOG_LEVELS.keys()))

    def save() -> None:
        """Enregistre la configuration saisie."""
        config["settings"]["date_cible"] = date_var.get()
        config["settings"]["debug_mode"] = debug_var.get()
        write_config_ini(config, log_file)
        messagebox.showinfo("Info", messages.CONFIGURATION_SAVED)
        root.destroy()
        from sele_saisie_auto.main_menu import main_menu

        main_menu(cle_aes, log_file, encryption_service)

    btn_row = create_a_frame(frame, padding=(10, 10))
    create_button_with_style(btn_row, "Sauvegarder", command=save)

    root.mainloop()


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = cli.parse_args(argv)

    log_file = get_log_file()
    with Logger(log_file) as logger:
        logger.info("Initialisation")

        config = read_config_ini(log_file)
        initialize_logger(config, log_level_override=args.log_level)

        multiprocessing.freeze_support()
        with EncryptionService(log_file) as encryption_service:
            cle_aes = encryption_service.cle_aes
            from sele_saisie_auto.main_menu import main_menu

            main_menu(cle_aes, log_file, encryption_service)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
