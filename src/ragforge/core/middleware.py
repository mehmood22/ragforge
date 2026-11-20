import json
import logging
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("ragforge.http")
SENSITIVE_HEADERS = {b"authorization", b"cookie", b"set-cookie", b"x-api-key"}
MAX_BODY_LOG_BYTES = 2048


def _sanitize_raw_headers(raw_headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for k, v in raw_headers:
        key_str = k.decode("latin-1")
        if k.lower() in SENSITIVE_HEADERS:
            sanitized[key_str] = "***REDACTED***"
        else:
            sanitized[key_str] = v.decode("latin-1", errors="replace")
    return sanitized


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid4().hex
        started_at = time.perf_counter()
        status_code = 500
        headers = _sanitize_raw_headers(list(scope.get("headers", [])))
        query_string = scope.get("query_string", b"").decode("utf-8", errors="replace")

        content_type = headers.get("content-type", headers.get("Content-Type", ""))
        buffered_chunks: list[bytes] = []
        captured_bytes = 0
        skip_body = "multipart/form-data" in content_type.lower()

        async def wrapped_receive() -> Message:
            nonlocal captured_bytes
            message = await receive()
            if not skip_body and message["type"] == "http.request":
                body = message.get("body", b"")
                if body and captured_bytes <= MAX_BODY_LOG_BYTES:
                    remaining = MAX_BODY_LOG_BYTES - captured_bytes
                    buffered_chunks.append(body[:remaining])
                    captured_bytes += len(body)
            return message

        async def wrapped_send(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                raw_resp_headers = list(message.get("headers", []))
                raw_resp_headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = {**message, "headers": raw_resp_headers}
            await send(message)

        try:
            await self.app(scope, wrapped_receive, wrapped_send)
        finally:
            duration_ms = (time.perf_counter() - started_at) * 1000
            raw_sample = b"".join(buffered_chunks)
            if skip_body:
                body_preview: object = "<multipart/form-data>"
            elif captured_bytes > MAX_BODY_LOG_BYTES:
                body_preview = f"<truncated {captured_bytes} bytes>"
            elif not raw_sample:
                body_preview = None
            elif "application/json" in content_type.lower():
                try:
                    body_preview = json.loads(raw_sample.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    body_preview = raw_sample.decode("utf-8", errors="replace")
            else:
                body_preview = raw_sample.decode("utf-8", errors="replace")

            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "query_string": query_string,
                    "headers": headers,
                    "request_body": body_preview,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
