"""Launcher module handling configuration and Selenium startup."""

from __future__ import annotations

import configparser
import multiprocessing
import tkinter as tk
from collections.abc import Callable, Iterable
from functools import partial
from multiprocessing import shared_memory
from tkinter import messagebox, ttk
from typing import cast

from sele_saisie_auto import cli, messages, saisie_automatiser_psatime
from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.automation.browser_session import BrowserSession
from sele_saisie_auto.config_manager import ConfigManager
from sele_saisie_auto.configuration import Services, service_configurator_factory
from sele_saisie_auto.dropdown_options import (
    cgi_options,
    cgi_options_billing_action,
    cgi_options_dejeuner,
    work_location_options,
    work_schedule_options,
)
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.enums import LogLevel
from sele_saisie_auto.gui_builder import (
    create_a_frame,
    create_button_with_style,
    create_combobox,
    create_modern_entry_with_grid,
    create_modern_label_with_grid,
    create_tab,
)
from sele_saisie_auto.interfaces import LoggerProtocol
from sele_saisie_auto.logger_utils import LOG_LEVEL_CHOICES
from sele_saisie_auto.logging_service import Logger, LoggingConfigurator, get_logger
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.orchestration import AutomationOrchestrator
from sele_saisie_auto.read_or_write_file_config_ini_utils import (
    read_config_ini,
    write_config_ini,
)
from sele_saisie_auto.resources.resource_manager import ResourceManager  # noqa: F401
from sele_saisie_auto.shared_utils import get_log_file
from sele_saisie_auto.styles import COLORS, setup_modern_style

__all__ = ["ResourceManager"]

DEFAULT_SETTINGS = {"date_cible": "", "debug_mode": "INFO"}

DAYS = (
    "dimanche",
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
)

WORK_SCHEDULE_LABELS = [o.label for o in work_schedule_options]
CGI_LABELS = [o.label for o in cgi_options]
CGI_DEJ_LABELS = [o.label for o in cgi_options_dejeuner]
BILLING_LABELS = [o.label for o in cgi_options_billing_action]
WORK_LOCATION_LABELS = [o.label for o in work_location_options]


def _remove_shared_memory(name: str) -> None:
    try:
        mem = shared_memory.SharedMemory(name=name)
    except FileNotFoundError:
        return
    try:
        mem.close()
    finally:
        try:
            mem.unlink()
        except FileNotFoundError:
            pass


def cleanup_memory_segments(memory_config: MemoryConfig | None = None) -> None:
    """Remove leftover shared memory segments.

    Parameters
    ----------
    memory_config:
        Names of the segments to remove. Defaults to :class:`MemoryConfig`.
    """

    cfg = memory_config or MemoryConfig()
    for name in (
        cfg.cle_name,
        cfg.data_name,
        cfg.login_name,
        cfg.password_name,
    ):
        _remove_shared_memory(name)


def run_psatime(
    log_file: str,
    menu: tk.Tk,
    logger: Logger | None = None,
    *,
    encryption_service: EncryptionService | Services | None = None,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Launch the Selenium automation after closing the menu."""
    menu.destroy()
    if logger is None:
        with get_logger(log_file) as log:
            _run_psa_time(
                log_file,
                cfg_loader=lambda: ConfigManager(log_file=log_file).load(),
                logger=log,
                encryption_service=encryption_service,
                headless=headless,
                no_sandbox=no_sandbox,
            )
    else:
        _run_psa_time(
            log_file,
            cfg_loader=lambda: ConfigManager(log_file=log_file).load(),
            logger=logger,
            encryption_service=encryption_service,
            headless=headless,
            no_sandbox=no_sandbox,
        )


def _run_psa_time(
    log_file: str,
    *,
    cfg_loader: Callable[[], AppConfig],
    logger: Logger,
    encryption_service: EncryptionService | Services | None,
    headless: bool,
    no_sandbox: bool,
) -> None:
    """Internal helper to initialize automation."""
    logger.info("Launching PSA time")
    cfg: AppConfig = cfg_loader()
    services: Services | None = None
    memory_config = None
    if isinstance(encryption_service, Services):
        services = encryption_service
        memory_config = services.encryption_service.memory_config
        service_configurator = service_configurator_factory(
            cfg, memory_config=memory_config
        )
    elif encryption_service is not None:
        memory_config = encryption_service.memory_config
        service_configurator = service_configurator_factory(
            cfg, memory_config=memory_config
        )
        waiter = service_configurator.create_waiter()
        browser_session = BrowserSession(log_file, cfg, waiter=waiter)
        login_handler = service_configurator.create_login_handler(
            log_file, encryption_service, browser_session
        )
        services = Services(
            encryption_service,
            browser_session,
            waiter,
            login_handler,
        )
    else:
        service_configurator = service_configurator_factory(cfg)

    automation = saisie_automatiser_psatime.PSATimeAutomation(
        log_file,
        cfg,
        logger=logger,
        services=services,
    )
    orchestrator = AutomationOrchestrator.from_components(
        automation.resource_manager,
        automation.page_navigator,
        service_configurator,
        automation.context,
        cast(LoggerProtocol, automation.logger),
    )
    orchestrator.run(headless=headless, no_sandbox=no_sandbox)


def run_psatime_with_credentials(
    encryption_service: EncryptionService,
    login_var: tk.StringVar,
    mdp_var: tk.StringVar,
    log_file: str,
    menu: tk.Tk,
    logger: Logger | None = None,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
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

    run_psatime(
        log_file,
        menu,
        logger=logger,
        encryption_service=encryption_service,
        headless=headless,
        no_sandbox=no_sandbox,
    )


def load_config_with_defaults(
    log_file: str,
) -> tuple[
    dict[str, dict[str, str]], configparser.ConfigParser | dict[str, dict[str, str]]
]:
    raw_cfg = read_config_ini(log_file)
    if isinstance(raw_cfg, configparser.ConfigParser):
        config = {
            section: dict(raw_cfg.items(section)) for section in raw_cfg.sections()
        }
    else:
        config = raw_cfg
    for key, val in DEFAULT_SETTINGS.items():
        config.setdefault("settings", {}).setdefault(key, val)
    return config, raw_cfg


def build_root() -> tuple[tk.Tk, ttk.Notebook | tk.Tk]:
    root = tk.Tk()
    root.title("Configuration")
    root.geometry("400x200")
    setup_modern_style(root, COLORS)
    if hasattr(root, "tk"):
        notebook = ttk.Notebook(root, style="Modern.TNotebook")
        notebook.pack(fill="both", expand=True)
        nb: ttk.Notebook | tk.Tk = notebook
    else:  # pragma: no cover - fallback for tests
        nb = root
    return root, nb


def tab_settings(
    nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]
) -> tuple[ttk.Frame, tk.StringVar, tk.StringVar]:
    frame = create_tab(cast(ttk.Notebook, nb), title="Paramètres")
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    date_var = tk.StringVar(value=config["settings"].get("date_cible", ""))
    debug_var = tk.StringVar(value=config["settings"].get("debug_mode", "INFO"))

    left = ttk.Frame(frame)
    left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    create_modern_label_with_grid(left, "Date cible (jj/mm/aaaa):", row=0, col=0)
    create_modern_entry_with_grid(left, date_var, row=0, col=1, width=15)
    create_modern_label_with_grid(left, "Log Level :", row=1, col=0)
    create_combobox(
        left,
        debug_var,
        LOG_LEVEL_CHOICES,
        row=1,
        col=1,
        width=12,
        state="readonly",
    )

    notes_frame = ttk.LabelFrame(frame, text="Notes")
    notes_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

    notes_text = (
        "Gestion de la Date :\n"
        "• La date peut être vide ou 'None'.\n"
        "• Si c'est vide ou 'None', l’outil sélectionne le prochain samedi.\n"
        "• Si nous sommes un samedi, il garde ce jour.\n\n"
        "Gestion du fichier config.ini :\n"
        "• Vous pouvez le modifier directement sans passer par la configuration.\n\n"
        "Si vous êtes en mission :\n"
        "• Dans l'onglet 'Planning de travail', sélectionnez 'En mission'.\n"
        "  Un nouveau cadre apparaît afin de remplir les informations de la mission."
    )

    style = ttk.Style(notes_frame)
    style.configure("Notes.TLabel", background="#FFF8DC")
    style.configure("Notes.TLabelframe", background="#FFF8DC")
    notes_label = ttk.Label(
        notes_frame,
        text=notes_text,
        style="Notes.TLabel",
        justify="left",
        wraplength=250,
    )
    notes_label.pack(anchor="nw", padx=8, pady=8, fill="both", expand=True)

    return frame, date_var, debug_var


def tab_planning(
    nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]
) -> tuple[dict[str, tuple[tk.StringVar, tk.StringVar]], dict[str, tk.StringVar]]:
    planning_tab = create_tab(cast(ttk.Notebook, nb), title="Planning de travail")

    headers = ("Jour", "Description", "Heures travaillées")
    for col, text in enumerate(headers):
        create_modern_label_with_grid(planning_tab, text, row=0, col=col)

    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar]] = {}
    for row_idx, day in enumerate(DAYS, start=1):
        create_modern_label_with_grid(
            planning_tab, day.capitalize(), row=row_idx, col=0, sticky="w"
        )
        existing = config.get("work_schedule", {}).get(day, "")
        opt, _, hours = existing.partition(",")
        opt_var = tk.StringVar(value=opt)
        hours_var = tk.StringVar(value=hours)
        create_combobox(
            planning_tab, opt_var, WORK_SCHEDULE_LABELS, row=row_idx, col=1, width=20
        )
        create_modern_entry_with_grid(
            planning_tab, hours_var, row=row_idx, col=2, width=10
        )
        schedule_vars[day] = (opt_var, hours_var)

    mission_frame = ttk.LabelFrame(planning_tab, text="Informations de mission")
    mission_frame.grid(row=1, column=3, rowspan=len(DAYS), padx=15, pady=5, sticky="n")
    labels = (
        "Project Code:",
        "Activity Code:",
        "Category Code:",
        "Sub Category Code:",
        "Billing Action:",
    )
    keys = (
        "project_code",
        "activity_code",
        "category_code",
        "sub_category_code",
        "billing_action",
    )
    project_vars: dict[str, tk.StringVar] = {}
    for i, (label, key) in enumerate(zip(labels, keys, strict=False)):
        create_modern_label_with_grid(mission_frame, label, row=i, col=0)
        value = config.get("project_information", {}).get(key, "")
        var = tk.StringVar(value=value)
        if key == "billing_action":
            create_combobox(mission_frame, var, BILLING_LABELS, row=i, col=1, width=15)
        else:
            create_modern_entry_with_grid(mission_frame, var, row=i, col=1, width=20)
        project_vars[key] = var

    return schedule_vars, project_vars


def tab_cgi(
    nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]
) -> dict[str, dict[str, tk.StringVar]]:
    cgi_tab = create_tab(cast(ttk.Notebook, nb), title="Informations CGI")
    headers = (
        "Jour",
        "période repos respectée",
        "plage horaire travail",
        "demi-journée travaillée",
        "durée pause déjeuner",
    )
    for col, text in enumerate(headers):
        create_modern_label_with_grid(cgi_tab, text, row=0, col=col)
    cgi_vars: dict[str, dict[str, tk.StringVar]] = {}
    for row_idx, day in enumerate(DAYS, start=1):
        create_modern_label_with_grid(
            cgi_tab, day.capitalize(), row=row_idx, col=0, sticky="w"
        )
        rest_var = tk.StringVar(
            value=config.get("additional_information_rest_period_respected", {}).get(
                day, ""
            )
        )
        work_var = tk.StringVar(
            value=config.get("additional_information_work_time_range", {}).get(day, "")
        )
        half_var = tk.StringVar(
            value=config.get("additional_information_half_day_worked", {}).get(day, "")
        )
        lunch_var = tk.StringVar(
            value=config.get("additional_information_lunch_break_duration", {}).get(
                day, ""
            )
        )
        create_combobox(cgi_tab, rest_var, CGI_LABELS, row=row_idx, col=1, width=7)
        create_combobox(cgi_tab, work_var, CGI_LABELS, row=row_idx, col=2, width=7)
        create_combobox(cgi_tab, half_var, CGI_LABELS, row=row_idx, col=3, width=7)
        create_combobox(cgi_tab, lunch_var, CGI_DEJ_LABELS, row=row_idx, col=4, width=5)
        cgi_vars[day] = {
            "rest": rest_var,
            "work": work_var,
            "half": half_var,
            "lunch": lunch_var,
        }
    return cgi_vars


def tab_locations(
    nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]
) -> dict[str, tuple[tk.StringVar, tk.StringVar]]:
    location_tab = create_tab(cast(ttk.Notebook, nb), title="Lieu de travail")
    headers = ("Jour", "Matin", "Après-midi")
    for col, text in enumerate(headers):
        create_modern_label_with_grid(location_tab, text, row=0, col=col)

    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]] = {}
    for row_idx, day in enumerate(DAYS, start=1):
        create_modern_label_with_grid(
            location_tab, day.capitalize(), row=row_idx, col=0, sticky="w"
        )
        am_var = tk.StringVar(value=config.get("work_location_am", {}).get(day, ""))
        pm_var = tk.StringVar(value=config.get("work_location_pm", {}).get(day, ""))
        create_combobox(
            location_tab, am_var, WORK_LOCATION_LABELS, row=row_idx, col=1, width=15
        )
        create_combobox(
            location_tab, pm_var, WORK_LOCATION_LABELS, row=row_idx, col=2, width=15
        )
        location_vars[day] = (am_var, pm_var)
    return location_vars


def update_schedule(
    config: dict[str, dict[str, str]],
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
) -> None:
    section = config.setdefault("work_schedule", {})
    for day, (opt_var, hours_var) in schedule_vars.items():
        section[day] = f"{opt_var.get()},{hours_var.get()}"


def update_cgi_info(
    config: dict[str, dict[str, str]], cgi_vars: dict[str, dict[str, tk.StringVar]]
) -> None:
    rest = config.setdefault("additional_information_rest_period_respected", {})
    work = config.setdefault("additional_information_work_time_range", {})
    half = config.setdefault("additional_information_half_day_worked", {})
    lunch = config.setdefault("additional_information_lunch_break_duration", {})
    for day, vars_dict in cgi_vars.items():
        rest[day] = vars_dict["rest"].get()
        work[day] = vars_dict["work"].get()
        half[day] = vars_dict["half"].get()
        lunch[day] = vars_dict["lunch"].get()


def update_project_info(
    config: dict[str, dict[str, str]], project_vars: dict[str, tk.StringVar]
) -> None:
    section = config.setdefault("project_information", {})
    for key, var in project_vars.items():
        section[key] = var.get()


def update_locations(
    config: dict[str, dict[str, str]],
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
) -> None:
    loc_am = config.setdefault("work_location_am", {})
    loc_pm = config.setdefault("work_location_pm", {})
    for day, (am_var, pm_var) in location_vars.items():
        loc_am[day] = am_var.get()
        loc_pm[day] = pm_var.get()


def _dict_to_configparser(data: dict[str, dict[str, str]]) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    for section, values in data.items():
        parser.add_section(section)
        for key, value in values.items():
            parser.set(section, key, value)
    return parser


def ensure_sections(
    raw_cfg: configparser.ConfigParser, sections: Iterable[str]
) -> None:
    for section in sections:
        if not raw_cfg.has_section(section):
            raw_cfg.add_section(section)


def write_raw_cfg(
    raw_cfg: configparser.ConfigParser,
    config: dict[str, dict[str, str]],
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    project_vars: dict[str, tk.StringVar],
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
    debug_val: str,
    log_file: str,
) -> None:
    ensure_sections(
        raw_cfg,
        [
            "settings",
            "work_schedule",
            "project_information",
            "additional_information_rest_period_respected",
            "additional_information_work_time_range",
            "additional_information_half_day_worked",
            "additional_information_lunch_break_duration",
            "work_location_am",
            "work_location_pm",
        ],
    )
    raw_cfg.set("settings", "date_cible", config["settings"]["date_cible"])
    raw_cfg.set("settings", "debug_mode", debug_val)
    for day, (opt_var, hours_var) in schedule_vars.items():
        raw_cfg.set("work_schedule", day, f"{opt_var.get()},{hours_var.get()}")
    for key, var in project_vars.items():
        raw_cfg.set("project_information", key, var.get())
    for day, vars_dict in cgi_vars.items():
        raw_cfg.set(
            "additional_information_rest_period_respected", day, vars_dict["rest"].get()
        )
        raw_cfg.set(
            "additional_information_work_time_range", day, vars_dict["work"].get()
        )
        raw_cfg.set(
            "additional_information_half_day_worked", day, vars_dict["half"].get()
        )
        raw_cfg.set(
            "additional_information_lunch_break_duration", day, vars_dict["lunch"].get()
        )
    for day, (am_var, pm_var) in location_vars.items():
        raw_cfg.set("work_location_am", day, am_var.get())
        raw_cfg.set("work_location_pm", day, pm_var.get())
    write_config_ini(raw_cfg, log_file)


def save_all(
    config: dict[str, dict[str, str]],
    raw_cfg: configparser.ConfigParser | dict[str, dict[str, str]],
    log_file: str,
    date_var: tk.StringVar,
    debug_var: tk.StringVar,
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    project_vars: dict[str, tk.StringVar],
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
) -> None:
    config["settings"]["date_cible"] = date_var.get()
    debug_val: str | LogLevel = debug_var.get()
    if isinstance(debug_val, LogLevel):
        debug_val = debug_val.value
    config["settings"]["debug_mode"] = debug_val
    update_schedule(config, schedule_vars)
    update_project_info(config, project_vars)
    update_cgi_info(config, cgi_vars)
    update_locations(config, location_vars)
    if isinstance(raw_cfg, configparser.ConfigParser):
        write_raw_cfg(
            raw_cfg,
            config,
            schedule_vars,
            cgi_vars,
            project_vars,
            location_vars,
            debug_val,
            log_file,
        )
    else:
        parser = _dict_to_configparser(config)
        write_config_ini(parser, log_file)


def save_and_close(
    config: dict[str, dict[str, str]],
    raw_cfg: configparser.ConfigParser | dict[str, dict[str, str]],
    log_file: str,
    date_var: tk.StringVar,
    debug_var: tk.StringVar,
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    project_vars: dict[str, tk.StringVar],
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
    cle_aes: bytes,
    root: tk.Tk,
    encryption_service: EncryptionService,
    headless: bool,
    no_sandbox: bool,
) -> None:
    save_all(
        config,
        raw_cfg,
        log_file,
        date_var,
        debug_var,
        schedule_vars,
        cgi_vars,
        project_vars,
        location_vars,
    )
    messagebox.showinfo("Info", messages.CONFIGURATION_SAVED)
    root.destroy()
    from sele_saisie_auto.main_menu import main_menu

    main_menu(
        cle_aes,
        log_file,
        encryption_service,
        headless=headless,
        no_sandbox=no_sandbox,
    )


def start_configuration(
    cle_aes: bytes,
    log_file: str,
    encryption_service: EncryptionService,
    *,
    headless: bool = False,
    no_sandbox: bool = False,
) -> None:
    """Minimal configuration window."""

    config, raw_cfg = load_config_with_defaults(log_file)
    root, notebook = build_root()
    frame, date_var, debug_var = tab_settings(notebook, config)
    schedule_vars, project_vars = tab_planning(notebook, config)
    cgi_vars = tab_cgi(notebook, config)
    location_vars = tab_locations(notebook, config)

    btn_row = create_a_frame(
        cast(ttk.Widget, root),
        side="bottom",
        fill="x",
        padx=0,
        pady=10,
        padding=(10, 0, 10, 0),
    )
    create_button_with_style(
        btn_row,
        "Sauvegarder",
        command=partial(
            save_and_close,
            config,
            raw_cfg,
            log_file,
            date_var,
            debug_var,
            schedule_vars,
            cgi_vars,
            project_vars,
            location_vars,
            cle_aes,
            root,
            encryption_service,
            headless,
            no_sandbox,
        ),
        side="right",
    )
    root.mainloop()


def main(argv: list[str] | None = None) -> None:
    """Entry point."""
    args = cli.parse_args(argv)

    log_file = get_log_file()
    with get_logger(log_file) as logger:
        logger.info("Initialisation")

        config = read_config_ini(log_file)
        LoggingConfigurator.setup(log_file, args.log_level, config)

        multiprocessing.freeze_support()
        cleanup_memory_segments()
        with EncryptionService(log_file) as encryption_service:
            cle_aes = cast(bytes, encryption_service.cle_aes)
            from sele_saisie_auto.main_menu import main_menu

            main_menu(
                cle_aes,
                log_file,
                encryption_service,
                headless=args.headless,
                no_sandbox=args.no_sandbox,
            )


if __name__ == "__main__":
    main()
