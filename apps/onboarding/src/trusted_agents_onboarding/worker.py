from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from .crypto import SecretBox
from .store import OnboardingStore


class WorkerConfigError(RuntimeError):
    pass


def load_runtime_config(store: OnboardingStore, tenant_id: str) -> dict[str, str]:
    """Load only the secrets for one tenant worker.

    This is intentionally narrow: a worker receives one tenant id and resolves only
    that tenant's Telegram/model credentials at runtime.
    """
    return {
        "tenant_id": tenant_id,
        "telegram_bot_token": store.get_secret(tenant_id, "telegram_bot_token"),
        "model_api_key": store.get_secret(tenant_id, "model_api_key"),
    }


def run_once(tenant_id: str, db_path: str) -> dict[str, str]:
    store = OnboardingStore(db_path, SecretBox.from_env())
    cfg = load_runtime_config(store, tenant_id)
    # Do not print secrets. Return masked operational state only.
    return {
        "tenant_id": cfg["tenant_id"],
        "telegram_token_loaded": str(bool(cfg["telegram_bot_token"])),
        "model_key_loaded": str(bool(cfg["model_api_key"])),
        "status": "ready_for_telegram_polling",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trusted Agents tenant worker template")
    parser.add_argument("--tenant-id", default=os.environ.get("TRUSTED_AGENTS_TENANT_ID"))
    parser.add_argument("--db", default=os.environ.get("TRUSTED_AGENTS_DB", "./data/onboarding.sqlite3"))
    parser.add_argument("--once", action="store_true", help="run a single readiness check and exit")
    args = parser.parse_args()
    if not args.tenant_id:
        raise WorkerConfigError("tenant id is required")

    if args.once:
        print(json.dumps(run_once(args.tenant_id, args.db), ensure_ascii=False))
        return

    while True:
        state = run_once(args.tenant_id, args.db)
        print(json.dumps(state, ensure_ascii=False))
        time.sleep(60)


if __name__ == "__main__":
    main()
