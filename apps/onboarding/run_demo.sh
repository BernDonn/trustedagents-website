#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install -e '.[dev]' >/dev/null

if [ ! -f .env.local ]; then
  key="$(python -m trusted_agents_onboarding.crypto)"
  umask 077
  {
    printf "export TRUSTED_AGENTS_MASTER_KEY='%s'\n" "$key"
    printf "export TRUSTED_AGENTS_DB='./data/onboarding.sqlite3'\n"
    printf "export TRUSTED_AGENTS_PAYMENT_PROVIDER='mollie'\n"
    printf "export TRUSTED_AGENTS_PUBLIC_BASE_URL='https://YOUR-PUBLIC-URL'\n"
    printf "export TRUSTED_AGENTS_MOLLIE_API_KEY='test_xxx'\n"
  } > .env.local
  echo "Nieuwe .env.local aangemaakt met placeholders. Vul TRUSTED_AGENTS_PUBLIC_BASE_URL en TRUSTED_AGENTS_MOLLIE_API_KEY aan voor een echte Mollie test-checkout."
fi

source .env.local

missing=0
for var in TRUSTED_AGENTS_MASTER_KEY TRUSTED_AGENTS_DB; do
  if [ -z "${!var:-}" ]; then
    echo "Ontbreekt: $var"
    missing=1
  fi
done

if [ "${TRUSTED_AGENTS_PAYMENT_PROVIDER:-}" = "mollie" ]; then
  if [ -z "${TRUSTED_AGENTS_PUBLIC_BASE_URL:-}" ] || [ "${TRUSTED_AGENTS_PUBLIC_BASE_URL}" = "https://YOUR-PUBLIC-URL" ]; then
    echo "Waarschuwing: TRUSTED_AGENTS_PUBLIC_BASE_URL staat nog niet op een echte publieke URL. Mollie webhooks werken dan nog niet."
  fi
  if [ -z "${TRUSTED_AGENTS_MOLLIE_API_KEY:-}" ] || [[ "${TRUSTED_AGENTS_MOLLIE_API_KEY}" != test_* ]]; then
    echo "Waarschuwing: TRUSTED_AGENTS_MOLLIE_API_KEY ontbreekt of lijkt geen Mollie test key."
  fi
fi

if [ "$missing" -ne 0 ]; then
  exit 1
fi

echo "Trusted Agents demo wordt gestart."
echo "Open in je browser: http://127.0.0.1:8088/demo"
echo "Admin: http://127.0.0.1:8088/admin"
echo "Health: http://127.0.0.1:8088/health"
echo "Stoppen: Ctrl+C"
python -m trusted_agents_onboarding.app
