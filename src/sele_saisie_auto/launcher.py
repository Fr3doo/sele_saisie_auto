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
    create_combobox_with_pack,
    create_labeled_frame,
    create_modern_entry_with_pack,
    create_modern_label_with_pack,
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
    style = ttk.Style(root)
    style.theme_use("clam")
    if hasattr(root, "tk"):
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)
        nb: ttk.Notebook | tk.Tk = notebook
    else:  # pragma: no cover - fallback for tests
        nb = root
    return root, nb


def tab_settings(
    nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]
) -> tuple[ttk.Frame, tk.StringVar, tk.StringVar]:
    frame = create_tab(cast(ttk.Notebook, nb), title="Paramètres")
    date_var = tk.StringVar(value=config["settings"].get("date_cible", ""))
    debug_var = tk.StringVar(value=config["settings"].get("debug_mode", "INFO"))
    date_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_modern_label_with_pack(date_row, "Date cible:", side="left")
    create_modern_entry_with_pack(date_row, date_var, side="left")
    debug_row = create_a_frame(frame, padding=(10, 10, 10, 10))
    create_modern_label_with_pack(debug_row, "Log Level:", side="left")
    create_combobox_with_pack(debug_row, debug_var, values=LOG_LEVEL_CHOICES)
    return frame, date_var, debug_var


def tab_planning(nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]) -> tuple[
    dict[str, tuple[tk.StringVar, tk.StringVar, tk.StringVar]],
    dict[str, tk.StringVar],
]:
    planning_tab = create_tab(cast(ttk.Notebook, nb), title="Planning de travail")

    main_frame = create_a_frame(planning_tab)
    planning_frame = create_a_frame(main_frame, side="left")
    mission_frame = create_labeled_frame(
        main_frame,
        text="Informations de mission",
        side="right",
        padx=10,
        pady=10,
    )

    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar, tk.StringVar]] = {}
    desc_section = config.get("work_description", {})
    for day in DAYS:
        row = create_a_frame(planning_frame, padding=(10, 10, 10, 10))
        create_modern_label_with_pack(row, f"{day.capitalize()}:", side="left")
        existing = config.get("work_schedule", {}).get(day, "")
        opt, _, hours = existing.partition(",")
        opt_var = tk.StringVar(value=opt)
        desc_var = tk.StringVar(value=desc_section.get(day, ""))
        hours_var = tk.StringVar(value=hours)
        create_combobox_with_pack(
            row, opt_var, values=WORK_SCHEDULE_LABELS, side="left"
        )
        create_modern_entry_with_pack(row, desc_var, side="left")
        create_modern_entry_with_pack(row, hours_var, side="left", width=8)
        schedule_vars[day] = (opt_var, desc_var, hours_var)

    mission_vars = {
        "project_code": tk.StringVar(
            value=config.get("project_information", {}).get("project_code", "")
        ),
        "activity_code": tk.StringVar(
            value=config.get("project_information", {}).get("activity_code", "")
        ),
        "category_code": tk.StringVar(
            value=config.get("project_information", {}).get("category_code", "")
        ),
        "sub_category_code": tk.StringVar(
            value=config.get("project_information", {}).get("sub_category_code", "")
        ),
        "billing_action": tk.StringVar(
            value=config.get("project_information", {}).get("billing_action", "")
        ),
    }
    for label, key in [
        ("Project Code", "project_code"),
        ("Activity Code", "activity_code"),
        ("Category Code", "category_code"),
        ("Sub Category Code", "sub_category_code"),
        ("Billing Action", "billing_action"),
    ]:
        row = create_a_frame(mission_frame, padding=(5, 5, 5, 5))
        create_modern_label_with_pack(row, f"{label}:", side="left")
        if key == "billing_action":
            create_combobox_with_pack(
                row, mission_vars[key], values=BILLING_LABELS, side="left"
            )
        else:
            create_modern_entry_with_pack(row, mission_vars[key], side="left")

    return schedule_vars, mission_vars


def tab_cgi(
    nb: ttk.Notebook | tk.Tk, config: dict[str, dict[str, str]]
) -> dict[str, dict[str, tk.StringVar]]:
    cgi_tab = create_tab(cast(ttk.Notebook, nb), title="Informations CGI")

    cgi_vars: dict[str, dict[str, tk.StringVar]] = {}
    for day in DAYS:
        row = create_a_frame(cgi_tab, padding=(5, 5, 5, 5))
        create_modern_label_with_pack(row, f"{day.capitalize()}:", side="left")
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
        create_combobox_with_pack(row, rest_var, values=CGI_LABELS, side="left")
        create_combobox_with_pack(row, work_var, values=CGI_LABELS, side="left")
        create_combobox_with_pack(row, half_var, values=CGI_LABELS, side="left")
        create_combobox_with_pack(row, lunch_var, values=CGI_DEJ_LABELS, side="left")
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
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]] = {}
    for day in DAYS:
        row = create_a_frame(location_tab, padding=(10, 10, 10, 10))
        create_modern_label_with_pack(row, f"{day.capitalize()}:", side="left")
        am_var = tk.StringVar(value=config.get("work_location_am", {}).get(day, ""))
        pm_var = tk.StringVar(value=config.get("work_location_pm", {}).get(day, ""))
        create_combobox_with_pack(row, am_var, values=WORK_LOCATION_LABELS, side="left")
        create_combobox_with_pack(row, pm_var, values=WORK_LOCATION_LABELS, side="left")
        location_vars[day] = (am_var, pm_var)
    return location_vars


def update_schedule(
    config: dict[str, dict[str, str]],
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar, tk.StringVar]],
) -> None:
    section = config.setdefault("work_schedule", {})
    desc_section = config.setdefault("work_description", {})
    for day, (opt_var, desc_var, hours_var) in schedule_vars.items():
        section[day] = f"{opt_var.get()},{hours_var.get()}"
        desc_section[day] = desc_var.get()


def update_cgi_info(
    config: dict[str, dict[str, str]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    mission_vars: dict[str, tk.StringVar],
) -> None:
    project_info = config.setdefault("project_information", {})
    for key, var in mission_vars.items():
        project_info[key] = var.get()

    rest = config.setdefault("additional_information_rest_period_respected", {})
    work = config.setdefault("additional_information_work_time_range", {})
    half = config.setdefault("additional_information_half_day_worked", {})
    lunch = config.setdefault("additional_information_lunch_break_duration", {})
    for day, vars_dict in cgi_vars.items():
        rest[day] = vars_dict["rest"].get()
        work[day] = vars_dict["work"].get()
        half[day] = vars_dict["half"].get()
        lunch[day] = vars_dict["lunch"].get()


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
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar, tk.StringVar]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    mission_vars: dict[str, tk.StringVar],
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
    debug_val: str,
    log_file: str,
) -> None:
    ensure_sections(
        raw_cfg,
        [
            "settings",
            "work_schedule",
            "work_description",
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
    for day, (opt_var, desc_var, hours_var) in schedule_vars.items():
        raw_cfg.set("work_schedule", day, f"{opt_var.get()},{hours_var.get()}")
        raw_cfg.set("work_description", day, desc_var.get())
    for key, var in mission_vars.items():
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
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar, tk.StringVar]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    mission_vars: dict[str, tk.StringVar],
    location_vars: dict[str, tuple[tk.StringVar, tk.StringVar]],
) -> None:
    config["settings"]["date_cible"] = date_var.get()
    debug_val: str | LogLevel = debug_var.get()
    if isinstance(debug_val, LogLevel):
        debug_val = debug_val.value
    config["settings"]["debug_mode"] = debug_val
    update_schedule(config, schedule_vars)
    update_cgi_info(config, cgi_vars, mission_vars)
    update_locations(config, location_vars)
    if isinstance(raw_cfg, configparser.ConfigParser):
        write_raw_cfg(
            raw_cfg,
            config,
            schedule_vars,
            cgi_vars,
            mission_vars,
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
    schedule_vars: dict[str, tuple[tk.StringVar, tk.StringVar, tk.StringVar]],
    cgi_vars: dict[str, dict[str, tk.StringVar]],
    mission_vars: dict[str, tk.StringVar],
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
        mission_vars,
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
    schedule_vars, mission_vars = tab_planning(notebook, config)
    cgi_vars = tab_cgi(notebook, config)
    location_vars = tab_locations(notebook, config)
    btn_row = create_a_frame(frame, padding=(10, 10, 10, 10))
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
            mission_vars,
            location_vars,
            cle_aes,
            root,
            encryption_service,
            headless,
            no_sandbox,
        ),
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
