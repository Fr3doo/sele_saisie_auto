from unittest.mock import MagicMock, call

import pytest

from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.shared_memory_service import SharedMemoryService


def _make_service(
    monkeypatch, shared_service: SharedMemoryService
) -> EncryptionService:
    """Create ``EncryptionService`` with patched logger helpers."""
    monkeypatch.setattr(
        "sele_saisie_auto.encryption_utils.get_logger", lambda lf: MagicMock()
    )
    monkeypatch.setattr(
        "sele_saisie_auto.encryption_utils.get_log_file", lambda: "log.html"
    )
    return EncryptionService("log.html", shared_memory_service=shared_service)


def test_enter_success_and_exit_cleanup(monkeypatch):
    mem_obj = object()
    shared = MagicMock(spec=SharedMemoryService)
    shared.stocker_en_memoire_partagee.return_value = mem_obj
    service = _make_service(monkeypatch, shared)
    expected_key = b"k" * service.memory_config.key_size
    monkeypatch.setattr(service, "generer_cle_aes", lambda _: expected_key)

    with service as enc:
        shared.stocker_en_memoire_partagee.assert_called_once_with(
            service.memory_config.cle_name, expected_key
        )
        assert enc._memoires == [mem_obj]
        assert enc.cle_aes == expected_key

    shared.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_segment_already_exists_then_clean_and_retry(monkeypatch):
    mem_obj = object()
    shared = MagicMock(spec=SharedMemoryService)
    shared.stocker_en_memoire_partagee.side_effect = [FileExistsError(), mem_obj]
    service = _make_service(monkeypatch, shared)
    expected_key = b"x" * service.memory_config.key_size
    monkeypatch.setattr(service, "generer_cle_aes", lambda _: expected_key)

    with service as enc:
        assert shared.stocker_en_memoire_partagee.call_count == 2
        shared.ensure_clean_segment.assert_called_once_with(
            service.memory_config.cle_name, len(expected_key)
        )
        assert shared.mock_calls == [
            call.stocker_en_memoire_partagee(
                service.memory_config.cle_name, expected_key
            ),
            call.ensure_clean_segment(
                service.memory_config.cle_name, len(expected_key)
            ),
            call.stocker_en_memoire_partagee(
                service.memory_config.cle_name, expected_key
            ),
        ]
        assert enc._memoires == [mem_obj]

    shared.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_generic_error_propagates_and_no_leak(monkeypatch):
    shared = MagicMock(spec=SharedMemoryService)
    shared.stocker_en_memoire_partagee.side_effect = ValueError("boom")
    service = _make_service(monkeypatch, shared)
    expected_key = b"y" * service.memory_config.key_size
    monkeypatch.setattr(service, "generer_cle_aes", lambda _: expected_key)

    with pytest.raises(ValueError, match="boom"):
        service.__enter__()

    assert service._memoires == []
    assert service.cle_aes is None
    shared.supprimer_memoire_partagee_securisee.assert_not_called()
    shared.ensure_clean_segment.assert_not_called()


def test_exit_suppresses_removal_errors(monkeypatch):
    mem_obj = object()
    shared = MagicMock(spec=SharedMemoryService)
    shared.stocker_en_memoire_partagee.return_value = mem_obj
    shared.supprimer_memoire_partagee_securisee.side_effect = RuntimeError("rm fail")
    service = _make_service(monkeypatch, shared)
    expected_key = b"z" * service.memory_config.key_size
    monkeypatch.setattr(service, "generer_cle_aes", lambda _: expected_key)

    with service:
        pass

    shared.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_store_credentials_creates_two_segments_and_cleanup(monkeypatch):
    mem_key, mem_login, mem_pwd = object(), object(), object()
    shared = MagicMock(spec=SharedMemoryService)
    shared.stocker_en_memoire_partagee.side_effect = [mem_key, mem_login, mem_pwd]
    service = _make_service(monkeypatch, shared)
    expected_key = b"w" * service.memory_config.key_size
    monkeypatch.setattr(service, "generer_cle_aes", lambda _: expected_key)
    login_blob = b"login"
    pwd_blob = b"pwd"

    with service as enc:
        assert enc._memoires == [mem_key]
        assert enc.cle_aes == expected_key
        enc.store_credentials(login_blob, pwd_blob)
        assert shared.stocker_en_memoire_partagee.call_args_list == [
            call(service.memory_config.cle_name, expected_key),
            call(service.memory_config.login_name, login_blob),
            call(service.memory_config.password_name, pwd_blob),
        ]
        assert enc._memoires == [mem_key, mem_login, mem_pwd]

    shared.supprimer_memoire_partagee_securisee.assert_has_calls(
        [call(mem_key), call(mem_login), call(mem_pwd)]
    )
    assert shared.supprimer_memoire_partagee_securisee.call_count == 3
    assert service.cle_aes is None
    assert service._memoires == []
