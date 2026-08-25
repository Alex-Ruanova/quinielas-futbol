terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.52"
    }
  }
}

provider "aws" {
  region = var.region
}

# Token con permisos Tunnel:Edit + DNS:Edit + Zone:Read sobre la zona,
# git-ignorado en la raiz del repo.
provider "cloudflare" {
  api_token = trimspace(file("${path.module}/../.cloudflare-token"))
}
