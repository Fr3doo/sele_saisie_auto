import sys
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from sele_saisie_auto.encryption_utils import EncryptionService  # noqa: E402


class DummyLogger:
    def debug(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def warning(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def critical(self, *a, **k):
        pass


@pytest.fixture
def no_io(monkeypatch):
    monkeypatch.setattr(
        "sele_saisie_auto.encryption_utils.get_logger", lambda _: DummyLogger()
    )
    monkeypatch.setattr("sele_saisie_auto.encryption_utils.get_log_file", lambda: "log")


def test_enter_success_and_exit_cleanup(no_io, monkeypatch):
    expected_key = b"k" * 32
    mem_obj = object()
    sms = MagicMock()
    sms.stocker_en_memoire_partagee.return_value = mem_obj

    service = EncryptionService(shared_memory_service=sms)
    monkeypatch.setattr(service, "generer_cle_aes", lambda n: expected_key)
    cle_name = service.memory_config.cle_name

    with service as enc:
        sms.stocker_en_memoire_partagee.assert_called_once_with(cle_name, expected_key)
        assert enc._memoires == [mem_obj]
        assert enc.cle_aes == expected_key

    sms.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_segment_already_exists_then_clean_and_retry(no_io, monkeypatch):
    expected_key = b"a" * 32
    mem_obj = object()
    sms = MagicMock()
    sms.stocker_en_memoire_partagee.side_effect = [FileExistsError(), mem_obj]
    sms.ensure_clean_segment = MagicMock()

    service = EncryptionService(shared_memory_service=sms)
    monkeypatch.setattr(service, "generer_cle_aes", lambda n: expected_key)
    cle_name = service.memory_config.cle_name

    with service as enc:
        assert sms.stocker_en_memoire_partagee.call_count == 2
        sms.ensure_clean_segment.assert_called_once_with(cle_name, len(expected_key))
        assert sms.mock_calls[1:] == [
            call.stocker_en_memoire_partagee(cle_name, expected_key),
            call.ensure_clean_segment(cle_name, len(expected_key)),
            call.stocker_en_memoire_partagee(cle_name, expected_key),
        ]
        assert enc._memoires == [mem_obj]

    sms.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_generic_error_propagates_and_no_leak(no_io, monkeypatch):
    expected_key = b"b" * 32
    sms = MagicMock()
    sms.stocker_en_memoire_partagee.side_effect = ValueError("boom")
    sms.ensure_clean_segment = MagicMock()

    service = EncryptionService(shared_memory_service=sms)
    monkeypatch.setattr(service, "generer_cle_aes", lambda n: expected_key)

    with pytest.raises(ValueError, match="boom"):
        service.__enter__()

    assert service._memoires == []
    assert service.cle_aes is None
    sms.supprimer_memoire_partagee_securisee.assert_not_called()
    sms.ensure_clean_segment.assert_not_called()


def test_exit_suppresses_removal_errors(no_io, monkeypatch):
    expected_key = b"c" * 32
    mem_obj = object()
    sms = MagicMock()
    sms.stocker_en_memoire_partagee.return_value = mem_obj
    sms.supprimer_memoire_partagee_securisee.side_effect = RuntimeError("rm fail")

    service = EncryptionService(shared_memory_service=sms)
    monkeypatch.setattr(service, "generer_cle_aes", lambda n: expected_key)

    with service:
        pass

    sms.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_store_credentials_creates_two_segments_and_cleanup(no_io, monkeypatch):
    expected_key = b"d" * 32
    mem_key = object()
    mem_login = object()
    mem_pwd = object()
    login_blob = b"user"
    pwd_blob = b"pass"

    sms = MagicMock()
    sms.stocker_en_memoire_partagee.side_effect = [mem_key, mem_login, mem_pwd]

    service = EncryptionService(shared_memory_service=sms)
    monkeypatch.setattr(service, "generer_cle_aes", lambda n: expected_key)

    cle_name = service.memory_config.cle_name
    login_name = service.memory_config.login_name
    password_name = service.memory_config.password_name

    with service as enc:
        assert enc._memoires == [mem_key]
        assert enc.cle_aes == expected_key

        enc.store_credentials(login_blob, pwd_blob)

        assert sms.stocker_en_memoire_partagee.call_args_list == [
            call(cle_name, expected_key),
            call(login_name, login_blob),
            call(password_name, pwd_blob),
        ]
        assert enc._memoires == [mem_key, mem_login, mem_pwd]

    assert sms.supprimer_memoire_partagee_securisee.call_args_list == [
        call(mem_key),
        call(mem_login),
        call(mem_pwd),
    ]
    assert service.cle_aes is None
    assert service._memoires == []
