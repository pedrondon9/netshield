output "droplet_ip" {
  description = "IP pública del Droplet"
  value       = data.digitalocean_droplet.server.ipv4_address
}

output "api_url" {
  description = "URL de la API"
  value       = "http://${data.digitalocean_droplet.server.ipv4_address}:8000"
}

output "mlflow_url" {
  description = "URL del servidor MLflow"
  value       = "http://${data.digitalocean_droplet.server.ipv4_address}:5000"
}

output "ssh_comando" {
  description = "Comando para conectarse al servidor"
  value       = "ssh root@${data.digitalocean_droplet.server.ipv4_address}"
}

output "spaces_datos" {
  description = "Bucket Spaces de datos"
  value       = digitalocean_spaces_bucket.datos.bucket_domain_name
}

output "spaces_modelos" {
  description = "Bucket Spaces de modelos"
  value       = digitalocean_spaces_bucket.modelos.bucket_domain_name
}
