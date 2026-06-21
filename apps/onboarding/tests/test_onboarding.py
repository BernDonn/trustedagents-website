from __future__ import annotations

import os

import pytest

from trusted_agents_onboarding.crypto import MASTER_KEY_ENV, SecretBox, generate_master_key
from trusted_agents_onboarding.models import OnboardingRequest, ValidationError
from trusted_agents_onboarding.store import OnboardingStore
from trusted_agents_onboarding.worker import run_once
from trusted_agents_onboarding.app import OnboardingHandler


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
