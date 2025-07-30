import logging
import time
import typing
from dataclasses import dataclass, field

from starlette.applications import ASGIApp
from starlette.types import Receive, Scope, Send

Message = typing.MutableMapping[str, typing.Any]


@dataclass
class ResponseInterceptor:
    outer_send: Send
    response_message: Message | None = None

    async def send(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self.response_message = message
        await self.outer_send(message)

    @property
    def status_code(self) -> int:
        if self.response_message is None:
            return 500
        return self.response_message.get("status", 500)

    @property
    def content_length(self) -> int | None:
        if self.response_message is None:
            return None
        for header in self.response_message.get("headers", []):
            if header[0] == b"content-length":
                try:
                    return int(header[1])
                except Exception:
                    pass
        return None

    @property
    def content_type(self) -> str | None:
        if self.response_message is None:
            return None
        for header in self.response_message.get("headers", []):
            if header[0] == b"content-type":
                try:
                    return header[1].decode("utf-8")
                except Exception:
                    pass
        return None


@dataclass
class ParsedScope:
    scope: Scope

    @property
    def method(self) -> str:
        method = self.scope.get("method")
        if method is None:
            raise ValueError("method is not set")
        return method

    @property
    def path(self) -> str:
        path = self.scope.get("path")
        if path is None:
            raise ValueError("path is not set")
        return path

    @property
    def query_string(self) -> str:
        query_string = self.scope.get("query_string")
        if query_string is None:
            return ""
        return query_string.decode("utf-8").strip()

    @property
    def full_path(self) -> str:
        qs = self.query_string
        if qs:
            return f"{self.path}?{qs}"
        return self.path


@dataclass
class AccessLogMiddleware:
    """
    Middleware to log access logs with a structured logger.

    Args:
        app: The ASGI application to wrap.
        logger: The structured logger to use.
    """

    app: ASGIApp
    logger: logging.LoggerAdapter
    ignore_hook: typing.Callable[[Scope], bool] = field(
        default_factory=lambda: lambda _: False
    )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)  # pragma: no cover
        if self.ignore_hook(scope):
            # ignored
            return await self.app(scope, receive, send)
        parsed_scope = ParsedScope(scope=scope)
        response_interceptor = ResponseInterceptor(outer_send=send)
        try:
            before = time.perf_counter()
            await self.app(scope, receive, response_interceptor.send)
        finally:
            after = time.perf_counter()
            duration = after - before
            if response_interceptor.status_code >= 400:
                log_fn = self.logger.warning
            else:
                log_fn = self.logger.info
            log_fn(
                "access log",
                method=parsed_scope.method,
                full_path=parsed_scope.full_path,
                status_code=response_interceptor.status_code,
                duration=duration,
                response_content_length=response_interceptor.content_length,
                response_content_type=response_interceptor.content_type,
            )
