"""Context managing encryption and shared memory lifecycle."""

from __future__ import annotations

from typing import Any

from sele_saisie_auto.encryption_utils import Credentials, EncryptionService

__all__ = ["ResourceContext"]


class ResourceContext:
    """Manage encrypted credentials and memory cleanup."""

    def __init__(
        self, log_file: str, encryption_service: EncryptionService | None = None
    ) -> None:
        self.log_file: str = log_file
        self.encryption_service = encryption_service or EncryptionService(log_file)
        self._credentials: Credentials | None = None

    def __enter__(self) -> "ResourceContext":
        if hasattr(self.encryption_service, "__enter__"):
            self.encryption_service.__enter__()
        return self

    def __exit__(
        self, exc_type: type | None, exc: Exception | None, tb: Any | None
    ) -> None:
        if hasattr(self.encryption_service, "__exit__"):
            self.encryption_service.__exit__(exc_type, exc, tb)
        if self._credentials is not None:
            for mem in (
                self._credentials.mem_key,
                self._credentials.mem_login,
                self._credentials.mem_password,
            ):
                if mem is not None:
                    try:
                        self.encryption_service.shared_memory_service.supprimer_memoire_partagee_securisee(
                            mem
                        )
                    except Exception:  # nosec B110 - cleanup best effort
                        pass
        self._credentials = None

    def get_credentials(self) -> Credentials:
        if self._credentials is None:
            self._credentials = self.encryption_service.retrieve_credentials()
        return self._credentials
