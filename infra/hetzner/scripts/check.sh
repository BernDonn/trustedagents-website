#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

command -v hcloud >/dev/null || { echo "Missing hcloud CLI"; exit 1; }
command -v tofu >/dev/null || { echo "Missing tofu/OpenTofu"; exit 1; }

if [[ -z "${TF_VAR_hcloud_token:-}" ]]; then
  echo "Missing TF_VAR_hcloud_token. Export it locally; do not commit it."
  exit 1
fi

if [[ ! -f terraform.tfvars ]]; then
  echo "Missing terraform.tfvars. Copy terraform.tfvars.example and edit it locally."
  exit 1
fi

tofu fmt -check
tofu init -input=false
tofu validate

echo "Local Hetzner scaffold checks passed. Run 'tofu plan' next."
