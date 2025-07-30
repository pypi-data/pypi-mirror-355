import debugg_ai_sdk
from debugg_ai_sdk.consts import OP, SPANDATA
from debugg_ai_sdk.integrations import Integration, DidNotEnable
from debugg_ai_sdk.tracing import BAGGAGE_HEADER_NAME
from debugg_ai_sdk.tracing_utils import Baggage, should_propagate_trace
from debugg_ai_sdk.utils import (
    SENSITIVE_DATA_SUBSTITUTE,
    capture_internal_exceptions,
    ensure_integration_enabled,
    logger,
    parse_url,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import Any


try:
    from httpx import AsyncClient, Client, Request, Response  # type: ignore
except ImportError:
    raise DidNotEnable("httpx is not installed")

__all__ = ["HttpxIntegration"]


class HttpxIntegration(Integration):
    identifier = "httpx"
    origin = f"auto.http.{identifier}"

    @staticmethod
    def setup_once():
        # type: () -> None
        """
        httpx has its own transport layer and can be customized when needed,
        so patch Client.send and AsyncClient.send to support both synchronous and async interfaces.
        """
        _install_httpx_client()
        _install_httpx_async_client()


def _install_httpx_client():
    # type: () -> None
    real_send = Client.send

    @ensure_integration_enabled(HttpxIntegration, real_send)
    def send(self, request, **kwargs):
        # type: (Client, Request, **Any) -> Response
        parsed_url = None
        with capture_internal_exceptions():
            parsed_url = parse_url(str(request.url), sanitize=False)

        with debugg_ai_sdk.start_span(
            op=OP.HTTP_CLIENT,
            name="%s %s"
            % (
                request.method,
                parsed_url.url if parsed_url else SENSITIVE_DATA_SUBSTITUTE,
            ),
            origin=HttpxIntegration.origin,
        ) as span:
            span.set_data(SPANDATA.HTTP_METHOD, request.method)
            if parsed_url is not None:
                span.set_data("url", parsed_url.url)
                span.set_data(SPANDATA.HTTP_QUERY, parsed_url.query)
                span.set_data(SPANDATA.HTTP_FRAGMENT, parsed_url.fragment)

            if should_propagate_trace(debugg_ai_sdk.get_client(), str(request.url)):
                for (
                    key,
                    value,
                ) in debugg_ai_sdk.get_current_scope().iter_trace_propagation_headers():
                    logger.debug(
                        "[Tracing] Adding `{key}` header {value} to outgoing request to {url}.".format(
                            key=key, value=value, url=request.url
                        )
                    )

                    if key == BAGGAGE_HEADER_NAME:
                        _add_debugg_ai_baggage_to_headers(request.headers, value)
                    else:
                        request.headers[key] = value

            rv = real_send(self, request, **kwargs)

            span.set_http_status(rv.status_code)
            span.set_data("reason", rv.reason_phrase)

            return rv

    Client.send = send


def _install_httpx_async_client():
    # type: () -> None
    real_send = AsyncClient.send

    async def send(self, request, **kwargs):
        # type: (AsyncClient, Request, **Any) -> Response
        if debugg_ai_sdk.get_client().get_integration(HttpxIntegration) is None:
            return await real_send(self, request, **kwargs)

        parsed_url = None
        with capture_internal_exceptions():
            parsed_url = parse_url(str(request.url), sanitize=False)

        with debugg_ai_sdk.start_span(
            op=OP.HTTP_CLIENT,
            name="%s %s"
            % (
                request.method,
                parsed_url.url if parsed_url else SENSITIVE_DATA_SUBSTITUTE,
            ),
            origin=HttpxIntegration.origin,
        ) as span:
            span.set_data(SPANDATA.HTTP_METHOD, request.method)
            if parsed_url is not None:
                span.set_data("url", parsed_url.url)
                span.set_data(SPANDATA.HTTP_QUERY, parsed_url.query)
                span.set_data(SPANDATA.HTTP_FRAGMENT, parsed_url.fragment)

            if should_propagate_trace(debugg_ai_sdk.get_client(), str(request.url)):
                for (
                    key,
                    value,
                ) in debugg_ai_sdk.get_current_scope().iter_trace_propagation_headers():
                    logger.debug(
                        "[Tracing] Adding `{key}` header {value} to outgoing request to {url}.".format(
                            key=key, value=value, url=request.url
                        )
                    )
                    if key == BAGGAGE_HEADER_NAME and request.headers.get(
                        BAGGAGE_HEADER_NAME
                    ):
                        # do not overwrite any existing baggage, just append to it
                        request.headers[key] += "," + value
                    else:
                        request.headers[key] = value

            rv = await real_send(self, request, **kwargs)

            span.set_http_status(rv.status_code)
            span.set_data("reason", rv.reason_phrase)

            return rv

    AsyncClient.send = send


def _add_debugg_ai_baggage_to_headers(headers, debugg_ai_baggage):
    # type: (MutableMapping[str, str], str) -> None
    """Add the DebuggAI baggage to the headers.

    This function directly mutates the provided headers. The provided debugg_ai_baggage
    is appended to the existing baggage. If the baggage already contains DebuggAI items,
    they are stripped out first.
    """
    existing_baggage = headers.get(BAGGAGE_HEADER_NAME, "")
    stripped_existing_baggage = Baggage.strip_debugg_ai_baggage(existing_baggage)

    separator = "," if len(stripped_existing_baggage) > 0 else ""

    headers[BAGGAGE_HEADER_NAME] = (
        stripped_existing_baggage + separator + debugg_ai_baggage
    )
