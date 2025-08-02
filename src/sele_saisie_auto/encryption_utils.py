# encryption_utils.py

import os
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Protocol, runtime_checkable

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from sele_saisie_auto.logger_utils import write_log
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
        # Garantit que ``write_log`` reçoit toujours une *str*
        self.log_file: str = log_file if log_file is not None else get_log_file()

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
        try:
            key = os.urandom(taille_cle)
            write_log("💀 Clé AES générée avec succès.", self.log_file, "CRITICAL")
            return key
        except Exception as e:
            write_log(
                f"❌ Erreur lors de la génération de la clé AES : {e}",
                self.log_file,
                "ERROR",
            )
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
            write_log("💀 Données chiffrées avec succès.", self.log_file, "CRITICAL")
            return bytes(iv_bytes + donnees_chiffrees)
        except Exception as e:
            write_log(
                f"❌ Erreur lors du chiffrement des données : {e}",
                self.log_file,
                "ERROR",
            )
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
            write_log("💀 Données déchiffrées avec succès.", self.log_file, "CRITICAL")
            decoded: str = donnees.decode()
            return decoded
        except Exception as e:
            write_log(
                f"❌ Erreur lors du déchiffrement des données : {e}",
                self.log_file,
                "ERROR",
            )
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
        # Toujours fournir un chemin de fichier valide à ``write_log``
        self.log_file: str = log_file if log_file is not None else get_log_file()
        self.backend = backend or DefaultEncryptionBackend(log_file)
        self.memory_config = memory_config or MemoryConfig()
        if shared_memory_service is None:
            logger = get_logger(log_file)
            self.shared_memory_service = SharedMemoryService(logger)
        else:
            self.shared_memory_service = shared_memory_service
        self.logger = get_logger(log_file)
        self.cle_aes: bytes | None = None
        self._memoires: list[shared_memory.SharedMemory] = []

    def remove_shared_memory(self, memoire: shared_memory.SharedMemory) -> None:
        """Delegate secure removal of ``memoire`` to the underlying service."""

        self.shared_memory_service.supprimer_memoire_partagee_securisee(memoire)

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
        self.cle_aes = self.generer_cle_aes(self.memory_config.key_size)
        mem = None
        try:
            mem = self.shared_memory_service.stocker_en_memoire_partagee(
                self.memory_config.cle_name,
                self.cle_aes,
            )
            self._memoires.append(mem)
        except FileExistsError:
            self.logger.info(
                "⚠️ Segment déjà présent, nettoyage puis nouvelle tentative"
            )
            try:
                self.shared_memory_service.ensure_clean_segment(
                    self.memory_config.cle_name,
                    len(self.cle_aes),
                )
                mem = self.shared_memory_service.stocker_en_memoire_partagee(
                    self.memory_config.cle_name,
                    self.cle_aes,
                )
                self._memoires.append(mem)
            except Exception as retry_exc:
                if mem is not None:
                    try:
                        self.remove_shared_memory(mem)
                    except Exception:  # nosec B110
                        pass
                self.cle_aes = None
                self.logger.error(
                    f"❌ Impossible d'initialiser la mémoire partagée : {retry_exc}"
                )
                raise
        except Exception as exc:
            if mem is not None:
                try:
                    self.remove_shared_memory(mem)
                except Exception:  # nosec B110
                    pass
            self.cle_aes = None
            self.logger.error(
                f"❌ Impossible d'initialiser la mémoire partagée : {exc}"
            )
            raise
        else:
            if self.log_file:
                self.logger.info("✅ Mémoire partagée initialisée")
        return self

    def store_credentials(self, login_data: bytes, password_data: bytes) -> None:
        """Save encrypted credentials in shared memory."""
        mem_login = self.shared_memory_service.stocker_en_memoire_partagee(
            self.memory_config.login_name,
            login_data,
        )
        mem_pwd = self.shared_memory_service.stocker_en_memoire_partagee(
            self.memory_config.password_name,
            password_data,
        )
        self._memoires.extend([mem_login, mem_pwd])

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        """Securely remove all allocated shared memories."""
        for mem in self._memoires:
            try:
                self.remove_shared_memory(mem)
            except Exception:  # nosec B110
                pass
        self._memoires.clear()
        self.cle_aes = None

    def retrieve_credentials(self) -> Credentials:
        """Retrieve encrypted credentials from shared memory."""
        mem_key, aes_key = self.shared_memory_service.recuperer_de_memoire_partagee(
            self.memory_config.cle_name,
            self.memory_config.key_size,
        )
        write_log(f"💀 Clé AES récupérée : {aes_key.hex()}", self.log_file, "CRITICAL")

        mem_login = shared_memory.SharedMemory(name=self.memory_config.login_name)
        taille_nom = len(bytes(mem_login.buf).rstrip(b"\x00"))
        login = bytes(mem_login.buf[:taille_nom])
        write_log(
            f"💀 Taille du login chiffré : {len(login)}",
            self.log_file,
            "CRITICAL",
        )

        mem_pwd = shared_memory.SharedMemory(name=self.memory_config.password_name)
        taille_pwd = len(bytes(mem_pwd.buf).rstrip(b"\x00"))
        password = bytes(mem_pwd.buf[:taille_pwd])
        write_log(
            f"💀 Taille du mot de passe chiffré : {len(password)}",
            self.log_file,
            "CRITICAL",
        )

        return Credentials(
            aes_key=aes_key,
            mem_key=mem_key,
            login=login,
            mem_login=mem_login,
            password=password,
            mem_password=mem_pwd,
        )
