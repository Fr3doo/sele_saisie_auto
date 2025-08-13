import pytest
from unittest.mock import Mock, call

from sele_saisie_auto.encryption_utils import EncryptionService
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.shared_memory_service import SharedMemoryService
from sele_saisie_auto.logging_service import Logger


@pytest.fixture(autouse=True)
def _patch_logger(monkeypatch):
    dummy_logger = Mock(spec=Logger)
    monkeypatch.setattr(
        "sele_saisie_auto.encryption_utils.get_logger", lambda lf: dummy_logger
    )
    monkeypatch.setattr("sele_saisie_auto.encryption_utils.get_log_file", lambda: "log")
    return dummy_logger


@pytest.fixture
def mem_cfg():
    return MemoryConfig()


def _make_service(mock_service: Mock, mem_cfg: MemoryConfig, expected_key: bytes) -> EncryptionService:
    service = EncryptionService(shared_memory_service=mock_service, memory_config=mem_cfg)
    service.generer_cle_aes = Mock(return_value=expected_key)
    return service


def test_enter_success_and_exit_cleanup(mem_cfg):
    expected_key = b"k" * mem_cfg.key_size
    mem_obj = object()

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.return_value = mem_obj

    service = _make_service(mock_service, mem_cfg, expected_key)

    with service as enc:
        mock_service.stocker_en_memoire_partagee.assert_called_once_with(
            mem_cfg.cle_name, expected_key
        )
        assert enc._memoires == [mem_obj]
        assert enc.cle_aes == expected_key

    mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_segment_already_exists_then_clean_and_retry(mem_cfg):
    expected_key = b"k" * mem_cfg.key_size
    mem_obj = object()

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.side_effect = [FileExistsError(), mem_obj]

    service = _make_service(mock_service, mem_cfg, expected_key)

    with service as enc:
        assert mock_service.stocker_en_memoire_partagee.call_count == 2
        mock_service.ensure_clean_segment.assert_called_once_with(
            mem_cfg.cle_name, len(expected_key)
        )
        expected_order = [
            call.stocker_en_memoire_partagee(mem_cfg.cle_name, expected_key),
            call.ensure_clean_segment(mem_cfg.cle_name, len(expected_key)),
            call.stocker_en_memoire_partagee(mem_cfg.cle_name, expected_key),
        ]
        assert mock_service.mock_calls[:3] == expected_order
        assert enc._memoires == [mem_obj]

    mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_generic_error_propagates_and_no_leak(mem_cfg):
    expected_key = b"k" * mem_cfg.key_size

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.side_effect = ValueError("boom")

    service = _make_service(mock_service, mem_cfg, expected_key)

    with pytest.raises(ValueError, match="boom"):
        service.__enter__()

    assert service._memoires == []
    assert service.cle_aes is None
    mock_service.supprimer_memoire_partagee_securisee.assert_not_called()
    mock_service.ensure_clean_segment.assert_not_called()


def test_exit_suppresses_removal_errors(mem_cfg):
    expected_key = b"k" * mem_cfg.key_size
    mem_obj = object()

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.return_value = mem_obj
    mock_service.supprimer_memoire_partagee_securisee.side_effect = RuntimeError("rm fail")

    service = _make_service(mock_service, mem_cfg, expected_key)

    with service:
        pass

    mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_store_credentials_creates_two_segments_and_cleanup(mem_cfg):
    expected_key = b"k" * mem_cfg.key_size
    mem_key = object()
    mem_login = object()
    mem_pwd = object()
    login_blob = b"login-data"
    pwd_blob = b"pwd-data"

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.side_effect = [
        mem_key,
        mem_login,
        mem_pwd,
    ]

    service = _make_service(mock_service, mem_cfg, expected_key)

    with service as enc:
        assert enc._memoires == [mem_key]
        assert enc.cle_aes == expected_key
        enc.store_credentials(login_blob, pwd_blob)
        expected_calls = [
            call(mem_cfg.cle_name, expected_key),
            call(mem_cfg.login_name, login_blob),
            call(mem_cfg.password_name, pwd_blob),
        ]
        assert mock_service.stocker_en_memoire_partagee.call_args_list == expected_calls
        assert enc._memoires == [mem_key, mem_login, mem_pwd]

    expected_rm_calls = [call(mem_key), call(mem_login), call(mem_pwd)]
    assert (
        mock_service.supprimer_memoire_partagee_securisee.call_args_list
        == expected_rm_calls
    )
    assert service.cle_aes is None
    assert service._memoires == []
