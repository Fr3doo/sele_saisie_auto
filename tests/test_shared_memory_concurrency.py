import sys
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import shared_memory
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.shared_memory_service import SharedMemoryService  # noqa: E402


@pytest.mark.skipif(sys.platform.startswith("win"), reason="unstable on Windows")
def test_concurrent_shared_memory_creation():
    service = SharedMemoryService(Logger(None))
    names = [f"concur_{uuid4().hex}" for _ in range(4)]

    def worker(name: str) -> None:
        mem = service.stocker_en_memoire_partagee(name, b"x")
        service.supprimer_memoire_partagee_securisee(mem)

    with ThreadPoolExecutor(max_workers=len(names)) as exc:
        list(exc.map(worker, names))

    for name in names:
        with pytest.raises(FileNotFoundError):
            shared_memory.SharedMemory(name=name)
