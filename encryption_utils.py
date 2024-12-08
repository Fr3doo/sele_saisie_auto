# encryption_utils.py

import os
from multiprocessing import Manager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from multiprocessing import shared_memory
from logger_utils import write_log

def generer_cle_aes(TAILLE_CLE=32, log_file=None) -> bytes:
    """Génère une clé AES-256 sécurisée."""
    try:
        key = os.urandom(TAILLE_CLE)
        write_log("💀 Clé AES générée avec succès.", log_file, "CRITICAL")
        return key
    except Exception as e:
        write_log(f"❌ Erreur lors de la génération de la clé AES : {e}", log_file, "ERROR")
        raise


def chiffrer_donnees(donnees: str, cle: bytes, TAILLE_BLOC=128, log_file=None) -> bytes:
    """Chiffre des données avec la clé AES-256."""
    try:
        chiffre = Cipher(algorithms.AES(cle), modes.CBC(os.urandom(16)))
        chiffreur = chiffre.encryptor()
        padder = PKCS7(TAILLE_BLOC).padder()

        donnees_pad = padder.update(donnees.encode()) + padder.finalize()
        donnees_chiffrees = chiffreur.update(donnees_pad) + chiffreur.finalize()

        write_log("💀 Données chiffrées avec succès.", log_file, "CRITICAL")
        return chiffre.mode.initialization_vector + donnees_chiffrees
    except Exception as e:
        write_log(f"❌ Erreur lors du chiffrement des données : {e}", log_file, "ERROR")
        raise


def stocker_en_memoire_partagee(nom: str, donnees: bytes, log_file=None):
    """Stocke des données dans la mémoire partagée."""
    try:
        memoire = shared_memory.SharedMemory(name=nom, create=True, size=len(donnees))
        memoire.buf[:len(donnees)] = donnees
        write_log(f"💀 Données stockées en mémoire partagée avec le nom '{nom}'.", log_file, "CRITICAL")
        return memoire
    except Exception as e:
        write_log(f"❌ Erreur lors du stockage en mémoire partagée : {e}", log_file, "ERROR")
        raise


def supprimer_memoire_partagee_securisee(memoire: shared_memory.SharedMemory, log_file=None):
    """Supprime la mémoire partagée de manière sécurisée."""
    try:
        for i in range(len(memoire.buf)):
            memoire.buf[i] = 0
        memoire.close()
        memoire.unlink()
        write_log("💀 Mémoire partagée supprimée de manière sécurisée.", log_file, "CRITICAL")
    except Exception as e:
        write_log(f"❌ Erreur lors de la suppression sécurisée de la mémoire partagée : {e}", log_file, "ERROR")
        raise


def recuperer_de_memoire_partagee(nom: str, taille: int, log_file=None) -> bytes:
    """Récupère des données depuis la mémoire partagée."""
    try:
        memoire = shared_memory.SharedMemory(name=nom)
        donnees = bytes(memoire.buf[:taille])
        write_log(f"💀 Données récupérées depuis la mémoire partagée avec le nom '{nom}'.", log_file, "CRITICAL")
        return memoire, donnees
    except Exception as e:
        write_log(f"❌ Erreur lors de la récupération depuis la mémoire partagée : {e}", log_file, "ERROR")
        raise


def dechiffrer_donnees(donnees_chiffrees: bytes, cle: bytes, TAILLE_BLOC=128, log_file=None) -> str:
    """Déchiffre des données avec la clé AES-256."""
    try:
        iv = donnees_chiffrees[:16]
        message_chiffre = donnees_chiffrees[16:]

        chiffre = Cipher(algorithms.AES(cle), modes.CBC(iv))
        dechiffreur = chiffre.decryptor()

        donnees_pad = dechiffreur.update(message_chiffre) + dechiffreur.finalize()

        unpadder = PKCS7(TAILLE_BLOC).unpadder()
        donnees = unpadder.update(donnees_pad) + unpadder.finalize()

        write_log("💀 Données déchiffrées avec succès.", log_file, "CRITICAL")
        return donnees.decode()
    except Exception as e:
        write_log(f"❌ Erreur lors du déchiffrement des données : {e}", log_file, "ERROR")
        raise
