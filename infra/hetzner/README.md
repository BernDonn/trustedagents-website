# Trusted Agents — Hetzner managed node

This folder contains the first deployable infrastructure scaffold for the **Managed Agent** route described in `DEPLOYMENT_AUTOMATION.md`.

## Purpose

Create one shared Hetzner Cloud node for the first production-like Trusted Agents environment:

- one managed node for multiple customer bot workers;
- Docker installed by cloud-init;
- a dedicated application directory;
- an internal Docker network for the future onboarding backend, agent workers, and data stores;
- backups enabled at the Hetzner server level;
- no customer secrets in Terraform state or in Git.

## Current status

This is ready for **plan/apply after a Hetzner Cloud API token is available**. Do not commit `.tfvars`, `.env`, private keys, or customer tokens.

## Prerequisites

Installed locally:

- `hcloud` CLI
- `tofu` / OpenTofu

A Hetzner Cloud project with:

- a Cloud API token;
- an SSH public key for server access;
- a confirmed billing account.

## Token handling

Use an environment variable for the Hetzner token. Do not put it in Git:

```bash
export TF_VAR_hcloud_token="..."
```

## Minimal workflow

```bash
cd infra/hetzner
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars locally; never commit it
tofu init
tofu fmt -check
tofu validate
tofu plan
```

Only run `tofu apply` after Bernard explicitly confirms the resulting monthly cost and server plan.

## Recommended MVP defaults

- Start with the CX32-class managed node from the capacity model.
- Cap the node at 10 paying bots until measured.
- Keep staging/test separate from production.
- Move heavy or privacy-sensitive customers to the Dedicated plan.

## What this does not do yet

This scaffold does **not** yet deploy the final onboarding backend, payment webhooks, encrypted secret store, or real Hermes/OpenClaw worker image. It prepares the infrastructure pattern so those pieces can be added cleanly.
