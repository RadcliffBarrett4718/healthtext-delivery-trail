from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .appointment_notifier import notify_appointment
from .infrai_client import InfraiClient, InfraiError
from .models import AppointmentReminder


class AppointmentHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/appointments/remind":
            self._reply(404, {"detail": "route not found"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(size))
            reminder = AppointmentReminder(**body)
            result = notify_appointment(InfraiClient(), reminder)
            self._reply(202, result.__dict__)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._reply(400, {"detail": str(exc)})
        except InfraiError as exc:
            status = exc.status_code if 400 <= exc.status_code < 500 else 502
            self._reply(status, {"code": exc.code, "detail": exc.detail})

    def _reply(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    ThreadingHTTPServer(("127.0.0.1", 8000), AppointmentHandler).serve_forever()


if __name__ == "__main__":
    main()
