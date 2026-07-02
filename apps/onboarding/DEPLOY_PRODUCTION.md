# Trusted Agents onboarding — server deployment runbook

This runbook assumes the first live version uses the files in this folder on one Docker-capable VPS.

## Files used on the server

- `.env.production` — copied from `.env.production.example` and filled locally on the server
- `docker-compose.production.yml`
- `deploy/Caddyfile` — copied from `deploy/Caddyfile.example` and edited locally on the server

## 1. Prepare the server working directory

Copy the onboarding folder contents to the server, then create local-only runtime files:

```bash
cp .env.production.example .env.production
mkdir -p deploy
cp deploy/Caddyfile.example deploy/Caddyfile
chmod 600 .env.production
```

Then edit:
- `.env.production`
- `deploy/Caddyfile`

## 2. Required edits before first boot

### `.env.production`
Set real values for:
- `TRUSTED_AGENTS_MASTER_KEY`
- `TRUSTED_AGENTS_PUBLIC_BASE_URL`
- `TRUSTED_AGENTS_MOLLIE_API_KEY`

### `deploy/Caddyfile`
Replace:
- `admin@example.com`
- `ONBOARDING_DOMAIN`

The domain in Caddy must match `TRUSTED_AGENTS_PUBLIC_BASE_URL`.

## 3. Start the stack

```bash
docker compose -f docker-compose.production.yml up -d --build
```

## 4. Verify container config

```bash
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs --tail=100
```

## 5. Verify the public app

Check these routes in order:
- `/health`
- `/demo`
- `/admin`

Expected first smoke test:

```bash
curl -s https://YOUR-ONBOARDING-DOMAIN/health
```

## 6. Verify payment flow

1. Create one test/pilot intake.
2. Create the checkout.
3. Confirm redirect back to `/admin`.
4. Confirm the tenant reaches `payment_pending` and then `activation_pending`.
5. Use manual activation only after the payment state is correct.

## 7. Roll forward / update

After code changes:

```bash
git pull
docker compose -f docker-compose.production.yml up -d --build
```

## 8. Minimum operational rules

- never commit `.env.production`
- never commit a real `deploy/Caddyfile` with private email/domain choices if they are not meant for public Git
- back up the onboarding data volume
- keep admin access limited until auth is added in-app or in front of it
