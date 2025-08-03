"""Utilities to manage data in shared memory."""

import os
from multiprocessing import shared_memory

from sele_saisie_auto.logging_service import Logger


def ensure_clean_segment(name: str, size: int) -> shared_memory.SharedMemory:
    """Return a freshly created shared memory segment.

    ``FileExistsError`` can occur when a previous execution crashes and leaves
    behind a shared memory block with the same ``name``.  The function first
    tries to create the segment directly.  If it already exists, it is opened,
    closed and unlinked before attempting the creation again.  This mirrors the
    behaviour expected by the tests where successive calls should always return
    a new segment without raising ``FileExistsError``.
    """

    try:
        return shared_memory.SharedMemory(name=name, create=True, size=size)
    except FileExistsError:
        # A leftover segment exists. Try to remove it and create a clean one.
        try:
            existing = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            # The segment disappeared between the create and open attempts.
            pass
        else:
            try:
                existing.close()
            finally:
                try:
                    existing.unlink()
                except FileNotFoundError:
                    pass

        # Retry creation after cleanup (will raise again if it still fails).
        return shared_memory.SharedMemory(name=name, create=True, size=size)


class SharedMemoryService:
    """Service to store and retrieve bytes in shared memory."""

    def __init__(self, logger: Logger) -> None:
        """Initialise le service avec un ``Logger`` déjà créé."""
        self.logger = logger

    def ensure_clean_segment(self, name: str, size: int) -> None:
        """Remove any existing segment named ``name`` and create a fresh one."""

        seg = ensure_clean_segment(name, size)
        seg.close()
        seg.unlink()

    def stocker_en_memoire_partagee(
        self, nom: str, donnees: bytes
    ) -> shared_memory.SharedMemory:
        """Create a shared memory segment and write ``donnees`` into it."""
        try:
            memoire = ensure_clean_segment(nom, len(donnees))
            memoire.buf[: len(donnees)] = donnees
            self.logger.critical(
                f"💀 Données stockées en mémoire partagée avec le nom '{nom}'."
            )
            return memoire
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
            self.logger.error(
                f"❌ Erreur lors de la récupération depuis la mémoire partagée : {e}"
            )
            raise

    def remove_shared_memory(self, memoire: shared_memory.SharedMemory) -> None:
        """Alias for :func:`supprimer_memoire_partagee_securisee`."""

        self.supprimer_memoire_partagee_securisee(memoire)
