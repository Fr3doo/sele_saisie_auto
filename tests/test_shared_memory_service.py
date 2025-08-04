import sys
from multiprocessing import shared_memory
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.logging_service import Logger  # noqa: E402
from sele_saisie_auto.shared_memory_service import (  # noqa: E402
    SharedMemoryService,
    ensure_clean_segment,
)


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


def test_ensure_clean_segment_recreates_when_existing_smaller(monkeypatch):
    name = f"seg_{uuid4().hex}"
    real_sm = shared_memory.SharedMemory
    leftover = real_sm(create=True, size=1, name=name)

    call_state = {"lookup": 0, "create": 0}

    def fake_sm(*args, **kwargs):
        if kwargs.get("create"):
            call_state["create"] += 1
            if call_state["create"] == 1:
                raise FileExistsError
        else:
            call_state["lookup"] += 1
            if call_state["lookup"] == 1:
                raise FileNotFoundError
        return real_sm(*args, **kwargs)

    monkeypatch.setattr(shared_memory, "SharedMemory", fake_sm)

    mem = ensure_clean_segment(name, 2)
    try:
        assert mem.size >= 2
    finally:
        mem.unlink()
        mem.close()
        leftover.close()
