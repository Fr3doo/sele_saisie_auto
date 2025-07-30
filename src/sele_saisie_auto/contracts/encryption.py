# src\sele_saisie_auto\contracts\encryption.py

from __future__ import annotations

from types import TracebackType
from typing import Protocol, runtime_checkable


@runtime_checkable
class EncryptionService(Protocol):
    """Contract for encryption services."""

    shared_memory_service: object

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes: ...

    def chiffrer_donnees(
        self, donnees: str, cle: bytes, taille_bloc: int = 128
    ) -> bytes: ...

    def dechiffrer_donnees(
        self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128
    ) -> str: ...

    def store_credentials(self, login_data: bytes, password_data: bytes) -> None: ...

    def retrieve_credentials(self) -> tuple[bytes, bytes]: ...

    def __enter__(self) -> EncryptionService: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
