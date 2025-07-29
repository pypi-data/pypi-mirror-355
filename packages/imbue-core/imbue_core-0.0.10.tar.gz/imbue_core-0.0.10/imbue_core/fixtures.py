"""These fixtures make it easy to mock out the loguru logger in tests.
"""
from unittest.mock import ANY

import pytest


@pytest.fixture
def mock_loguru_log(mocker):
    """Mock out the loguru logger for testing.

    Error works, not sure about the other levels. Check them out as you use them.
    """
    mock = mocker.patch("loguru.logger._log")
    mock.get_errors = lambda: get_loglines_at_level(mock, "error")
    mock.get_info = lambda: get_loglines_at_level(mock, "info")
    mock.get_warnings = lambda: get_loglines_at_level(mock, "warning")
    yield mock


def get_loglines_at_level(mock_loguru_log, level=ANY):
    return [call for call in mock_loguru_log.mock_calls if len(call.args) > 1 and str(call.args[0]).lower() == level]
