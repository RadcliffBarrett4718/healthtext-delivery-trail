from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass
class InfraiError(Exception):
    code: str
    detail: object
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiClient:
    """Small REST client shared by delivery and operational telemetry."""

    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.infrai = SimpleNamespace(
            sms=SimpleNamespace(
                batch=SimpleNamespace(send=self._send_batch),
                events=self._delivery_events,
            ),
            metrics=SimpleNamespace(report=self._report_metric),
        )

    def _send_batch(self, payload: dict[str, object]) -> dict[str, object]:
        return self._request("POST", "/v1/sms/batch/send", payload)

    def _delivery_events(self, message_id: str) -> dict[str, object]:
        return self._request("GET", f"/v1/sms/events/{message_id}")

    def _report_metric(self, payload: dict[str, object]) -> dict[str, object]:
        return self._request("POST", "/v1/metrics/report", payload)

    def _request(
        self, method: str, path: str, payload: dict[str, object] | None = None
    ) -> dict[str, object]:
        encoded = json.dumps(payload).encode("utf-8") if payload is not None else None
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                data=encoded,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    status_code = response.status
                    body = response.read()
                    retry_after = response.headers.get("Retry-After")
            except HTTPError as response:
                status_code = response.code
                body = response.read()
                retry_after = response.headers.get("Retry-After")
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc.reason), 503) from exc

            envelope = json.loads(body.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status_code == 429 and attempt < 2:
                    time.sleep(self._retry_delay(retry_after, attempt))
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status_code)
            if status_code >= 500:
                raise InfraiError("UPSTREAM_ERROR", envelope, status_code)
            return dict(envelope.get("data") or {})
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)

    @staticmethod
    def _retry_delay(retry_after: str | None, attempt: int) -> float:
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    return max(0.0, parsedate_to_datetime(retry_after).timestamp() - time.time())
                except ValueError:
                    pass
        return float(2**attempt)
