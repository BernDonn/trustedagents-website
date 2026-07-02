# Trusted Agents onboarding — production checklist

This is the shortest path from the current MVP to a live Mollie-backed onboarding flow.

## Recommended hosting shape

Use the existing containerized onboarding app on one VPS behind the existing reverse-proxy scaffold in `infra/hetzner/`.

Why this route:
- it matches the current repo structure;
- the onboarding app already has a Dockerfile;
- the Hetzner scaffold already anticipates a reverse proxy and a shared application node;
- it keeps the first live setup simple enough to debug.

## Before you deploy

Prepare these inputs outside Git:
- one production Fernet master key;
- one Mollie live API key;
- one public HTTPS URL dedicated to the onboarding backend;
- one persistent volume/path for the SQLite database;
- one decision about how Bernard will authenticate to `/admin` in the next hardening pass.

## Runtime env for the first live version

Use `.env.production.example` as the template and provide real values only on the server.
Use `docker-compose.production.yml` for the first live stack and copy `deploy/Caddyfile.example` to a local-only `deploy/Caddyfile` on the server.

Minimum live variables:
- `TRUSTED_AGENTS_MASTER_KEY`
- `TRUSTED_AGENTS_DB`
- `TRUSTED_AGENTS_PUBLIC_BASE_URL`
- `TRUSTED_AGENTS_PAYMENT_PROVIDER`
- `TRUSTED_AGENTS_MOLLIE_API_KEY`
- `TRUSTED_AGENTS_ENV=production`

## Deployment sequence

1. Build or pull the onboarding container image.
2. Mount a persistent data location for the onboarding database.
3. Load the production env file on the server.
4. Start the onboarding backend behind the reverse proxy.
5. Confirm the public HTTPS base URL serves:
   - `/demo`
   - `/admin`
   - `/health`
6. In Mollie, configure the website/business profile to match Trusted Agents.
7. Ensure checkout redirects point back to the same public onboarding URL.
8. Ensure the Mollie webhook points to the same backend base URL.

## First live verification pass

Run these checks in order:

1. Health check returns OK over the public HTTPS URL.
2. Demo onboarding form creates a tenant successfully.
3. Checkout creation returns a Mollie checkout URL.
4. After returning from Mollie, `/admin` highlights the correct tenant.
5. Automatic or manual payment sync changes the tenant from:
   - `intake_received` / `not_started`
   - to `payment_pending` / `open`
   - to `activation_pending` / `paid`
6. `Markeer actief` remains available as the manual bridge to the first real activation workflow.

## Recommended go-live order

### Phase A — protected live pilot
- keep traffic low;
- use one or two real pilot tenants;
- validate paid → activation_pending end to end;
- keep the final agent activation manual.

### Phase B — operational hardening
After the first successful paid pilots, add:
- admin authentication in front of `/admin`;
- rate limiting / CSRF-or-origin protections for browser endpoints;
- backup policy for the persistent data volume;
- structured logging and basic alerting;
- migration path from SQLite to Postgres if multiple app instances become necessary.

## What is intentionally still deferred

The current onboarding backend is ready for a first paid pilot, but these items are intentionally not part of the first go-live:
- recurring subscriptions;
- full automatic agent provisioning immediately after payment;
- multi-instance app deployment;
- a customer self-service billing portal.

## Practical recommendation

For the first live version, treat a successful payment as:
- financial confirmation;
- intake confirmed;
- activation queue entry.

Do not treat `paid` as equivalent to a fully provisioned live agent yet.
