"""Main menu interface."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.gui_builder import (
    create_button_without_style,
    create_labeled_frame,
    create_modern_entry_with_grid,
    create_modern_entry_with_grid_for_password,
    create_modern_label_with_grid,
)
from sele_saisie_auto.launcher import run_psatime_with_credentials, start_configuration


def main_menu(
    cle_aes: bytes,
    log_file: str,
    encryption_service: EncryptionService,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Display the main menu allowing credential entry."""
    menu = tk.Tk()
    menu.title("Program PSATime Auto")
    menu.resizable(False, False)
    menu.geometry("400x300")

    # Conteneur ttk pour satisfaire les helpers typés « ttk.Widget »
    root_frame = ttk.Frame(menu)
    root_frame.pack(fill="both", expand=True)

    login_var = tk.StringVar()
    mdp_var = tk.StringVar()

    tk.Label(menu, text="Program PSATime Auto", font=("Segoe UI", 14)).pack(pady=10)
    credentials = create_labeled_frame(
        root_frame,
        text="Identifiants",
        padx=20,
        pady=10,
        padding=(10, 5, 10, 5),  # 4 valeurs requises
    )
    create_modern_label_with_grid(credentials, text="Login:", row=0, col=0)
    login_entry = create_modern_entry_with_grid(
        credentials, var=login_var, row=0, col=1
    )
    create_modern_label_with_grid(credentials, text="@cgi.com", row=0, col=2)

    create_modern_label_with_grid(credentials, text="Mot de passe:", row=1, col=0)
    create_modern_entry_with_grid_for_password(credentials, var=mdp_var, row=1, col=1)

    # Fonction séparée pour éviter le lambda qui retournait une liste
    def launch_psatime() -> None:
        """Démarre PSATime avec les identifiants saisis."""
        run_psatime_with_credentials(
            encryption_service,
            login_var,
            mdp_var,
            log_file,
            menu,
            headless=headless,
            no_sandbox=no_sandbox,
    )

    launch = create_button_without_style(
        root_frame,
        text="Lancer votre PSATime",
        command=launch_psatime,          
    )
    launch.bind("<Return>", lambda _: launch.invoke())

    # Fonction séparée pour éviter le lambda qui retournait une liste
    def open_config() -> None:
        menu.destroy()
        start_configuration(
            cle_aes,
            log_file,
            encryption_service,
            headless=headless,
            no_sandbox=no_sandbox,
        )

    config_btn = create_button_without_style(
        root_frame,
        text="Configurer le lancement",
        command=open_config,
    )
    config_btn.bind("<Return>", lambda _: config_btn.invoke())

    login_entry.focus()
    menu.mainloop()
