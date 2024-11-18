# encryption_utils.py

import os
from multiprocessing import Manager
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from multiprocessing import shared_memory

# fonction utilisé dans : le main.py
def generer_cle_aes(TAILLE_CLE=32) -> bytes:
    """Génère une clé AES-256 sécurisée."""
    return os.urandom(TAILLE_CLE)

# fonction utilisé dans : le main.py
def chiffrer_donnees(donnees: str, cle: bytes, TAILLE_BLOC = 128) -> bytes:
    """Chiffre des données avec la clé AES-256."""
    chiffre = Cipher(algorithms.AES(cle), modes.CBC(os.urandom(16)))
    chiffreur = chiffre.encryptor()
    padder = PKCS7(TAILLE_BLOC).padder()

    donnees_pad = padder.update(donnees.encode()) + padder.finalize()
    donnees_chiffrees = chiffreur.update(donnees_pad) + chiffreur.finalize()

    # On combine le IV et les données chiffrées pour transmission
    return chiffre.mode.initialization_vector + donnees_chiffrees

# fonction utilisé dans : le main.py
def stocker_en_memoire_partagee(nom: str, donnees: bytes):
    """Stocke des données dans la mémoire partagée."""
    memoire = shared_memory.SharedMemory(name=nom, create=True, size=len(donnees))
    memoire.buf[:len(donnees)] = donnees
    return memoire

# fonction utilisé dans : le main.py et le saisie_automatiser_psatime.py
def supprimer_memoire_partagee_securisee(memoire: shared_memory.SharedMemory):
    """Supprime la mémoire partagée de manière sécurisée."""
    for i in range(len(memoire.buf)):
        memoire.buf[i] = 0  # Remplace les données par des zéros
    memoire.close()
    memoire.unlink()

# fonction utilisé dans le saisie_automatiser_psatime.py
def recuperer_de_memoire_partagee(nom: str, taille: int) -> bytes:
    """Récupère des données depuis la mémoire partagée."""
    memoire = shared_memory.SharedMemory(name=nom)
    donnees = bytes(memoire.buf[:taille])
    return memoire, donnees

# fonction utilisé dans le saisie_automatiser_psatime.py
def dechiffrer_donnees(donnees_chiffrees: bytes, cle: bytes, TAILLE_BLOC = 128) -> str:
    """Déchiffre des données avec la clé AES-256."""
    iv = donnees_chiffrees[:16]
    message_chiffre = donnees_chiffrees[16:]

    chiffre = Cipher(algorithms.AES(cle), modes.CBC(iv))
    dechiffreur = chiffre.decryptor()

    donnees_pad = dechiffreur.update(message_chiffre) + dechiffreur.finalize()

    # Supprimer le padding PKCS7
    unpadder = PKCS7(TAILLE_BLOC).unpadder()
    donnees = unpadder.update(donnees_pad) + unpadder.finalize()

    return donnees.decode()