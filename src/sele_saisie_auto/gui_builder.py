# gui_builder.py

"""Fonctions utilitaires pour la création de widgets Tkinter."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any, Literal

# Types lisibles -----------------------------------------------------------
Orient = Literal["horizontal", "vertical"]
PackFill = Literal["none", "x", "y", "both"]
Side = Literal["left", "right", "top", "bottom"]
Padding = tuple[int, int, int, int]


# Helpers internes (réduisent la complexité des fonctions publiques) -------
def _frame_kwargs(style: str, padding: Padding | None) -> dict[str, Any]:
    """Construire les kwargs pour ttk.Frame/LabelFrame avec padding optionnel."""
    return {"style": style, **({"padding": padding} if padding is not None else {})}


def _pack(
    widget: tk.Widget,
    *,
    side: Side | None = None,
    fill: PackFill | None = None,
    expand: bool = True,
    padx: int = 0,
    pady: int = 0,
    ipady: int | None = None,
) -> None:
    """Appliquer pack() en ignorant proprement les valeurs None."""
    opts: dict[str, Any] = {"expand": expand, "padx": padx, "pady": pady}
    if side is not None:
        opts["side"] = side
    if fill is not None:
        opts["fill"] = fill
    if ipady is not None:
        opts["ipady"] = ipady
    widget.pack(**opts)


# Widgets simples ----------------------------------------------------------
def seperator_ttk(
    menu: ttk.Widget,
    orient: Orient = "horizontal",
    fill: PackFill = "x",
    padx: int = 10,
    pady: int = 5,
) -> None:
    """Ajouter un séparateur ttk à ``menu``."""
    separator = ttk.Separator(menu, orient=orient)
    separator.pack(fill=fill, padx=padx, pady=pady)


def create_tab(
    notebook: ttk.Notebook, title: str, style: str = "Modern.TFrame", padding: int = 20
) -> ttk.Frame:
    """Créer un onglet dans ``notebook``."""
    if not hasattr(notebook, "add"):
        raise AttributeError("Notebook object must implement an 'add' method")

    tab_frame = ttk.Frame(notebook, style=style, padding=padding)
    notebook.add(tab_frame, text=title)
    return tab_frame


def create_title_label_with_grid(
    frame: ttk.Frame,
    text: str,
    row: int,
    col: int,
    style: str = "Title.TLabel",
    padx: int = 5,
    pady: int = 5,
    sticky: str = "w",
) -> ttk.Label:
    """Créer un label de titre positionné avec ``grid``."""
    title_label = ttk.Label(frame, text=text, style=style)
    title_label.grid(row=row, column=col, padx=padx, pady=pady, sticky=sticky)
    return title_label


# ↓ Fonctions initialement en complexité B, maintenant A -------------------
def create_a_frame(
    parent: ttk.Widget,
    style: str = "Modern.TFrame",
    side: Side | None = None,
    fill: PackFill = "both",
    expand: bool = True,
    padx: int = 0,
    pady: int = 0,
    padding: Padding | None = None,
) -> ttk.Frame:
    """Créer un ``ttk.Frame`` configuré et positionné avec ``pack``."""
    frame = ttk.Frame(parent, **_frame_kwargs(style, padding))
    _pack(frame, side=side, fill=fill, expand=expand, padx=padx, pady=pady)
    return frame


def create_labeled_frame(
    parent: ttk.Widget,
    text: str = "",
    style: str = "Parametres.TLabelframe",
    side: Side | None = None,
    fill: PackFill = "both",
    expand: bool = True,
    padx: int = 0,
    pady: int = 0,
    padding: Padding | None = None,
) -> ttk.LabelFrame:
    """Créer un ``ttk.LabelFrame`` avec ``pack``."""
    label_frame = ttk.LabelFrame(parent, text=text, **_frame_kwargs(style, padding))
    _pack(label_frame, side=side, fill=fill, expand=expand, padx=padx, pady=pady)
    return label_frame


# Autres fabriques (déjà en A, petites améliorations de robustesse) --------
def create_modern_label_with_pack(
    frame: ttk.Widget,
    text: str,
    style: str = "Modern.TLabel",
    side: Side | None = None,
    padx: int = 0,
    pady: int = 0,
    sticky: str | None = None,  # conservé pour compatibilité, non utilisé par pack()
) -> ttk.Label:
    """Créer un label stylisé positionné avec ``pack``."""
    modern_label_pack = ttk.Label(frame, text=text, style=style)
    _pack(modern_label_pack, side=side, padx=padx, pady=pady)
    return modern_label_pack


def create_modern_entry_with_pack(
    frame: ttk.Widget,
    var: tk.Variable,
    width: int = 20,
    style: str = "Settings.TEntry",
    side: Side | None = None,
    padx: int = 0,
    pady: int = 0,
) -> ttk.Entry:
    """Créer une zone de saisie stylisée positionnée avec ``pack``."""
    modern_entry_pack = ttk.Entry(frame, textvariable=var, width=width, style=style)
    _pack(modern_entry_pack, side=side, padx=padx, pady=pady)
    return modern_entry_pack


def create_modern_checkbox_with_pack(
    parent: ttk.Widget,
    var: tk.Variable,
    style_checkbox: str = "Modern.TCheckbutton",
    side: Side | None = None,
    padx: int = 0,
    pady: int = 0,
) -> ttk.Checkbutton:
    """Créer une case à cocher positionnée avec ``pack``."""
    checkbox = ttk.Checkbutton(parent, variable=var, style=style_checkbox)
    _pack(checkbox, side=side, padx=padx, pady=pady)
    return checkbox


def create_modern_label_with_grid(
    frame: ttk.Widget,
    text: str,
    row: int,
    col: int,
    style: str = "Modern.TLabel",
    padx: int = 5,
    pady: int = 5,
    sticky: str = "w",
) -> ttk.Label:
    """Créer un label stylisé positionné avec ``grid``."""
    modern_label_grid = ttk.Label(frame, text=text, style=style)
    modern_label_grid.grid(row=row, column=col, padx=padx, pady=pady, sticky=sticky)
    return modern_label_grid


def create_modern_entry_with_grid(
    frame: ttk.Widget,
    var: tk.Variable,
    row: int,
    col: int,
    width: int = 20,
    style: str = "Modern.TEntry",
    padx: int = 5,
    pady: int = 5,
) -> ttk.Entry:
    """Créer une zone de saisie positionnée avec ``grid``."""
    modern_entry_grid = ttk.Entry(frame, textvariable=var, width=width, style=style)
    modern_entry_grid.grid(row=row, column=col, padx=padx, pady=pady)
    return modern_entry_grid


def create_modern_entry_with_grid_for_password(
    frame: ttk.Widget,
    var: tk.Variable,
    row: int,
    col: int,
    width: int = 20,
    style: str = "Modern.TEntry",
    padx: int = 5,
    pady: int = 5,
) -> ttk.Entry:
    """Créer un champ de mot de passe positionné avec ``grid``."""
    modern_entry_grid_for_password = ttk.Entry(
        frame,
        textvariable=var,
        show="*",
        width=width,
        style=style,
    )
    modern_entry_grid_for_password.grid(row=row, column=col, padx=padx, pady=pady)
    return modern_entry_grid_for_password


def create_combobox_with_pack(
    frame: ttk.Widget,
    var: tk.Variable,
    values: list[str],
    width: int = 20,
    style: str = "Modern.TCombobox",
    state: str = "normal",
    side: Side = "top",
    padx: int = 5,
    pady: int = 5,
) -> ttk.Combobox:
    """Créer une ``Combobox`` positionnée avec ``pack``."""
    modern_combobox_pack = ttk.Combobox(
        frame,
        textvariable=var,
        values=values,
        width=width,
        style=style,
        state=state,
    )
    _pack(modern_combobox_pack, side=side, padx=padx, pady=pady)
    return modern_combobox_pack


def create_combobox(
    frame: ttk.Widget,
    var: tk.Variable,
    values: list[str],
    row: int,
    col: int,
    width: int = 20,
    style: str = "Modern.TCombobox",
    state: str = "normal",
    padx: int = 5,
    pady: int = 8,
) -> ttk.Combobox:
    """Créer une ``Combobox`` positionnée avec ``grid``."""
    modern_combobox_grid = ttk.Combobox(
        frame,
        textvariable=var,
        values=values,
        width=width,
        style=style,
        state=state,
    )
    modern_combobox_grid.grid(row=row, column=col, padx=padx, pady=pady)
    return modern_combobox_grid


def create_button_with_style(
    frame: ttk.Widget,
    text: str,
    command: Callable[[], Any] | str | None,
    style: str = "Modern.TButton",
    side: Side | None = None,
    fill: PackFill | None = None,
    padx: int | None = None,
    pady: int | None = None,
    ipady: int | None = None,
) -> ttk.Button:
    """Créer un ``ttk.Button`` stylisé et positionné avec ``pack``."""
    kwargs: dict[str, Any] = {"text": text, "style": style}
    if command is not None:
        kwargs["command"] = command
    button = ttk.Button(frame, **kwargs)
    _pack(
        button,
        side=side,
        fill=fill,
        padx=0 if padx is None else padx,
        pady=0 if pady is None else pady,
        ipady=ipady,
    )
    return button


def create_button_without_style(
    frame: tk.Widget,
    text: str,
    command: Callable[[], Any] | str | None,
    side: Side | None = None,
    fill: PackFill = "x",
    padx: int = 20,
    pady: int = 5,
    ipady: int = 5,
) -> tk.Button:
    """Créer un ``tk.Button`` sans style et positionné avec ``pack``."""
    kwargs: dict[str, Any] = {"text": text}
    if command is not None:
        kwargs["command"] = command
    button = tk.Button(frame, **kwargs)
    _pack(button, side=side, fill=fill, padx=padx, pady=pady, ipady=ipady)
    return button
