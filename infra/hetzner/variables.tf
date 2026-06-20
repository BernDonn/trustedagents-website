variable "hcloud_token" {
  description = "Hetzner Cloud API token. Pass via TF_VAR_hcloud_token; never commit it."
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Short project prefix for resources."
  type        = string
  default     = "trusted-agents"
}

variable "environment" {
  description = "Environment label."
  type        = string
  default     = "staging"
}

variable "location" {
  description = "Hetzner location slug. Keep this in a European region."
  type        = string
  default     = "fsn1"
}

variable "server_type" {
  description = "Managed node size. CX33 is the first production-like MVP default from the capacity model."
  type        = string
  default     = "cx33"
}

variable "image" {
  description = "Base OS image."
  type        = string
  default     = "ubuntu-24.04"
}

variable "ssh_public_key" {
  description = "SSH public key allowed to access the node."
  type        = string
}

variable "admin_cidrs" {
  description = "CIDR ranges allowed for administration. Keep narrow."
  type        = list(string)
}

variable "enable_backups" {
  description = "Enable Hetzner automatic server backups."
  type        = bool
  default     = true
}

variable "agent_capacity_cap" {
  description = "Initial operational cap for paying bot workers on this node."
  type        = number
  default     = 10
}
