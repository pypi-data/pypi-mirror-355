"""Tests for the behaviour of errors in our system."""

from imbue_core.async_monkey_patches import log_exception
from imbue_core.errors import ImbueRuntimeException
from imbue_core.fixtures import mock_loguru_log
from imbue_core.serialization import SerializedException

_ = mock_loguru_log


def test_imbue_runtime_exceptions__logged_only_once(mock_loguru_log):
    with mock_loguru_log:
        try:
            raise ImbueRuntimeException("This is our exception")
        except ImbueRuntimeException as e:
            log_exception(e, "Ensuring  this is logged once")
            log_exception(e, "Should not be logged twice")

    assert len(mock_loguru_log.get_errors()) == 1, "This should not have logged again"


def test_imbue_runtime_exceptions__retain_logged_status(mock_loguru_log):
    with mock_loguru_log:
        try:
            raise ImbueRuntimeException("This is our exception")
        except ImbueRuntimeException as e:
            log_exception(e, "Ensuring  this is logged once")
            assert e._was_logged_by_log_exception
            sre = SerializedException.build(e)

        reconstructed_exception = sre.construct_instance()
        assert reconstructed_exception._was_logged_by_log_exception
        log_exception(reconstructed_exception, "This should not actually log")

    assert len(mock_loguru_log.get_errors()) == 1, "This should not have logged again"
