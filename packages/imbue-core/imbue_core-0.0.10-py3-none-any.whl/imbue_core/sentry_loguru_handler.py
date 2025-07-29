"""
inlines sentry_sdk.integrations.loguru and sentry_sdk.integrations.logging, so we can make some changes.
i'm intentionally keeping most of the old logic so this still behaves roughly as expected/documented.

we probably could/should go through and fully streamline this though to do just what we need.

The changes so far (could be out of date):
- adds `strip_extra` to the breadcrumb handler
- adds `add_extra_info_hook` to the event handler, with a watchdog to make sure it doesn't slow things down
"""
import enum
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from datetime import timezone
from fnmatch import fnmatch
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Tuple

import sentry_sdk
from sentry_sdk import new_scope
from sentry_sdk.attachments import Attachment

# "This disables recording (both in breadcrumbs and as events) calls to a logger of a specific name.  Among other uses, many of our integrations
# use this to prevent their actions being recorded as breadcrumbs. Exposed to users as a way to quiet spammy loggers."
# We have to import it so that existing setters work properly
from sentry_sdk.integrations.logging import _IGNORED_LOGGERS
from sentry_sdk.types import Event
from sentry_sdk.types import Hint
from sentry_sdk.utils import current_stacktrace
from sentry_sdk.utils import event_from_exception
from sentry_sdk.utils import to_string

from imbue_core.constants import HIGH_PRIORITY_LEVEL
from imbue_core.constants import LOW_PRIORITY_LEVEL
from imbue_core.constants import MEDIUM_PRIORITY_LEVEL

# for formatting the log message. we don't want the timestamp/level because sentry already tracks that,
# and it messes up event grouping since this string becomes the event title.
SENTRY_LOG_FORMAT = "{name}:{function}:{line} - {message}"


class SentryLoguruLoggingLevels(enum.IntEnum):
    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    # additional loguru levels for sentry hotwiring
    LOW_PRIORITY = LOW_PRIORITY_LEVEL
    MEDIUM_PRIORITY = MEDIUM_PRIORITY_LEVEL
    HIGH_PRIORITY = HIGH_PRIORITY_LEVEL
    ERROR = 40
    CRITICAL = 50


class _BaseHandler(logging.Handler):
    COMMON_RECORD_ATTRS = frozenset(
        (
            "args",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "linenno",
            "lineno",
            "message",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack",
            "tags",
            "taskName",
            "thread",
            "threadName",
            "stack_info",
        )
    )

    def _can_record(self, record: logging.LogRecord) -> bool:
        """Prevents ignored loggers from recording"""
        for logger in _IGNORED_LOGGERS:
            if fnmatch(record.name, logger):
                return False
        return True

    def _extra_from_record(self, record: logging.LogRecord) -> dict[str, object]:
        return {
            k: v
            for k, v in vars(record).items()
            if k not in self.COMMON_RECORD_ATTRS and (not isinstance(k, str) or not k.startswith("_"))
        }

    def _logging_to_event_level(self, record: logging.LogRecord) -> str:
        try:
            return SentryLoguruLoggingLevels(record.levelno).name.lower()
        except ValueError:
            return record.levelname.lower() if record.levelname else ""


class SentryEventHandler(_BaseHandler):
    """A logging handler that emits Sentry events for each log record."""

    def __init__(
        self,
        level: int = logging.NOTSET,
        add_extra_info_hook: Optional[Callable[[Event, Hint], Tuple[Event, Hint]]] = None,
    ) -> None:
        super().__init__(level=level)
        self.add_extra_info_hook = add_extra_info_hook
        self.add_extra_info_previously_timed_out = False

    def emit(self, record: logging.LogRecord) -> Any:
        self.format(record)
        return self._emit(record)

    def _emit(self, record: logging.LogRecord) -> None:
        if not self._can_record(record):
            return

        client = sentry_sdk.get_client()
        if not client.is_active():
            return

        client_options = client.options

        # exc_info might be None or (None, None, None)
        #
        # exc_info may also be any falsy value due to Python stdlib being
        # liberal with what it receives and Celery's billiard being "liberal"
        # with what it sends. See
        # https://github.com/getsentry/sentry-python/issues/904
        if record.exc_info and record.exc_info[0] is not None:
            event, hint = event_from_exception(
                record.exc_info,
                client_options=client_options,
                mechanism={"type": "logging", "handled": True},
            )
        elif (record.exc_info and record.exc_info[0] is None) or record.stack_info:
            event = {}
            hint = {}
            event["threads"] = {
                "values": [
                    {
                        "stacktrace": current_stacktrace(
                            include_local_variables=client_options["include_local_variables"],
                            max_value_length=client_options["max_value_length"],
                        ),
                        "crashed": False,
                        "current": True,
                    }
                ]
            }
        else:
            event = {}
            hint = {}

        hint["log_record"] = record

        level = self._logging_to_event_level(record)
        if level in {"debug", "info", "warning", "error", "critical", "fatal"}:
            # standard levels
            event["level"] = level  # type: ignore[typeddict-item]
        elif level in {"low_prio", "med_prio", "high_prio"}:
            # artificial sentry priority induction
            match level:
                case "low_prio":
                    event["level"] = "info"
                case "med_prio":
                    event["level"] = "warning"
                case "high_prio":
                    event["level"] = "error"

        event["logger"] = record.name

        # Log records from `warnings` module as separate issues
        record_captured_from_warnings_module = record.name == "py.warnings" and record.msg == "%s"
        if record_captured_from_warnings_module:
            # use the actual message and not "%s" as the message
            # this prevents grouping all warnings under one "%s" issue
            msg = record.args[0]  # type: ignore

            event["logentry"] = {
                "message": msg,
                "params": (),
            }

        else:
            event["logentry"] = {
                "message": to_string(record.msg),
                "params": record.args,
            }

        event["extra"] = self._extra_from_record(record)

        if self.add_extra_info_hook:
            event, hint = self.add_extra_with_watchdog(event, hint, timeout=1)

        sentry_sdk.capture_event(event, hint)

    def add_extra_with_watchdog(self, event: Event, hint: Hint, timeout: float) -> Event:
        """Call the add_extra_info_hook with a watchdog so we can skip it if it's slow, and get another sentry error about that."""
        if self.add_extra_info_previously_timed_out:
            return event
        if "attachments" not in hint:
            hint["attachments"] = []
        executor = ThreadPoolExecutor()
        future = executor.submit(self.add_extra_info_hook, event, hint)
        try:
            event, hint = future.result(timeout=timeout)
            executor.shutdown()
            return event, hint
        except TimeoutError as e:
            # this is unexpected; log another sentry event about it.
            log_error_inside_sentry(e, f"add_extra_info_hook took longer than {timeout} seconds")
            # this will leave the thread still running; there's no real way to cancel it.
            # we'll at least set this flag so future errors don't try to run the (bugged?) hook again.
            executor.shutdown(wait=False)
            self.add_extra_info_previously_timed_out = True

        # continue with the main event without the extra info
        return event, hint


class SentryBreadcrumbHandler(_BaseHandler):
    """
    A logging handler that records breadcrumbs for each log record.

    Note that you do not have to use this class if the logging integration is enabled, which it is by default.
    """

    def __init__(self, level: int = logging.NOTSET, strip_extra: bool = False) -> None:
        super().__init__(level=level)
        self.strip_extra = strip_extra

    def emit(self, record: logging.LogRecord) -> Any:
        self.format(record)
        return self._emit(record)

    def _emit(self, record: logging.LogRecord) -> None:
        if not self._can_record(record):
            return

        sentry_sdk.add_breadcrumb(self._breadcrumb_from_record(record), hint={"log_record": record})

    def _breadcrumb_from_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        return {
            "type": "log",
            "level": self._logging_to_event_level(record),
            "category": record.name,
            "message": record.message,
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc),
            "data": self._extra_from_record(record) if not self.strip_extra else {},
        }


def log_error_inside_sentry(
    exception: Exception,
    message: str,
    extra: Optional[Dict[str, str]] = None,
    attachments: Optional[Iterable[Attachment]] = None,
) -> None:
    """Log an error to sentry that happens during processing of a sentry event.

    This needs to be done very carefully to ensure it won't fail - we don't want to have to have a fallback-fallback handler.
    The caller should ensure everything passed into this is small so there's no chance of size issues.
    """
    client = sentry_sdk.get_client()
    # we want to get rid of any breadcrumbs, attachments, and other stuff that might have caused the original request to fail.
    # this will obviously make it harder to debug; we may want to selectively add some of this back.
    with new_scope() as scope:
        scope.clear()
        event, hint = event_from_exception(
            exception, client_options=client.options, mechanism={"type": "watchdog", "handled": True}
        )
        event["message"] = message
        if extra is not None:
            if "extra" not in event:
                event["extra"] = {}
            for k, v in extra.items():
                event["extra"][k] = v
        if attachments is not None:
            if "attachments" not in hint:
                hint["attachments"] = []
            for attachment in attachments:
                hint["attachments"].append(attachment)
        # Note that new_scope() gives a new "current scope" but doesn't affect the global or isolation scope,
        # which is where most info is actually stored. Typically all 3 scopes are merged before logging the event.
        # So we'll make sure to call capture_event in such a way that this merging doesn't happen.
        client.capture_event(event=event, hint=hint, scope=scope)
