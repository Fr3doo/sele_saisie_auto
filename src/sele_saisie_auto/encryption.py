"""Public entrypoint for encryption utilities."""

from __future__ import annotations

from .encryption_utils import EncryptionService as _EncryptionService


class DefaultEncryptionService(_EncryptionService):
    """Default implementation relying on :class:`EncryptionService`."""

    pass


__all__ = ["DefaultEncryptionService"]
