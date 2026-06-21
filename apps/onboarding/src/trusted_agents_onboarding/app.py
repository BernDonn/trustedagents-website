from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .crypto import SecretBox, SecretConfigError
from .models import OnboardingRequest, ValidationError
from .payments import PaymentConfigError, PaymentGateway, PaymentGatewayError, build_payment_gateway
from .store import OnboardingStore, TenantRecord

DB_ENV = "TRUSTED_AGENTS_DB"
DEFAULT_DB = "./data/onboarding.sqlite3"


def build_store() -> OnboardingStore:
    return OnboardingStore(os.environ.get(DB_ENV, DEFAULT_DB), SecretBox.from_env())


class OnboardingHandler(BaseHTTPRequestHandler):
    server_version = "TrustedAgentsOnboarding/0.2"

    @property
    def store(self) -> OnboardingStore:
        return self.server.store  # type: ignore[attr-defined]

    @property
    def payment_gateway(self) -> PaymentGateway:
        factory = self.server.payment_gateway_factory  # type: ignore[attr-defined]
        return factory()

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static_root(self) -> Path:
        return Path(__file__).resolve().parent / "static"

    def _send_static(self, relative_path: str) -> bool:
        root = self._static_root()
        requested = (root / relative_path).resolve()
        try:
            requested.relative_to(root.resolve())
        except ValueError:
            return False
        if not requested.is_file():
            return False
        content_type = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        body = requested.read_bytes()
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

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

    def _read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 10_000:
            raise ValidationError("payload too large")
        raw = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(raw, keep_blank_values=True)
        return {key: values[-1] for key, values in parsed.items() if values}

    def _tenant_response(self, tenant: TenantRecord) -> dict:
        return {
            "tenant_id": tenant.id,
            "status": tenant.status,
            "payment_status": tenant.payment_status,
            "payment_provider": tenant.payment_provider,
            "payment_reference": tenant.payment_reference,
            "checkout_url": tenant.payment_checkout_url,
        }

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/demo"}:
            if self._send_static("index.html"):
                return
        if path == "/admin":
            if self._send_static("admin.html"):
                return
        if path.startswith("/static/"):
            if self._send_static(path.removeprefix("/static/")):
                return
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
                        **self._tenant_response(tenant),
                        "next_step": "create_payment_session",
                    },
                )
                return
            if path == "/api/payments/create-checkout":
                data = self._read_json()
                tenant_id = str(data.get("tenant_id", "")).strip()
                if not tenant_id:
                    raise ValidationError("tenant_id is required")
                tenant_ctx = self.store.get_payment_context(tenant_id)
                session = self.payment_gateway.create_payment(tenant_ctx)
                tenant = self.store.record_payment_session(
                    tenant_id=tenant_id,
                    provider=session.provider,
                    payment_reference=session.payment_id,
                    checkout_url=session.checkout_url,
                    payment_status=session.status,
                )
                self._json(
                    HTTPStatus.CREATED,
                    {
                        **self._tenant_response(tenant),
                        "checkout_url": session.checkout_url,
                        "amount": {"currency": session.amount_currency, "value": session.amount_value},
                    },
                )
                return
            if path == "/api/payments/mollie/webhook":
                content_type = self.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    payload = self._read_json()
                else:
                    payload = self._read_form()
                payment_id = str(payload.get("id", "")).strip()
                if not payment_id:
                    raise ValidationError("payment id is required")
                status = self.payment_gateway.fetch_payment(payment_id)
                tenant = self.store.get_tenant_by_payment_reference(status.payment_id)
                if status.is_paid:
                    self.store.mark_payment_active(tenant.id, status.payment_id)
                else:
                    self.store.mark_payment_status(tenant.id, status.status, status.payment_id)
                self._json(HTTPStatus.OK, {"ok": True, "payment_id": status.payment_id, "status": status.status})
                return
            if path == "/api/payments/manual-active":
                data = self._read_json()
                tenant_id = str(data.get("tenant_id", "")).strip()
                if not tenant_id:
                    raise ValidationError("tenant_id is required")
                self.store.mark_payment_active(tenant_id, str(data.get("subscription_id", "manual-test")))
                tenant = self.store.get_tenant(tenant_id)
                self._json(HTTPStatus.OK, self._tenant_response(tenant))
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except ValidationError as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "validation_error", "message": str(exc)})
        except SecretConfigError as exc:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "secret_config_error", "message": str(exc)})
        except PaymentConfigError as exc:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "payment_config_error", "message": str(exc)})
        except PaymentGatewayError as exc:
            self._json(HTTPStatus.BAD_GATEWAY, {"error": "payment_gateway_error", "message": str(exc)})
        except KeyError as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": str(exc)})

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Avoid logging request bodies or secret-bearing fields.
        print(f"{self.address_string()} - {format % args}")


def run(host: str = "127.0.0.1", port: int = 8088) -> None:
    store = build_store()
    server = ThreadingHTTPServer((host, port), OnboardingHandler)
    server.store = store  # type: ignore[attr-defined]
    server.payment_gateway_factory = build_payment_gateway  # type: ignore[attr-defined]
    print(f"Trusted Agents onboarding backend listening on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(os.environ.get("TRUSTED_AGENTS_HOST", "127.0.0.1"), int(os.environ.get("TRUSTED_AGENTS_PORT", "8088")))
