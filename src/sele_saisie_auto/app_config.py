"""Application configuration dataclass and loader."""

from __future__ import annotations

import os
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Any

from sele_saisie_auto.dropdown_options import (
    BillingActionOption,
    CGILunchOption,
    CGIOption,
    WorkLocationOption,
    WorkScheduleOption,
)
from sele_saisie_auto.dropdown_options import cgi_options as default_cgi_options
from sele_saisie_auto.dropdown_options import (
    cgi_options_billing_action as default_cgi_options_billing_action,
)
from sele_saisie_auto.dropdown_options import (
    cgi_options_dejeuner as default_cgi_options_dejeuner,
)
from sele_saisie_auto.dropdown_options import (
    work_location_options as default_work_location_options,
)
from sele_saisie_auto.dropdown_options import (
    work_schedule_options as default_work_schedule_options,
)
from sele_saisie_auto.read_or_write_file_config_ini_utils import read_config_ini


@dataclass
class AppConfigRaw:
    """Raw configuration container."""

    parser: ConfigParser


@dataclass
class AppConfig:
    """Structured configuration loaded from ``config.ini``."""

    encrypted_login: str
    encrypted_mdp: str
    url: str
    date_cible: str | None
    debug_mode: str
    liste_items_planning: list[str]
    work_schedule: dict[str, tuple[str, str]]
    project_information: dict[str, str]
    additional_information: dict[str, dict[str, str]]
    work_location_am: dict[str, str]
    work_location_pm: dict[str, str]
    work_location_options: list[WorkLocationOption]
    cgi_options: list[CGIOption]
    cgi_options_dejeuner: list[CGILunchOption]
    cgi_options_billing_action: list[BillingActionOption]
    work_schedule_options: list[WorkScheduleOption]
    default_timeout: int
    long_timeout: int
    raw: ConfigParser

    @staticmethod
    def _charger_credentials(parser: ConfigParser) -> tuple[str, str]:
        """Extrait les identifiants chiffrés depuis ``parser``."""
        encrypted_login = parser.get("credentials", "login", fallback="")
        encrypted_mdp = parser.get("credentials", "mdp", fallback="")
        return encrypted_login, encrypted_mdp

    @staticmethod
    def _charger_autres_parametres(
        parser: ConfigParser,
    ) -> dict[str, Any]:  # noqa: C901
        """Récupère les autres paramètres de configuration."""
        url = parser.get("settings", "url", fallback="")
        date_cible = parser.get("settings", "date_cible", fallback=None)
        if date_cible and date_cible.strip().lower() in {"none", ""}:
            date_cible = None
        debug_mode = parser.get("settings", "debug_mode", fallback="INFO")
        liste_items = parser.get("settings", "liste_items_planning", fallback="")
        liste_items_planning = [
            item.strip().strip('"') for item in liste_items.split(",") if item.strip()
        ]
        default_timeout = parser.getint("settings", "default_timeout", fallback=10)
        long_timeout = parser.getint("settings", "long_timeout", fallback=20)

        work_schedule: dict[str, tuple[str, str]] = {}
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

        additional_information: dict[str, dict[str, str]] = {}
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

        from typing import TypeVar

        T = TypeVar("T")

        def parse_list_from_section(
            section: str,
            option: str,
            default: list[T],
            cls: type[T],
        ) -> list[T]:
            """Extrait et convertit une liste depuis ``section``."""
            if parser.has_section(section):
                values = parser.get(section, option, fallback="")
                return [
                    cls(item.strip().strip('"'))
                    for item in values.split(",")
                    if item.strip()
                ]
            return default

        work_location_options = parse_list_from_section(
            "work_location_options",
            "values",
            default_work_location_options,
            WorkLocationOption,
        )
        cgi_options = parse_list_from_section(
            "cgi_options",
            "values",
            default_cgi_options,
            CGIOption,
        )
        cgi_options_dejeuner = parse_list_from_section(
            "cgi_options_dejeuner",
            "values",
            default_cgi_options_dejeuner,
            CGILunchOption,
        )
        if parser.has_section("cgi_options_billing_action"):
            cgi_options_billing_action = [
                BillingActionOption(label=k, code=v)
                for k, v in parser.items("cgi_options_billing_action")
            ]
        else:
            cgi_options_billing_action = default_cgi_options_billing_action
        work_schedule_options = parse_list_from_section(
            "work_schedule_options",
            "values",
            default_work_schedule_options,
            WorkScheduleOption,
        )

        return {
            "url": url,
            "date_cible": date_cible,
            "debug_mode": debug_mode,
            "liste_items_planning": liste_items_planning,
            "work_schedule": work_schedule,
            "project_information": project_information,
            "additional_information": additional_information,
            "work_location_am": work_location_am,
            "work_location_pm": work_location_pm,
            "work_location_options": work_location_options,
            "cgi_options": cgi_options,
            "cgi_options_dejeuner": cgi_options_dejeuner,
            "cgi_options_billing_action": cgi_options_billing_action,
            "work_schedule_options": work_schedule_options,
            "default_timeout": default_timeout,
            "long_timeout": long_timeout,
        }

    @classmethod
    def from_parser(cls, parser: ConfigParser) -> AppConfig:
        """Build an ``AppConfig`` instance from a ``ConfigParser``."""
        encrypted_login, encrypted_mdp = cls._charger_credentials(parser)
        autres = cls._charger_autres_parametres(parser)
        return cls(
            encrypted_login=encrypted_login,
            encrypted_mdp=encrypted_mdp,
            **autres,
            raw=parser,
        )

    @classmethod
    def from_raw(cls, raw: AppConfigRaw) -> AppConfig:
        """Build ``AppConfig`` from a :class:`AppConfigRaw`."""

        return cls.from_parser(raw.parser)


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
        ("settings", "default_timeout"): "PSATIME_DEFAULT_TIMEOUT",
        ("settings", "long_timeout"): "PSATIME_LONG_TIMEOUT",
    }
    for (section, option), env_var in env_map.items():
        value = os.getenv(env_var)
        if value is not None:
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, option, value)

    raw_cfg = AppConfigRaw(parser=parser)
    cfg = AppConfig.from_raw(raw_cfg)
    if not cfg.url.strip():
        raise ValueError("L'URL de connexion ne peut pas être vide.")
    if not cfg.encrypted_login.strip() or not cfg.encrypted_mdp.strip():
        raise ValueError("Le login et le mot de passe doivent être renseignés.")

    return cfg
