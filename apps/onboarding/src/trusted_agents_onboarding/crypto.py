from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken


MASTER_KEY_ENV = "TRUSTED_AGENTS_MASTER_KEY"


class SecretConfigError(RuntimeError):
    """Raised when encrypted secret storage is not configured safely."""


@dataclass(frozen=True)
class SecretBox:
    fernet: Fernet

    @classmethod
    def from_env(cls) -> "SecretBox":
        key = os.environ.get(MASTER_KEY_ENV, "").strip()
        if not key:
            raise SecretConfigError(
                f"Missing {MASTER_KEY_ENV}. Generate one with: python -m trusted_agents_onboarding.crypto"
            )
        try:
            # Fernet validates length/base64 here.
            return cls(Fernet(key.encode("utf-8")))
        except Exception as exc:  # pragma: no cover - exact cryptography exception varies
            raise SecretConfigError(f"Invalid {MASTER_KEY_ENV}; expected a Fernet key") from exc

    def encrypt(self, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("secret value may not be empty")
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self.fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretConfigError("Stored secret cannot be decrypted with the current master key") from exc


def generate_master_key() -> str:
    return Fernet.generate_key().decode("utf-8")


if __name__ == "__main__":
    # Printed only on explicit operator request. Do not commit this value.
    print(generate_master_key())
