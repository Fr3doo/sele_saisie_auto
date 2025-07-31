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
    """Créer un onglet dans ``notebook``.

    Parameters
    ----------
    notebook : ttk.Notebook
        Le ``Notebook`` cible. Doit exposer une méthode ``add``.
    title : str
        Titre de l'onglet.
    style : str, optional
        Style appliqué au ``Frame`` créé.
    padding : int, optional
        Marge interne du ``Frame``.

    Returns
    -------
    ttk.Frame
        Le ``Frame`` nouvellement ajouté.

    Raises
    ------
    AttributeError
        Si ``notebook`` ne dispose pas d'une méthode ``add``.
    """

    if not hasattr(notebook, "add"):
        raise AttributeError(
            "Notebook object must implement an 'add' method"
        )  # pragma: no cover - defensive programming

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
    if padding is None:
        frame = ttk.Frame(parent, style=style)
    else:
        frame = ttk.Frame(parent, style=style, padding=padding)

    pack_kwargs: dict[str, Any] = {"expand": expand}
    if side is not None:
        pack_kwargs["side"] = side
    if fill is not None:
        pack_kwargs["fill"] = fill
    if padx is not None:
        pack_kwargs["padx"] = padx
    if pady is not None:
        pack_kwargs["pady"] = pady

    frame.pack(**pack_kwargs)
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
    if padding is None:
        label_frame = ttk.LabelFrame(parent, text=text, style=style)
    else:
        label_frame = ttk.LabelFrame(
            parent,
            text=text,
            style=style,
            padding=padding,
        )

    pack_kwargs: dict[str, Any] = {"expand": expand}
    if side is not None:
        pack_kwargs["side"] = side
    if fill is not None:
        pack_kwargs["fill"] = fill
    if padx is not None:
        pack_kwargs["padx"] = padx
    if pady is not None:
        pack_kwargs["pady"] = pady

    label_frame.pack(**pack_kwargs)
    return label_frame


def create_modern_label_with_pack(
    frame: ttk.Widget,
    text: str,
    style: str = "Modern.TLabel",
    side: Side | None = None,
    padx: int = 0,
    pady: int = 0,
    sticky: str | None = None,
) -> ttk.Label:
    """Créer un label stylisé positionné avec ``pack``."""
    modern_label_pack = ttk.Label(frame, text=text, style=style)
    pack_kwargs: dict[str, Any] = {
        "side": side,
        "padx": padx,
        "pady": pady,
        "sticky": sticky,
    }
    modern_label_pack.pack(**pack_kwargs)
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
    pack_kwargs: dict[str, Any] = {
        "side": side,
        "padx": padx,
        "pady": pady,
    }
    modern_entry_pack.pack(**pack_kwargs)
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
    pack_kwargs: dict[str, Any] = {
        "side": side,
        "padx": padx,
        "pady": pady,
    }
    checkbox.pack(**pack_kwargs)
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
    pack_kwargs: dict[str, Any] = {
        "side": side,
        "padx": padx,
        "pady": pady,
    }
    modern_combobox_pack.pack(**pack_kwargs)
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
    if command is None:
        button = ttk.Button(frame, text=text, style=style)
    else:
        button = ttk.Button(frame, text=text, command=command, style=style)

    pack_kwargs: dict[str, Any] = {
        "side": side,
        "fill": fill,
        "padx": padx,
        "pady": pady,
        "ipady": ipady,
    }

    button.pack(**pack_kwargs)
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
    if command is None:
        button = tk.Button(frame, text=text)
    else:
        button = tk.Button(frame, text=text, command=command)

    pack_kwargs: dict[str, Any] = {
        "side": side,
        "fill": fill,
        "padx": padx,
        "pady": pady,
        "ipady": ipady,
    }

    button.pack(**pack_kwargs)
    return button
