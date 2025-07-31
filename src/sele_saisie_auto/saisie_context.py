from __future__ import annotations

from dataclasses import dataclass

from sele_saisie_auto.app_config import AppConfig
from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.shared_memory_service import SharedMemoryService


@dataclass
class SaisieContext:
    """Container for runtime configuration and services."""

    config: AppConfig
    encryption_service: EncryptionService
    shared_memory_service: SharedMemoryService
    project_mission_info: dict[str, str]
    descriptions: list[dict[str, object]]

    def remove_shared_memory(self, mem) -> None:
        """Delegate cleanup to ``SharedMemoryService``."""

        self.shared_memory_service.supprimer_memoire_partagee_securisee(mem)


__all__ = ["SaisieContext"]
