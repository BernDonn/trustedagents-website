# Trusted Agents — deployment automation blueprint

Status: tier strategy chosen — implement three routes: Starter managed, Dedicated, and Bring-your-own.

## What the Trustable flow appears to do

From Bernard's screenshots, the onboarding pattern is:

1. Customer enters email address.
2. Customer chooses Hermes Agent or OpenClaw Bot.
3. Customer pastes a Telegram Bot Token.
4. Customer pastes an Anthropic / Claude API key.
5. Customer accepts terms and a responsibility checkbox.
6. Customer starts installation.
7. Platform creates an order and redirects to payment.
8. After subscription payment, platform provisions the bot/agent and connects Telegram + Claude.

Important: uploaded screenshots showed live secrets. Treat the Telegram token and Anthropic key as temporary/test-only and rotate/revoke them before any real use.

## Hetzner vs Hostinger for this product

### Hetzner Cloud

Best fit for automated AI-agent provisioning.

Strengths:
- Mature developer cloud: REST API, CLI, Terraform provider and cloud-init support.
- Server creation can include `user_data` / cloud-init so a fresh VPS can be configured automatically on first boot.
- Terraform provider is widely used and maintained under `hetznercloud/hcloud`.
- Strong European positioning with Germany/Finland regions.
- Very good price/performance for small Linux workloads.
- Better suited to automated lifecycle operations: create server, attach firewall, attach SSH key, create DNS, snapshot, destroy.

Risks / limits:
- Price changes must be monitored.
- Hetzner may be stricter about account validation and abuse handling.
- We still need our own provisioning backend, secret storage, monitoring and support.

### Hostinger VPS

Usable, but less ideal for this product as the primary automation layer.

Strengths:
- Affiliate/referral angle may be commercially useful.
- Beginner-friendly dashboard.
- VPS API/Terraform provider exists, including VPS provisioning and post-install scripts.
- Good for simple customer websites or manually managed VPS hosting.

Risks / limits:
- Terraform provider is newer/smaller than Hetzner's ecosystem.
- Hostinger VPS is often positioned as easy unmanaged VPS rather than developer cloud infrastructure.
- Automation can work, but lifecycle confidence is lower than Hetzner for a SaaS-like provisioning product.

## Recommendation

Use Hetzner Cloud as the default managed infrastructure for Trusted Agents.

Keep Hostinger as:
- optional affiliate/referral hosting recommendation,
- a low-cost customer-hosted option,
- or a non-critical alternative if a customer explicitly wants it.

Do not make Hostinger the default automated backend unless tests prove the API, Terraform provider, post-install scripts, DNS and cancellation lifecycle are reliable enough.

## Product architecture for €29/month

### Important margin point

At €29/month, avoid giving every customer a fully separate VPS by default unless the VPS cost, monitoring and support are tightly controlled.

Recommended pricing model, now chosen as the public product structure:

1. **Starter — €29/month per bot**
   - Runs in a managed shared Trusted Agents environment.
   - Each customer gets isolated container/process, encrypted secrets and separate Telegram bot config.
   - Best margin and easiest operations.
   - This is the default offer on the website: `Managed Agent`.

2. **Dedicated — higher price, public starting point €79/month**
   - Customer gets a dedicated Hetzner VPS or equivalent private workspace.
   - Better isolation and easier story for privacy-sensitive clients.
   - Includes VPS cost, maintenance, monitoring and backups.
   - This is the second public offer: `Private Agent Server`.

3. **Bring-your-own-cloud / own Mac**
   - Setup fee + monthly support.
   - For customers who want to own infrastructure.
   - Customer keeps the infrastructure relationship; Trusted Agents provides setup, updates/support and clear responsibility boundaries.
   - This is the third public offer: `Eigen cloud of Mac`.

## End-to-end onboarding flow

### Public website

The static Trusted Agents website remains marketing and trust-building.

Add a secure onboarding app behind a button like:

`Deploy mijn agent`

This app cannot be purely static GitHub Pages because it needs to:
- create payments,
- receive payment webhooks,
- store secrets encrypted,
- provision infrastructure,
- start/stop bots.

### Suggested customer flow

1. Customer chooses plan: Starter €29/month, Dedicated, or Bring-your-own.
2. Customer enters email and company name.
3. Customer creates Telegram bot via BotFather and pastes token.
4. Customer pastes Anthropic/OpenRouter API key or chooses provider route.
5. Customer accepts responsibility checkboxes:
   - I am responsible for checking AI output.
   - I understand the agent can make mistakes.
   - I understand I may only provide lawful data.
   - I approve sensitive actions before they happen.
6. Customer pays subscription.
7. Payment webhook marks subscription active.
8. Provisioner starts customer bot/agent.
9. Customer receives Telegram welcome message.
10. Admin dashboard shows status: active, paused, payment failed, cancelled.

## Payment flow

### Best fit for Dutch customers

Use Mollie or Stripe, but consider Mollie first for the Dutch market.

Mollie advantages:
- Strong iDEAL support.
- SEPA Direct Debit recurring payments are natural for Dutch customers.
- Customer can avoid card-based signup if desired.
- Good fit for monthly B2B invoices/subscriptions.

Stripe advantages:
- Excellent subscriptions API, Checkout, webhooks and customer portal.
- Good developer tooling.
- Strong if we later want international cards and self-service portal.

Recommended first version:
- Use Mollie for iDEAL first payment + SEPA mandate / recurring collection, or manual monthly invoice if Bernard wants maximum control.
- Use Stripe if faster implementation is preferred and card/SEPA visibility is acceptable.

### What happens when customer pays €29/month

1. Website creates a subscription checkout session.
2. Customer pays first invoice/mandate.
3. Payment provider sends webhook: `subscription active` or `invoice paid`.
4. Our backend creates an internal tenant record:
   - customer_id
   - subscription_id
   - plan
   - bot_token_secret_ref
   - model_key_secret_ref
   - status=provisioning
5. Provisioner deploys or starts agent.
6. If payment later fails/cancels:
   - status becomes `past_due` or `cancelled`
   - bot is paused after grace period
   - secrets remain encrypted or are deleted per policy

## Provisioning design

### Starter shared environment

Run one or more Hetzner VPS instances managed by Trusted Agents:

- Reverse proxy / API backend
- Postgres or SQLite for early MVP
- Encrypted secret storage
- Per-customer bot workers
- Systemd, Docker Compose or Nomad-like process supervisor
- Logs per tenant with retention limits

Each bot worker receives only its own token/key at runtime.

### Starter capacity model

Initial assumption: the €29/month Managed Agent does **not** give every customer a dedicated VPS. It runs multiple isolated customer workers on a shared Trusted Agents server. The customer supplies or pays separately for model usage; the €29 covers the managed bot/agent layer, hosting, updates, monitoring and support.

Hetzner cost assumptions used for planning:

- Germany/Finland cost-optimized CX prices seen in public Hetzner material: CX22 €3.79/mo, CX32 €6.80/mo, CX42 €16.40/mo, CX52 €32.40/mo, excluding VAT.
- Add IPv4 planning cost: about €0.50/mo.
- Add automatic backups planning cost: about 20% of server base price.
- Add Dutch VAT for internal gross comparison: 21%.

Planning table:

| Plan | Resources | Planned customer range | Est. infra cost incl. VAT + IPv4 + backup | Infra cost/customer |
|---|---:|---:|---:|---:|
| CX22 | 2 vCPU / 4 GB / 40 GB | 3–5 | ~€6.11/mo | ~€1.22–€2.04 |
| CX32 | 4 vCPU / 8 GB / 80 GB | 8–15 | ~€10.48/mo | ~€0.70–€1.31 |
| CX42 | 8 vCPU / 16 GB / 160 GB | 20–40 | ~€24.42/mo | ~€0.61–€1.22 |
| CX52 | 16 vCPU / 32 GB / 320 GB | 40–80 | ~€47.65/mo | ~€0.60–€1.19 |

Important: these are planning ranges, not guarantees. Real capacity depends on whether each customer runs a lightweight Telegram/OpenClaw worker, a heavier Hermes profile, scheduled tasks, memory/database usage, and concurrent traffic.

Recommended MVP path:

1. Start with **CX32** as the first production-like shared node.
2. Cap it initially at **10 paying bots** until measured.
3. Instrument memory, CPU, disk, response latency, Telegram errors and model-call failures.
4. If stable, raise cap to 15 bots or move to CX42.
5. Keep one staging/test node separate from production.
6. Move privacy-sensitive or heavy users into Dedicated.

### Dedicated VPS environment

For higher-tier customers:

1. Backend calls Hetzner API or Terraform.
2. Creates VPS with SSH key, firewall and cloud-init.
3. cloud-init installs Docker, Hermes/OpenClaw runtime, monitoring, updates and deploy agent bootstrap.
4. Backend pushes encrypted customer config or the server pulls it from a one-time bootstrap token.
5. Health check confirms Telegram bot is alive.
6. Customer receives welcome message.

## Secrets policy

Do not store raw API keys in normal database columns.

Minimum:
- encrypt secrets at rest,
- never log tokens,
- mask tokens in admin UI,
- support key rotation,
- delete secrets on cancellation if not needed,
- keep audit events without secret values.

Better:
- use a small secrets service or age/sops-encrypted files,
- store only secret references in the app database.

## Local infrastructure scaffold

The repository now contains `infra/hetzner/` with the first OpenTofu/Hetzner structure for the Managed Agent node:

- `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf`
- `cloud-init.yaml.tftpl` for first-boot Docker preparation
- `terraform.tfvars.example` for local non-secret configuration
- `scripts/check.sh` for local checks
- local `.gitignore` to keep tokens, tfvars, state and private keys out of Git

The scaffold has been initialized, applied to staging, and verified with OpenTofu. The current staging node is ready for application deployment experiments, but production should remain separate.

## Managed Agent application scaffold

The repository now also contains `apps/onboarding/` with the first application layer:

- onboarding intent endpoint for customer plan/email/token intake;
- encrypted secret storage using a local master key;
- tenant and audit records in SQLite for MVP testing;
- manual payment activation endpoint as a stand-in for Mollie/Stripe webhooks;
- worker template that loads one tenant's Telegram/model credentials at runtime and prints only masked status;
- Dockerfile and local Compose file for the first deployable container shape.

This is not yet customer-live: payment webhooks, HTTPS/admin auth, production secret management and real Telegram polling still need to be added.

## MVP implementation steps

1. Build small onboarding backend.
2. Add a `Deploy mijn agent` page/form to trustedagents.nl.
3. Add Mollie or Stripe test-mode subscription.
4. Implement webhook handler.
5. Store customer/bot records.
6. Store secrets encrypted.
7. Deploy first shared Hetzner VPS.
8. Build bot worker template that connects Telegram to model provider.
9. Test activation, cancellation and failed payment.
10. Add admin dashboard for Bernard.

## Immediate next decision

Choose payment provider for MVP:

- **Mollie** if Dutch iDEAL + SEPA recurring and less card-name exposure matter most.
- **Stripe** if developer speed and hosted customer portal matter most.

Infrastructure decision:

- **Hetzner default** for managed automation.
- **Hostinger optional** for affiliate/customer-hosted route.
