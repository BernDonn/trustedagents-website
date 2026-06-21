from __future__ import annotations

import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .crypto import SecretBox
from .models import OnboardingRequest
from .payments import TenantPaymentContext


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  plan TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  company_name TEXT NOT NULL,
  model_provider TEXT NOT NULL,
  status TEXT NOT NULL,
  payment_status TEXT NOT NULL,
  payment_provider TEXT,
  payment_reference TEXT,
  payment_checkout_url TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tenant_secrets (
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  ciphertext TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (tenant_id, name),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

TENANT_EXTRA_COLUMNS = {
    "payment_provider": "TEXT",
    "payment_reference": "TEXT",
    "payment_checkout_url": "TEXT",
}


@dataclass(frozen=True)
class TenantRecord:
    id: str
    email: str
    plan: str
    customer_name: str
    company_name: str
    model_provider: str
    status: str
    payment_status: str
    payment_provider: str | None
    payment_reference: str | None
    payment_checkout_url: str | None
    created_at: str
    updated_at: str


class OnboardingStore:
    def __init__(self, db_path: str | Path, secret_box: SecretBox):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.secret_box = secret_box
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init_db(self) -> None:
        with self.connect() as con:
            con.executescript(SCHEMA)
            existing = {row["name"] for row in con.execute("PRAGMA table_info(tenants)").fetchall()}
            for name, type_sql in TENANT_EXTRA_COLUMNS.items():
                if name not in existing:
                    con.execute(f"ALTER TABLE tenants ADD COLUMN {name} {type_sql}")

    def create_tenant(self, req: OnboardingRequest) -> TenantRecord:
        now = datetime.now(timezone.utc).isoformat()
        tenant_id = f"tenant_{uuid.uuid4().hex}"
        record = TenantRecord(
            id=tenant_id,
            email=req.email,
            plan=req.plan,
            customer_name=req.customer_name,
            company_name=req.company_name,
            model_provider=req.model_provider,
            status="pending_payment",
            payment_status="not_started",
            payment_provider=None,
            payment_reference=None,
            payment_checkout_url=None,
            created_at=now,
            updated_at=now,
        )
        secrets = {
            "telegram_bot_token": req.telegram_bot_token,
            "model_api_key": req.model_api_key or "openai-codex-oauth-placeholder",
        }
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO tenants(
                    id,email,plan,customer_name,company_name,model_provider,status,payment_status,
                    payment_provider,payment_reference,payment_checkout_url,created_at,updated_at
                )
                VALUES (
                    :id,:email,:plan,:customer_name,:company_name,:model_provider,:status,:payment_status,
                    :payment_provider,:payment_reference,:payment_checkout_url,:created_at,:updated_at
                )
                """,
                asdict(record),
            )
            for name, plain in secrets.items():
                con.execute(
                    "INSERT INTO tenant_secrets(tenant_id,name,ciphertext,created_at) VALUES (?,?,?,?)",
                    (tenant_id, name, self.secret_box.encrypt(plain), now),
                )
            con.execute(
                "INSERT INTO audit_events(id,tenant_id,event_type,message,created_at) VALUES (?,?,?,?,?)",
                (f"evt_{uuid.uuid4().hex}", tenant_id, "tenant.created", "Tenant created from onboarding form", now),
            )
        return record

    def get_tenant(self, tenant_id: str) -> TenantRecord:
        with self.connect() as con:
            row = con.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown tenant {tenant_id}")
        return TenantRecord(**dict(row))

    def get_payment_context(self, tenant_id: str) -> TenantPaymentContext:
        tenant = self.get_tenant(tenant_id)
        return TenantPaymentContext(
            tenant_id=tenant.id,
            email=tenant.email,
            company_name=tenant.company_name,
            plan=tenant.plan,
        )

    def get_tenant_by_payment_reference(self, payment_reference: str) -> TenantRecord:
        with self.connect() as con:
            row = con.execute("SELECT * FROM tenants WHERE payment_reference=?", (payment_reference,)).fetchone()
        if not row:
            raise KeyError(f"unknown payment reference {payment_reference}")
        return TenantRecord(**dict(row))

    def record_payment_session(
        self,
        tenant_id: str,
        provider: str,
        payment_reference: str,
        checkout_url: str,
        payment_status: str,
    ) -> TenantRecord:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as con:
            cur = con.execute(
                """
                UPDATE tenants
                SET payment_provider=?, payment_reference=?, payment_checkout_url=?, payment_status=?, updated_at=?
                WHERE id=?
                """,
                (provider, payment_reference, checkout_url, payment_status, now, tenant_id),
            )
            if cur.rowcount != 1:
                raise KeyError(f"unknown tenant {tenant_id}")
            con.execute(
                "INSERT INTO audit_events(id,tenant_id,event_type,message,created_at) VALUES (?,?,?,?,?)",
                (
                    f"evt_{uuid.uuid4().hex}",
                    tenant_id,
                    "payment.session_created",
                    f"Payment session created via {provider}: {payment_reference}",
                    now,
                ),
            )
        return self.get_tenant(tenant_id)

    def mark_payment_active(self, tenant_id: str, provider_subscription_id: str = "manual-test") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as con:
            cur = con.execute(
                "UPDATE tenants SET status=?, payment_status=?, updated_at=? WHERE id=?",
                ("provisioning", "active", now, tenant_id),
            )
            if cur.rowcount != 1:
                raise KeyError(f"unknown tenant {tenant_id}")
            con.execute(
                "INSERT INTO audit_events(id,tenant_id,event_type,message,created_at) VALUES (?,?,?,?,?)",
                (f"evt_{uuid.uuid4().hex}", tenant_id, "payment.active", f"Subscription active: {provider_subscription_id}", now),
            )

    def mark_payment_status(self, tenant_id: str, payment_status: str, payment_reference: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        message = f"Payment status updated: {payment_status}"
        if payment_reference:
            message = f"Payment status updated: {payment_status} ({payment_reference})"
        with self.connect() as con:
            cur = con.execute(
                "UPDATE tenants SET status=?, payment_status=?, updated_at=? WHERE id=?",
                ("pending_payment", payment_status, now, tenant_id),
            )
            if cur.rowcount != 1:
                raise KeyError(f"unknown tenant {tenant_id}")
            con.execute(
                "INSERT INTO audit_events(id,tenant_id,event_type,message,created_at) VALUES (?,?,?,?,?)",
                (f"evt_{uuid.uuid4().hex}", tenant_id, f"payment.{payment_status}", message, now),
            )

    def list_tenants(self) -> list[TenantRecord]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM tenants ORDER BY created_at DESC").fetchall()
        return [TenantRecord(**dict(r)) for r in rows]

    def get_secret(self, tenant_id: str, name: str) -> str:
        with self.connect() as con:
            row = con.execute(
                "SELECT ciphertext FROM tenant_secrets WHERE tenant_id=? AND name=?", (tenant_id, name)
            ).fetchone()
        if not row:
            raise KeyError(f"secret {name} not found for tenant")
        return self.secret_box.decrypt(row["ciphertext"])
