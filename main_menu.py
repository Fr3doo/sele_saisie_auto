"""Main menu interface."""

from __future__ import annotations

import tkinter as tk

from gui_builder import (
    create_button_without_style,
    create_labeled_frame,
    create_modern_entry_with_grid,
    create_modern_entry_with_grid_for_password,
    create_modern_label_with_grid,
)
from launcher import run_psatime_with_credentials, start_configuration


def main_menu(cle_aes: bytes, log_file: str, encryption_service) -> None:
    """Display the main menu allowing credential entry."""
    menu = tk.Tk()
    menu.title("Program PSATime Auto")
    menu.resizable(False, False)
    menu.geometry("400x300")

    login_var = tk.StringVar()
    mdp_var = tk.StringVar()

    tk.Label(menu, text="Program PSATime Auto", font=("Segoe UI", 14)).pack(pady=10)
    credentials = create_labeled_frame(
        menu, text="Identifiants", padx=20, pady=10, padding=(10, 5)
    )
    create_modern_label_with_grid(credentials, text="Login:", row=0, col=0)
    login_entry = create_modern_entry_with_grid(
        credentials, var=login_var, row=0, col=1
    )
    create_modern_label_with_grid(credentials, text="@cgi.com", row=0, col=2)

    create_modern_label_with_grid(credentials, text="Mot de passe:", row=1, col=0)
    create_modern_entry_with_grid_for_password(credentials, var=mdp_var, row=1, col=1)

    launch = create_button_without_style(
        menu,
        text="Lancer votre PSATime",
        command=lambda: run_psatime_with_credentials(
            encryption_service, cle_aes, login_var, mdp_var, log_file, menu
        ),
    )
    launch.bind("<Return>", lambda _: launch.invoke())

    config_btn = create_button_without_style(
        menu,
        text="Configurer le lancement",
        command=lambda: [
            menu.destroy(),
            start_configuration(cle_aes, log_file, encryption_service),
        ],
    )
    config_btn.bind("<Return>", lambda _: config_btn.invoke())

    login_entry.focus()
    menu.mainloop()
