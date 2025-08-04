"""Utilities to manage data in shared memory."""

import os
from multiprocessing import shared_memory

from sele_saisie_auto.logging_service import Logger


def ensure_clean_segment(name: str, size: int) -> shared_memory.SharedMemory:
    """Return a shared memory segment ready for writing.

    ``multiprocessing.shared_memory`` raises ``FileExistsError`` when a segment
    with the requested ``name`` already exists.  This situation commonly occurs
    when a previous run crashes without cleaning the segment.  The helper below
    first tries to remove any stale block and then creates a fresh one.  If the
    operating system still reports that the name is in use (for instance because
    another handle is lingering on Windows), the existing segment is reused after
    its buffer has been cleared.
    """

    # Attempt to remove an existing segment if present
    try:
        existing = shared_memory.SharedMemory(name=name)
    except FileNotFoundError:
        pass
    else:
        try:
            existing.unlink()
        finally:
            existing.close()

    # First try to create a brand new segment
    try:
        return shared_memory.SharedMemory(name=name, create=True, size=size)
    except FileExistsError:
        # Fall back to reusing or recreating the existing segment
        existing = shared_memory.SharedMemory(name=name)
        if existing.size < size:
            try:
                existing.unlink()
            finally:
                existing.close()
            return shared_memory.SharedMemory(name=name, create=True, size=size)
        existing.buf[: existing.size] = b"\x00" * existing.size
        return existing


class SharedMemoryService:
    """Service to store and retrieve bytes in shared memory."""

    def __init__(self, logger: Logger) -> None:
        """Initialise le service avec un ``Logger`` déjà créé."""
        self.logger = logger

    def ensure_clean_segment(self, name: str, size: int) -> None:
        """Remove an existing segment if it is still present.

        This method is mainly useful for cleaning up when a previous execution
        crashed before calling ``unlink``.  It does **not** return a handle and
        simply ensures the name no longer refers to a shared memory block.
        """

        try:
            seg = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            return
        try:
            seg.unlink()
        except FileNotFoundError:
            pass
        finally:
            try:
                seg.close()
            except FileNotFoundError:
                pass

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
