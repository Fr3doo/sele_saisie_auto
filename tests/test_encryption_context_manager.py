from unittest.mock import Mock, call

import pytest

from sele_saisie_auto.exceptions import AutomationExitError
from sele_saisie_auto.logging_service import Logger
from sele_saisie_auto.memory_config import MemoryConfig
from sele_saisie_auto.shared_memory_service import SharedMemoryService
from tests.conftest import assert_call_prefix, assert_call_sequence, store_setup


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


def test_enter_success_and_exit_cleanup(mem_cfg, service_factory):
    expected_key = b"k" * mem_cfg.key_size
    mem_obj = object()

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.return_value = mem_obj

    service = service_factory(mock_service, mem_cfg, expected_key)

    with service as enc:
        mock_service.stocker_en_memoire_partagee.assert_called_once_with(
            mem_cfg.cle_name, expected_key
        )
        assert enc._memoires == [mem_obj]
        assert enc.cle_aes == expected_key

    mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def _setup_retry_service(mem_cfg: MemoryConfig, service_factory):
    expected_key = b"k" * mem_cfg.key_size
    mem_obj = object()
    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.side_effect = [FileExistsError(), mem_obj]
    service = service_factory(mock_service, mem_cfg, expected_key)
    return service, mock_service, expected_key, mem_obj


def test_enter_segment_retry_calls_clean_and_retry(mem_cfg, service_factory):
    service, mock_service, expected_key, _ = _setup_retry_service(
        mem_cfg, service_factory
    )

    with service:
        assert mock_service.stocker_en_memoire_partagee.call_count == 2
        mock_service.ensure_clean_segment.assert_called_once_with(
            mem_cfg.cle_name, len(expected_key)
        )
        assert_call_prefix(
            mock_service,
            call.stocker_en_memoire_partagee(mem_cfg.cle_name, expected_key),
            call.ensure_clean_segment(mem_cfg.cle_name, len(expected_key)),
            call.stocker_en_memoire_partagee(mem_cfg.cle_name, expected_key),
        )


def test_enter_segment_retry_state_and_cleanup(mem_cfg, service_factory):
    service, mock_service, expected_key, mem_obj = _setup_retry_service(
        mem_cfg, service_factory
    )

    with service as enc:
        assert enc._memoires == [mem_obj]
        assert enc.cle_aes == expected_key

    mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_enter_generic_error_propagates_and_no_leak(mem_cfg, service_factory):
    expected_key = b"k" * mem_cfg.key_size

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.side_effect = ValueError("boom")

    service = service_factory(mock_service, mem_cfg, expected_key)

    with pytest.raises(ValueError, match="boom"):
        service.__enter__()

    assert service._memoires == []
    assert service.cle_aes is None
    mock_service.supprimer_memoire_partagee_securisee.assert_not_called()
    mock_service.ensure_clean_segment.assert_not_called()


def test_exit_suppresses_removal_errors(mem_cfg, service_factory):
    expected_key = b"k" * mem_cfg.key_size
    mem_obj = object()

    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.return_value = mem_obj
    mock_service.supprimer_memoire_partagee_securisee.side_effect = RuntimeError(
        "rm fail"
    )

    service = service_factory(mock_service, mem_cfg, expected_key)

    with service:
        pass

    mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(mem_obj)
    assert service.cle_aes is None
    assert service._memoires == []


def test_store_credentials_creates_two_segments_in_order(mem_cfg, service_factory):
    (
        service,
        mock_service,
        expected_key,
        _mem_key,
        _mem_login,
        _mem_pwd,
        login_blob,
        pwd_blob,
    ) = store_setup(mem_cfg, service_factory)

    with service as enc:
        enc.store_credentials(login_blob, pwd_blob)
        assert_call_sequence(
            mock_service.stocker_en_memoire_partagee,
            call(mem_cfg.cle_name, expected_key),
            call(mem_cfg.login_name, login_blob),
            call(mem_cfg.password_name, pwd_blob),
        )


def test_store_credentials_tracks_segments(mem_cfg, service_factory):
    (
        service,
        _mock_service,
        expected_key,
        mem_key,
        mem_login,
        mem_pwd,
        login_blob,
        pwd_blob,
    ) = store_setup(mem_cfg, service_factory)

    with service as enc:
        assert enc._memoires == [mem_key]
        assert enc.cle_aes == expected_key
        enc.store_credentials(login_blob, pwd_blob)
        assert enc._memoires == [mem_key, mem_login, mem_pwd]


def test_store_credentials_cleans_up_on_exit(mem_cfg, service_factory):
    (
        service,
        mock_service,
        _expected_key,
        mem_key,
        mem_login,
        mem_pwd,
        login_blob,
        pwd_blob,
    ) = store_setup(mem_cfg, service_factory)

    with service as enc:
        enc.store_credentials(login_blob, pwd_blob)

    assert_call_sequence(
        mock_service.supprimer_memoire_partagee_securisee,
        call(mem_key),
        call(mem_login),
        call(mem_pwd),
    )
    assert service.cle_aes is None
    assert service._memoires == []


def test_retrieve_credentials_missing_segment_cleans_key_best_effort(
    mem_cfg, service_factory
):
    expected_key = b"k" * mem_cfg.key_size
    mem_key = object()
    mock_service = Mock(spec=SharedMemoryService)
    mock_service.stocker_en_memoire_partagee.return_value = object()
    mock_service.recuperer_de_memoire_partagee.return_value = (mem_key, expected_key)
    service = service_factory(mock_service, mem_cfg, expected_key)
    service._lire_segment = Mock(side_effect=FileNotFoundError)

    with service as enc:
        with pytest.raises(AutomationExitError, match="identifiants non trouvés"):
            enc.retrieve_credentials()
        mock_service.supprimer_memoire_partagee_securisee.assert_called_once_with(
            mem_key
        )
