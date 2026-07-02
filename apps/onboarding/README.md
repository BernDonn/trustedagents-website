# Trusted Agents onboarding backend

This is the first managed-agent application scaffold behind the static `trustedagents.nl` site.

It is intentionally small and dependency-light:

- local HTTP API using Python's standard library;
- SQLite tenant/audit store for the MVP;
- encrypted secret storage with `cryptography.Fernet`;
- a worker template that loads only one tenant's secrets at runtime;
- first Mollie payment-session + webhook plumbing for test mode.

## Local setup

```bash
cd apps/onboarding
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Generate a local master key. Do not commit it:

```bash
python -m trusted_agents_onboarding.crypto
```

Create a local env file:

```bash
cat > .env.local <<'EOF'
export TRUSTED_AGENTS_MASTER_KEY='PASTE_GENERATED_KEY_HERE'
export TRUSTED_AGENTS_DB='./data/onboarding.sqlite3'
export TRUSTED_AGENTS_PAYMENT_PROVIDER='mollie'
export TRUSTED_AGENTS_PUBLIC_BASE_URL='http://127.0.0.1:8088'
export TRUSTED_AGENTS_MOLLIE_API_KEY='test_xxx'
EOF
chmod 600 .env.local
```

Start the backend:

```bash
source .env.local
python -m trusted_agents_onboarding.app
```

Open the demo in a browser at the local backend root. The backend serves:

- `/demo` — onboardingformulier
- `/admin` — Bernard adminoverzicht
- `/health` — health check

Health check:

```bash
curl -s http://127.0.0.1:8088/health
```

## Create a test onboarding intent + Mollie checkout

Use fake/test-only secrets locally:

```bash
curl -s -X POST http://127.0.0.1:8088/api/onboarding/intents \
  -H 'Content-Type: application/json' \
  -d '{
    "email":"test@example.nl",
    "plan":"starter",
    "customer_name":"Test User",
    "company_name":"Test BV",
    "telegram_bot_token":"TEST_TELEGRAM_TOKEN",
    "model_provider":"anthropic",
    "model_api_key":"TEST_MODEL_KEY",
    "accepted_responsibility":true,
    "accepted_terms":true
  }'
```

Then create a Mollie checkout session for that tenant:

```bash
curl -s -X POST http://127.0.0.1:8088/api/payments/create-checkout \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"tenant_xxx"}'
```

The response includes:

- `checkout_url`
- `payment_reference`
- `payment_provider`
- updated `payment_status`

## Webhook flow

Mollie will POST a payment `id` to the webhook. The backend then fetches the canonical payment status from Mollie and updates the tenant:

```bash
curl -s -X POST http://127.0.0.1:8088/api/payments/mollie/webhook \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'id=tr_xxx'
```

For local demo fallback you can still mark the payment active manually:

```bash
curl -s -X POST http://127.0.0.1:8088/api/payments/manual-active \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"tenant_xxx","subscription_id":"manual-test"}'
```

## Worker readiness template

```bash
python -m trusted_agents_onboarding.worker --tenant-id tenant_xxx --once
```

The worker prints only booleans/status, never the loaded token values.

## Production notes

Before this handles real customers:

- keep Mollie in **test mode** until the website/business profile is approval-ready;
- replace one-off payment creation with the final subscription/recurring design you choose;
- move the master key into a proper secret manager or SOPS/age workflow;
- put the API behind HTTPS and an admin auth layer;
- add rate limiting and CSRF/origin policy for browser forms;
- replace SQLite with Postgres if multiple app instances are needed;
- run one worker process/container per active tenant.

See also:
- `PRODUCTION_CHECKLIST.md` — recommended first live deployment sequence;
- `.env.production.example` — server-side runtime variable template.
