output "managed_node_name" {
  description = "Created managed node name."
  value       = hcloud_server.managed_node.name
}

output "managed_node_plan" {
  description = "Hetzner server type used for the managed node."
  value       = var.server_type
}

output "agent_capacity_cap" {
  description = "Initial operational cap for paying bot workers."
  value       = var.agent_capacity_cap
}
