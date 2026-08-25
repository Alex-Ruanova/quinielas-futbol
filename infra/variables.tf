variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "quinielas"
}

variable "domain" {
  type    = string
  default = "norvaru.com"
}

# Un solo nivel de subdominio: el certificado universal de Cloudflare no cubre
# sub-subdominios (api.nexutest.norvaru.com requeriria un cert dedicado).
variable "subdomain" {
  description = "Subdominio de la app. La API cuelga de '<subdomain>-api'."
  type        = string
  default     = "nexutest"
}

variable "backend_port" {
  description = "Puerto de uvicorn dentro del task. Solo lo alcanza el sidecar."
  type        = number
  default     = 8000
}

variable "budget_email" {
  description = "Email que recibe las alertas de presupuesto"
  type        = string
}

variable "budget_limit_usd" {
  type    = number
  default = 50
}
