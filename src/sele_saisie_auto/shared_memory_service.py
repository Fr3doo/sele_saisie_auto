"""Utilities to manage data in shared memory."""

import os
from multiprocessing import shared_memory

from sele_saisie_auto.logging_service import Logger


def ensure_clean_segment(name: str, size: int) -> shared_memory.SharedMemory:
    """Return a new shared memory segment with ``name`` and ``size``.

    If a segment with the same name already exists, it is closed and unlinked
    before the new one is created. This helper avoids ``FileExistsError`` when
    a previous run left behind a shared memory block.
    """

    try:
        existing = shared_memory.SharedMemory(name=name)
    except FileNotFoundError:
        pass
    else:
        try:
            existing.close()
        finally:
            try:
                existing.unlink()
            except FileNotFoundError:
                pass

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
        """Create a shared memory segment and write ``donnees`` into it.

        If a segment with the same name already exists (e.g. left behind by a
        previous run that crashed), the service attempts to reuse it instead of
        raising ``FileExistsError``. On Windows an open handle can make unlink
        operations fail, so reusing the segment is the safest cross-platform
        option.
        """

        size = len(donnees)
        try:
            memoire = ensure_clean_segment(nom, size)
        except FileExistsError:
            # The segment could not be removed (commonly on Windows when an
            # handle is still open). Fallback to reusing the existing block.
            self.logger.info(f"⚠️ Segment '{nom}' déjà présent, réutilisation en cours")
            memoire = shared_memory.SharedMemory(name=nom)
            if memoire.size < size:
                # Segment too small: try to remove and recreate it with the
                # expected size. Any failure will propagate to help debugging.
                try:
                    memoire.close()
                    memoire.unlink()
                except FileNotFoundError:
                    pass
                memoire = shared_memory.SharedMemory(name=nom, create=True, size=size)

        memoire.buf[:size] = donnees
        self.logger.critical(
            f"💀 Données stockées en mémoire partagée avec le nom '{nom}'."
        )
        return memoire

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
