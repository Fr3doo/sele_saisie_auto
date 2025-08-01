import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.memory_config import MemoryConfig  # noqa: E402


def test_defaults():
    cfg = MemoryConfig()
    assert cfg.cle_name == "memoire_partagee_cle"
    assert cfg.data_name == "memoire_partagee_donnees"
    assert cfg.key_size == 32
    assert cfg.block_size == 128
