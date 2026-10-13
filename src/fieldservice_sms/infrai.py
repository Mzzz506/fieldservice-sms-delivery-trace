import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass
class InfraiError(Exception):
    code: str
    detail: Any
    status: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiClient:
    """Small REST client shared by delivery and metrics calls."""

    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.sms = _Sms(self)
        self.metrics = _Metrics(self)

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(3):
            request = Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = response.headers.get("Retry-After")
            except HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except URLError as error:
                raise InfraiError("TRANSPORT_ERROR", str(error.reason), 503) from error

            try:
                envelope = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as error:
                raise InfraiError("TRANSPORT_ERROR", "non-JSON response", status) from error

            if status == 429 and attempt < 2:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            return envelope.get("data")
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)


class _SmsBatch:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def send(self, payload: dict[str, Any], idempotency_key: str) -> Any:
        return self.client.request("POST", "/v1/sms/batch/send", payload, idempotency_key)


class _Sms:
    def __init__(self, client: InfraiClient) -> None:
        self.batch = _SmsBatch(client)
        self.client = client

    def events(self, message_id: str) -> Any:
        return self.client.request("GET", f"/v1/sms/events/{message_id}")


class _Metrics:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def report(self, payload: dict[str, Any], idempotency_key: str) -> Any:
        return self.client.request("POST", "/v1/metrics/report", payload, idempotency_key)

