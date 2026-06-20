from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_PLANS = {"starter", "dedicated", "bring-your-own"}
VALID_MODEL_PROVIDERS = {"anthropic", "openrouter", "openai-codex", "other"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class OnboardingRequest:
    email: str
    plan: str
    customer_name: str
    company_name: str
    telegram_bot_token: str
    model_provider: str
    model_api_key: str
    accepted_responsibility: bool
    accepted_terms: bool

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "OnboardingRequest":
        data = cls(
            email=str(payload.get("email", "")).strip().lower(),
            plan=str(payload.get("plan", "")).strip(),
            customer_name=str(payload.get("customer_name", "")).strip(),
            company_name=str(payload.get("company_name", "")).strip(),
            telegram_bot_token=str(payload.get("telegram_bot_token", "")).strip(),
            model_provider=str(payload.get("model_provider", "")).strip(),
            model_api_key=str(payload.get("model_api_key", "")).strip(),
            accepted_responsibility=bool(payload.get("accepted_responsibility")),
            accepted_terms=bool(payload.get("accepted_terms")),
        )
        data.validate()
        return data

    def validate(self) -> None:
        if "@" not in self.email or "." not in self.email.split("@")[-1]:
            raise ValidationError("valid email is required")
        if self.plan not in VALID_PLANS:
            raise ValidationError(f"plan must be one of {sorted(VALID_PLANS)}")
        if self.model_provider not in VALID_MODEL_PROVIDERS:
            raise ValidationError(f"model_provider must be one of {sorted(VALID_MODEL_PROVIDERS)}")
        if not self.customer_name:
            raise ValidationError("customer_name is required")
        if not self.telegram_bot_token:
            raise ValidationError("telegram_bot_token is required")
        if not self.model_api_key and self.model_provider != "openai-codex":
            raise ValidationError("model_api_key is required for this provider")
        if not self.accepted_responsibility:
            raise ValidationError("responsibility confirmation is required")
        if not self.accepted_terms:
            raise ValidationError("terms acceptance is required")
