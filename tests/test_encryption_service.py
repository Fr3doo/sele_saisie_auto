import sys
from multiprocessing import shared_memory
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

from encryption_utils import EncryptionService  # noqa: E402


def test_generer_cle_aes_default_length():
    service = EncryptionService()
    key = service.generer_cle_aes()
    assert isinstance(key, bytes)
    assert len(key) == 32


def test_chiffrement_et_dechiffrement():
    service = EncryptionService()
    key = service.generer_cle_aes()
    message = "Bonjour"

    donnees_chiffrees = service.chiffrer_donnees(message, key)
    assert message.encode() != donnees_chiffrees

    resultat = service.dechiffrer_donnees(donnees_chiffrees, key)
    assert resultat == message


def test_gestion_memoire_partagee():
    service = EncryptionService()
    data = b"secrets"
    name = f"test_mem_{uuid4().hex}"

    shm = service.stocker_en_memoire_partagee(name, data)
    try:
        opened, retrieved = service.recuperer_de_memoire_partagee(
            name,
            len(data),
        )
        try:
            assert retrieved == data
        finally:
            opened.close()

        service.supprimer_memoire_partagee_securisee(shm)

        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)
    finally:
        # Nettoyage au cas où la suppression aurait échoué
        try:
            shm.close()
            shm.unlink()
        except FileNotFoundError:
            pass


def test_generer_cle_aes_error(monkeypatch):
    service = EncryptionService()

    def raise_error(n):
        raise OSError("boom")

    monkeypatch.setattr("os.urandom", raise_error)

    with pytest.raises(OSError):
        service.generer_cle_aes()


def test_chiffrer_donnees_error(monkeypatch):
    service = EncryptionService()
    key = service.generer_cle_aes()

    class DummyCipher:
        def __init__(self, *a, **k):
            raise ValueError("fail")

    monkeypatch.setattr("encryption_utils.Cipher", DummyCipher)

    with pytest.raises(ValueError):
        service.chiffrer_donnees("msg", key)
