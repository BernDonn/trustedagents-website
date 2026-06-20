from __future__ import annotations

import json
import os
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .crypto import SecretBox, SecretConfigError
from .models import OnboardingRequest, ValidationError
from .store import OnboardingStore

DB_ENV = "TRUSTED_AGENTS_DB"
DEFAULT_DB = "./data/onboarding.sqlite3"


def build_store() -> OnboardingStore:
    return OnboardingStore(os.environ.get(DB_ENV, DEFAULT_DB), SecretBox.from_env())


class OnboardingHandler(BaseHTTPRequestHandler):
    server_version = "TrustedAgentsOnboarding/0.1"

    @property
    def store(self) -> OnboardingStore:
        return self.server.store  # type: ignore[attr-defined]

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 100_000:
            raise ValidationError("payload too large")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValidationError("invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValidationError("JSON object expected")
        return data

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._json(HTTPStatus.OK, {"ok": True, "service": "trusted-agents-onboarding"})
            return
        if path == "/api/admin/tenants":
            tenants = [asdict(t) for t in self.store.list_tenants()]
            self._json(HTTPStatus.OK, {"tenants": tenants})
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/onboarding/intents":
                req = OnboardingRequest.from_json(self._read_json())
                tenant = self.store.create_tenant(req)
                self._json(
                    HTTPStatus.CREATED,
                    {
                        "tenant_id": tenant.id,
                        "status": tenant.status,
                        "payment_status": tenant.payment_status,
                        "next_step": "create_payment_session",
                    },
                )
                return
            if path == "/api/payments/manual-active":
                data = self._read_json()
                tenant_id = str(data.get("tenant_id", "")).strip()
                if not tenant_id:
                    raise ValidationError("tenant_id is required")
                self.store.mark_payment_active(tenant_id, str(data.get("subscription_id", "manual-test")))
                self._json(HTTPStatus.OK, {"tenant_id": tenant_id, "status": "provisioning"})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except ValidationError as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": str(exc)})
        except SecretConfigError as exc:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "secret_config_error", "message": str(exc)})
        except KeyError as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": str(exc)})

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Avoid logging request bodies or secret-bearing fields.
        print(f"{self.address_string()} - {format % args}")


def run(host: str = "127.0.0.1", port: int = 8088) -> None:
    store = build_store()
    server = ThreadingHTTPServer((host, port), OnboardingHandler)
    server.store = store  # type: ignore[attr-defined]
    print(f"Trusted Agents onboarding backend listening on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(os.environ.get("TRUSTED_AGENTS_HOST", "127.0.0.1"), int(os.environ.get("TRUSTED_AGENTS_PORT", "8088")))
