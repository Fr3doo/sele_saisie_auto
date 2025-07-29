"""Public entrypoint for encryption utilities."""

from __future__ import annotations

from typing import Any

from .encryption_utils import Credentials
from .encryption_utils import EncryptionService as _EncryptionService
from .shared_memory_service import SharedMemoryService


class DefaultEncryptionService:
    """Default implementation relying on :class:`EncryptionService`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._service = _EncryptionService(*args, **kwargs)

    # ------------------------------------------------------------------
    # Expose EncryptionService API through delegation
    # ------------------------------------------------------------------
    @property
    def shared_memory_service(
        self,
    ) -> SharedMemoryService:  # pragma: no cover - simple proxy
        return self._service.shared_memory_service

    def generer_cle_aes(self, taille_cle: int = 32) -> bytes:
        return self._service.generer_cle_aes(taille_cle)

    def chiffrer_donnees(
        self, donnees: str, cle: bytes, taille_bloc: int = 128
    ) -> bytes:
        return self._service.chiffrer_donnees(donnees, cle, taille_bloc)

    def dechiffrer_donnees(
        self, donnees_chiffrees: bytes, cle: bytes, taille_bloc: int = 128
    ) -> str:
        return self._service.dechiffrer_donnees(donnees_chiffrees, cle, taille_bloc)

    def store_credentials(self, login_data: bytes, password_data: bytes) -> None:
        self._service.store_credentials(login_data, password_data)

    def retrieve_credentials(self) -> Credentials:
        return self._service.retrieve_credentials()

    def __enter__(self) -> "DefaultEncryptionService":
        self._service.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        self._service.__exit__(exc_type, exc, tb)


__all__ = ["DefaultEncryptionService"]
