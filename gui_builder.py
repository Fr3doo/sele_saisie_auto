# pragma: no cover
# gui_builder.py
"""Fonctions utilitaires pour la création de widgets Tkinter."""

import tkinter as tk
from tkinter import ttk


def seperator_ttk(
    menu: ttk.Widget,
    orient: str = "horizontal",
    fill: str = "x",
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
    tab_frame = ttk.Frame(notebook, style=style, padding=padding)
    notebook.add(tab_frame, text=title)
    return tab_frame


def create_Title_label_with_grid(
    frame: ttk.Frame,
    text: str,
    row: int,
    col: int,
    style: str = "Title.TLabel",
    padx: int = 5,
    pady: int = 5,
    sticky: str | None = "w",
) -> ttk.Label:
    """Créer un label de titre positionné avec ``grid``."""
    title_label = ttk.Label(frame, text=text, style=style)
    title_label.grid(row=row, column=col, padx=padx, pady=pady, sticky=sticky)
    return title_label


def create_a_frame(
    parent: ttk.Widget,
    style: str = "Modern.TFrame",
    side: str | None = None,
    fill: str = "both",
    expand: bool = True,
    padx: int = 0,
    pady: int = 0,
    padding: tuple[int, int, int, int] | None = None,
) -> ttk.Frame:
    """Créer un ``ttk.Frame`` configuré et positionné avec ``pack``."""
    frame = ttk.Frame(parent, style=style, padding=padding)
    frame.pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)
    return frame


def create_labeled_frame(
    parent: ttk.Widget,
    text: str = "",
    style: str = "Parametres.TLabelframe",
    side: str | None = None,
    fill: str = "both",
    expand: bool = True,
    padx: int = 0,
    pady: int = 0,
    padding: tuple[int, int, int, int] | None = None,
) -> ttk.LabelFrame:
    """Créer un ``ttk.LabelFrame`` avec ``pack``."""
    label_frame = ttk.LabelFrame(parent, text=text, style=style, padding=padding)
    label_frame.pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady)
    return label_frame


def create_Modern_label_with_pack(
    frame: ttk.Widget,
    text: str,
    style: str = "Modern.TLabel",
    side: str | None = None,
    padx: int = 0,
    pady: int = 0,
    sticky: str | None = None,
) -> ttk.Label:
    """Créer un label stylisé positionné avec ``pack``."""
    modern_label_pack = ttk.Label(frame, text=text, style=style)
    modern_label_pack.pack(side=side, padx=padx, pady=pady, sticky=sticky)
    return modern_label_pack


def create_Modern_entry_with_pack(
    frame: ttk.Widget,
    var: tk.Variable,
    width: int = 20,
    style: str = "Settings.TEntry",
    side: str | None = None,
    padx: int = 0,
    pady: int = 0,
) -> ttk.Entry:
    """Créer une zone de saisie stylisée positionnée avec ``pack``."""
    modern_entry_pack = ttk.Entry(frame, textvariable=var, width=width, style=style)
    modern_entry_pack.pack(side=side, padx=padx, pady=pady)
    return modern_entry_pack


def create_Modern_checkbox_with_pack(
    parent: ttk.Widget,
    var: tk.Variable,
    style_checkbox: str = "Modern.TCheckbutton",
    side: str | None = None,
    padx: int = 0,
    pady: int = 0,
) -> ttk.Checkbutton:
    """Créer une case à cocher positionnée avec ``pack``."""
    checkbox = ttk.Checkbutton(parent, variable=var, style=style_checkbox)
    checkbox.pack(side=side, padx=padx, pady=pady)
    return checkbox


def create_Modern_label_with_grid(
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


def create_Modern_entry_with_grid(
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


def create_Modern_entry_with_grid_for_password(
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
    side: str = "top",
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
    modern_combobox_pack.pack(side=side, padx=padx, pady=pady)
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
    command,
    style: str = "Modern.TButton",
    side: str | None = None,
    fill: str | None = None,
    padx: int | None = None,
    pady: int | None = None,
    ipady: int | None = None,
) -> ttk.Button:
    """Créer un ``ttk.Button`` stylisé et positionné avec ``pack``."""
    button = ttk.Button(frame, text=text, command=command, style=style)
    button.pack(side=side, fill=fill, padx=padx, pady=pady, ipady=ipady)
    return button


def create_button_without_style(
    frame: tk.Widget,
    text: str,
    command,
    side: str | None = None,
    fill: str = "x",
    padx: int = 20,
    pady: int = 5,
    ipady: int = 5,
) -> tk.Button:
    """Créer un ``tk.Button`` sans style et positionné avec ``pack``."""
    button = tk.Button(frame, text=text, command=command)
    button.pack(side=side, fill=fill, padx=padx, pady=pady, ipady=ipady)
    return button
