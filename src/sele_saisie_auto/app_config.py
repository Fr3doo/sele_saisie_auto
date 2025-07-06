"""Application configuration dataclass and loader."""

from __future__ import annotations

import os
from collections.abc import Callable
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict, TypeVar

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

T = TypeVar("T")


class DayValues(TypedDict, total=False):
    """Mapping day name -> value."""

    dimanche: NotRequired[str]
    lundi: NotRequired[str]
    mardi: NotRequired[str]
    mercredi: NotRequired[str]
    jeudi: NotRequired[str]
    vendredi: NotRequired[str]
    samedi: NotRequired[str]


class AdditionalInformation(TypedDict):
    """Nested info collected for CGI fields."""

    periode_repos_respectee: DayValues
    horaire_travail_effectif: DayValues
    plus_demi_journee_travaillee: DayValues
    duree_pause_dejeuner: DayValues


class ProjectInformation(TypedDict, total=False):
    """Informations sur le projet courant."""

    project_code: str
    activity_code: str
    category_code: str
    sub_category_code: str
    billing_action: str


class WorkSchedule(TypedDict, total=False):
    """Planning de travail pour la semaine."""

    dimanche: tuple[str, str]
    lundi: tuple[str, str]
    mardi: tuple[str, str]
    mercredi: tuple[str, str]
    jeudi: tuple[str, str]
    vendredi: tuple[str, str]
    samedi: tuple[str, str]


class WorkLocation(TypedDict, total=False):
    """Lieu de travail matin/après-midi."""

    dimanche: str
    lundi: str
    mardi: str
    mercredi: str
    jeudi: str
    vendredi: str
    samedi: str


def parse_list(
    parser: ConfigParser,
    section: str,
    option: str,
    default: list[T],
    ctor: Callable[[str], T],
) -> list[T]:
    """Extrait ``option`` de ``section`` et convertit chaque valeur via ``ctor``.

    Retourne la liste obtenue ou ``default`` si la section est absente.
    """

    if parser.has_section(section):
        values = parser.get(section, option, fallback="")
        return [
            ctor(item.strip().strip('"')) for item in values.split(",") if item.strip()
        ]
    return default


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
    work_schedule: WorkSchedule
    project_information: ProjectInformation
    additional_information: AdditionalInformation
    work_location_am: WorkLocation
    work_location_pm: WorkLocation
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

    # ------------------------------------------------------------------
    # Private helpers used to load chunks of configuration
    # ------------------------------------------------------------------

    @staticmethod
    def _charger_settings(parser: ConfigParser) -> dict[str, Any]:
        """Charge ``settings`` et retourne ``{"url", "date_cible", "debug_mode", "liste_items_planning", "default_timeout", "long_timeout"}``."""

        url = parser.get("settings", "url", fallback="")
        date_cible = parser.get("settings", "date_cible", fallback=None)
        if date_cible and date_cible.strip().lower() in {"none", ""}:
            date_cible = None
        debug_mode = parser.get("settings", "debug_mode", fallback="INFO")
        liste_items_planning = parse_list(
            parser,
            "settings",
            "liste_items_planning",
            [],
            lambda x: x,
        )
        default_timeout = parser.getint("settings", "default_timeout", fallback=10)
        long_timeout = parser.getint("settings", "long_timeout", fallback=20)

        return {
            "url": url,
            "date_cible": date_cible,
            "debug_mode": debug_mode,
            "liste_items_planning": liste_items_planning,
            "default_timeout": default_timeout,
            "long_timeout": long_timeout,
        }

    @staticmethod
    def _charger_work_schedule(parser: ConfigParser) -> dict[str, WorkSchedule]:
        """Extrait ``work_schedule`` et retourne ``{"work_schedule": {...}}``."""

        work_schedule: WorkSchedule = {}
        if parser.has_section("work_schedule"):
            for day, value in parser.items("work_schedule"):
                work_schedule[day] = (
                    value.partition(",")[0].strip(),
                    value.partition(",")[2].strip(),
                )

        return {"work_schedule": work_schedule}

    @staticmethod
    def _charger_project_information(
        parser: ConfigParser,
    ) -> dict[str, ProjectInformation]:
        """Extrait ``project_information`` et retourne ``{"project_information": {...}}``."""

        project_information: ProjectInformation = (
            dict(parser.items("project_information"))  # type: ignore[typeddict-item]
            if parser.has_section("project_information")
            else {}
        )

        return {"project_information": project_information}

    @staticmethod
    def _charger_additional_information(
        parser: ConfigParser,
    ) -> dict[str, AdditionalInformation]:
        """Extrait les informations complémentaires et retourne ``{"additional_information": {...}}``."""

        additional_information: AdditionalInformation = {}
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

        return {"additional_information": additional_information}

    @staticmethod
    def _charger_work_locations(parser: ConfigParser) -> dict[str, WorkLocation]:
        """Extrait les localisations et retourne ``{"work_location_am": ..., "work_location_pm": ...}``."""

        work_location_am: WorkLocation = (
            dict(parser.items("work_location_am"))  # type: ignore[typeddict-item]
            if parser.has_section("work_location_am")
            else {}
        )
        work_location_pm: WorkLocation = (
            dict(parser.items("work_location_pm"))  # type: ignore[typeddict-item]
            if parser.has_section("work_location_pm")
            else {}
        )

        return {
            "work_location_am": work_location_am,
            "work_location_pm": work_location_pm,
        }

    @staticmethod
    def _charger_dropdown_options(parser: ConfigParser) -> dict[str, Any]:
        """Charge les listes d'options et retourne un dictionnaire.

        Contient ``work_location_options``, ``cgi_options``, ``cgi_options_dejeuner``,
        ``cgi_options_billing_action`` et ``work_schedule_options``.
        """

        work_location_options = parse_list(
            parser,
            "work_location_options",
            "values",
            default_work_location_options,
            WorkLocationOption,
        )
        cgi_options = parse_list(
            parser,
            "cgi_options",
            "values",
            default_cgi_options,
            CGIOption,
        )
        cgi_options_dejeuner = parse_list(
            parser,
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
        work_schedule_options = parse_list(
            parser,
            "work_schedule_options",
            "values",
            default_work_schedule_options,
            WorkScheduleOption,
        )

        return {
            "work_location_options": work_location_options,
            "cgi_options": cgi_options,
            "cgi_options_dejeuner": cgi_options_dejeuner,
            "cgi_options_billing_action": cgi_options_billing_action,
            "work_schedule_options": work_schedule_options,
        }

    @staticmethod
    def _charger_autres_parametres(
        parser: ConfigParser,
    ) -> dict[str, Any]:
        """Récupère les autres paramètres de configuration."""

        parts: list[dict[str, Any]] = [
            AppConfig._charger_settings(parser),
            AppConfig._charger_work_schedule(parser),
            AppConfig._charger_project_information(parser),
            AppConfig._charger_additional_information(parser),
            AppConfig._charger_work_locations(parser),
            AppConfig._charger_dropdown_options(parser),
        ]

        merged: dict[str, Any] = {}
        for part in parts:
            merged.update(part)

        return merged

    @classmethod
    def from_parser(cls, parser: ConfigParser) -> AppConfig:
        """Build an ``AppConfig`` instance from a ``ConfigParser``."""
        encrypted_login, encrypted_mdp = cls._charger_credentials(parser)
        autres: dict[str, Any] = cls._charger_autres_parametres(parser)
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


ENV_VAR_MAP: dict[tuple[str, str], str] = {
    ("credentials", "login"): "PSATIME_LOGIN",
    ("credentials", "mdp"): "PSATIME_MDP",
    ("settings", "url"): "PSATIME_URL",
    ("settings", "date_cible"): "PSATIME_DATE_CIBLE",
    ("settings", "debug_mode"): "PSATIME_DEBUG_MODE",
    ("settings", "liste_items_planning"): "PSATIME_LISTE_ITEMS_PLANNING",
    ("settings", "default_timeout"): "PSATIME_DEFAULT_TIMEOUT",
    ("settings", "long_timeout"): "PSATIME_LONG_TIMEOUT",
}


def load_config(log_file: str | None) -> AppConfig:
    """Load ``config.ini`` and return an :class:`AppConfig`.

    Environment variables take precedence over values found in the
    configuration file.
    """
    parser = read_config_ini(log_file=log_file)

    for (section, option), env_var in ENV_VAR_MAP.items():
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
