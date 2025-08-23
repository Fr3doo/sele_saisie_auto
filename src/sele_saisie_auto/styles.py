from __future__ import annotations

import tkinter as tk
from tkinter import ttk

COLORS: dict[str, str] = {
    "background": "#F5F6FA",
    "secondary": "#E8ECF5",
    "primary": "#2F54EB",
    "hover": "#4D70F0",
    "text": "#1E2A38",
    "danger": "#E43F5A",
    "success": "#2BB57B",
}


def setup_modern_style(root: tk.Misc, colors: dict[str, str] = COLORS) -> None:
    """Configure ttk styles used throughout the application."""
    if not hasattr(root, "tk"):
        return
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Modern.TFrame", background=colors["background"])
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
    )
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
            foreground=[("selected", colors["background"]), ("active", colors["text"])],
        )
    entry_opts = {"fieldbackground": colors["secondary"], "padding": [5, 5]}
    style.configure("Modern.TEntry", **entry_opts)
    style.configure("Settings.TEntry", **entry_opts)  # alias de fait pour compatibilité
    style.configure(
        "Modern.TCombobox",
        background=colors["secondary"],
        fieldbackground=colors["secondary"],
        padding=[5, 5],
    )
    button_opts = {
        "padding": [20, 10],
        "foreground": colors["background"],
        "font": ("Segoe UI", 10, "bold"),
    }
    style.configure("Modern.TButton", background=colors["primary"], **button_opts)
    style.configure("Danger.TButton", background=colors["danger"], **button_opts)
    if hasattr(style, "map"):
        style.map("Modern.TButton", background=[("active", colors["hover"])])
        style.map("Danger.TButton", background=[("active", colors["hover"])])
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
        font=("Segoe UI", 10, "bold"),
    )
