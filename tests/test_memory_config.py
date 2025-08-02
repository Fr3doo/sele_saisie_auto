import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.memory_config import MemoryConfig  # noqa: E402


def test_defaults():
    cfg = MemoryConfig()
    assert cfg.cle_name == "memoire_partagee_cle"
    assert cfg.data_name == "memoire_partagee_donnees"
    assert cfg.login_name == "memoire_nom"
    assert cfg.password_name == "memoire_mdp"
    assert cfg.key_size == 32
    assert cfg.block_size == 128


def test_suffix():
    cfg = MemoryConfig(suffix="123")
    assert cfg.cle_name.endswith("_123")
    assert cfg.login_name.endswith("_123")


def test_factories():
    cfg_pid = MemoryConfig.with_pid(1)
    assert cfg_pid.cle_name.endswith("_1")
    cfg_uuid = MemoryConfig.with_uuid()
    assert cfg_uuid.cle_name.startswith("memoire_partagee_cle_")
