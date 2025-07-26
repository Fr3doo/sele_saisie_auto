from typing import Protocol, runtime_checkable

from sele_saisie_auto.encryption import DefaultEncryptionService
from sele_saisie_auto.contracts.encryption import EncryptionService


def test_default_encryption_service_complies() -> None:
    assert isinstance(DefaultEncryptionService(), EncryptionService)
