# pragma: no cover
"""Launcher module handling configuration and Selenium startup."""

from __future__ import annotations

import argparse
import multiprocessing
import tkinter as tk
from tkinter import messagebox, ttk

from encryption_utils import EncryptionService
from gui_builder import (
    create_a_frame,
    create_button_with_style,
    create_combobox_with_pack,
    create_Modern_entry_with_pack,
    create_Modern_label_with_pack,
    create_tab,
)
from logger_utils import LOG_LEVELS, close_logs, initialize_logger, write_log
from main_menu import main_menu
from read_or_write_file_config_ini_utils import read_config_ini, write_config_ini
from shared_utils import get_log_file

DEFAULT_SETTINGS = {"date_cible": "", "debug_mode": "INFO"}


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


def run_psatime(log_file: str, menu: tk.Tk) -> None:
    """Launch the Selenium automation after closing the menu."""
    menu.destroy()
    write_log("Launching PSA time", log_file, "INFO")
    import saisie_automatiser_psatime

    saisie_automatiser_psatime.main(log_file)


def run_psatime_with_credentials(
    encryption_service: EncryptionService,
    cle_aes: bytes,
    login_var: tk.StringVar,
    mdp_var: tk.StringVar,
    log_file: str,
    menu: tk.Tk,
) -> None:
    """Encrypt credentials and start PSA time after closing the menu."""
    login = login_var.get()
    password = mdp_var.get()
    if not login or not password:
        messagebox.showerror("Erreur", "Veuillez entrer vos identifiants")
        return

    data_login = encryption_service.chiffrer_donnees(login, cle_aes)
    data_pwd = encryption_service.chiffrer_donnees(password, cle_aes)
    encryption_service.stocker_en_memoire_partagee("memoire_nom", data_login)
    encryption_service.stocker_en_memoire_partagee("memoire_mdp", data_pwd)

    run_psatime(log_file, menu)


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
    create_Modern_label_with_pack(date_row, "Date cible:", side="left")
    create_Modern_entry_with_pack(date_row, date_var, side="left")

    debug_row = create_a_frame(frame, padding=(10, 10))
    create_Modern_label_with_pack(debug_row, "Log Level:", side="left")
    create_combobox_with_pack(debug_row, debug_var, values=list(LOG_LEVELS.keys()))

    def save() -> None:
        config["settings"]["date_cible"] = date_var.get()
        config["settings"]["debug_mode"] = debug_var.get()
        write_config_ini(config, log_file)
        messagebox.showinfo("Info", "Configuration enregistrée")
        root.destroy()
        main_menu(cle_aes, log_file, encryption_service)

    btn_row = create_a_frame(frame, padding=(10, 10))
    create_button_with_style(btn_row, "Sauvegarder", command=save)

    root.mainloop()


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = parse_args(argv)

    log_file = get_log_file()
    write_log("Initialisation", log_file, "INFO")

    config = read_config_ini(log_file)
    initialize_logger(config, log_level_override=args.log_level)

    multiprocessing.freeze_support()
    encryption_service = EncryptionService(log_file)
    cle_aes = encryption_service.generer_cle_aes(32)
    main_menu(cle_aes, log_file, encryption_service)
    close_logs(log_file)


if __name__ == "__main__":
    main()
