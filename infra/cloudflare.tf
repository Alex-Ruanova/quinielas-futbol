locals {
  # Un solo nivel de subdominio: el certificado universal de Cloudflare no
  # cubre sub-subdominios (api.nexutest.x requeriria un cert dedicado).
  app_hostname = "${var.subdomain}.${var.domain}"
  api_hostname = "${var.subdomain}-api.${var.domain}"
}

data "cloudflare_zone" "main" {
  name = var.domain
}

# ── Tunel: el sidecar cloudflared del task lo conecta HACIA Cloudflare ──────
# (solo egreso: no requiere ningun puerto abierto en el security group)

resource "random_id" "tunnel_secret" {
  byte_length = 35
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "backend" {
  account_id = data.cloudflare_zone.main.account_id
  name       = "${var.project}-backend"
  secret     = random_id.tunnel_secret.b64_std
  config_src = "cloudflare"
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "backend" {
  account_id = data.cloudflare_zone.main.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.backend.id

  config {
    ingress_rule {
      hostname = local.api_hostname
      service  = "http://localhost:${var.backend_port}"
    }
    ingress_rule {
      service = "http_status:404"
    }
  }
}

resource "aws_secretsmanager_secret" "tunnel_token" {
  name                    = "${var.project}/tunnel-token"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "tunnel_token" {
  secret_id     = aws_secretsmanager_secret.tunnel_token.id
  secret_string = cloudflare_zero_trust_tunnel_cloudflared.backend.tunnel_token
}

# ── DNS ──────────────────────────────────────────────────────────────────────

resource "cloudflare_record" "api" {
  zone_id = data.cloudflare_zone.main.id
  name    = "${var.subdomain}-api"
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.backend.id}.cfargotunnel.com"
  proxied = true
}

resource "cloudflare_record" "app" {
  zone_id = data.cloudflare_zone.main.id
  name    = var.subdomain
  type    = "CNAME"
  content = aws_s3_bucket_website_configuration.frontend.website_endpoint
  proxied = true
}
