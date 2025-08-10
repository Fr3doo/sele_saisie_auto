# encryption_utils.py

import os
from contextlib import suppress
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Protocol, runtime_checkable

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from sele_saisie_auto.exceptions import AutomationExitError
from sele_saisie_auto.logging_service import get_logger
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.shared_memory_service import SharedMemoryService
from sele_saisie_auto.shared_utils import get_log_file


@runtime_checkable
class EncryptionBackend(Protocol):
    """Interface minimale pour chiffrer et déchiffrer."""

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes: ...

    def chiffrer_donnees(
        self, donnees: str, cle: bytes, taille_bloc: int = 128
    ) -> bytes: ...

    def dechiffrer_donnees(
        self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128
    ) -> str: ...


class DefaultEncryptionBackend:
    """Backend concret reposant sur ``cryptography``."""

    def __init__(self, log_file: str | None = None) -> None:
        self.logger = get_logger(log_file)

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
        try:
            return os.urandom(taille_cle)
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de la clé AES : {e}")
            raise

    def chiffrer_donnees(
        self, donnees: str, cle: bytes, taille_bloc: int = 128
    ) -> bytes:
        try:
            chiffre = Cipher(algorithms.AES(cle), modes.CBC(os.urandom(16)))
            chiffreur = chiffre.encryptor()
            padder = PKCS7(taille_bloc).padder()
            donnees_pad = padder.update(donnees.encode()) + padder.finalize()
            donnees_chiffrees = chiffreur.update(donnees_pad) + chiffreur.finalize()
            iv_bytes: bytes = bytes(chiffre.mode.initialization_vector)
            self.logger.info("Données chiffrées avec succès.")
            return bytes(iv_bytes + donnees_chiffrees)
        except Exception as e:
            self.logger.error(f"Erreur lors du chiffrement des données : {e}")
            raise

    def dechiffrer_donnees(
        self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128
    ) -> str:
        try:
            iv = donnees_chiffrees[:16]
            message_chiffre = donnees_chiffrees[16:]
            chiffre = Cipher(algorithms.AES(cle), modes.CBC(iv))
            dechiffreur = chiffre.decryptor()
            donnees_pad = dechiffreur.update(message_chiffre) + dechiffreur.finalize()
            unpadder = PKCS7(taille_bloc).unpadder()
            donnees = unpadder.update(donnees_pad) + unpadder.finalize()
            self.logger.info("Données déchiffrées avec succès.")
            decoded: str = donnees.decode()
            return decoded
        except Exception as e:
            self.logger.error(f"Erreur lors du déchiffrement des données : {e}")
            raise


@dataclass
class Credentials:
    """Encrypted credentials and their shared memory handles."""

    aes_key: bytes
    mem_key: shared_memory.SharedMemory
    login: bytes
    mem_login: shared_memory.SharedMemory
    password: bytes
    mem_password: shared_memory.SharedMemory


class EncryptionService:
    """Service chargé de chiffrer et déchiffrer les données sensibles."""

    def __init__(
        self,
        log_file: str | None = None,
        shared_memory_service: SharedMemoryService | None = None,
        backend: EncryptionBackend | None = None,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        """Prépare le service de chiffrement."""
        # Toujours fournir un chemin de fichier valide pour le logger
        self.log_file: str = log_file if log_file is not None else get_log_file()
        self.backend = backend or DefaultEncryptionBackend(self.log_file)
        self.memory_config = memory_config or MemoryConfig()
        if shared_memory_service is None:
            logger = get_logger(self.log_file)
            self.shared_memory_service = SharedMemoryService(logger)
        else:
            self.shared_memory_service = shared_memory_service
        self.logger = get_logger(self.log_file)
        self.cle_aes: bytes | None = None
        self._memoires: list[shared_memory.SharedMemory] = []

    def remove_shared_memory(self, memoire: shared_memory.SharedMemory) -> None:
        """Delegate secure removal of ``memoire`` to the underlying service."""

        self.shared_memory_service.supprimer_memoire_partagee_securisee(memoire)

    def _creer_segment_si_besoin(
        self, nom: str, donnees: bytes
    ) -> shared_memory.SharedMemory:
        """Create a shared memory segment, retrying once if it already exists."""

        try:
            return self.shared_memory_service.stocker_en_memoire_partagee(nom, donnees)
        except FileExistsError:
            self.logger.info(
                "⚠️ Segment déjà présent, nettoyage puis nouvelle tentative"
            )
            self.shared_memory_service.ensure_clean_segment(nom, len(donnees))
            return self.shared_memory_service.stocker_en_memoire_partagee(nom, donnees)
        except Exception as exc:
            self.logger.error(f"❌ Impossible de créer le segment '{nom}' : {exc}")
            raise

    def _lire_segment(self, nom: str) -> tuple[shared_memory.SharedMemory, bytes]:
        """Read a segment and return the useful bytes without trailing nulls."""

        mem = shared_memory.SharedMemory(name=nom)
        raw = bytes(mem.buf)
        taille = len(raw.rstrip(b"\x00"))
        data = raw[:taille]
        self.logger.info(f"Segment '{nom}' lu ({taille} octets)")
        return mem, data

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
        """Génère aléatoirement une clé AES."""

        return self.backend.generer_cle_aes(taille_cle)

    def chiffrer_donnees(
        self, donnees: str, cle: bytes, taille_bloc: int = 128
    ) -> bytes:
        """Chiffre ``donnees`` avec la clé ``cle``."""

        return self.backend.chiffrer_donnees(donnees, cle, taille_bloc)

    def dechiffrer_donnees(
        self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128
    ) -> str:
        """Déchiffre ``donnees_chiffrees`` avec ``cle``."""

        return self.backend.dechiffrer_donnees(donnees_chiffrees, cle, taille_bloc)

    # ------------------------------------------------------------------
    # Context manager utilities
    # ------------------------------------------------------------------

    def __enter__(self) -> "EncryptionService":
        """Generate and store the AES key in shared memory."""

        key = self.generer_cle_aes(self.memory_config.key_size)
        mem = self._creer_segment_si_besoin(self.memory_config.cle_name, key)
        try:
            self._memoires.append(mem)
        except Exception:
            with suppress(Exception):
                self.remove_shared_memory(mem)
            raise
        self.cle_aes = key
        self.logger.info("✅ Mémoire partagée initialisée")
        return self

    def store_credentials(self, login_data: bytes, password_data: bytes) -> None:
        """Save encrypted credentials in shared memory atomically."""

        mem_login = self._creer_segment_si_besoin(
            self.memory_config.login_name, login_data
        )
        try:
            mem_pwd = self._creer_segment_si_besoin(
                self.memory_config.password_name, password_data
            )
        except Exception:
            with suppress(Exception):
                self.remove_shared_memory(mem_login)
            raise

        self._memoires.extend([mem_login, mem_pwd])

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        """Securely remove all allocated shared memories."""
        for mem in self._memoires:
            with suppress(Exception):  # nosec B110
                self.remove_shared_memory(mem)
        self._memoires.clear()
        self.cle_aes = None

    def retrieve_credentials(self) -> Credentials:
        """Retrieve encrypted credentials from shared memory.

        The caller must release the returned segments via
        :meth:`close_credentials`.
        """
        mem_key, aes_key = self.shared_memory_service.recuperer_de_memoire_partagee(
            self.memory_config.cle_name,
            self.memory_config.key_size,
        )
        self.logger.info("Clé AES récupérée depuis la mémoire partagée")

        try:
            mem_login, login = self._lire_segment(self.memory_config.login_name)
            mem_pwd, password = self._lire_segment(self.memory_config.password_name)
        except FileNotFoundError as exc:
            msg = "identifiants non trouvés : lancez d'abord psatime-launcher"
            self.logger.error(msg)
            with suppress(Exception):
                self.remove_shared_memory(mem_key)
            raise AutomationExitError(msg) from exc

        return Credentials(
            aes_key=aes_key,
            mem_key=mem_key,
            login=login,
            mem_login=mem_login,
            password=password,
            mem_password=mem_pwd,
        )

    def close_credentials(self, creds: Credentials) -> None:
        """Best-effort release of shared memory segments from ``creds``."""

        for mem in (creds.mem_key, creds.mem_login, creds.mem_password):
            with suppress(Exception):  # nosec B110
                self.remove_shared_memory(mem)
