from __future__ import annotations

import tkinter as tk
from tkinter import ttk

"""Central definition of the application's colour palette."""

# Palette inspirée de Material/Flat design pour une interface moderne.
COLORS: dict[str, str] = {
    "background": "#F5F6FA",
    "secondary": "#E8ECF5",
    "primary": "#2F54EB",
    "hover": "#4D70F0",
    "text": "#1E2A38",
    "danger": "#E43F5A",
    "success": "#2BB57B",
    "on_primary": "#FFFFFF",
}


def setup_modern_style(root: tk.Misc, colors: dict[str, str] = COLORS) -> None:
    """Configure ttk styles for a consistent modern look."""

    if not hasattr(root, "tk"):
        # ``root`` is not a Tk widget; ignore silently to keep DRY/KISS.
        return

    style = ttk.Style(root)
    style.theme_use("clam")

    # Surfaces de base
    root.configure(bg=colors["background"])  # type: ignore[call-arg]
    style.configure("Modern.TFrame", background=colors["background"])

    # Typographie et texte
    style.configure(
        "Modern.TLabel",
        background=colors["background"],
        foreground=colors["text"],
        font=("Segoe UI", 10),
    )
    style.configure(
        "Title.TLabel",
        font=("Segoe UI", 11, "bold"),
        foreground=colors["primary"],
        background=colors["background"],
    )

    # Notebook et onglets
    style.configure("Modern.TNotebook", background=colors["background"])
    style.configure(
        "Modern.TNotebook.Tab",
        padding=[15, 5],
        font=("Segoe UI", 9),
        background=colors["secondary"],
        foreground=colors["text"],
    )
    if hasattr(style, "map"):
        style.map(
            "Modern.TNotebook.Tab",
            background=[("selected", colors["primary"]), ("active", colors["hover"])],
            foreground=[("selected", colors["on_primary"]), ("active", colors["text"])],
        )

    # Zones de saisie et combobox
    entry_opts = {"fieldbackground": colors["secondary"], "padding": [5, 5]}
    style.configure("Modern.TEntry", **entry_opts)
    style.configure("Settings.TEntry", **entry_opts)  # compatibilité
    style.configure(
        "Modern.TCombobox",
        background=colors["secondary"],
        fieldbackground=colors["secondary"],
        padding=[5, 5],
    )

    # Boutons
    button_opts = {
        "padding": [20, 10],
        "foreground": colors["on_primary"],
        "font": ("Segoe UI", 10, "bold"),
    }
    style.configure("Modern.TButton", background=colors["primary"], **button_opts)
    style.configure("Danger.TButton", background=colors["danger"], **button_opts)
    if hasattr(style, "map"):
        style.map("Modern.TButton", background=[("active", colors["hover"])])
        style.map("Danger.TButton", background=[("active", colors["hover"])])

    # Cadres paramétrage
    style.configure(
        "Parametres.TLabelframe",
        background=colors["background"],
        padding=10,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Parametres.TLabelframe.Label",
        background=colors["background"],
        foreground=colors["text"],
        font=("Segoe UI", 10, "bold"),
    )
