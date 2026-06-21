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
  } > .env.local
fi

source .env.local

echo "Trusted Agents demo wordt gestart."
echo "Open in je browser: http://127.0.0.1:8088/demo"
echo "Admin: http://127.0.0.1:8088/admin"
echo "Stoppen: Ctrl+C"
python -m trusted_agents_onboarding.app
