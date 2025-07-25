"""Utilities to manage data in shared memory."""

import os
from multiprocessing import shared_memory

from sele_saisie_auto.logging_service import Logger


class SharedMemoryService:
    """Service to store and retrieve bytes in shared memory."""

    def __init__(self, logger: Logger) -> None:
        """Initialise le service avec un ``Logger`` déjà créé."""
        self.logger = logger

    def stocker_en_memoire_partagee(self, nom: str, donnees: bytes):
        """Create a shared memory segment and write ``donnees`` into it."""
        try:
            memoire = shared_memory.SharedMemory(
                name=nom, create=True, size=len(donnees)
            )
            memoire.buf[: len(donnees)] = donnees
            self.logger.critical(
                f"💀 Données stockées en mémoire partagée avec le nom '{nom}'."
            )
            return memoire
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(f"❌ Erreur lors du stockage en mémoire partagée : {e}")
            raise

    def supprimer_memoire_partagee_securisee(
        self, memoire: shared_memory.SharedMemory
    ) -> None:
        """Erase and remove a shared memory segment."""
        try:
            for i in range(len(memoire.buf)):
                memoire.buf[i] = 0
            memoire.close()
            memoire.unlink()
            self.logger.critical("💀 Mémoire partagée supprimée de manière sécurisée.")
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(
                f"❌ Erreur lors de la suppression sécurisée de la mémoire partagée : {e}"
            )
            raise

    def recuperer_de_memoire_partagee(
        self, nom: str, taille: int
    ) -> tuple[shared_memory.SharedMemory, bytes]:
        """Read bytes from an existing shared memory segment."""
        if os.name == "posix":
            path = f"/dev/shm/{nom}"  # nosec B108
            if not os.path.exists(path):
                self.logger.warning(f"Shared memory segment '{nom}' is not accessible.")
                raise FileNotFoundError(nom)
        try:
            memoire = shared_memory.SharedMemory(name=nom)
            donnees = bytes(memoire.buf[:taille])
            self.logger.critical(
                f"💀 Données récupérées depuis la mémoire partagée avec le nom '{nom}'."
            )
            return memoire, donnees
        except FileNotFoundError:
            self.logger.warning(f"Shared memory segment '{nom}' is not accessible.")
            raise
        except Exception as e:  # pragma: no cover - defensive
            self.logger.error(
                f"❌ Erreur lors de la récupération depuis la mémoire partagée : {e}"
            )
            raise
