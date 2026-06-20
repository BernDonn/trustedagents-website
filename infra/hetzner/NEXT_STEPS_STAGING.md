# Next steps — Hetzner staging

Goal: create the first Trusted Agents staging node on Hetzner Cloud using the CX32 plan.

## 1. Create or select a Hetzner Cloud project

In Hetzner Console:

1. Log in to Hetzner Console.
2. Go to Cloud.
3. Create/select a project for Trusted Agents staging.
4. A clear project name is recommended, for example `trusted-agents-staging`.

## 2. Generate a Cloud API token

Inside that Hetzner Cloud project:

1. Open **Security**.
2. Open **API tokens**.
3. Click **Generate API token**.
4. Name it something recognizable, for example `trusted-agents-staging-provisioner`.
5. Choose **Read & Write** because provisioning must create and manage resources.
6. Copy the token once. Hetzner will not show it again.

Do not paste the token into chat. Use one of the safe handoff methods below.

## 3. Safe token handoff

Preferred local method:

```bash
cd /Users/bernarddonners/Desktop/TrustedAgents-website-prototype/infra/hetzner
export TF_VAR_hcloud_token='PASTE_TOKEN_HERE'
```

Then tell Eva: "token staat in de terminal".

Alternative: save it in a local password manager and paste only when Eva is ready to run the plan. Never commit it.

## 4. What Eva will do after the token is available

1. Prepare local `terraform.tfvars` from `terraform.tfvars.example`.
2. Fill staging defaults:
   - environment: `staging`
   - server type: `cx32`
   - backups enabled
   - capacity cap: `10`
3. Add an admin public key.
4. Restrict admin access.
5. Run:
   - `tofu fmt -check`
   - `tofu validate`
   - `tofu plan`
6. Show the plan summary and cost/risk checkpoint.
7. Only run `tofu apply` after explicit approval.

## 5. Important

The API token is needed for both staging and production. Staging is just the safer first environment where the provisioning flow can be tested before real customers are connected.
