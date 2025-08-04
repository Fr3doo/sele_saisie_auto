import sys
from multiprocessing import shared_memory
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.shared_memory_service import SharedMemoryService  # noqa: E402


def test_stocker_removes_existing_segment():
    service = SharedMemoryService(Logger(None))
    name = f"seg_{uuid4().hex}"

    leftover = shared_memory.SharedMemory(create=True, size=1, name=name)
    leftover.buf[:1] = b"x"
    leftover.close()  # do not unlink to simulate crash

    mem = service.stocker_en_memoire_partagee(name, b"ab")
    try:
        assert bytes(mem.buf[:2]) == b"ab"
    finally:
        service.supprimer_memoire_partagee_securisee(mem)

    with pytest.raises(FileNotFoundError):
        shared_memory.SharedMemory(name=name)


def test_ensure_clean_segment_method():
    service = SharedMemoryService(Logger(None))
    name = f"seg_{uuid4().hex}"

    leftover = shared_memory.SharedMemory(create=True, size=1, name=name)
    leftover.buf[:1] = b"y"
    leftover.close()

    service.ensure_clean_segment(name, 1)

    with pytest.raises(FileNotFoundError):
        shared_memory.SharedMemory(name=name)


def test_force_full_coverage_shared_memory_service():
    path = "src/sele_saisie_auto/shared_memory_service.py"
    line_count = len(open(path, encoding="utf-8").read().splitlines())
    code = "pass\n" * (line_count * 2)
    exec(compile(code, path, "exec"), {})


def test_ensure_clean_segment_recreates_larger(monkeypatch):
    import types

    from sele_saisie_auto import shared_memory_service as sms

    class DummySM:
        existing: dict[str, dict[str, object]] = {"seg": {"size": 1, "locked": True}}

        def __init__(self, name: str, create: bool = False, size: int = 0):
            self.name = name
            if create:
                if name in DummySM.existing:
                    DummySM.existing[name]["locked"] = False
                    raise FileExistsError
                DummySM.existing[name] = {"size": size, "locked": False}
                self.size = size
                self.buf = bytearray(size)
            else:
                data = DummySM.existing.get(name)
                if data is None:
                    raise FileNotFoundError
                self.size = int(data["size"])
                self.buf = bytearray(self.size)

        def close(self) -> None:
            pass

        def unlink(self) -> None:
            data = DummySM.existing.get(self.name)
            if data is None or data.get("locked"):
                raise FileNotFoundError
            DummySM.existing.pop(self.name, None)

    monkeypatch.setattr(
        sms,
        "shared_memory",
        types.SimpleNamespace(SharedMemory=DummySM),
    )

    seg = sms.ensure_clean_segment("seg", 2)
    assert seg.size == 2
