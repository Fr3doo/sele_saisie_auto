"""Utilities to manage data in shared memory."""

from multiprocessing import shared_memory

from logger_utils import write_log


class SharedMemoryService:
    """Service to store and retrieve bytes in shared memory."""

    def __init__(self, log_file: str | None = None) -> None:
        self.log_file = log_file

    def stocker_en_memoire_partagee(self, nom: str, donnees: bytes):
        """Create a shared memory segment and write ``donnees`` into it."""
        try:
            memoire = shared_memory.SharedMemory(
                name=nom, create=True, size=len(donnees)
            )
            memoire.buf[: len(donnees)] = donnees
            write_log(
                f"💀 Données stockées en mémoire partagée avec le nom '{nom}'.",
                self.log_file,
                "CRITICAL",
            )
            return memoire
        except Exception as e:  # pragma: no cover - defensive
            write_log(
                f"❌ Erreur lors du stockage en mémoire partagée : {e}",
                self.log_file,
                "ERROR",
            )
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
            write_log(
                "💀 Mémoire partagée supprimée de manière sécurisée.",
                self.log_file,
                "CRITICAL",
            )
        except Exception as e:  # pragma: no cover - defensive
            write_log(
                f"❌ Erreur lors de la suppression sécurisée de la mémoire partagée : {e}",
                self.log_file,
                "ERROR",
            )
            raise

    def recuperer_de_memoire_partagee(
        self, nom: str, taille: int
    ) -> tuple[shared_memory.SharedMemory, bytes]:
        """Read bytes from an existing shared memory segment."""
        try:
            memoire = shared_memory.SharedMemory(name=nom)
            donnees = bytes(memoire.buf[:taille])
            write_log(
                f"💀 Données récupérées depuis la mémoire partagée avec le nom '{nom}'.",
                self.log_file,
                "CRITICAL",
            )
            return memoire, donnees
        except Exception as e:  # pragma: no cover - defensive
            write_log(
                f"❌ Erreur lors de la récupération depuis la mémoire partagée : {e}",
                self.log_file,
                "ERROR",
            )
            raise
