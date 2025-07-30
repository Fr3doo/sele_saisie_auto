# config_manager.py
"""Gestion centralisée du fichier ``config.ini``."""

import shutil
from configparser import ConfigParser
from pathlib import Path

from sele_saisie_auto import messages
from sele_saisie_auto.app_config import AppConfig, load_config
from sele_saisie_auto.logger_utils import DEFAULT_LOG_LEVEL, write_log
from sele_saisie_auto.read_or_write_file_config_ini_utils import (
    get_runtime_config_path,
    write_config_ini,
)
from sele_saisie_auto.shared_utils import get_log_file


class ConfigManager:
    """Charge et sauvegarde ``config.ini`` au besoin."""

    def __init__(self, log_file: str | None = None) -> None:
        """Initialise le gestionnaire avec un fichier log optionnel."""
        self.log_file: str | None = log_file
        self._config: ConfigParser | None = None

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` if a configuration is currently loaded."""
        return self._config is not None

    @property
    def config(self) -> ConfigParser:
        """Retourne la configuration chargée."""
        if self._config is None:
            raise RuntimeError("La configuration n'est pas chargée. Utilisez load().")
        return self._config

    def load(self) -> AppConfig:
        """Lit ``config.ini`` et retourne un ``AppConfig``."""
        cfg_path = Path(get_runtime_config_path(log_file=self.log_file))
        if not cfg_path.exists():
            default_cfg = Path(__file__).resolve().parents[2] / "config.ini"
            if default_cfg.exists():
                shutil.copy(default_cfg, cfg_path)
            else:
                cp = ConfigParser()
                cp["settings"] = {"url": "http://localhost"}
                with open(cfg_path, "w", encoding="utf-8") as f:
                    cp.write(f)
            write_log(
                f"Le fichier de configuration '{cfg_path}' est {messages.INTROUVABLE}. Un fichier par défaut a été créé.",
                self.log_file or get_log_file(),
                DEFAULT_LOG_LEVEL,
            )
        app_cfg = load_config(log_file=self.log_file)
        self._config = app_cfg.raw
        return app_cfg

    def save(self) -> str:
        """Enregistre la configuration actuelle dans ``config.ini``."""
        if self._config is None:
            raise RuntimeError("Aucune configuration chargée pour la sauvegarde.")
        return write_config_ini(self._config, log_file=self.log_file)
