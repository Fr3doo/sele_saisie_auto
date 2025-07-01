# encryption_utils.py

import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from multiprocessing import shared_memory
from logger_utils import write_log


class EncryptionService:
    """Service chargé de chiffrer et déchiffrer les données sensibles."""

    def __init__(self, log_file: str | None = None) -> None:
        self.log_file = log_file

    def generer_cle_aes(self, TAILLE_CLE: int = 32) -> bytes:
        """Génère aléatoirement une clé AES.

        Args:
            TAILLE_CLE (int): Longueur de la clé en octets (32 par défaut pour
                AES-256).

        Returns:
            bytes: Clé AES générée.
        """
        try:
            key = os.urandom(TAILLE_CLE)
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
        self, donnees: str, cle: bytes, TAILLE_BLOC: int = 128
    ) -> bytes:
        """Chiffre une chaîne de caractères avec AES en mode CBC.

    L'initialisation vector (IV) généré est préfixé aux données chiffrées
    pour pouvoir être réutilisé lors du déchiffrement. Un padding PKCS7 est
    appliqué afin d'obtenir une longueur multiple de ``TAILLE_BLOC``.

    Args:
        donnees (str): Texte à chiffrer.
        cle (bytes): Clé AES utilisée pour le chiffrement.
        TAILLE_BLOC (int): Taille du bloc pour le padding PKCS7.
    Returns:
        bytes: IV suivi des données chiffrées.
    """
        try:
            chiffre = Cipher(algorithms.AES(cle), modes.CBC(os.urandom(16)))
            chiffreur = chiffre.encryptor()
            padder = PKCS7(TAILLE_BLOC).padder()

            donnees_pad = padder.update(donnees.encode()) + padder.finalize()
            donnees_chiffrees = (
                chiffreur.update(donnees_pad) + chiffreur.finalize()
            )

            write_log("💀 Données chiffrées avec succès.", self.log_file, "CRITICAL")
            return chiffre.mode.initialization_vector + donnees_chiffrees
        except Exception as e:
            write_log(
                f"❌ Erreur lors du chiffrement des données : {e}",
                self.log_file,
                "ERROR",
            )
            raise


    def stocker_en_memoire_partagee(self, nom: str, donnees: bytes):
        """Crée un segment de mémoire partagée et y écrit les ``donnees``.

    Args:
        nom (str): Nom attribué au segment créé.
        donnees (bytes): Valeurs à écrire dans la zone partagée.

    Returns:
        SharedMemory: L'objet représentant le segment créé.
    """
        try:
            memoire = shared_memory.SharedMemory(name=nom, create=True, size=len(donnees))
            memoire.buf[:len(donnees)] = donnees
            write_log(
                f"💀 Données stockées en mémoire partagée avec le nom '{nom}'.",
                self.log_file,
                "CRITICAL",
            )
            return memoire
        except Exception as e:
            write_log(
                f"❌ Erreur lors du stockage en mémoire partagée : {e}",
                self.log_file,
                "ERROR",
            )
            raise


    def supprimer_memoire_partagee_securisee(
        self, memoire: shared_memory.SharedMemory
    ) -> None:
        """Efface et détruit un segment de mémoire partagée.

    Le contenu du segment est rempli de zéros avant fermeture puis suppression
    définitive.

    Args:
            memoire (shared_memory.SharedMemory): Segment à nettoyer et supprimer.
    """
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
        except Exception as e:
            write_log(
                f"❌ Erreur lors de la suppression sécurisée de la mémoire partagée : {e}",
                self.log_file,
                "ERROR",
            )
            raise


    def recuperer_de_memoire_partagee(
        self, nom: str, taille: int
    ) -> tuple[shared_memory.SharedMemory, bytes]:
        """Lit des octets depuis un segment de mémoire partagée existant.

    Args:
        nom (str): Nom du segment à ouvrir.
        taille (int): Nombre d'octets à lire dans ce segment.

    Returns:
        tuple[shared_memory.SharedMemory, bytes]:
            Le segment ouvert ainsi que les données récupérées.
    """
        try:
            memoire = shared_memory.SharedMemory(name=nom)
            donnees = bytes(memoire.buf[:taille])
            write_log(
                f"💀 Données récupérées depuis la mémoire partagée avec le nom '{nom}'.",
                self.log_file,
                "CRITICAL",
            )
            return memoire, donnees
        except Exception as e:
            write_log(
                f"❌ Erreur lors de la récupération depuis la mémoire partagée : {e}",
                self.log_file,
                "ERROR",
            )
            raise


    def dechiffrer_donnees(
        self, donnees_chiffrees: bytes, cle: bytes, TAILLE_BLOC: int = 128
    ) -> str:
        """Déchiffre un message chiffré par :func:`chiffrer_donnees`.

    Les premiers 16 octets doivent correspondre à l'IV utilisé lors du
    chiffrement. Le reste des données est alors déchiffré puis dépaddé à
    l'aide de PKCS7.

    Args:
        donnees_chiffrees (bytes): IV suivi du texte chiffré.
        cle (bytes): Clé AES utilisée pour le déchiffrement.
        TAILLE_BLOC (int): Taille de bloc pour le padding PKCS7.

    Returns:
        str: Contenu original déchiffré.
    """
        try:
            iv = donnees_chiffrees[:16]
            message_chiffre = donnees_chiffrees[16:]

            chiffre = Cipher(algorithms.AES(cle), modes.CBC(iv))
            dechiffreur = chiffre.decryptor()

            donnees_pad = dechiffreur.update(message_chiffre) + dechiffreur.finalize()

            unpadder = PKCS7(TAILLE_BLOC).unpadder()
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
