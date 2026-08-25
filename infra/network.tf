# MVP sobre la VPC default (subnets publicas, sin NAT — el task usa IP publica).
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "backend" {
  name        = "${var.project}-backend"
  description = "Fargate backend"
  vpc_id      = data.aws_vpc.default.id

  # Sin ingreso: el trafico entra por el tunel de Cloudflare (solo-egreso).
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project}-rds"
  description = "RDS Postgres - solo desde el backend"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Postgres desde Fargate"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
