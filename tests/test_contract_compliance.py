from sele_saisie_auto.contracts.encryption import EncryptionService
from sele_saisie_auto.encryption import DefaultEncryptionService


def test_default_encryption_service_complies() -> None:
    assert isinstance(DefaultEncryptionService(), EncryptionService)
