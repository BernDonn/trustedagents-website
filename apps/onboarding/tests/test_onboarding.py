from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from urllib import parse, request

import pytest

from trusted_agents_onboarding.app import OnboardingHandler
from trusted_agents_onboarding.crypto import MASTER_KEY_ENV, SecretBox, generate_master_key
from trusted_agents_onboarding.models import OnboardingRequest, ValidationError
from trusted_agents_onboarding.payments import PaymentSession, PaymentStatus, TenantPaymentContext
from trusted_agents_onboarding.store import OnboardingStore
from trusted_agents_onboarding.worker import run_once
from http.server import ThreadingHTTPServer


@dataclass
class FakeGateway:
    payment_status: str = "open"

    def __post_init__(self):
        self.created: dict[str, TenantPaymentContext] = {}

    def create_payment(self, tenant: TenantPaymentContext) -> PaymentSession:
        payment_id = f"tr_{tenant.tenant_id[-8:]}"
        self.created[payment_id] = tenant
        return PaymentSession(
            provider="mollie",
            payment_id=payment_id,
            checkout_url=f"https://checkout.example/{payment_id}",
            status=self.payment_status,
            amount_value="29.00" if tenant.plan == "starter" else "79.00",
            amount_currency="EUR",
        )

    def fetch_payment(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(
            provider="mollie",
            payment_id=payment_id,
            status=self.payment_status,
            is_paid=self.payment_status == "paid",
        )


class DemoServer:
    def __init__(self, store: OnboardingStore, gateway: FakeGateway):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), OnboardingHandler)
        self.httpd.store = store  # type: ignore[attr-defined]
        self.httpd.payment_gateway_factory = lambda: gateway  # type: ignore[attr-defined]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_port}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()


def api_json(url: str, method: str = "GET", payload: dict | None = None, headers: dict[str, str] | None = None) -> dict:
    data = None
    req_headers = headers or {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers = {**req_headers, "Content-Type": "application/json"}
    req = request.Request(url, data=data, method=method, headers=req_headers)
    with request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_static_pages_are_present():
    root = OnboardingHandler._static_root.__get__(object(), OnboardingHandler)()
    assert (root / "index.html").is_file()
    assert (root / "admin.html").is_file()
    assert (root / "styles.css").is_file()


def test_onboarding_stores_encrypted_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv(MASTER_KEY_ENV, generate_master_key())
    store = OnboardingStore(tmp_path / "onboarding.sqlite3", SecretBox.from_env())
    req = OnboardingRequest.from_json(
        {
            "email": "USER@Example.nl",
            "plan": "starter",
            "customer_name": "Test User",
            "company_name": "Test BV",
            "telegram_bot_token": "telegram-secret-value",
            "model_provider": "anthropic",
            "model_api_key": "model-secret-value",
            "accepted_responsibility": True,
            "accepted_terms": True,
        }
    )

    tenant = store.create_tenant(req)

    assert tenant.email == "user@example.nl"
    assert tenant.status == "pending_payment"
    assert tenant.payment_status == "not_started"
    assert store.get_secret(tenant.id, "telegram_bot_token") == "telegram-secret-value"

    raw_db = (tmp_path / "onboarding.sqlite3").read_bytes()
    assert b"telegram-secret-value" not in raw_db
    assert b"model-secret-value" not in raw_db


def test_rejects_missing_responsibility_confirmation():
    with pytest.raises(ValidationError):
        OnboardingRequest.from_json(
            {
                "email": "test@example.nl",
                "plan": "starter",
                "customer_name": "Test User",
                "company_name": "Test BV",
                "telegram_bot_token": "telegram-secret-value",
                "model_provider": "anthropic",
                "model_api_key": "model-secret-value",
                "accepted_responsibility": False,
                "accepted_terms": True,
            }
        )


def test_worker_loads_only_masked_status(tmp_path, monkeypatch):
    monkeypatch.setenv(MASTER_KEY_ENV, generate_master_key())
    db = tmp_path / "onboarding.sqlite3"
    store = OnboardingStore(db, SecretBox.from_env())
    tenant = store.create_tenant(
        OnboardingRequest.from_json(
            {
                "email": "test@example.nl",
                "plan": "starter",
                "customer_name": "Test User",
                "company_name": "Test BV",
                "telegram_bot_token": "telegram-secret-value",
                "model_provider": "anthropic",
                "model_api_key": "model-secret-value",
                "accepted_responsibility": True,
                "accepted_terms": True,
            }
        )
    )

    state = run_once(tenant.id, str(db))

    assert state == {
        "tenant_id": tenant.id,
        "telegram_token_loaded": "True",
        "model_key_loaded": "True",
        "status": "ready_for_telegram_polling",
    }
    assert "telegram-secret-value" not in str(state)
    assert "model-secret-value" not in str(state)


def test_mollie_checkout_and_webhook_flow(tmp_path, monkeypatch):
    monkeypatch.setenv(MASTER_KEY_ENV, generate_master_key())
    store = OnboardingStore(tmp_path / "onboarding.sqlite3", SecretBox.from_env())
    gateway = FakeGateway(payment_status="open")

    with DemoServer(store, gateway) as server:
        tenant_payload = api_json(
            f"{server.base_url}/api/onboarding/intents",
            method="POST",
            payload={
                "email": "demo@example.nl",
                "plan": "starter",
                "customer_name": "Demo User",
                "company_name": "Demo BV",
                "telegram_bot_token": "telegram-secret-value",
                "model_provider": "anthropic",
                "model_api_key": "model-secret-value",
                "accepted_responsibility": True,
                "accepted_terms": True,
            },
        )
        tenant_id = tenant_payload["tenant_id"]
        assert tenant_payload["payment_status"] == "not_started"

        checkout_payload = api_json(
            f"{server.base_url}/api/payments/create-checkout",
            method="POST",
            payload={"tenant_id": tenant_id},
        )
        assert checkout_payload["payment_provider"] == "mollie"
        assert checkout_payload["payment_status"] == "open"
        assert checkout_payload["checkout_url"].startswith("https://checkout.example/")
        payment_id = checkout_payload["payment_reference"]

        gateway.payment_status = "paid"
        form_data = parse.urlencode({"id": payment_id}).encode("utf-8")
        req = request.Request(
            f"{server.base_url}/api/payments/mollie/webhook",
            data=form_data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with request.urlopen(req, timeout=5) as resp:
            webhook_payload = json.loads(resp.read().decode("utf-8"))
        assert webhook_payload["status"] == "paid"

        admin_payload = api_json(f"{server.base_url}/api/admin/tenants")
        tenant = admin_payload["tenants"][0]
        assert tenant["id"] == tenant_id
        assert tenant["status"] == "provisioning"
        assert tenant["payment_status"] == "active"
        assert tenant["payment_provider"] == "mollie"
        assert tenant["payment_reference"] == payment_id
