# encryption_utils.py

import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from logger_utils import write_log
from shared_memory_service import SharedMemoryService


class EncryptionService:
    """Service chargé de chiffrer et déchiffrer les données sensibles."""

    def __init__(
        self,
        log_file: str | None = None,
        shared_memory_service: SharedMemoryService | None = None,
    ) -> None:
        self.log_file = log_file
        self.shared_memory_service = shared_memory_service or SharedMemoryService(
            log_file
        )

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
        """Génère aléatoirement une clé AES.

        Args:
            taille_cle (int): Longueur de la clé en octets (32 par défaut pour
                AES-256).

        Returns:
            bytes: Clé AES générée.
        """
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
        """Chiffre une chaîne de caractères avec AES en mode CBC.

        L'initialisation vector (IV) généré est préfixé aux données chiffrées
        pour pouvoir être réutilisé lors du déchiffrement. Un padding PKCS7 est
        appliqué afin d'obtenir une longueur multiple de ``taille_bloc``.

        Args:
            donnees (str): Texte à chiffrer.
            cle (bytes): Clé AES utilisée pour le chiffrement.
            taille_bloc (int): Taille du bloc pour le padding PKCS7.
        Returns:
            bytes: IV suivi des données chiffrées.
        """
        try:
            chiffre = Cipher(algorithms.AES(cle), modes.CBC(os.urandom(16)))
            chiffreur = chiffre.encryptor()
            padder = PKCS7(taille_bloc).padder()

            donnees_pad = padder.update(donnees.encode()) + padder.finalize()
            donnees_chiffrees = chiffreur.update(donnees_pad) + chiffreur.finalize()

            write_log("💀 Données chiffrées avec succès.", self.log_file, "CRITICAL")
            return chiffre.mode.initialization_vector + donnees_chiffrees
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
        """Déchiffre un message chiffré par :func:`chiffrer_donnees`.

        Les premiers 16 octets doivent correspondre à l'IV utilisé lors du
        chiffrement. Le reste des données est alors déchiffré puis dépaddé à
        l'aide de PKCS7.

        Args:
            donnees_chiffrees (bytes): IV suivi du texte chiffré.
            cle (bytes): Clé AES utilisée pour le déchiffrement.
            taille_bloc (int): Taille de bloc pour le padding PKCS7.

        Returns:
            str: Contenu original déchiffré.
        """
        try:
            iv = donnees_chiffrees[:16]
            message_chiffre = donnees_chiffrees[16:]

            chiffre = Cipher(algorithms.AES(cle), modes.CBC(iv))
            dechiffreur = chiffre.decryptor()

            donnees_pad = dechiffreur.update(message_chiffre) + dechiffreur.finalize()

            unpadder = PKCS7(taille_bloc).unpadder()
            donnees = unpadder.update(donnees_pad) + unpadder.finalize()

            write_log("💀 Données déchiffrées avec succès.", self.log_file, "CRITICAL")
            return donnees.decode()
        except Exception as e:
            write_log(
                f"❌ Erreur lors du déchiffrement des données : {e}",
                self.log_file,
                "ERROR",
            )
            raise
