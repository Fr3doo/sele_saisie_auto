from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class MemoryConfig:
    """Shared memory configuration constants."""

    cle_name: str = "memoire_partagee_cle"
    data_name: str = "memoire_partagee_donnees"
    login_name: str = "memoire_nom"
    password_name: str = "memoire_mdp"
    key_size: int = 32  # AES-256
    block_size: int = 128  # padding block
    suffix: str | None = None

    def __post_init__(self) -> None:
        if self.suffix:
            for field in ("cle_name", "data_name", "login_name", "password_name"):
                value = getattr(self, field)
                setattr(self, field, f"{value}_{self.suffix}")

    @classmethod
    def with_pid(cls, pid: int | None = None) -> MemoryConfig:
        """Return a config using the given process id as suffix."""

        return cls(suffix=str(pid or os.getpid()))

    @classmethod
    def with_uuid(cls) -> MemoryConfig:
        """Return a config using a random UUID as suffix."""

        return cls(suffix=uuid4().hex)
