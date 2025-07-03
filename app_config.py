"""Application configuration dataclass and loader."""

from __future__ import annotations

import os
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from dropdown_options import cgi_options as default_cgi_options
from dropdown_options import (
    cgi_options_billing_action as default_cgi_options_billing_action,
)
from dropdown_options import cgi_options_dejeuner as default_cgi_options_dejeuner
from dropdown_options import work_location_options as default_work_location_options
from dropdown_options import work_schedule_options as default_work_schedule_options
from read_or_write_file_config_ini_utils import read_config_ini


@dataclass
class AppConfig:
    """Structured configuration loaded from ``config.ini``."""

    encrypted_login: str
    encrypted_mdp: str
    url: str
    date_cible: Optional[str]
    debug_mode: str
    liste_items_planning: List[str]
    work_schedule: Dict[str, Tuple[str, str]]
    project_information: Dict[str, str]
    additional_information: Dict[str, Dict[str, str]]
    work_location_am: Dict[str, str]
    work_location_pm: Dict[str, str]
    work_location_options: List[str]
    cgi_options: List[str]
    cgi_options_dejeuner: List[str]
    cgi_options_billing_action: Dict[str, str]
    work_schedule_options: List[str]
    raw: ConfigParser

    @classmethod
    def from_parser(cls, parser: ConfigParser) -> "AppConfig":
        """Build an ``AppConfig`` instance from a ``ConfigParser``."""
        encrypted_login = parser.get("credentials", "login", fallback="")
        encrypted_mdp = parser.get("credentials", "mdp", fallback="")
        url = parser.get("settings", "url", fallback="")
        date_cible = parser.get("settings", "date_cible", fallback=None)
        if date_cible and date_cible.strip().lower() in {"none", ""}:
            date_cible = None
        debug_mode = parser.get("settings", "debug_mode", fallback="INFO")
        liste_items = parser.get("settings", "liste_items_planning", fallback="")
        liste_items_planning = [
            item.strip().strip('"') for item in liste_items.split(",") if item.strip()
        ]

        work_schedule: Dict[str, Tuple[str, str]] = {}
        if parser.has_section("work_schedule"):
            for day, value in parser.items("work_schedule"):
                work_schedule[day] = (
                    value.partition(",")[0].strip(),
                    value.partition(",")[2].strip(),
                )

        project_information = (
            dict(parser.items("project_information"))
            if parser.has_section("project_information")
            else {}
        )

        additional_information: Dict[str, Dict[str, str]] = {}
        if parser.has_section("additional_information_rest_period_respected"):
            additional_information["periode_repos_respectee"] = dict(
                parser.items("additional_information_rest_period_respected")
            )
        if parser.has_section("additional_information_work_time_range"):
            additional_information["horaire_travail_effectif"] = dict(
                parser.items("additional_information_work_time_range")
            )
        if parser.has_section("additional_information_half_day_worked"):
            additional_information["plus_demi_journee_travaillee"] = dict(
                parser.items("additional_information_half_day_worked")
            )
        if parser.has_section("additional_information_lunch_break_duration"):
            additional_information["duree_pause_dejeuner"] = dict(
                parser.items("additional_information_lunch_break_duration")
            )

        work_location_am = (
            dict(parser.items("work_location_am"))
            if parser.has_section("work_location_am")
            else {}
        )
        work_location_pm = (
            dict(parser.items("work_location_pm"))
            if parser.has_section("work_location_pm")
            else {}
        )

        def parse_list_from_section(
            section: str, option: str, default: List[str]
        ) -> List[str]:
            if parser.has_section(section):
                values = parser.get(section, option, fallback="")
                return [
                    item.strip().strip('"')
                    for item in values.split(",")
                    if item.strip()
                ]
            return default

        work_location_options = parse_list_from_section(
            "work_location_options",
            "values",
            default_work_location_options,
        )
        cgi_options = parse_list_from_section(
            "cgi_options", "values", default_cgi_options
        )
        cgi_options_dejeuner = parse_list_from_section(
            "cgi_options_dejeuner",
            "values",
            default_cgi_options_dejeuner,
        )
        cgi_options_billing_action = (
            {k.lower(): v for k, v in parser.items("cgi_options_billing_action")}
            if parser.has_section("cgi_options_billing_action")
            else default_cgi_options_billing_action
        )
        work_schedule_options = parse_list_from_section(
            "work_schedule_options",
            "values",
            default_work_schedule_options,
        )

        return cls(
            encrypted_login=encrypted_login,
            encrypted_mdp=encrypted_mdp,
            url=url,
            date_cible=date_cible,
            debug_mode=debug_mode,
            liste_items_planning=liste_items_planning,
            work_schedule=work_schedule,
            project_information=project_information,
            additional_information=additional_information,
            work_location_am=work_location_am,
            work_location_pm=work_location_pm,
            work_location_options=work_location_options,
            cgi_options=cgi_options,
            cgi_options_dejeuner=cgi_options_dejeuner,
            cgi_options_billing_action=cgi_options_billing_action,
            work_schedule_options=work_schedule_options,
            raw=parser,
        )


def load_config(log_file: str | None) -> AppConfig:
    """Load ``config.ini`` and return an :class:`AppConfig`.

    Environment variables take precedence over values found in the
    configuration file.
    """
    parser = read_config_ini(log_file=log_file)

    env_map = {
        ("credentials", "login"): "PSATIME_LOGIN",
        ("credentials", "mdp"): "PSATIME_MDP",
        ("settings", "url"): "PSATIME_URL",
        ("settings", "date_cible"): "PSATIME_DATE_CIBLE",
        ("settings", "debug_mode"): "PSATIME_DEBUG_MODE",
        ("settings", "liste_items_planning"): "PSATIME_LISTE_ITEMS_PLANNING",
    }
    for (section, option), env_var in env_map.items():
        value = os.getenv(env_var)
        if value is not None:
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, option, value)

    return AppConfig.from_parser(parser)
