variable "do_token" {
  description = "Token de API de DigitalOcean (cloud.digitalocean.com/account/api/tokens)"
  type        = string
  sensitive   = true
}

variable "spaces_access_id" {
  description = "Access Key ID para DO Spaces (cloud.digitalocean.com/account/api/spaces-keys)"
  type        = string
  sensitive   = true
}

variable "spaces_secret_key" {
  description = "Secret Key para DO Spaces"
  type        = string
  sensitive   = true
}

variable "droplet_name" {
  description = "Nombre exacto del Droplet existente en DigitalOcean"
  type        = string
}

variable "do_region" {
  description = "Región del Droplet: ams3, fra1, nyc3... (debe coincidir con la del Droplet)"
  type        = string
}

variable "nombre_proyecto" {
  description = "Prefijo para los recursos nuevos (registry, buckets, firewall)"
  type        = string
  default     = "netshield"
}

variable "entorno" {
  description = "Entorno: dev | staging | prod"
  type        = string
  default     = "dev"
}

variable "email_alertas" {
  description = "Email para recibir alertas de monitoreo"
  type        = string
  sensitive   = true
}
