from dataclasses import dataclass


@dataclass
class MemoryConfig:
    """Shared memory configuration constants."""

    cle_name: str = "memoire_partagee_cle"
    data_name: str = "memoire_partagee_donnees"
    key_size: int = 32  # AES-256
    block_size: int = 128  # padding block
