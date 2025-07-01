# config_manager.py
"""Gestion centralisée du fichier ``config.ini``."""

from configparser import ConfigParser
from typing import Optional

from read_or_write_file_config_ini_utils import read_config_ini, write_config_ini


class ConfigManager:
    """Charge et sauvegarde ``config.ini`` au besoin."""

    def __init__(self, log_file: Optional[str] = None) -> None:
        self.log_file = log_file
        self._config: Optional[ConfigParser] = None

    @property
    def config(self) -> ConfigParser:
        if self._config is None:
            raise RuntimeError("La configuration n'est pas chargée. Utilisez load().")
        return self._config

    def load(self) -> ConfigParser:
        """Lit ``config.ini`` et retourne un ``ConfigParser``."""
        config = read_config_ini(log_file=self.log_file)
        self._config = config
        return config

    def save(self) -> str:
        """Enregistre la configuration actuelle dans ``config.ini``."""
        if self._config is None:
            raise RuntimeError("Aucune configuration chargée pour la sauvegarde.")
        return write_config_ini(self._config, log_file=self.log_file)
