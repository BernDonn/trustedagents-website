from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from urllib import error, request

PAYMENT_PROVIDER_ENV = "TRUSTED_AGENTS_PAYMENT_PROVIDER"
PUBLIC_BASE_URL_ENV = "TRUSTED_AGENTS_PUBLIC_BASE_URL"
MOLLIE_API_KEY_ENV = "TRUSTED_AGENTS_MOLLIE_API_KEY"
MOLLIE_API_BASE_ENV = "TRUSTED_AGENTS_MOLLIE_API_BASE"
MOLLIE_DEFAULT_API_BASE = "https://api.mollie.com/v2"
DEFAULT_PAYMENT_PROVIDER = "mollie"
PLAN_AMOUNTS = {
    "starter": Decimal("29.00"),
    "dedicated": Decimal("79.00"),
    "bring-your-own": Decimal("149.00"),
}


class PaymentConfigError(RuntimeError):
    pass


class PaymentGatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class PaymentSession:
    provider: str
    payment_id: str
    checkout_url: str
    status: str
    amount_value: str
    amount_currency: str


@dataclass(frozen=True)
class PaymentStatus:
    provider: str
    payment_id: str
    status: str
    is_paid: bool


@dataclass(frozen=True)
class TenantPaymentContext:
    tenant_id: str
    email: str
    company_name: str
    plan: str


class PaymentGateway:
    def create_payment(self, tenant: TenantPaymentContext) -> PaymentSession:
        raise NotImplementedError

    def fetch_payment(self, payment_id: str) -> PaymentStatus:
        raise NotImplementedError


class MollieGateway(PaymentGateway):
    def __init__(self, api_key: str, public_base_url: str, api_base: str = MOLLIE_DEFAULT_API_BASE):
        self.api_key = api_key
        self.public_base_url = public_base_url.rstrip("/")
        self.api_base = api_base.rstrip("/")

    def create_payment(self, tenant: TenantPaymentContext) -> PaymentSession:
        amount = _amount_for_plan(tenant.plan)
        payload = {
            "amount": {"currency": "EUR", "value": amount},
            "description": f"Trusted Agents — {tenant.plan} — {tenant.company_name}",
            "redirectUrl": f"{self.public_base_url}/admin?tenant_id={tenant.tenant_id}&from_checkout=1",
            "webhookUrl": f"{self.public_base_url}/api/payments/mollie/webhook",
            "metadata": {
                "tenant_id": tenant.tenant_id,
                "plan": tenant.plan,
                "email": tenant.email,
            },
        }
        response = self._request_json("/payments", payload)
        checkout_url = response.get("_links", {}).get("checkout", {}).get("href")
        payment_id = response.get("id")
        status = response.get("status")
        if not isinstance(checkout_url, str) or not checkout_url:
            raise PaymentGatewayError("Mollie response missing checkout URL")
        if not isinstance(payment_id, str) or not payment_id:
            raise PaymentGatewayError("Mollie response missing payment id")
        if not isinstance(status, str) or not status:
            raise PaymentGatewayError("Mollie response missing payment status")
        return PaymentSession(
            provider="mollie",
            payment_id=payment_id,
            checkout_url=checkout_url,
            status=status,
            amount_value=amount,
            amount_currency="EUR",
        )

    def fetch_payment(self, payment_id: str) -> PaymentStatus:
        response = self._request_json(f"/payments/{payment_id}", None, method="GET")
        status = response.get("status")
        returned_payment_id = response.get("id")
        if not isinstance(status, str) or not status:
            raise PaymentGatewayError("Mollie response missing payment status")
        if not isinstance(returned_payment_id, str) or not returned_payment_id:
            raise PaymentGatewayError("Mollie response missing payment id")
        return PaymentStatus(
            provider="mollie",
            payment_id=returned_payment_id,
            status=status,
            is_paid=status == "paid",
        )

    def _request_json(self, path: str, payload: dict[str, Any] | None, method: str = "POST") -> dict[str, Any]:
        data = None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(f"{self.api_base}{path}", data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise PaymentGatewayError(f"Mollie API error ({exc.code}): {body[:300]}") from exc
        except error.URLError as exc:
            raise PaymentGatewayError(f"Mollie API unreachable: {exc.reason}") from exc
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PaymentGatewayError("Mollie returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise PaymentGatewayError("Mollie returned an unexpected payload")
        return result


def build_payment_gateway() -> PaymentGateway:
    provider = os.environ.get(PAYMENT_PROVIDER_ENV, DEFAULT_PAYMENT_PROVIDER).strip().lower()
    if provider != "mollie":
        raise PaymentConfigError(f"unsupported payment provider: {provider}")
    api_key = os.environ.get(MOLLIE_API_KEY_ENV, "").strip()
    if not api_key:
        raise PaymentConfigError(f"missing {MOLLIE_API_KEY_ENV}")
    public_base_url = os.environ.get(PUBLIC_BASE_URL_ENV, "").strip()
    if not public_base_url:
        raise PaymentConfigError(f"missing {PUBLIC_BASE_URL_ENV}")
    api_base = os.environ.get(MOLLIE_API_BASE_ENV, MOLLIE_DEFAULT_API_BASE).strip() or MOLLIE_DEFAULT_API_BASE
    return MollieGateway(api_key=api_key, public_base_url=public_base_url, api_base=api_base)


def _amount_for_plan(plan: str) -> str:
    amount = PLAN_AMOUNTS.get(plan)
    if amount is None:
        raise PaymentConfigError(f"unsupported plan for payment: {plan}")
    return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
