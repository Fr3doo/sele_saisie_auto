from __future__ import annotations

from tkinter import Tk, ttk

COLORS = {
    "background": "#f5f5f5",
    "secondary": "#e6e6e6",
    "primary": "#1976D2",
    "hover": "#1565C0",
    "text": "#333333",
}


def setup_modern_style(root: Tk, colors: dict[str, str] = COLORS) -> None:
    """Configure les styles ttk utilisés dans l'interface."""
    try:
        style = ttk.Style(root)
    except Exception:  # pragma: no cover - environnement de test sans Tk
        return
    style.theme_use("clam")

    # Containers généraux
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
            foreground=[("selected", colors["background"]), ("active", colors["text"])],
        )

    # Entrées et combobox
    style.configure(
        "Modern.TEntry",
        fieldbackground=colors["secondary"],
        padding=[5, 5],
    )
    style.configure(
        "Settings.TEntry",
        fieldbackground=colors["secondary"],
        padding=[5, 5],
    )
    style.configure(
        "Modern.TCombobox",
        background=colors["secondary"],
        fieldbackground=colors["secondary"],
        padding=[5, 5],
    )

    # Boutons
    style.configure(
        "Modern.TButton",
        padding=[20, 10],
        background=colors["primary"],
        foreground=colors["background"],
        font=("Segoe UI", 10, "bold"),
    )
    if hasattr(style, "map"):
        style.map("Modern.TButton", background=[("active", colors["hover"])])

    # LabelFrame Paramètres
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
