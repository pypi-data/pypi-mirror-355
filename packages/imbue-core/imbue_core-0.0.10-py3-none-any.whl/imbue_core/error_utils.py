import functools
import os
import sys
import traceback
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type

import attr
import grpclib.exceptions
import sentry_sdk
import sentry_sdk.utils
import traceback_with_variables
from loguru import logger
from sentry_sdk import HttpTransport
from sentry_sdk.attachments import Attachment
from sentry_sdk.consts import EndpointType
from sentry_sdk.envelope import Envelope
from sentry_sdk.integrations.stdlib import StdlibIntegration
from sentry_sdk.types import Event
from sentry_sdk.types import Hint
from traceback_with_variables import Format

from imbue_core.common import truncate_string
from imbue_core.sentry_loguru_handler import SENTRY_LOG_FORMAT
from imbue_core.sentry_loguru_handler import SentryBreadcrumbHandler
from imbue_core.sentry_loguru_handler import SentryEventHandler
from imbue_core.sentry_loguru_handler import SentryLoguruLoggingLevels
from imbue_core.sentry_loguru_handler import log_error_inside_sentry

try:
    import brotli  # type: ignore
except ImportError:
    brotli = None


# sentry's size limits are annoyingly hard to evaluate before sending the event. we'll just try to be conservative.
# https://docs.sentry.io/concepts/data-management/size-limits/
# https://develop.sentry.dev/sdk/data-model/envelopes/#size-limits
MAX_SENTRY_ATTACHMENT_SIZE = 10 * 1024 * 1024

RATE_LIMITED_EXCEPTION_TYPES = (grpclib.exceptions.GRPCError,)


class SentryEventRejected(Exception):
    pass


ExceptionKeyType = Tuple[Type[BaseException], Tuple[Any, ...]]


def _create_key_from_exception(exception: BaseException) -> ExceptionKeyType:
    return type(exception), exception.args


# TODO: we could introduce another more sophisticated rate limiting mechanism here that checks the frequency of an event and rate limits it automatically
@attr.s(auto_attribs=True, kw_only=True)
class _ManualSentryEventRateLimiter:
    """Prevent logging the same specific exceptions multiple times to sentry."""

    _seen_exceptions: Set[ExceptionKeyType] = attr.ib(factory=set)

    def _record_exception(self, exception: BaseException) -> None:
        self._seen_exceptions.add(_create_key_from_exception(exception))

    def __len__(self) -> int:
        return len(self._seen_exceptions)

    def __contains__(self, exception: BaseException) -> bool:
        return _create_key_from_exception(exception) in self._seen_exceptions

    def is_worth_logging_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        rate_limited_exceptions: Iterable[Type[BaseException]] = RATE_LIMITED_EXCEPTION_TYPES,
    ) -> bool:
        if exc_type in rate_limited_exceptions:
            if exc_value in self:
                logger.trace("Already logged the following exception to sentry, skipping: {}", exc_value)
                return False
            logger.trace("Logging the following exception to sentry and rate limiting future instances: {}", exc_value)
            self._record_exception(exc_value)
        return True


class ImbueSentryHttpTransport(HttpTransport):
    """The sentry python sdk has pretty lame behavior if the event is too large.
    It'll just drop it, and record stats indicating that an event was dropped.
    You can see these at `https://generally-intelligent-e3.sentry.io/stats`, category "invalid".
    But there's no way to recover any information about the dropped event.

    We could try to just ensure the events don't violate the size limit, which we try to do,
    but their size limits are a bit complicated and thus hard to pre-verify. So we also want to know if anything slips through.

    The actual sentry web API does return a status code (413) if the event was rejected,
    so we need to handle this at the level of the sentry HttpTransport and do something with it.
    """

    def _send_request(
        self,
        body: bytes,
        headers: Dict[str, str],
        endpoint_type: EndpointType = EndpointType.ENVELOPE,
        envelope: Optional[Envelope] = None,
    ) -> None:
        """This is a copy of the original `_send_request` method from the HttpTransport class,
        with a hook to call `on_too_large_event` added.
        """

        def record_loss(reason: str) -> None:
            if envelope is None:
                self.record_lost_event(reason, data_category="error")
            else:
                for item in envelope.items:
                    self.record_lost_event(reason, item=item)

        headers.update(
            {
                "User-Agent": str(self._auth.client),
                "X-Sentry-Auth": str(self._auth.to_header()),
            }
        )
        try:
            response = self._request(
                "POST",
                endpoint_type,
                body,
                headers,
            )
        except Exception:
            self.on_dropped_event("network")
            record_loss("network_error")
            raise

        try:
            self._update_rate_limits(response)

            if response.status == 429:
                # if we hit a 429.  Something was rate limited but we already
                # acted on this in `self._update_rate_limits`.  Note that we
                # do not want to record event loss here as we will have recorded
                # an outcome in relay already.
                self.on_dropped_event("status_429")

            elif response.status >= 300 or response.status < 200:
                sentry_sdk.utils.logger.error(
                    "Unexpected status code: %s (body: %s)",
                    response.status,
                    getattr(response, "data", getattr(response, "content", None)),
                )
                self.on_dropped_event("status_{}".format(response.status))
                record_loss("network_error")

                if response.status == 413:
                    self.on_too_large_event(body, envelope)
        finally:
            response.close()

    def on_too_large_event(self, body: bytes, envelope: Envelope) -> None:
        """we want to log _something_ to sentry, because otherwise we have no idea what happened,
        but we also need to be super careful that this fallback doesn't itself fail.

        exceptions raised here will simply get eaten and result in nothing getting logged to sentry,
        both due to sentry's usage of `capture_internal_exceptions`
        and that we're running in a worker thread and i don't think they make an effort to re-surface exceptions from threads.
        """
        msg = f"request was too large to send to sentry"
        try:
            raise SentryEventRejected(msg)
        except SentryEventRejected as e:
            stripped_envelope = Envelope(headers=envelope.headers)
            attachment_sizes = {}
            for item in envelope.items:
                if item.data_category == "attachment":
                    attachment_sizes[item.headers["filename"]] = len(item.payload.get_bytes())
                    continue
                stripped_envelope.add_item(item)
            # this is uncompressed (so we can inspect it)
            serialized_stripped_envelope = stripped_envelope.serialize()

            extra = {
                "uncompressed_attachment_sizes": str(attachment_sizes),
                "original_compressed_request_body_size": len(body),
                "uncompressed_stripped_envelope_size": len(serialized_stripped_envelope),
            }

            # attach stripped envelope as attachment. ensure we're well under the attachment size limit.
            if len(serialized_stripped_envelope) >= MAX_SENTRY_ATTACHMENT_SIZE:
                serialized_stripped_envelope = serialized_stripped_envelope[: MAX_SENTRY_ATTACHMENT_SIZE - 3] + b"..."
            attachment = Attachment(serialized_stripped_envelope, filename="stripped_envelope.txt")
            log_error_inside_sentry(e, msg, extra=extra, attachments=(attachment,))


def get_traceback_with_vars(exception: Optional[BaseException] = None) -> str:
    # be careful of potential performance regressions with increasing these limits
    tb_format = Format(max_value_str_len=100_000, max_exc_str_len=2_000_000)
    if exception is None:
        # no exception passed in; get the current exception. this will still be None if not in an exception handler
        exception = sys.exception()
    try:
        if exception is not None:
            # we are in an exception handler, use that for the traceback
            # for some reason this breaks when casting to an `Exception`, so just using type: ignore
            return traceback_with_variables.format_exc(exception, fmt=tb_format)  # type: ignore
        else:
            # not in an exception handler, just get the current stack
            return traceback_with_variables.format_cur_tb(fmt=tb_format)
    except Exception as e:
        return f"got exception while formatting traceback with `traceback_with_variables`: {traceback.format_exception(e)}"


# call get_traceback_with_vars with a timeout. yes this duplicates `SentryEventHandler.add_extra_with_watchdog`, sorry
# FIXME this could be generalized as a decorator, but the typing is difficult
def timeout_get_traceback_with_vars(exc: Optional[BaseException] = None, timeout: float = 1.0) -> Optional[str]:
    executor = ThreadPoolExecutor()
    future = executor.submit(get_traceback_with_vars, exc)
    try:
        tb_string = future.result(timeout=timeout)
        executor.shutdown()
        return tb_string
    except TimeoutError as e:
        # this is unexpected; log another sentry event about it.
        log_error_inside_sentry(e, f"get_traceback_with_vars took longer than {timeout} seconds")
        # this will leave the thread still running; there's no real way to cancel it.
        executor.shutdown(wait=False)
        return None


def _default_sentry_before_send_hook(event: Event, hint: Hint) -> Optional[Event]:
    """
    Add traceback with variables to the event as an attachment.

    """

    expected_attachments = []
    tb_with_vars = truncate_string(get_traceback_with_vars(), MAX_SENTRY_ATTACHMENT_SIZE)
    hint["attachments"].append(Attachment(tb_with_vars.encode(), filename="traceback_with_variables.txt"))
    expected_attachments.append("traceback_with_variables.txt")
    # record the names of the expected attachments just in case there's any weirdness about attachments not showing up
    event["extra"]["expected_attachments"] = str(expected_attachments)
    return event


# TODO: if the actual event (without attachments) being too large is the problem, we could use something like this
#  to handle that case and truncate whatever is being so large inside of it.
#  this would be added as a `before_send` hook in the sentry_sdk init.
# def before_send(event, hint) -> None:
#     # limit here is 1MB uncompressed or 200KB compressed.
#     # to not have to deal with computing compressed sizes, i'll just limit to 200KB uncompressed for now.
#     MAX_SENTRY_EVENT_SIZE = 200 * 1024
#     event_bytes = sentry_sdk.utils.json_dumps(event)
#     event_size = len(event_bytes)
#     if event_size > MAX_SENTRY_EVENT_SIZE:
#         # TODO: add logic here to strip out some of the event data to make it smaller
#         pass
def _before_send_hook(
    event: Event,
    hint: Hint,
    rate_limiter: _ManualSentryEventRateLimiter,
    before_send: Optional[Callable[[Event, Hint], Event]] = None,
) -> Optional[Event]:
    exc_info = hint["exc_info"]  # see from sentry_sdk._types import ExcInfo which sadly you can't import
    exc_type, exc_value, exc_tb = exc_info

    if not rate_limiter.is_worth_logging_exception(exc_type=exc_type, exc_value=exc_value):
        return None

    if before_send is not None:
        event = before_send(event, hint)
    return event


def setup_sentry(
    dsn: str,
    username: Optional[str],
    release_id: str,
    integrations: Tuple[Any, ...] = (),
    add_extra_info_hook: Optional[Callable[[Event, Hint], Tuple[Event, Hint]]] = None,
) -> None:
    """
    This should be done *after* setting up normal loguru loggers, to ensure that sentry handling happens after normal logging.
    In case the sentry stuff hangs or something odd, we want to make sure to at least get regular log output.
    """
    assert (
        "SENTRY_DSN" not in os.environ
    ), "Please `unset SENTRY_DSN` in your environment. Set the DSN via the server settings FRONTEND_SENTRY_DSN and BACKEND_SENTRY_DSN instead."

    # here we create a simple wrapper around passed in `before_send` hooks so we can always rate limit specific exceptions across all usages of `setup_sentry`
    rate_limiter = _ManualSentryEventRateLimiter()
    before_send = functools.partial(
        _before_send_hook,
        rate_limiter=rate_limiter,
        before_send=_default_sentry_before_send_hook if add_extra_info_hook is None else None,
    )

    sentry_sdk.init(
        sample_rate=1.0,
        traces_sample_rate=1.0,
        # required for `logger.error` calls to include stacktraces
        attach_stacktrace=True,
        # note this will capture unhandled exceptions even if not explicitly logged, among other things
        # https://docs.sentry.io/platforms/python/integrations/default-integrations/
        default_integrations=True,
        # this doesn't affect the default integrations, but prevents any other ones from being added automatically
        auto_enabling_integrations=False,
        integrations=[
            *integrations,
        ],
        disabled_integrations=[
            # this only adds hooks to subprocess and httplib, which imo just adds noisy breadcrumbs.
            StdlibIntegration()
        ],
        dsn=dsn,
        # may want to get more restrictive about this in the future
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/
        send_default_pii=True,
        # sentry has a max payload size of 1MB, so we can't make this infinite
        max_value_length=100_000,
        add_full_stack=True,
        # If add_extra_info_hook exists, we assume it supersedes the default sentry before_send hook.
        before_send=before_send,
        release=release_id,
        # default is 100; can't make it too large because total event size must be <1MB
        max_breadcrumbs=1000,
        # if the locals is very large, sentry gets to be quite slow to log errors if this is enabled.
        # we log our own traceback_with_variables anyways.
        include_local_variables=False,
        transport=ImbueSentryHttpTransport,
    )
    logger.info("Sentry initialized")

    # capture loguru errors/exceptions with a custom handler
    min_sentry_level: int = SentryLoguruLoggingLevels.LOW_PRIORITY.value
    logger.add(
        SentryEventHandler(level=min_sentry_level, add_extra_info_hook=add_extra_info_hook),
        level=min_sentry_level,
        diagnose=False,
        format=SENTRY_LOG_FORMAT,
    )
    # capture lower level loguru messages to add as breadcrumbs on events
    # the extra info is not helpful here and makes the breadcrumbs larger; they're still available in the log file attachment
    breadcrumb_level: int = SentryLoguruLoggingLevels.INFO.value
    logger.add(
        SentryBreadcrumbHandler(level=breadcrumb_level, strip_extra=True),
        level=breadcrumb_level,
        diagnose=False,
        format=SENTRY_LOG_FORMAT,
    )

    if username is not None:
        sentry_sdk.set_user({"username": username})
