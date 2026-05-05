terraform {
  required_version = ">= 1.5"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  # Estado remoto en DO Spaces — crear el bucket "netshield-tf-state" manualmente una sola vez
  # antes del primer terraform init. Las credenciales se pasan vía -backend-config en cd.yml.
  backend "s3" {
    bucket                      = "netshield-tf-state"
    key                         = "prod/terraform.tfstate"
    region                      = "us-east-1"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    force_path_style            = true
  }
}

provider "digitalocean" {
  token             = var.do_token
  spaces_access_id  = var.spaces_access_id
  spaces_secret_key = var.spaces_secret_key
}

# ── Container Registry ────────────────────────────────────────────────────────

resource "digitalocean_container_registry" "netshield" {
  name                   = var.nombre_proyecto
  subscription_tier_slug = "basic"
  region                 = var.do_region
}

# ── Referencia al Droplet existente ──────────────────────────────────────────

data "digitalocean_droplet" "server" {
  name = var.droplet_name
}

# ── Spaces: datos y artefactos MLflow ────────────────────────────────────────

resource "digitalocean_spaces_bucket" "datos" {
  name   = "${var.nombre_proyecto}-data-${var.entorno}"
  region = var.do_region
  acl    = "private"
  versioning { enabled = true }
}

resource "digitalocean_spaces_bucket" "modelos" {
  name   = "${var.nombre_proyecto}-models-${var.entorno}"
  region = var.do_region
  acl    = "private"
  versioning { enabled = true }
}

# ── Firewall aplicado al Droplet existente ────────────────────────────────────

resource "digitalocean_firewall" "netshield" {
  name        = "${var.nombre_proyecto}-${var.entorno}"
  droplet_ids = [data.digitalocean_droplet.server.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  inbound_rule {
    protocol         = "tcp"
    port_range       = "8000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # MLflow — restringir a IPs de confianza en prod
  inbound_rule {
    protocol         = "tcp"
    port_range       = "5000"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# ── Alertas de monitoreo ──────────────────────────────────────────────────────

resource "digitalocean_monitor_alert" "cpu_alta" {
  alerts {
    email = [var.email_alertas]
  }
  window      = "5m"
  type        = "v1/insights/droplet/cpu"
  compare     = "GreaterThan"
  value       = 85
  enabled     = true
  description = "${var.nombre_proyecto}: CPU supera el 85%"
  entities    = [data.digitalocean_droplet.server.id]
}

resource "digitalocean_monitor_alert" "memoria_alta" {
  alerts {
    email = [var.email_alertas]
  }
  window      = "5m"
  type        = "v1/insights/droplet/memory_utilization_percent"
  compare     = "GreaterThan"
  value       = 90
  enabled     = true
  description = "${var.nombre_proyecto}: Memoria supera el 90%"
  entities    = [data.digitalocean_droplet.server.id]
}

resource "digitalocean_monitor_alert" "disco_alto" {
  alerts {
    email = [var.email_alertas]
  }
  window      = "5m"
  type        = "v1/insights/droplet/disk_utilization_percent"
  compare     = "GreaterThan"
  value       = 80
  enabled     = true
  description = "${var.nombre_proyecto}: Disco supera el 80%"
  entities    = [data.digitalocean_droplet.server.id]
}
