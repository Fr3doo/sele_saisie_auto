import sys
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from sele_saisie_auto.encryption_utils import EncryptionService


def _make_service(monkeypatch, shared, expected_key: bytes) -> EncryptionService:
    monkeypatch.setattr(
        "sele_saisie_auto.encryption_utils.get_logger", lambda *_: MagicMock()
    )
    monkeypatch.setattr(
        "sele_saisie_auto.encryption_utils.get_log_file", lambda: "log"
    )
    service = EncryptionService(shared_memory_service=shared)
    service.generer_cle_aes = MagicMock(return_value=expected_key)
    return service


def test_enter_success_and_exit_cleanup(monkeypatch):
    mem_obj = object()
    expected_key = b"k" * 32
    shared = MagicMock()
    shared.stocker_en_memoire_partagee.return_value = mem_obj
    shared.supprimer_memoire_partagee_securisee = MagicMock()
    shared.ensure_clean_segment = MagicMock()

    service = _make_service(monkeypatch, shared, expected_key)
    cle_name = service.memory_config.cle_name

    with service as enc:
        shared.stocker_en_memoire_partagee.assert_called_once_with(cle_name, expected_key)
        assert enc._memoires == [mem_obj]
        assert enc.cle_aes == expected_key

    shared.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_segment_already_exists_then_clean_and_retry(monkeypatch):
    mem_obj = object()
    expected_key = b"k" * 32
    shared = MagicMock()
    shared.stocker_en_memoire_partagee.side_effect = [FileExistsError(), mem_obj]
    shared.supprimer_memoire_partagee_securisee = MagicMock()
    shared.ensure_clean_segment = MagicMock()

    service = _make_service(monkeypatch, shared, expected_key)
    cle_name = service.memory_config.cle_name

    with service as enc:
        assert shared.stocker_en_memoire_partagee.call_count == 2
        shared.ensure_clean_segment.assert_called_once_with(cle_name, len(expected_key))
        expected_calls = [
            call.stocker_en_memoire_partagee(cle_name, expected_key),
            call.ensure_clean_segment(cle_name, len(expected_key)),
            call.stocker_en_memoire_partagee(cle_name, expected_key),
        ]
        assert shared.method_calls == expected_calls
        assert enc._memoires == [mem_obj]

    shared.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_generic_error_propagates_and_no_leak(monkeypatch):
    expected_key = b"k" * 32
    shared = MagicMock()
    shared.stocker_en_memoire_partagee.side_effect = ValueError("boom")
    shared.supprimer_memoire_partagee_securisee = MagicMock()
    shared.ensure_clean_segment = MagicMock()

    service = _make_service(monkeypatch, shared, expected_key)

    with pytest.raises(ValueError, match="boom"):
        service.__enter__()

    assert service._memoires == []
    assert service.cle_aes is None
    shared.supprimer_memoire_partagee_securisee.assert_not_called()
    shared.ensure_clean_segment.assert_not_called()


def test_exit_suppresses_removal_errors(monkeypatch):
    mem_obj = object()
    expected_key = b"k" * 32
    shared = MagicMock()
    shared.stocker_en_memoire_partagee.return_value = mem_obj
    shared.supprimer_memoire_partagee_securisee.side_effect = RuntimeError("rm fail")
    shared.ensure_clean_segment = MagicMock()

    service = _make_service(monkeypatch, shared, expected_key)

    with service:
        pass

    shared.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_store_credentials_creates_two_segments_and_cleanup(monkeypatch):
    mem_key = object()
    mem_login = object()
    mem_pwd = object()
    expected_key = b"k" * 32
    login_blob = b"user"
    pwd_blob = b"pass"

    shared = MagicMock()
    shared.stocker_en_memoire_partagee.side_effect = [mem_key, mem_login, mem_pwd]
    shared.supprimer_memoire_partagee_securisee = MagicMock()
    shared.ensure_clean_segment = MagicMock()

    service = _make_service(monkeypatch, shared, expected_key)
    cle_name = service.memory_config.cle_name
    login_name = service.memory_config.login_name
    password_name = service.memory_config.password_name

    with service as enc:
        assert enc._memoires == [mem_key]
        assert enc.cle_aes == expected_key
        enc.store_credentials(login_blob, pwd_blob)
        expected_store_calls = [
            call(cle_name, expected_key),
            call(login_name, login_blob),
            call(password_name, pwd_blob),
        ]
        assert shared.stocker_en_memoire_partagee.call_args_list == expected_store_calls
        assert enc._memoires == [mem_key, mem_login, mem_pwd]

    expected_remove_calls = [call(mem_key), call(mem_login), call(mem_pwd)]
    assert shared.supprimer_memoire_partagee_securisee.call_args_list == expected_remove_calls
    assert service.cle_aes is None
    assert service._memoires == []
