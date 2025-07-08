import sys
from multiprocessing import shared_memory
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.encryption_utils import EncryptionService  # noqa: E402
from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.shared_memory_service import SharedMemoryService  # noqa: E402


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
    service = SharedMemoryService(Logger(None))
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

    monkeypatch.setattr("sele_saisie_auto.encryption_utils.Cipher", DummyCipher)

    with pytest.raises(ValueError):
        service.chiffrer_donnees("msg", key)


def test_stocker_en_memoire_partagee_error(monkeypatch):
    service = SharedMemoryService(Logger(None))

    def fail(*a, **k):
        raise ValueError("fail")

    monkeypatch.setattr(shared_memory, "SharedMemory", fail)

    with pytest.raises(ValueError):
        service.stocker_en_memoire_partagee("name", b"d")


class DummyMem:
    def __init__(self):
        self.buf = bytearray(b"123")

    def close(self):
        raise OSError("close fail")

    def unlink(self):
        pass


def test_supprimer_memoire_partagee_securisee_error():
    service = SharedMemoryService(Logger(None))
    with pytest.raises(OSError):
        service.supprimer_memoire_partagee_securisee(DummyMem())


def test_recuperer_de_memoire_partagee_error(monkeypatch):
    service = SharedMemoryService(Logger(None))

    def fail(*a, **k):
        raise FileNotFoundError("oops")

    monkeypatch.setattr(shared_memory, "SharedMemory", fail)

    with pytest.raises(FileNotFoundError):
        service.recuperer_de_memoire_partagee("name", 4)


def test_dechiffrer_donnees_error(monkeypatch):
    service = EncryptionService()
    key = service.generer_cle_aes()
    data = service.chiffrer_donnees("x", key)

    class BadCipher:
        def __init__(self, *a, **k):
            raise ValueError("boom")

    monkeypatch.setattr("sele_saisie_auto.encryption_utils.Cipher", BadCipher)

    with pytest.raises(ValueError):
        service.dechiffrer_donnees(data, key)


def test_context_manager_stores_and_cleans():
    service = EncryptionService()
    with service as enc:
        assert enc.cle_aes and len(enc.cle_aes) == 32
        enc.store_credentials(b"login", b"pwd")
        assert enc._memoires
    # after context exit memories list should be cleared
    assert enc._memoires == []


def test_retrieve_credentials():
    service = EncryptionService()
    with service as enc:
        enc.store_credentials(b"user", b"pass")
        creds = enc.retrieve_credentials()
        try:
            assert creds.login == b"user"
            assert creds.password == b"pass"
            assert creds.aes_key == enc.cle_aes
        finally:
            creds.mem_key.close()
            creds.mem_login.close()
            creds.mem_password.close()


def test_full_encryption_shared_memory_flow():
    service = EncryptionService()
    login = "john"
    password = "s3cr3t"

    with service as enc:
        key = enc.cle_aes
        enc_login = enc.chiffrer_donnees(login, key)
        enc_pwd = enc.chiffrer_donnees(password, key)
        enc.store_credentials(enc_login, enc_pwd)
        creds = enc.retrieve_credentials()
        try:
            assert enc.dechiffrer_donnees(creds.login, key) == login
            assert enc.dechiffrer_donnees(creds.password, key) == password
        finally:
            creds.mem_key.close()
            creds.mem_login.close()
            creds.mem_password.close()


def test_retrieve_after_exit_fails():
    service = EncryptionService()
    with service as enc:
        enc.store_credentials(b"u", b"p")

    with pytest.raises(FileNotFoundError):
        service.retrieve_credentials()
